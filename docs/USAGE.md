# Usage

## Install

```bash
git clone https://github.com/Wsh7Ash/wiretape
cd wiretape
python -m pip install -e ".[dev]"
```

Without installing, prefix with `PYTHONPATH=src python -m wiretape`.

## Send one request

Author the raw message exactly as it should appear on the wire:

```text
GET /v1/orders/42 HTTP/1.1
Accept: application/json
```

```bash
wiretape send order.http --host api.example.test --port 443
```

```text
HTTP/1.1 200 OK
Content-Type: application/json
...

{"id": "42", "status": "created"}

[38.4 ms, 240 bytes]
```

`--out captures/` also writes the response octets; `--json` emits a
machine-readable record with both digests.

## Write a tape

Start from the example and change the origin and scope:

```bash
cp examples/demo.tape.json my-hunt.tape.json
```

Rules that matter:

- `scope` lists hostnames. A request to any other host is refused before a
  socket opens, whether it comes from `origin` or from a step's `origin`.
- `{{name}}` references must be produced by an earlier `extract` or declared in
  `variables`. `wiretape lint` tells you which ones are not.
- Headers are a list of pairs, so duplicates survive. A dict also works and is
  read in insertion order.
- `expect` can name `status`, `contains`, `absent` and `regex` together.

## Run it

```bash
wiretape lint my-hunt.tape.json          # static checks, no packets
wiretape run  my-hunt.tape.json --dry-run # scope and routing only
wiretape run  my-hunt.tape.json --capture captures --report captures/run.json
```

Add `--allow-shell` only when you have read every `shell` step:

```bash
wiretape run my-hunt.tape.json --allow-shell
```

```text
warning: --allow-shell executes commands from the tape as your user
PASS login          200      6.9 ms  obtain a session token
PASS read-own-order 200      1.9 ms  read the owner's order with the extracted token
-- 6/6 steps passed
```

Useful flags:

| Flag | Effect |
|---|---|
| `--fail-fast` | stop after the first failure; later steps are marked skipped |
| `--force` | run even when `lint` reports problems |
| `--insecure` | skip TLS verification (lab only) |
| `--capture DIR` | write raw request/response files plus `run.json` |
| `--report FILE` | write the redacted run report |
| `--json` | print the report as JSON instead of the table |

Exit code is `0` only when every step passed.

## Extract and reuse values

```json
"extract": {
  "token": { "from": "body", "regex": "\"access_token\": \"([^\"]+)\"" },
  "session": { "from": "header", "header": "Set-Cookie", "required": false },
  "status_seen": { "from": "status" }
}
```

Then reference `{{token}}` in a later header, target or command. An extraction
that misses while `required` is true fails the step and names the value.

## Shell steps

A shell step runs a command with the variables substituted, captures stdout,
stderr and the exit code, and passes only on exit `0`.

```json
{
  "id": "digest-capture",
  "kind": "shell",
  "command": "python -c \"import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('captures/login.response.http').read_bytes()).hexdigest()[:16])\""
}
```

Feed the command a captured file rather than a URL: analysis stays reproducible
offline, and the capture digest proves what was analysed.

## Export

```bash
wiretape export my-hunt.tape.json --to curl --run-report captures/run.json
wiretape export my-hunt.tape.json --to har  --run-report captures/run.json --out evidence.har
wiretape export my-hunt.tape.json --to markdown --run-report captures/run.json
wiretape export my-hunt.tape.json --to raw --run-report captures/run.json
```

- `curl` substitutes values the run extracted, so the commands are the ones that
  worked; credentials become `<redacted>`.
- `har` opens in browser devtools and other HAR readers.
- `markdown` is the table to paste into a report.
- `raw` is the captured octets for another tool.

Then read the export before sending it anywhere. The `export-redaction-gate`
skill is the checklist.

## Rehearse locally

```bash
python examples/demo_server.py 8080   # in one terminal
wiretape run examples/demo.tape.json --capture captures
```

Point a new tape at `http://127.0.0.1:8080` with `"scope": ["127.0.0.1"]` first,
confirm every assertion behaves, then change the origin to the authorised host
and add it to scope. The demo server deletes `/orders/42` on cleanup, so restart
it between complete runs.

## Working with the skills

```bash
wiretape list --phase export
wiretape search replay redirects
wiretape show export-curl-reproduction
```

The same 50 skills are plain files under `skills/`, loadable by any `SKILL.md`
consumer. To serve them over MCP, see
[skillmcp](https://github.com/Wsh7Ash/skillmcp).

## Regenerating the corpus

```bash
wiretape build     # writes skills/, pack.json and results/validation.json
wiretape validate  # fails on disk drift or a broken floor
python -m pytest -q
```
