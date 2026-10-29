"""Execute a tape: requests, extractions, assertions and (gated) commands.

Three safety properties are enforced here rather than documented and hoped for:

1. **Scope** — a request whose resolved host is not listed in ``tape.scope`` is
   refused before a socket is opened.
2. **Shell** — shell steps do not run unless the caller passes
   ``allow_shell=True``. A tape is data, and data should not be able to execute
   commands just because an agent loaded it.
3. **Redaction** — anything returned for printing or exporting goes through
   :mod:`wiretape.redact` first.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .exchange import ExchangeError, RawRequest, send
from .redact import redact
from .tape import Step, Tape, TapeError, substitute


@dataclass
class StepResult:
    """What one step did, and whether it did what the tape claimed."""

    id: str
    kind: str
    name: str = ""
    ok: bool = False
    status: int | None = None
    elapsed_ms: float = 0.0
    request_digest: str = ""
    response_digest: str = ""
    failures: list[str] = field(default_factory=list)
    extracted: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    body_text: str = ""
    headers: tuple[tuple[str, str], ...] = ()
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    skipped: str | None = None
    sent: bytes = b""
    received: bytes = b""

    def public(self) -> dict[str, Any]:
        """A redacted view safe to print, log or export."""
        payload: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "ok": self.ok,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }
        if self.status is not None:
            payload["status"] = self.status
        if self.request_digest:
            payload["request_sha256"] = self.request_digest
        if self.response_digest:
            payload["response_sha256"] = self.response_digest
        if self.failures:
            payload["failures"] = [redact(item) for item in self.failures]
        if self.extracted:
            payload["extracted"] = {k: redact(v) for k, v in self.extracted.items()}
        if self.error:
            payload["error"] = redact(self.error)
        if self.skipped:
            payload["skipped"] = redact(self.skipped)
        if self.command:
            payload["command"] = redact(self.command)
        if self.returncode is not None:
            payload["returncode"] = self.returncode
        if self.stdout:
            payload["stdout"] = redact(self.stdout[-4000:])
        if self.stderr:
            payload["stderr"] = redact(self.stderr[-2000:])
        if self.body_text:
            payload["body_preview"] = redact(self.body_text[:2000])
        return payload


@dataclass
class RunReport:
    tape: str
    origin: str
    scope: tuple[str, ...]
    results: list[StepResult] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(result.ok for result in self.results)

    @property
    def failed(self) -> list[StepResult]:
        return [result for result in self.results if not result.ok]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tape": self.tape,
            "origin": self.origin,
            "scope": list(self.scope),
            "passed": self.passed,
            "steps": [result.public() for result in self.results],
            "variables": {k: redact(v) for k, v in self.variables.items()},
        }


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _substitute_request(request: RawRequest, variables: dict[str, str], step_id: str) -> RawRequest:
    headers = tuple(
        (
            substitute(name, variables, f"{step_id} header name"),
            substitute(value, variables, f"{step_id} header {name}"),
        )
        for name, value in request.headers
    )
    body = substitute(request.body.decode("utf-8", "replace"), variables, f"{step_id} body")
    return RawRequest(
        method=request.method,
        target=substitute(request.target, variables, f"{step_id} target"),
        version=request.version,
        headers=headers,
        body=body.encode("utf-8"),
    )


def _write_capture(directory: Path, step_id: str, result: StepResult) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if result.sent:
        (directory / f"{step_id}.request.http").write_bytes(result.sent)
    if result.received:
        (directory / f"{step_id}.response.http").write_bytes(result.received)


def run_tape(
    tape: Tape,
    *,
    allow_shell: bool = False,
    verify_tls: bool = True,
    fail_fast: bool = False,
    dry_run: bool = False,
    capture_dir: str | Path | None = None,
    on_step: Any = None,
) -> RunReport:
    """Walk the tape in order, carrying extracted variables forward."""
    variables = dict(tape.variables)
    report = RunReport(tape=tape.name, origin=tape.origin, scope=tape.scope)
    stop = False

    for step in tape.steps:
        result = StepResult(id=step.id, kind=step.kind, name=step.name)
        if stop:
            result.skipped = "earlier step failed (fail-fast)"
            report.results.append(result)
            continue

        if step.kind == "wait":
            if not dry_run:
                time.sleep(max(0.0, step.seconds))
            result.ok = True
            results_append(report, result, on_step)
            continue

        if step.kind == "shell":
            try:
                command = substitute(step.command or "", variables, f"{step.id} command")
            except TapeError as exc:
                result.error = str(exc)
                results_append(report, result, on_step)
                stop = stop or fail_fast
                continue
            result.command = command
            if dry_run:
                result.ok = True
                result.skipped = "dry run"
                results_append(report, result, on_step)
                continue
            if not allow_shell:
                result.error = "shell step refused: pass --allow-shell to run commands"
                results_append(report, result, on_step)
                stop = stop or fail_fast
                continue
            started = time.monotonic()
            try:
                completed = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=step.timeout,
                )
            except subprocess.TimeoutExpired:
                result.elapsed_ms = (time.monotonic() - started) * 1000
                result.error = f"command timed out after {step.timeout}s"
                results_append(report, result, on_step)
                stop = stop or fail_fast
                continue
            result.elapsed_ms = (time.monotonic() - started) * 1000
            result.stdout = completed.stdout or ""
            result.stderr = completed.stderr or ""
            result.returncode = completed.returncode
            result.ok = completed.returncode == 0
            if not result.ok:
                result.failures.append(f"command exited {completed.returncode}")
            results_append(report, result, on_step)
            stop = stop or (fail_fast and not result.ok)
            continue

        # ---------------------------------------------------------- request
        assert step.request is not None
        origin = substitute(step.origin or tape.origin, variables, f"{step.id} origin")
        host = urlsplit(origin).hostname or ""
        scheme = urlsplit(origin).scheme or "https"
        port = urlsplit(origin).port or (443 if scheme == "https" else 80)
        if not tape.in_scope(host):
            result.error = f"host {host!r} is not in tape scope ({', '.join(tape.scope)})"
            results_append(report, result, on_step)
            stop = stop or fail_fast
            continue
        if dry_run:
            # Variables produced by earlier steps have no value yet, so a dry run
            # checks routing and scope and leaves substitution to the real run.
            result.ok = True
            result.skipped = "dry run"
            results_append(report, result, on_step)
            continue
        try:
            request = _substitute_request(step.request, variables, step.id)
        except TapeError as exc:
            result.error = str(exc)
            results_append(report, result, on_step)
            stop = stop or fail_fast
            continue

        result.sent = request.to_bytes(port if port not in (80, 443) else None)
        result.request_digest = _digest(result.sent)

        exchange = send(
            request,
            host=host,
            port=port,
            scheme=scheme,
            timeout=step.timeout,
            verify_tls=verify_tls,
        )
        result.elapsed_ms = exchange.elapsed_ms
        result.received = exchange.received_bytes
        if exchange.error or exchange.response is None:
            result.error = exchange.error or "no response"
            results_append(report, result, on_step)
            stop = stop or fail_fast
            continue

        response = exchange.response
        result.status = response.status
        result.headers = response.headers
        result.body_text = response.text
        result.response_digest = _digest(exchange.received_bytes)

        result.failures.extend(step.expect.check(response.status, response.text))
        for item in step.extract:
            try:
                value = item.apply(response.status, response.headers, response.text)
            except TapeError as exc:
                result.failures.append(str(exc))
                continue
            if value is None:
                if item.required:
                    result.failures.append(f"could not extract {item.name!r}")
                continue
            result.extracted[item.name] = value
            variables[item.name] = value

        result.ok = not result.failures
        if capture_dir:
            _write_capture(Path(capture_dir), step.id, result)
        results_append(report, result, on_step)
        stop = stop or (fail_fast and not result.ok)

    report.variables = variables
    if capture_dir:
        Path(capture_dir).mkdir(parents=True, exist_ok=True)
        Path(capture_dir, "run.json").write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report


def results_append(report: RunReport, result: StepResult, on_step: Any) -> None:
    """Append a result and notify a caller-supplied progress hook."""
    report.results.append(result)
    if on_step is not None:
        on_step(result)
