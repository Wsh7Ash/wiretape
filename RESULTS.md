# Results

Every number here comes from a run on this machine: a real socket to
`examples/demo_server.py`, not a mock.

## Environment

- OS: Windows (MSYS2 shell), Python 3.14.3
- Runtime: Python 3.10+ standard library only; `pytest` as dev dependency
- Network: loopback only. TLS paths exist but were not exercised here; the demo
  target is plain HTTP on `127.0.0.1:8080`.

## Corpus gate

```text
$ python -m wiretape validate
wiretape: 50/50 skills valid
  ok  steps>=6 signals>=4 patterns>=3 pitfalls>=3 words>=180 refs canonical https
```

Phase distribution: `capture` 9, `replay` 8, `extract` 9, `assert` 8,
`execute` 8, `export` 8 — 50 unique slugs, 50 unique titles, each rendered skill
at or above the 180-word floor.

## Test suite

```text
$ python -m pytest -q
........................................                                 [100%]
```

40 tests, split between behaviour and corpus:

- **sockets**: parse/serialize round trips, duplicate headers, real GET through
  `send`, redirect refusal, scope refusal before any bytes are written.
- **runner**: extraction feeding the next step, assertion failures naming the
  observed status, shell refusal without `--allow-shell`, shell execution with
  it, non-zero exit propagation, dry run, capture files and digests.
- **redaction**: headers, query parameters, JSON bodies, JWT and bearer blobs,
  order and duplicates preserved.
- **exporters**: runnable curl with redaction and substituted variables, HAR
  entry shape, markdown table, raw bundle, unknown target rejected.
- **corpus**: floors, uniqueness, phase balance, disk-sync against `skills/`,
  `pack.json`, the green `results/validation.json`, and the real CLI as a
  subprocess.

## Demo run

```text
$ python -m wiretape lint examples/demo.tape.json
demo-order-flow: 6 steps, scope 127.0.0.1 - ok

$ python -m wiretape run examples/demo.tape.json --allow-shell --capture captures --report captures/run.json
warning: --allow-shell executes commands from the tape as your user
PASS login          200      6.9 ms  obtain a session token
PASS read-own-order 200      1.9 ms  read the owner's order with the extracted token
PASS attempt-admin  403      1.5 ms  confirm this role cannot reach the admin route
PASS cleanup-order  204      1.5 ms  delete the object this tape touched
PASS confirm-deleted 404      2.6 ms  prove the cleanup happened
PASS digest-capture        134.6 ms  hash the login capture for the evidence trail
-- 6/6 steps passed
```

Files written by that run:

| File | Contents |
|---|---|
| `captures/login.request.http` | the exact bytes sent, `Host` synthesized because the tape omitted it |
| `captures/login.response.http` | the received octets, unmodified |
| `captures/read-own-order.response.http` | `{"id": "42", "status": "created", "total": 19}` |
| `captures/run.json` | redacted step results, extracted variables, digests |

## Failure output

A deliberately wrong expectation is the useful case, so it is what the second
demo exercised before the assertion was fixed to match reality:

```text
FAIL read-own-order 404      3.4 ms  read the owner's order with the extracted token
     check: status 404 not in [200]
     check: body lacks '"status": "created"'
     check: could not extract 'order_id'
-- 2/6 steps passed
```

That run also caught a real gap: the tape was executed a second time against the
same server, whose demo state had already been cleaned up by the first run. The
tape reported the 404 honestly instead of treating it as success, which is the
behaviour the `execute-cleanup-step` skill asks for in reverse: the cleanup step
is what makes the first run pass and the second one start from a clean world.

## Export check

```text
$ python -m wiretape export examples/demo.tape.json --to curl --run-report captures/run.json
...
curl --silent --show-error --include --path-as-is --request DELETE http://127.0.0.1:8080/orders/42 \
  --header 'Authorization: <redacted>'
```

- `{{order_id}}` from the run report is substituted into the printed command.
- The `Authorization` value is `<redacted>`, verified by a test that greps the
  artifact for the literal token string.
- `--path-as-is` is present so curl does not normalise the path.

## Fixes made during the build

- **Dry run failed on variables produced by earlier steps.** A dry run has no
  response to extract from, so substitution raised `unknown variable`. Dry run
  now checks origin and scope and defers substitution, which is what "send
  nothing" should mean.
- **HAR export leaked secret query values.** Values were redacted but not by
  parameter name, so `?token=abc123` survived. Query pairs now use the same
  secret-parameter list as the redactor.
- **Exporters printed unresolved references.** `curl` and `markdown` exports of
  a completed run showed `{{order_id}}` instead of the id the run extracted.
  Both now fill known variables from the run report.
- **Capture directory was not created for a dry run.** Writing `run.json`
  failed with `FileNotFoundError`; the directory is now created unconditionally.

## Known limitations

- TLS paths (`--insecure`, SNI handling) are implemented but untested here: the
  demo target is plain HTTP.
- `_read_response` handles `Content-Length` and read-to-close. Chunked bodies are
  read until the connection closes rather than being de-chunked, so a keep-alive
  chunked response needs a `Connection: close` header in the tape.
- The shell gate is a policy, not a sandbox: an enabled command runs with your
  user's privileges. The `execute-shell-step-gate` skill exists for that reason.
- HAR timings are zero-filled; only the measured exchange time is real.
