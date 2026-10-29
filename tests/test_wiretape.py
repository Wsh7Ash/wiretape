"""Behavioural tests: real sockets against a local server, no network."""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wiretape.exchange import RawRequest, RawResponse, send  # noqa: E402
from wiretape.exporters import export, export_curl, export_har  # noqa: E402
from wiretape.redact import redact, redact_headers  # noqa: E402
from wiretape.runner import run_tape  # noqa: E402
from wiretape.tape import Tape, TapeError, lint_tape, substitute  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    """A tiny target: tokens, cookies, a 403 and an echo."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args: object) -> None:  # silence test noise
        return

    def _body(self) -> bytes:
        length = int(self.headers.get("content-length") or 0)
        return self.rfile.read(length) if length else b""

    def _respond(self, status: int, body: bytes, headers: list[tuple[str, str]] | None = None) -> None:
        self.send_response(status)
        for name, value in headers or []:
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/orders/404"):
            self._respond(404, b'{"error":"not_found"}')
        elif self.path.startswith("/orders/"):
            order_id = self.path.rsplit("/", 1)[-1]
            self._respond(200, json.dumps({"id": order_id, "status": "created"}).encode())
        elif self.path.startswith("/admin"):
            self._respond(403, b'{"error":"forbidden","detail":"role required"}')
        elif self.path.startswith("/session"):
            body = b'{"access_token":"tok-live-123456","user":"alice"}'
            self._respond(
                200,
                body,
                [("Set-Cookie", "sid=s3cr3t-session; Path=/; HttpOnly")],
            )
        else:
            self._respond(200, b'{"ok":true,"path":"' + self.path.encode() + b'"}')

    def do_POST(self) -> None:  # noqa: N802
        body = self._body()
        self._respond(201, b'{"id":"order-42","echo":' + json.dumps(body.decode()).encode() + b"}")

    def do_DELETE(self) -> None:  # noqa: N802
        if "404" in self.path:
            self._respond(404, b'{"error":"not_found"}')
        else:
            self._respond(204, b"")


@pytest.fixture(scope="module")
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    yield f"http://{host}:{port}", host, port
    httpd.shutdown()
    httpd.server_close()


def _request(method: str = "GET", target: str = "/orders/42", headers=(), body: bytes = b"") -> RawRequest:
    return RawRequest(method, target, "HTTP/1.1", headers, body)


# ------------------------------------------------------------------ exchange


def test_parse_preserves_header_order_and_duplicates() -> None:
    raw = (
        b"GET /x HTTP/1.1\r\nHost: a.test\r\nX-Forwarded-For: 10.0.0.1\r\n"
        b"X-Forwarded-For: 127.0.0.1\r\nCookie: a=1\r\n\r\n"
    )
    request = RawRequest.parse(raw)
    assert [name for name, _ in request.headers] == [
        "Host",
        "X-Forwarded-For",
        "X-Forwarded-For",
        "Cookie",
    ]
    assert request.to_bytes() .count(b"X-Forwarded-For") == 2


def test_parse_request_preserves_body_bytes() -> None:
    raw = b"POST /v1/orders HTTP/1.1\r\nContent-Length: 9\r\n\r\n{\"a\": 1}"
    request = RawRequest.parse(raw)
    assert request.body == b'{"a": 1}'
    assert b'{"a": 1}' in request.to_bytes()


def test_parse_rejects_bad_message() -> None:
    with pytest.raises(Exception):
        RawRequest.parse(b"NOT A REQUEST\r\n\r\n")
    with pytest.raises(Exception):
        RawRequest.parse(b"GET /x HTTP/1.1\r\nbadheader\r\n\r\n")


def test_parse_response_and_accessors() -> None:
    raw = b"HTTP/1.1 301 Moved\r\nLocation: https://elsewhere.test/\r\nContent-Length: 0\r\n\r\n"
    response = RawResponse.parse(raw)
    assert response.status == 301
    assert response.header("location") == "https://elsewhere.test/"
    assert response.text == ""


def test_send_records_digests_and_status(server) -> None:
    origin, host, port = server
    exchange = send(_request(headers=(("Accept", "application/json"),)), host=host, port=port, scheme="http")
    assert exchange.ok
    assert exchange.response is not None and exchange.response.status == 200
    assert '"id": "42"' in exchange.response.text
    assert exchange.sent_bytes.startswith(b"GET /orders/42 HTTP/1.1")
    assert b"Host: 127.0.0.1:" in exchange.sent_bytes


def test_send_does_not_follow_redirects(server) -> None:
    _, host, port = server
    exchange = send(_request(target="/session"), host=host, port=port, scheme="http")
    assert exchange.response is not None and exchange.response.status == 200
    assert exchange.response.header("set-cookie").startswith("sid=")


# ---------------------------------------------------------------------- tape


def _tape(origin: str, steps: list[dict]) -> Tape:
    return Tape.from_dict(
        {
            "schema": 1,
            "name": "order-flow",
            "origin": origin,
            "scope": ["127.0.0.1"],
            "variables": {},
            "steps": steps,
        }
    )


def test_substitute_refuses_unknown_variable() -> None:
    assert substitute("/orders/{{id}}", {"id": "42"}) == "/orders/42"
    with pytest.raises(TapeError, match="unknown variable"):
        substitute("/orders/{{missing}}", {})


def test_run_tape_extracts_and_asserts(server) -> None:
    origin, _, _ = server
    tape = _tape(
        origin,
        [
            {
                "id": "login",
                "request": {"method": "GET", "target": "/session"},
                "extract": {"token": {"from": "body", "regex": '"access_token":"([^"]+)"'}},
                "expect": {"status": [200], "contains": "alice"},
            },
            {
                "id": "read-own",
                "request": {
                    "method": "GET",
                    "target": "/orders/42",
                    "headers": {"Authorization": "Bearer {{token}}"},
                },
                "extract": {"created_id": {"from": "body", "regex": '"id": "([^"]+)"'}},
                "expect": {"status": [200], "contains": "created"},
            },
            {
                "id": "cleanup",
                "request": {"method": "DELETE", "target": "/orders/{{created_id}}"},
                "expect": {"status": [204]},
            },
            {
                "id": "read-admin",
                "request": {"method": "GET", "target": "/admin"},
                "expect": {"status": [403], "contains": "role required"},
            },
        ],
    )
    report = run_tape(tape)
    assert report.passed, [r.failures or r.error for r in report.results]
    assert report.results[0].extracted["token"] == "tok-live-123456"
    assert report.results[1].extracted["created_id"] == "42"
    assert report.results[1].status == 200
    assert report.results[2].status == 204
    assert report.results[3].status == 403


def test_run_tape_fails_when_expectation_is_wrong(server) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "admin-should-pass", "request": {"method": "GET", "target": "/admin"}, "expect": {"status": [200]}}])
    report = run_tape(tape)
    assert not report.passed
    assert "status 403 not in [200]" in report.results[0].failures[0]


def test_run_tape_refuses_out_of_scope_host() -> None:
    tape = Tape.from_dict(
        {
            "name": "scoped",
            "origin": "https://api.example.test",
            "scope": ["api.example.test"],
            "steps": [
                {
                    "id": "elsewhere",
                    "origin": "https://other.example.test",
                    "request": {"method": "GET", "target": "/"},
                }
            ],
        }
    )
    report = run_tape(tape)
    assert not report.passed
    assert "not in tape scope" in (report.results[0].error or "")
    assert report.results[0].sent == b""


def test_run_tape_refuses_shell_without_flag(server, tmp_path) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "cmd", "kind": "shell", "command": "echo hello-from-tape"}])
    report = run_tape(tape)
    assert not report.passed
    assert "refused" in (report.results[0].error or "")


def test_run_tape_runs_shell_with_flag_and_captures_output(server) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "cmd", "kind": "shell", "command": "echo hello-from-tape"}])
    report = run_tape(tape, allow_shell=True)
    assert report.passed
    assert "hello-from-tape" in report.results[0].stdout
    assert report.results[0].returncode == 0


def test_run_tape_reports_command_failure(server) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "cmd", "kind": "shell", "command": "exit 3"}])
    report = run_tape(tape, allow_shell=True)
    assert not report.passed
    assert report.results[0].returncode == 3


def test_dry_run_sends_nothing(server, tmp_path) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "read", "request": {"method": "GET", "target": "/orders/1"}}])
    report = run_tape(tape, dry_run=True, capture_dir=tmp_path / "cap")
    assert report.passed
    assert report.results[0].status is None
    assert report.results[0].skipped == "dry run"


def test_capture_writes_raw_exchanges(server, tmp_path) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "read", "request": {"method": "GET", "target": "/orders/7"}}])
    report = run_tape(tape, capture_dir=tmp_path / "cap")
    assert report.passed
    assert (tmp_path / "cap" / "read.request.http").read_bytes().startswith(b"GET /orders/7")
    assert b'"id": "7"' in (tmp_path / "cap" / "read.response.http").read_bytes()
    payload = json.loads((tmp_path / "cap" / "run.json").read_text(encoding="utf-8"))
    assert payload["passed"] is True


def test_lint_flags_unknown_variable_and_bad_scope() -> None:
    tape = Tape.from_dict(
        {
            "name": "lintme",
            "origin": "https://api.example.test",
            "scope": ["api.example.test"],
            "steps": [
                {
                    "id": "one",
                    "request": {"method": "GET", "target": "/a/{{nope}}"},
                }
            ],
        }
    )
    problems = lint_tape(tape)
    assert any("never produced" in problem for problem in problems)

    outside = Tape.from_dict(
        {
            "name": "outside",
            "origin": "https://api.example.test",
            "scope": ["api.example.test"],
            "steps": [{"id": "two", "origin": "https://evil.test", "request": {"method": "GET", "target": "/"}}],
        }
    )
    assert any("not in scope" in problem for problem in lint_tape(outside))


# -------------------------------------------------------------------- redact


def test_redact_covers_headers_params_and_bodies() -> None:
    text = (
        "Authorization: Bearer abcdefghijklmnop\n"
        "Cookie: sid=secretvalue\n"
        "GET /x?token=abc123&safe=1 HTTP/1.1\n"
        '{"access_token": "tok-live-123456", "user": "alice"}'
    )
    out = redact(text)
    assert "abcdefghijklmnop" not in out
    assert "secretvalue" not in out
    assert "abc123" not in out
    assert "tok-live-123456" not in out
    assert "alice" in out
    assert "safe=1" in out


def test_redact_headers_preserves_order_and_duplicates() -> None:
    headers = (("Host", "a.test"), ("Cookie", "sid=1"), ("Cookie", "other=2"), ("X-Trace", "abc"))
    out = redact_headers(headers)
    assert [name for name, _ in out] == ["Host", "Cookie", "Cookie", "X-Trace"]
    assert out[1][1] == out[2][1] == "<redacted>"


# ----------------------------------------------------------------- exporters


def test_curl_export_is_runnable_and_redacted(server) -> None:
    origin, _, _ = server
    tape = _tape(
        origin,
        [
            {
                "id": "write",
                "request": {
                    "method": "DELETE",
                    "target": "/orders/9",
                    "headers": [["Authorization", "Bearer live-token-value"], ["X-Dup", "1"], ["X-Dup", "2"]],
                },
            }
        ],
    )
    script = export_curl(tape)
    assert "--path-as-is" in script
    assert "--request DELETE" in script
    assert "live-token-value" not in script
    assert script.count("--header") == 3


def test_har_export_shape(server, tmp_path) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "read", "request": {"method": "GET", "target": "/orders/1?token=abc123"}}])
    report = run_tape(tape)
    har = export_har(tape, report)
    entry = har["log"]["entries"][0]
    assert entry["request"]["method"] == "GET"
    assert entry["response"]["status"] == 200
    assert entry["request"]["queryString"][0]["value"] == "<redacted>"
    assert har["log"]["version"] == "1.2"


def test_markdown_and_raw_export(server) -> None:
    origin, _, _ = server
    tape = _tape(origin, [{"id": "read", "request": {"method": "GET", "target": "/orders/1"}}])
    report = run_tape(tape)
    markdown = export("markdown", tape, report)
    assert "| `read` | request | 200 | `/orders/1` | PASS |" in markdown
    raw = export("raw", tape, report)
    assert raw.startswith("GET /orders/1 HTTP/1.1")


def test_export_rejects_unknown_target() -> None:
    tape = Tape.from_dict({"name": "x", "origin": "https://a.test", "scope": ["a.test"], "steps": [{"id": "s", "request": {"method": "GET", "target": "/"}}]})
    with pytest.raises(ValueError):
        export("nope", tape)
