# Architecture

wiretape is one small library with a hard rule at each boundary: the bytes you
wrote are the bytes that leave, the bytes that arrived are the bytes that stay,
and nothing secret leaves the process unredacted.

```text
exchange.py     RawRequest / RawResponse / Exchange
                 parse · serialize · socket send · Content-Length read
     │
tape.py         Step / Tape / Extract / Expect
                 variables {{name}} · lint_tape · JSON load/save
     │
runner.py       StepResult / RunReport / run_tape
                 scope guard · shell gate · extraction carry-forward
     │
exporters.py    curl · HAR 1.2 · markdown · raw octets
     │
cli.py          send · run · lint · steps · export · corpus commands
```

`redact.py` sits beside all of them: every path that produces text for a human or
a file calls it.

## exchange.py

`RawRequest` holds method, target, version, an ordered tuple of header pairs and
the body as bytes. Headers are a tuple, not a dict, because a dict silently drops
the second `X-Forwarded-For` and reorders everything — exactly the properties a
smuggling or cache test depends on.

`to_bytes(host_header)` serializes and adds `Host` **only** when the author left
it out, since a request without `Host` cannot be routed at all. That is the only
synthesized byte in the tool, and the tests assert it.

`send()` opens one connection, optionally wraps it in TLS, writes the bytes and
reads until the headers plus either `Content-Length` bytes or connection close.
Redirects are not followed: a 302 is evidence. `follow_redirects=True` exists for
the deliberate case and issues one fresh GET to the `Location`.

`RawResponse` keeps `raw`, so a digest is always computed over what arrived
rather than over a re-serialization.

## tape.py

A `Step` is a `request`, `shell` or `wait`. A `Tape` adds a name, an origin, a
**scope list of hostnames**, variables and an ordered step tuple.

`substitute()` raises on an unknown name. Degrading `{{id}}` to an empty string
would turn `/users/{{id}}` into `/users/`, which tests the collection endpoint
instead of the object — a silent change of question, so it is an error.

`Extract` supports `body` (regex with a capture group), `header`, `status` and a
`required` flag. `Expect` supports `status` lists, `contains`, `absent` and
`regex`, each returning a human-readable failure rather than a bare boolean, so a
failed run says `status 403 not in [200]` instead of `False`.

`lint_tape()` is the static gate: origin host in scope, Host header consistent
with the origin, extraction regexes compile, expect regex compiles, and every
referenced variable is produced by an earlier step or declared in `variables`.

## runner.py

`run_tape()` walks the steps with one mutable variable map. Before a request it
resolves the origin, checks the host against `tape.scope`, and refuses before a
socket is opened. Shell steps return `refused` unless `allow_shell=True`, and a
timeout or non-zero exit is recorded, never smoothed over.

Results carry the SHA-256 of the sent and received bytes (first 16 hex
characters), extracted values, failures, command output and — in `public()` — a
redacted view that every printer and exporter uses.

Dry run is a distinct path: it validates routing and scope and skips
substitution, because variables from earlier steps do not exist yet.

## exporters.py

- **curl** is `--path-as-is` (no path normalisation), explicit `--request`, one
  `--header` per authored header and `--data-raw` for the body, with extracted
  variables filled from a run report.
- **HAR 1.2** keeps header arrays in order, keeps duplicates and redacts values,
  including secret query parameters by name.
- **markdown** is a table plus a failures section and an extracted-variables
  table, so a report can be generated rather than retyped.
- **raw** is the captured octets, for import elsewhere.

## The corpus harness

The 50 skills use the same harness as the other packs in this series: authored as
dicts under `corpus/part1..3.py`, rendered to `SKILL.md`, validated against
structural floors and a disk-drift check, then written by `build` together with
`pack.json` and `results/validation.json`.

## Extension points

| Want to | Change |
|---|---|
| add a step kind | `KINDS` in `tape.py`, a branch in `Step.from_dict` and `run_tape` |
| add an extraction source | `Extract.apply` |
| add an assertion type | `Expect` + `check` + `to_dict` |
| add an export format | a function in `exporters.py`, one line in `export()` |
| add a skill | one dict in `corpus/partN.py`, then `build` |
