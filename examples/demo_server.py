"""A tiny local target so the demo tape can be rehearsed without a network.

    python examples/demo_server.py 8080

Endpoints:
    GET  /session          -> {access_token, user} plus a Set-Cookie header
    GET  /orders/{id}      -> the order, if the bearer token is present
    GET  /admin            -> 403 always (the "bug" is not here)
    DELETE /orders/{id}    -> 204, or 404 for an unknown id
"""

from __future__ import annotations

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = "demo-token-not-a-real-secret"
ORDERS = {"42": {"id": "42", "status": "created", "total": 19}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n")

    def _json(self, status: int, payload: dict, headers: list[tuple[str, str]] | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        for name, value in headers or []:
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorised(self) -> bool:
        return (self.headers.get("authorization") or "") == f"Bearer {TOKEN}"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/session":
            self._json(
                200,
                {"access_token": TOKEN, "user": "demo-hunter"},
                [("Set-Cookie", "sid=demo-session-value; Path=/; HttpOnly")],
            )
            return
        if self.path == "/admin":
            self._json(403, {"error": "forbidden", "detail": "role required"})
            return
        match = re.fullmatch(r"/orders/([^/?]+)", self.path)
        if match:
            if not self._authorised():
                self._json(401, {"error": "unauthorised"})
                return
            order = ORDERS.get(match.group(1))
            if order is None:
                self._json(404, {"error": "not_found"})
                return
            self._json(200, order)
            return
        self._json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        match = re.fullmatch(r"/orders/([^/?]+)", self.path)
        if match and match.group(1) in ORDERS:
            ORDERS.pop(match.group(1))
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._json(404, {"error": "not_found"})


def main(argv: list[str]) -> int:
    port = int(argv[1]) if len(argv) > 1 else 8080
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"demo target on http://127.0.0.1:{port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
