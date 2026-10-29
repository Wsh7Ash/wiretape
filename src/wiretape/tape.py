"""The tape: an ordered, variable-driven sequence of exchanges and commands.

A tape is the artifact a hunter keeps. It records what was sent, what came back,
what was extracted from the reply and what the reply had to prove. Because it is
declarative JSON, a tape can be replayed by a human, by an agent, or by CI, and
the same file is what gets exported to curl, HAR or a report.

Why a tape instead of a proxy history: a proxy records what happened. A tape
records what must happen next, and fails loudly when the target disagrees.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .exchange import RawRequest

VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
KINDS = ("request", "shell", "wait")
SCHEMA = 1


class TapeError(ValueError):
    """A tape that cannot be loaded, substituted or executed as written."""


def substitute(text: str, variables: dict[str, str], where: str = "") -> str:
    """Replace ``{{name}}`` references, refusing unknown ones.

    A missing variable must never degrade to an empty string: ``/users/{{id}}``
    silently becoming ``/users/`` is how a tape ends up testing the collection
    endpoint instead of the object.
    """

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in variables:
            where_text = f" in {where}" if where else ""
            raise TapeError(f"unknown variable {{{{{name}}}}}{where_text}")
        return str(variables[name])

    return VAR_RE.sub(replace, text)


def referenced_vars(value: Any) -> set[str]:
    """Every variable name referenced anywhere inside a JSON-ish value."""
    found: set[str] = set()
    if isinstance(value, str):
        found.update(VAR_RE.findall(value))
    elif isinstance(value, dict):
        for item in value.values():
            found |= referenced_vars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found |= referenced_vars(item)
    return found


def _headers(spec: Any) -> tuple[tuple[str, str], ...]:
    """Headers from a dict (value may be a list) or an ordered pair list."""
    if spec is None:
        return ()
    out: list[tuple[str, str]] = []
    if isinstance(spec, dict):
        for name, value in spec.items():
            if isinstance(value, (list, tuple)):
                out.extend((str(name), str(item)) for item in value)
            else:
                out.append((str(name), str(value)))
        return tuple(out)
    if isinstance(spec, (list, tuple)):
        for item in spec:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise TapeError(f"header entry must be a [name, value] pair: {item!r}")
            out.append((str(item[0]), str(item[1])))
        return tuple(out)
    raise TapeError("headers must be an object or a list of pairs")


@dataclass(frozen=True)
class Extract:
    """How to pull a value out of a response for later steps."""

    name: str
    source: str = "body"  # body | header | status | url
    pattern: str | None = None
    header: str | None = None
    group: int = 1
    required: bool = True

    def apply(self, status: int, headers: tuple[tuple[str, str], ...], body: str) -> str | None:
        if self.source == "status":
            return str(status)
        if self.source == "header":
            wanted = (self.header or "").lower()
            for name, value in headers:
                if name.lower() == wanted:
                    return value
            return None
        if self.source == "body":
            if not self.pattern:
                return None
            match = re.search(self.pattern, body, re.MULTILINE)
            if not match:
                return None
            try:
                return match.group(self.group)
            except IndexError:
                return match.group(0)
        raise TapeError(f"extract {self.name!r}: unknown source {self.source!r}")

    @classmethod
    def from_dict(cls, name: str, raw: Any) -> "Extract":
        if isinstance(raw, str):
            return cls(name=name, pattern=raw)
        if not isinstance(raw, dict):
            raise TapeError(f"extract {name!r} must be a string or an object")
        return cls(
            name=name,
            source=str(raw.get("from", "body")),
            pattern=raw.get("regex") or raw.get("pattern"),
            header=raw.get("header"),
            group=int(raw.get("group", 1)),
            required=bool(raw.get("required", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"from": self.source}
        if self.pattern:
            out["regex"] = self.pattern
        if self.header:
            out["header"] = self.header
        if self.group != 1:
            out["group"] = self.group
        if not self.required:
            out["required"] = False
        return out


@dataclass(frozen=True)
class Expect:
    """What the response has to prove for the step to pass."""

    status: tuple[int, ...] = ()
    contains: str | None = None
    absent: str | None = None
    regex: str | None = None

    @classmethod
    def from_dict(cls, raw: Any) -> "Expect":
        if not raw:
            return cls()
        if not isinstance(raw, dict):
            raise TapeError("expect must be an object")
        status = raw.get("status", ())
        if isinstance(status, int):
            statuses = (status,)
        else:
            statuses = tuple(int(item) for item in status)
        return cls(
            status=statuses,
            contains=raw.get("contains"),
            absent=raw.get("absent"),
            regex=raw.get("regex"),
        )

    def check(self, status: int, body: str) -> list[str]:
        """Return failed check names; empty means the step passed."""
        failures: list[str] = []
        if self.status and status not in self.status:
            failures.append(f"status {status} not in {sorted(self.status)}")
        if self.contains and self.contains not in body:
            failures.append(f"body lacks {self.contains!r}")
        if self.absent and self.absent in body:
            failures.append(f"body contains forbidden {self.absent!r}")
        if self.regex and not re.search(self.regex, body, re.MULTILINE):
            failures.append(f"body does not match /{self.regex}/")
        return failures

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.status:
            out["status"] = list(self.status)
        if self.contains:
            out["contains"] = self.contains
        if self.absent:
            out["absent"] = self.absent
        if self.regex:
            out["regex"] = self.regex
        return out


@dataclass(frozen=True)
class Step:
    """One unit of work: a request, a shell command, or a pause."""

    id: str
    name: str = ""
    kind: str = "request"
    origin: str | None = None
    request: RawRequest | None = None
    command: str | None = None
    seconds: float = 0.0
    timeout: float = 15.0
    expect: Expect = field(default_factory=Expect)
    extract: tuple[Extract, ...] = ()
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Step":
        if not isinstance(raw, dict):
            raise TapeError("each step must be an object")
        step_id = str(raw.get("id") or "").strip()
        if not step_id:
            raise TapeError("every step needs an id")
        kind = str(raw.get("kind", "request"))
        if kind not in KINDS:
            raise TapeError(f"step {step_id}: unknown kind {kind!r}")
        extract = tuple(
            Extract.from_dict(name, spec)
            for name, spec in dict(raw.get("extract") or {}).items()
        )
        common = dict(
            id=step_id,
            name=str(raw.get("name", "")),
            kind=kind,
            timeout=float(raw.get("timeout", 15.0)),
            expect=Expect.from_dict(raw.get("expect")),
            extract=extract,
            notes=str(raw.get("notes", "")),
        )
        if kind == "request":
            req = raw.get("request")
            if not isinstance(req, dict):
                raise TapeError(f"step {step_id}: request step needs a request object")
            body = req.get("body", "")
            request = RawRequest(
                method=str(req.get("method", "GET")).upper(),
                target=str(req.get("target", "/")),
                version=str(req.get("version", "HTTP/1.1")),
                headers=_headers(req.get("headers")),
                body=body.encode("utf-8") if isinstance(body, str) else bytes(body),
            )
            return cls(origin=raw.get("origin"), request=request, **common)
        if kind == "shell":
            command = raw.get("command")
            if not isinstance(command, str) or not command.strip():
                raise TapeError(f"step {step_id}: shell step needs a command")
            return cls(command=command, **common)
        return cls(seconds=float(raw.get("seconds", 0.5)), **common)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id, "kind": self.kind}
        if self.name:
            out["name"] = self.name
        if self.origin:
            out["origin"] = self.origin
        if self.request is not None:
            out["request"] = {
                "method": self.request.method,
                "target": self.request.target,
                "version": self.request.version,
                "headers": [[name, value] for name, value in self.request.headers],
                "body": self.request.body.decode("utf-8", "replace"),
            }
        if self.command:
            out["command"] = self.command
        if self.kind == "wait":
            out["seconds"] = self.seconds
        if self.timeout != 15.0:
            out["timeout"] = self.timeout
        if self.expect.to_dict():
            out["expect"] = self.expect.to_dict()
        if self.extract:
            out["extract"] = {item.name: item.to_dict() for item in self.extract}
        if self.notes:
            out["notes"] = self.notes
        return out


@dataclass(frozen=True)
class Tape:
    """A named, scoped sequence of steps."""

    name: str
    scope: tuple[str, ...]
    origin: str
    steps: tuple[Step, ...]
    variables: dict[str, str] = field(default_factory=dict)
    description: str = ""
    schema: int = SCHEMA

    @property
    def origin_host(self) -> str:
        host = urlsplit(self.origin).hostname
        if not host:
            raise TapeError(f"origin {self.origin!r} has no host")
        return host

    def in_scope(self, host: str) -> bool:
        host = host.lower().rstrip(".")
        return any(host == entry.lower().rstrip(".") for entry in self.scope)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Tape":
        if not isinstance(raw, dict):
            raise TapeError("tape must be a JSON object")
        schema = int(raw.get("schema", SCHEMA))
        if schema != SCHEMA:
            raise TapeError(f"unsupported tape schema {schema}")
        name = str(raw.get("name") or "untitled").strip()
        scope = raw.get("scope")
        if not isinstance(scope, list) or not scope:
            raise TapeError("tape needs a non-empty scope list of hostnames")
        origin = str(raw.get("origin") or f"https://{scope[0]}")
        steps_raw = raw.get("steps")
        if not isinstance(steps_raw, list) or not steps_raw:
            raise TapeError("tape needs at least one step")
        steps = tuple(Step.from_dict(step) for step in steps_raw)
        ids = [step.id for step in steps]
        duplicates = {step_id for step_id in ids if ids.count(step_id) > 1}
        if duplicates:
            raise TapeError("duplicate step ids: " + ", ".join(sorted(duplicates)))
        variables = {str(k): str(v) for k, v in dict(raw.get("variables") or {}).items()}
        return cls(
            name=name,
            scope=tuple(str(item) for item in scope),
            origin=origin,
            steps=steps,
            variables=variables,
            description=str(raw.get("description", "")),
            schema=schema,
        )

    @classmethod
    def load(cls, path: str | Path) -> "Tape":
        data = Path(path).read_text(encoding="utf-8")
        try:
            raw = json.loads(data)
        except json.JSONDecodeError as exc:
            raise TapeError(f"{path}: invalid JSON: {exc}") from exc
        return cls.from_dict(raw)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "name": self.name,
            "description": self.description,
            "origin": self.origin,
            "scope": list(self.scope),
            "variables": dict(self.variables),
            "steps": [step.to_dict() for step in self.steps],
        }

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return target


def lint_tape(tape: Tape) -> list[str]:
    """Static problems worth fixing before a run costs packets."""
    problems: list[str] = []
    if not tape.scope:
        problems.append("scope is empty")
    for step in tape.steps:
        if step.kind != "request" or step.request is None:
            continue
        origin = step.origin or tape.origin
        host = urlsplit(origin).hostname or ""
        if not tape.in_scope(host):
            problems.append(f"{step.id}: origin host {host!r} is not in scope")
        if step.request.header("host") and step.request.header("host") not in (None, host):
            problems.append(
                f"{step.id}: Host header {step.request.header('host')!r} differs from origin {host!r}"
            )
        if step.request.method in ("POST", "PUT", "PATCH") and not step.request.body:
            problems.append(f"{step.id}: {step.request.method} with an empty body")
        for item in step.extract:
            if item.source == "body" and not item.pattern:
                problems.append(f"{step.id}: extract {item.name!r} needs a regex")
            if item.source == "header" and not item.header:
                problems.append(f"{step.id}: extract {item.name!r} needs a header name")
            if item.pattern:
                try:
                    re.compile(item.pattern)
                except re.error as exc:
                    problems.append(f"{step.id}: extract {item.name!r} bad regex: {exc}")
        if step.expect.regex:
            try:
                re.compile(step.expect.regex)
            except re.error as exc:
                problems.append(f"{step.id}: expect.regex invalid: {exc}")
    produced: set[str] = set(tape.variables)
    for step in tape.steps:
        for name in sorted(referenced_vars(step.to_dict())):
            if name not in produced:
                problems.append(f"{step.id}: variable {{{{{name}}}}} is never produced")
        produced.update(item.name for item in step.extract)
    return problems
