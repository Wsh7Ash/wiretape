"""Export a tape or a run: curl, HAR 1.2, raw text and a markdown report.

Exports are the artifact that outlives the session. Three rules apply to all of
them:

- credentials are redacted, always, because an export is pasted somewhere;
- header order and duplicates are preserved, because that is often the bug;
- a replay command must be runnable as printed, so the origin is made absolute
  and the body is quoted exactly once.
"""

from __future__ import annotations

import json
import re
import shlex
from typing import Any

from .redact import redact
from .runner import RunReport, StepResult
from .tape import Step, Tape


def _url(origin: str, target: str) -> str:
    if target.startswith(("http://", "https://")):
        return target
    return origin.rstrip("/") + (target if target.startswith("/") else "/" + target)


def _variables(tape: Tape, report: RunReport | None) -> dict[str, str]:
    """Tape variables plus everything a run extracted, later values winning."""
    values = dict(tape.variables)
    if report is not None:
        for result in report.results:
            values.update(result.extracted)
    return values


def _fill(text: str, variables: dict[str, str]) -> str:
    """Replace known references and leave unknown ones visible as placeholders."""

    def replace(match: re.Match[str]) -> str:
        return variables.get(match.group(1), match.group(0))

    return re.sub(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}", replace, text)


def curl_for(
    step: Step,
    tape: Tape,
    *,
    redact_secrets: bool = True,
    variables: dict[str, str] | None = None,
) -> str:
    """One runnable curl command for a request step."""
    assert step.request is not None
    values = variables or {}
    url = _url(step.origin or tape.origin, _fill(step.request.target, values))
    parts = [
        "curl",
        "--silent",
        "--show-error",
        "--include",
        "--path-as-is",
        "--request",
        step.request.method,
        shlex.quote(url),
    ]
    for name, value in step.request.headers:
        shown = "<redacted>" if (redact_secrets and _is_secret(name)) else _fill(value, values)
        parts += ["--header", shlex.quote(f"{name}: {shown}")]
    body = _fill(step.request.body.decode("utf-8", "replace"), values)
    if body:
        if redact_secrets:
            body = redact(body)
        parts += ["--data-raw", shlex.quote(body)]
    return " ".join(parts)


def _is_secret(name: str) -> bool:
    from .redact import SECRET_HEADERS

    return name.lower() in SECRET_HEADERS


def export_curl(tape: Tape, *, include_shell: bool = True, report: RunReport | None = None) -> str:
    """A shell script that replays every request step in order.

    Values a run extracted are substituted, so the printed commands are the ones
    that actually worked rather than a template full of references.
    """
    values = _variables(tape, report)
    lines = [
        "#!/usr/bin/env bash",
        f"# replay of tape {tape.name!r} against {tape.origin}",
        "# credentials are redacted; fill them from your environment before running",
        "set -euo pipefail",
        "",
    ]
    for step in tape.steps:
        lines.append(f"# step {step.id}: {step.name or step.kind}")
        if step.kind == "request":
            lines.append(curl_for(step, tape, variables=values))
        elif step.kind == "shell" and include_shell:
            lines.append(f"# shell step (run manually): {step.command}")
        else:
            lines.append(f"# wait {step.seconds}s")
        lines.append("")
    return "\n".join(lines)


def _har_headers(headers: tuple[tuple[str, str], ...]) -> list[dict[str, str]]:
    return [{"name": name, "value": redact(value)} for name, value in headers]


def export_har(tape: Tape, report: RunReport | None = None) -> dict[str, Any]:
    """HAR 1.2, with the captured responses when a run is supplied."""
    by_id: dict[str, StepResult] = {}
    if report is not None:
        by_id = {result.id: result for result in report.results}
    entries: list[dict[str, Any]] = []
    for step in tape.steps:
        if step.kind != "request" or step.request is None:
            continue
        result = by_id.get(step.id)
        url = _url(step.origin or tape.origin, step.request.target)
        body = step.request.body.decode("utf-8", "replace")
        entry: dict[str, Any] = {
            "startedDateTime": "1970-01-01T00:00:00.000Z",
            "time": round(result.elapsed_ms, 2) if result else 0.0,
            "request": {
                "method": step.request.method,
                "url": redact(url),
                "httpVersion": step.request.version,
                "headers": _har_headers(step.request.headers),
                "queryString": _query_pairs(step.request.target),
                "headersSize": -1,
                "bodySize": len(step.request.body),
                "postData": {"mimeType": "text/plain", "text": redact(body)} if body else None,
            },
            "response": {
                "status": result.status if result and result.status is not None else 0,
                "statusText": "",
                "httpVersion": "HTTP/1.1",
                "headers": _har_headers(result.headers) if result else [],
                "content": {
                    "size": len(result.body_text) if result else 0,
                    "mimeType": _content_type(result) if result else "text/plain",
                    "text": redact(result.body_text[:100_000]) if result else "",
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": len(result.received) if result else 0,
            },
            "cache": {},
            "timings": {"send": 0, "wait": 0, "receive": 0},
            "comment": f"wiretape step {step.id}",
        }
        if entry["request"]["postData"] is None:
            del entry["request"]["postData"]
        entries.append(entry)
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "wiretape", "version": "1.0.0"},
            "pages": [
                {
                    "startedDateTime": "1970-01-01T00:00:00.000Z",
                    "id": "tape",
                    "title": tape.name,
                    "pageTimings": {"onContentLoad": -1, "onLoad": -1},
                }
            ],
            "entries": entries,
        }
    }


def _query_pairs(target: str) -> list[dict[str, str]]:
    from urllib.parse import parse_qsl, urlsplit

    from .redact import PLACEHOLDER, SECRET_PARAMS

    pairs = parse_qsl(urlsplit(target).query, keep_blank_values=True)
    return [
        {
            "name": name,
            "value": PLACEHOLDER if name.lower() in SECRET_PARAMS else redact(value),
        }
        for name, value in pairs
    ]


def _content_type(result: StepResult) -> str:
    for name, value in result.headers:
        if name.lower() == "content-type":
            return value
    return "text/plain"


def export_raw(report: RunReport) -> str:
    """Every exchange as raw HTTP, the format another tool can import."""
    chunks: list[str] = []
    for result in report.results:
        if result.sent:
            chunks.append(result.sent.decode("latin-1").replace("\r\n", "\n"))
        if result.received:
            chunks.append(result.received.decode("latin-1").replace("\r\n", "\n"))
    return redact("\n\n".join(chunks))


def export_markdown(tape: Tape, report: RunReport | None = None) -> str:
    """A report-ready table plus per-step evidence."""
    lines = [f"# Tape: {tape.name}", ""]
    if tape.description:
        lines += [tape.description, ""]
    lines += [f"- origin: `{tape.origin}`", f"- scope: {', '.join(f'`{h}`' for h in tape.scope)}", ""]
    lines += ["| Step | Kind | Status | Path | Result |", "|---|---|---|---|---|"]
    by_id = {result.id: result for result in report.results} if report else {}
    values = _variables(tape, report)
    for step in tape.steps:
        result = by_id.get(step.id)
        where = _fill(step.request.target, values) if step.request else (step.command or "")[:40]
        status = str(result.status) if result and result.status is not None else "-"
        verdict = "PASS" if result and result.ok else ("FAIL" if result else "not run")
        lines.append(f"| `{step.id}` | {step.kind} | {status} | `{redact(where)}` | {verdict} |")
    if report:
        failures = report.failed
        lines += ["", f"## Failures ({len(failures)})", ""]
        if not failures:
            lines.append("None: every step met its expectation.")
        for result in failures:
            lines.append(f"### `{result.id}`")
            for failure in result.failures:
                lines.append(f"- {redact(failure)}")
            if result.error:
                lines.append(f"- error: {redact(result.error)}")
            lines.append("")
        extracted = {
            name: value for result in report.results for name, value in result.extracted.items()
        }
        if extracted:
            lines += ["## Extracted variables", "", "| Name | Value |", "|---|---|"]
            for name, value in extracted.items():
                lines.append(f"| `{name}` | `{redact(value)}` |")
    return "\n".join(lines).rstrip() + "\n"


def export(kind: str, tape: Tape, report: RunReport | None = None) -> str:
    """Dispatch on a CLI ``--to`` value and always return text."""
    if kind == "curl":
        return export_curl(tape, report=report)
    if kind == "har":
        return json.dumps(export_har(tape, report), indent=2, ensure_ascii=False) + "\n"
    if kind == "markdown":
        return export_markdown(tape, report)
    if kind == "raw":
        if report is None:
            raise ValueError("raw export needs a run")
        return export_raw(report)
    raise ValueError(f"unknown export target {kind!r}")
