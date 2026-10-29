# Examples

Two files, both real:

- `demo_server.py` — a loopback target with a session endpoint, one order, an
  admin route that always returns 403, and a delete that honours cleanup.
- `demo.tape.json` — a six step tape: login, read as the owner, prove the admin
  route is refused, delete, confirm the delete, then hash the capture.

## Run it

```bash
# terminal 1
python examples/demo_server.py 8080

# terminal 2
wiretape lint examples/demo.tape.json
wiretape run  examples/demo.tape.json --allow-shell --capture captures --report captures/run.json
```

```text
PASS login          200      6.9 ms  obtain a session token
PASS read-own-order 200      1.9 ms  read the owner's order with the extracted token
PASS attempt-admin  403      1.5 ms  confirm this role cannot reach the admin route
PASS cleanup-order  204      1.5 ms  delete the object this tape touched
PASS confirm-deleted 404      2.6 ms  prove the cleanup happened
PASS digest-capture        134.6 ms  hash the login capture for the evidence trail
-- 6/6 steps passed
```

The tape deletes `/orders/42`, so restart the demo server before running it a
second time. A second run against the same process is a genuinely useful
exercise: every step after the first read fails with an honest 404 rather than
passing silently.

## Look at the result

```bash
wiretape export examples/demo.tape.json --to markdown --run-report captures/run.json
wiretape export examples/demo.tape.json --to curl     --run-report captures/run.json
wiretape export examples/demo.tape.json --to har      --run-report captures/run.json --out captures/demo.har
```

`captures/` then contains:

| File | What it is |
|---|---|
| `login.request.http` | the exact bytes sent |
| `login.response.http` | the exact bytes received, including the `Set-Cookie` |
| `*.request.http` / `*.response.http` | one pair per request step |
| `run.json` | redacted results, extracted variables, digests |

## Point it somewhere else

1. Copy the tape.
2. Change `origin` to the authorised host and put its hostname in `scope`.
3. Run with `--dry-run` first; it checks scope and routing without a packet.
4. Then run for real, and read `lint` output before you do.
