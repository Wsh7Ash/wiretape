# Contributing

Two kinds of change land here: code and skills. Both are gated the same way.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m wiretape validate
```

## House rules

These are not style preferences; tests depend on them.

1. **Never normalise a message you were asked to send.** Header order, casing,
   duplicates, the request target and body bytes are the author's.
2. **Only `Host` may be synthesized**, and only when the author omitted it.
3. **A missing variable is an error.** Do not add a default-to-empty fallback.
4. **Redirects are not followed** unless asked. A 302 is data.
5. **Every output path redacts.** If you add a printer, exporter or log line, it
   goes through `redact()`.
6. **No new dependencies** at runtime. Standard library only.

## Adding a skill

Skills are dicts in [`src/wiretape/corpus/`](src/wiretape/corpus/). Do not edit
`skills/**/SKILL.md` by hand: `build` rewrites them and `validate` reports drift.

| Rule | Floor |
|---|---|
| steps | 6, each at least 25 chars |
| signals | 4, each at least 15 chars |
| patterns | 3 `(label, code)` pairs, label at least 8 chars, code at least 20 |
| pitfalls | 3, each at least 30 chars |
| done-when | 2 |
| references | 1, `[label](https://...)` |
| summary | 40 chars |
| rendered words | 180 |
| `meta.phase` | one of capture, replay, extract, assert, execute, export |

Rejected outright: placeholder tokens, machine-local paths, duplicate slugs or
titles, and non-https references.

Write for an agent that must act. Every step should be something an observer
could watch happen and score.

## Adding a step kind or assertion

1. Add the kind to `KINDS` and to `Step.from_dict` / `Step.to_dict`.
2. Handle it in `run_tape`, including the refusal path for anything executable.
3. Extend `lint_tape` so a malformed instance is caught before a run.
4. Add a test that fails on the old behaviour, then make it pass.

## Tests

- Behaviour tests may open a loopback socket. They must not touch the internet.
- Prefer asserting on recorded facts (status, digests, extracted values) over
  asserting that a function was called.
- Any test of redaction should grep the artifact for the literal secret.
- No `sleep` for synchronisation; start servers in a fixture and poll.

## Reporting

Bugs and feature requests: open an issue with the command, the output and what
you expected. Security issues: [SECURITY.md](SECURITY.md), not the tracker.
