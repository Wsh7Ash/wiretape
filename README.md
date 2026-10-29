# wiretape

Record, replay, extract, assert and export **raw HTTP exchanges**, and run
request + command sequences, without an intercepting proxy. Ships with **50
validated skills** for the whole capture-to-report workflow.

A proxy is a program between you and the socket. wiretape removes the middle:
you author a *tape* — an ordered JSON list of requests, assertions, extractions
and (opt-in) shell commands — and it transmits exactly those bytes, stores
exactly what came back, and gives you curl, HAR, raw HTTP and markdown exports of
the result.

```text
wiretape run    examples/demo.tape.json --capture captures --report captures/run.json
wiretape export examples/demo.tape.json --to markdown --run-report captures/run.json
wiretape export examples/demo.tape.json --to curl
wiretape send   order.http --host api.example.test --port 443
```

## Why a tape instead of a proxy history

| Proxy behaviour | What it costs you | What wiretape does |
|---|---|---|
| Normalises header casing and order | The framing bug disappears | Sends the header list you wrote, in order |
| Merges duplicate headers | Request smuggling and IP spoof tests get flattened | Keeps every duplicate line |
| Follows redirects | The 302 *is* the finding | Stores the redirect, never follows by default |
| Records history only | Nothing says what you have not tried | Each step carries the assertion that must pass |
| GUI-bound | Cannot run in CI or from an agent | One CLI, exit codes, JSON output |
| Stores secrets in history | Reports leak tokens | Redaction on every export, verified by test |

## A tape

```json
{
  "schema": 1,
  "name": "demo-order-flow",
  "origin": "http://127.0.0.1:8080",
  "scope": ["127.0.0.1"],
  "steps": [
    {
      "id": "login",
      "request": { "method": "GET", "target": "/session", "headers": [["Accept", "application/json"]] },
      "extract": { "token": { "from": "body", "regex": "\"access_token\": \"([^\"]+)\"" } },
      "expect": { "status": [200], "contains": "demo-hunter" }
    },
    {
      "id": "read-own-order",
      "request": {
        "method": "GET",
        "target": "/orders/42",
        "headers": [["Authorization", "Bearer {{token}}"]]
      },
      "extract": { "order_id": { "from": "body", "regex": "\"id\": \"([^\"]+)\"" } },
      "expect": { "status": [200], "contains": "\"status\": \"created\"" }
    },
    { "id": "attempt-admin", "request": { "method": "GET", "target": "/admin" },
      "expect": { "status": [403], "contains": "role required" } },
    { "id": "cleanup-order", "request": { "method": "DELETE", "target": "/orders/{{order_id}}" },
      "expect": { "status": [204] } }
  ]
}
```

Step kinds are `request`, `shell` and `wait`. An extraction produces a variable
that later steps reference as `{{name}}`; a missing variable is an error, never
an empty string.

## Running it

```text
$ python examples/demo_server.py 8080 &
$ wiretape run examples/demo.tape.json --allow-shell --capture captures --report captures/run.json
warning: --allow-shell executes commands from the tape as your user
PASS login          200      6.9 ms  obtain a session token
PASS read-own-order 200      1.9 ms  read the owner's order with the extracted token
PASS attempt-admin  403      1.5 ms  confirm this role cannot reach the admin route
PASS cleanup-order  204      1.5 ms  delete the object this tape touched
PASS confirm-deleted 404      2.6 ms  prove the cleanup happened
PASS digest-capture        134.6 ms  hash the login capture for the evidence trail
-- 6/6 steps passed
```

When an assertion is wrong, the step says which check failed and what was
observed:

```text
FAIL read-own-order 404      3.4 ms  read the owner's order with the extracted token
     check: status 404 not in [200]
     check: body lacks '"status": "created"'
     check: could not extract 'order_id'
```

## Exports

```text
$ wiretape export examples/demo.tape.json --to curl --run-report captures/run.json
#!/usr/bin/env bash
# replay of tape 'demo-order-flow' against http://127.0.0.1:8080
# credentials are redacted; fill them from your environment before running
set -euo pipefail

# step read-own-order: read the owner's order with the extracted token
curl --silent --show-error --include --path-as-is --request GET http://127.0.0.1:8080/orders/42 \
  --header 'Authorization: <redacted>' --header 'Accept: application/json'
```

```text
$ wiretape export examples/demo.tape.json --to markdown --run-report captures/run.json
| Step | Kind | Status | Path | Result |
|---|---|---|---|---|
| `login` | request | 200 | `/session` | PASS |
| `read-own-order` | request | 200 | `/orders/42` | PASS |
| `attempt-admin` | request | 403 | `/admin` | PASS |
| `cleanup-order` | request | 204 | `/orders/42` | PASS |
| `confirm-deleted` | request | 404 | `/orders/42` | PASS |
```

`--to har` writes HAR 1.2 for devtools readers; `--to raw` writes the captured
request and response octets for import into another tool. Extracted values are
substituted into exports from the run report, so the printed commands are the
ones that worked.

## Three guarantees, enforced in code

1. **Scope.** A request whose resolved host is not in `tape.scope` is refused
   *before* a socket opens. There is no flag that bypasses this.
2. **Shell.** Shell steps do not run unless you pass `--allow-shell`, and the
   warning is printed before the first command. A tape is data an agent may have
   written; data should not be able to execute commands by default.
3. **Redaction.** Every export and every printed result passes through the
   redactor: `Authorization`, `Cookie`, `Set-Cookie`, `X-Api-Key`, bearer tokens,
   JWTs and secret query parameters become `<redacted>`. A test asserts a known
   token is absent from the exported artifacts.

## Commands

| Command | Purpose |
|---|---|
| `send FILE --host H [--port P]` | Transmit one raw request, print the response, optionally save bytes |
| `run TAPE` | Execute steps in order: capture, extract, assert, redact |
| `lint TAPE` | Scope, variable, regex and Host-header checks before spending packets |
| `steps TAPE` | Show the tape's steps and expectations |
| `export TAPE --to curl\|har\|markdown\|raw` | Evidence in the format the reader needs |
| `validate` | The corpus gate: structure, floors, disk sync |
| `list` / `show` / `search` / `build` | Browse and regenerate the 50 skills |

Flags worth knowing: `--dry-run` (resolve and lint, send nothing), `--fail-fast`,
`--insecure` (skip TLS verification, for a lab only), `--capture DIR`,
`--json`, `--report runs.json`.

## The 50 skills

| Phase | Count | Covers |
|---|---|---|
| `capture` | 9 | exact baselines, DevTools import, header order and duplicates, content length, request targets, Host versus SNI, response octets, credential hygiene, naming |
| `replay` | 8 | identical replay, stability sampling, retargeting, redirects as evidence, header mutation, stateful sequences, body encodings, connection reuse |
| `extract` | 9 | tokens, cookies, CSRF, created ids, greedy vs lazy, required vs optional, proof by use, header precedence, timing and size |
| `assert` | 8 | exact status, body substrings, absence for negatives, structured regex, header presence, role comparisons, minimal evidence, error-path parity |
| `execute` | 8 | the shell gate, command output as evidence, timeouts, offline analysis, local labs, fail-fast choices, cleanup, bounded concurrency |
| `export` | 8 | curl, HAR, raw bundles, markdown, redaction verification, digest provenance, sharing scope, finding-to-step maps |

```text
$ wiretape validate
wiretape: 50/50 skills valid
  ok  steps>=6 signals>=4 patterns>=3 pitfalls>=3 words>=180 refs canonical https
```

## Install

```bash
git clone https://github.com/Wsh7Ash/wiretape
cd wiretape
python -m pip install -e ".[dev]"
python -m pytest -q
```

Python 3.10+, standard library only at runtime; `pytest` is the sole dev
dependency. Tests start a real local HTTP server and exercise the socket path,
the tape runner, redaction and every exporter.

## Related packs

- [httpdeck](https://github.com/Wsh7Ash/httpdeck) plans tests from a HAR capture.
- [reqforge](https://github.com/Wsh7Ash/reqforge) sends single raw exchanges.
- [dorkforge](https://github.com/Wsh7Ash/dorkforge) compiles search dorks.
- [skillmcp](https://github.com/Wsh7Ash/skillmcp) serves these skill packs over MCP.

## License

MIT.
