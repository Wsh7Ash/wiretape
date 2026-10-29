"""wiretape command line interface.

Domain commands (``send``, ``run``, ``lint``, ``steps``, ``export``) sit beside
the shared corpus commands (``validate``, ``list``, ``show``, ``search``,
``build``) that every pack in this series exposes, so an agent that learned one
pack can drive this one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .corpus import PACK, SKILLS
from .exchange import ExchangeError, RawRequest, send
from .exporters import export
from .model import Skill
from .redact import redact
from .render import build_pack, render_skill, word_count
from .runner import RunReport, run_tape
from .tape import Tape, TapeError, lint_tape
from .validate import (
    MAX_DESCRIPTION,
    MIN_DONE,
    MIN_PATTERNS,
    MIN_PITFALLS,
    MIN_SIGNALS,
    MIN_STEPS,
    MIN_SUMMARY,
    MIN_WORDS,
    Issue,
    validate_pack,
)

FLOORS = {
    "min_steps": MIN_STEPS,
    "min_signals": MIN_SIGNALS,
    "min_patterns": MIN_PATTERNS,
    "min_pitfalls": MIN_PITFALLS,
    "min_done_when": MIN_DONE,
    "min_summary_chars": MIN_SUMMARY,
    "min_words": MIN_WORDS,
    "max_description_chars": MAX_DESCRIPTION,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _report(issues: list[Issue], total: int, as_json: bool, title: str) -> int:
    bad = {issue.slug for issue in issues if issue.slug}
    valid = total - len(bad)
    if as_json:
        print(
            json.dumps(
                {
                    "pack": title,
                    "checked": total,
                    "valid": valid,
                    "passed": not issues,
                    "floors": FLOORS,
                    "issues": [
                        {"slug": i.slug, "rule": i.rule, "message": i.message}
                        for i in issues
                    ],
                },
                indent=2,
            )
        )
    else:
        print(f"{title}: {valid}/{total} skills valid")
        for issue in issues:
            print(f"  FAIL {issue}")
        if not issues:
            print(
                f"  ok  steps>={MIN_STEPS} signals>={MIN_SIGNALS} patterns>={MIN_PATTERNS} "
                f"pitfalls>={MIN_PITFALLS} words>={MIN_WORDS} refs canonical https"
            )
    return 0 if not issues else 1


# ------------------------------------------------------------------ corpus


def cmd_validate(args: argparse.Namespace) -> int:
    issues = validate_pack(PACK, SKILLS)
    root = Path(args.root) if args.root else repo_root()
    if not args.skip_files:
        for skill in SKILLS:
            path = root / "skills" / skill.slug / "SKILL.md"
            if not path.exists():
                issues.append(Issue(skill.slug, "file-missing", f"{path.relative_to(root)} missing"))
                continue
            if path.read_text(encoding="utf-8") != render_skill(PACK, skill):
                issues.append(
                    Issue(skill.slug, "file-drift", "SKILL.md on disk differs from the corpus render")
                )
    return _report(issues, len(SKILLS), args.json, PACK["name"])


def cmd_list(args: argparse.Namespace) -> int:
    skills: list[Skill] = [
        skill
        for skill in SKILLS
        if (not args.tag or args.tag in skill.tags)
        and (not args.phase or skill.meta_get("phase") == args.phase)
    ]
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "slug": s.slug,
                        "title": s.title,
                        "tags": list(s.tags),
                        "meta": s.meta,
                        "words": word_count(render_skill(PACK, s)),
                    }
                    for s in skills
                ],
                indent=2,
            )
        )
        return 0
    for skill in skills:
        print(f"{skill.slug:42s} {skill.meta_get('phase', '-'):12s} {skill.title}")
    print(f"-- {len(skills)} skills")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    for skill in SKILLS:
        if skill.slug == args.slug:
            print(render_skill(PACK, skill), end="")
            return 0
    print(f"unknown skill: {args.slug}", file=sys.stderr)
    return 1


def cmd_search(args: argparse.Namespace) -> int:
    terms = [term.lower() for term in args.terms]
    scored = []
    for skill in SKILLS:
        haystack = " ".join(
            [skill.slug, skill.title, skill.summary, " ".join(skill.tags), " ".join(skill.steps)]
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            scored.append((score, skill))
    scored.sort(key=lambda pair: (-pair[0], pair[1].slug))
    for score, skill in scored[: args.limit]:
        print(f"{score:3d}  {skill.slug:42s} {skill.title}")
    if not scored:
        print("no matches")
        return 1
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else repo_root()
    build_pack(root, PACK, SKILLS)
    issues = validate_pack(PACK, SKILLS)
    for skill in SKILLS:
        path = root / "skills" / skill.slug / "SKILL.md"
        if path.read_text(encoding="utf-8") != render_skill(PACK, skill):
            issues.append(Issue(skill.slug, "file-drift", "render mismatch"))
    bad = {issue.slug for issue in issues if issue.slug}
    report = {
        "pack": PACK["name"],
        "version": PACK["version"],
        "expected_skills": PACK.get("expected_skills", len(SKILLS)),
        "checked": len(SKILLS),
        "valid": len(SKILLS) - len(bad),
        "passed": not issues,
        "floors": FLOORS,
        "issues": [{"slug": i.slug, "rule": i.rule, "message": i.message} for i in issues],
    }
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"built {len(SKILLS)} skills -> {root / 'skills'}")
    return 0 if not issues else 1


# ------------------------------------------------------------------- domain


def cmd_send(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2
    try:
        request = RawRequest.parse(raw)
    except ExchangeError as exc:
        print(f"cannot parse request: {exc}", file=sys.stderr)
        return 2
    exchange = send(
        request,
        host=args.host,
        port=args.port,
        scheme=args.scheme,
        timeout=args.timeout,
        verify_tls=not args.insecure,
    )
    if exchange.error:
        print(f"error: {exchange.error}", file=sys.stderr)
        return 1
    assert exchange.response is not None
    response = exchange.response
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{path.stem}.response.http").write_bytes(exchange.received_bytes)
    if args.json:
        print(
            json.dumps(
                {
                    "status": response.status,
                    "reason": redact(response.reason),
                    "headers": [[n, redact(v)] for n, v in response.headers],
                    "elapsed_ms": round(exchange.elapsed_ms, 2),
                    "request_sha256": __import__("hashlib").sha256(exchange.sent_bytes).hexdigest(),
                    "response_sha256": __import__("hashlib").sha256(exchange.received_bytes).hexdigest(),
                    "body": redact(response.text),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(f"{response.version} {response.status} {response.reason}".rstrip())
        for name, value in response.headers:
            print(f"{name}: {redact(value)}")
        print()
        print(redact(response.text), end="" if response.text.endswith("\n") else "\n")
        print(f"\n[{exchange.elapsed_ms:.1f} ms, {len(exchange.received_bytes)} bytes]")
    return 0


def _load_tape(path: str) -> Tape | None:
    try:
        tape = Tape.load(path)
    except (OSError, TapeError) as exc:
        print(f"cannot load tape: {exc}", file=sys.stderr)
        return None
    return tape


def cmd_run(args: argparse.Namespace) -> int:
    tape = _load_tape(args.tape)
    if tape is None:
        return 2
    problems = lint_tape(tape)
    if problems and not args.force:
        print("tape does not lint; fix these or pass --force:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2
    if args.allow_shell:
        print(
            "warning: --allow-shell executes commands from the tape as your user",
            file=sys.stderr,
        )
    report = run_tape(
        tape,
        allow_shell=args.allow_shell,
        verify_tls=not args.insecure,
        fail_fast=args.fail_fast,
        dry_run=args.dry_run,
        capture_dir=args.capture,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        for result in report.results:
            mark = "PASS" if result.ok else ("SKIP" if result.skipped else "FAIL")
            status = f" {result.status}" if result.status is not None else ""
            print(f"{mark} {result.id:14s}{status:5s} {result.elapsed_ms:7.1f} ms  {result.name}")
            for failure in result.failures:
                print(f"     check: {redact(failure)}")
            if result.error:
                print(f"     error: {redact(result.error)}")
            if result.skipped:
                print(f"     {result.skipped}")
        print(f"-- {sum(1 for r in report.results if r.ok)}/{len(report.results)} steps passed")
    if args.report:
        Path(args.report).write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return 0 if report.passed else 1


def cmd_lint(args: argparse.Namespace) -> int:
    tape = _load_tape(args.tape)
    if tape is None:
        return 2
    problems = lint_tape(tape)
    if args.json:
        print(json.dumps({"tape": tape.name, "passed": not problems, "problems": problems}, indent=2))
    elif problems:
        for problem in problems:
            print(f"problem: {problem}")
    else:
        print(f"{tape.name}: {len(tape.steps)} steps, scope {', '.join(tape.scope)} - ok")
    return 0 if not problems else 1


def cmd_steps(args: argparse.Namespace) -> int:
    tape = _load_tape(args.tape)
    if tape is None:
        return 2
    if args.json:
        print(json.dumps([step.to_dict() for step in tape.steps], indent=2, ensure_ascii=False))
        return 0
    print(f"{tape.name}  origin={tape.origin}  scope={', '.join(tape.scope)}")
    for step in tape.steps:
        if step.kind == "request" and step.request is not None:
            detail = f"{step.request.method:7s} {step.request.target}"
        elif step.kind == "shell":
            detail = f"$ {redact(step.command or '')}"
        else:
            detail = f"wait {step.seconds}s"
        checks = step.expect.to_dict()
        suffix = f"  expect={checks}" if checks else ""
        print(f"  {step.id:14s} {step.kind:8s} {detail}{suffix}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    tape = _load_tape(args.tape)
    if tape is None:
        return 2
    report = None
    if args.run_report:
        try:
            payload = json.loads(Path(args.run_report).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"cannot read run report: {exc}", file=sys.stderr)
            return 2
        report = RunReport(tape=payload.get("tape", tape.name), origin=payload.get("origin", tape.origin), scope=tuple(payload.get("scope", ())))
        from .runner import StepResult

        for item in payload.get("steps", []):
            result = StepResult(
                id=item.get("id", "?"),
                kind=item.get("kind", "request"),
                name=item.get("name", ""),
                ok=bool(item.get("ok")),
                status=item.get("status"),
                elapsed_ms=float(item.get("elapsed_ms", 0.0)),
                body_text=item.get("body_preview", ""),
                sent=b"",
                received=b"",
            )
            result.headers = tuple((str(k), str(v)) for k, v in item.get("headers", []))
            result.extracted = {str(k): str(v) for k, v in (item.get("extracted") or {}).items()}
            result.failures = [str(v) for v in (item.get("failures") or [])]
            result.error = item.get("error")
            report.results.append(result)
    if args.to == "raw" and report is None:
        print("raw export needs --run-report", file=sys.stderr)
        return 2
    text = export(args.to, tape, report)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}")
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PACK["name"], description=PACK["description"])
    parser.add_argument("--version", action="version", version=f"{PACK['name']} {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("send", help="transmit one raw request and print the response")
    p.add_argument("file")
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--scheme", default="https", choices=["http", "https"])
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--insecure", action="store_true", help="skip TLS verification")
    p.add_argument("--out", default=None, help="directory for captured response bytes")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("run", help="execute a tape: requests, extracts, assertions, commands")
    p.add_argument("tape")
    p.add_argument("--allow-shell", action="store_true", help="run shell steps (off by default)")
    p.add_argument("--fail-fast", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="resolve and lint without sending")
    p.add_argument("--force", action="store_true", help="run even if the tape does not lint")
    p.add_argument("--insecure", action="store_true")
    p.add_argument("--capture", default=None, help="directory for raw exchanges and run.json")
    p.add_argument("--json", action="store_true")
    p.add_argument("--report", default=None, help="write the redacted run report here")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("lint", help="static checks: scope, variables, regexes")
    p.add_argument("tape")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("steps", help="show a tape's steps")
    p.add_argument("tape")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_steps)

    p = sub.add_parser("export", help="export to curl, HAR, markdown or raw HTTP")
    p.add_argument("tape")
    p.add_argument("--to", required=True, choices=["curl", "har", "markdown", "raw"])
    p.add_argument("--run-report", default=None)
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("validate", help="run every corpus rule and check disk sync")
    p.add_argument("--json", action="store_true")
    p.add_argument("--root", default=None)
    p.add_argument("--skip-files", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("list", help="list skills")
    p.add_argument("--tag", default=None)
    p.add_argument("--phase", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="print one SKILL.md")
    p.add_argument("slug")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("search", help="rank skills by keyword")
    p.add_argument("terms", nargs="+")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("build", help="regenerate skills/, pack.json and results/")
    p.add_argument("--root", default=None)
    p.set_defaults(func=cmd_build)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
