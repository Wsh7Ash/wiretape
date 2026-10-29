---
name: execute-timeout-discipline
description: "Give every request and command an explicit timeout so a hung target cannot stall a whole run. Use when a tape runs unattended, against a slow service or with a command that may block"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, timeout, reliability]
---

# Execute Timeout Discipline

> Give every request and command an explicit timeout so a hung target cannot stall a whole run

**Use when:** a tape runs unattended, against a slow service or with a command that may block

**Avoid when:** the operation is a deliberate long poll whose duration is the thing being measured

## Procedure

1. Set a per step timeout that is generous for a healthy target and short enough to notice
2. Keep the default timeout explicit in the tape rather than relying on the tool's default
3. Distinguish a timeout from a refusal in the result, because they mean different things
4. Record the configured timeout in the report so a reader can judge a slow result
5. Raise a single step's timeout when justified, rather than raising all of them
6. Re-run a timed out step once before treating the timeout as the finding

## Signals

- the result says timeout rather than a connection error
- the elapsed time is close to the configured limit
- a second run completes, showing the first was a transient stall
- a command timeout leaves no orphan process behind

## Patterns

**1. Per step limit**

```text
timeout 5 on a read, timeout 60 on a report generation command
```

**2. Timeout verdict**

```text
send failed: timed out after 5.0s
```

**3. Escalation**

```text
one step raised to 30s after two timeouts, others unchanged
```

## Pitfalls

- Leaving the default in place and reporting a target as down after one slow reply
- Setting a timeout so low that TLS handshakes on a loaded host fail
- Treating a timeout as proof of a vulnerability instead of a symptom

## Done when

- every step has an explicit timeout appropriate to it
- timeouts are reported distinctly from refusals and connection errors

## References

- [Python - socket timeouts](https://docs.python.org/3/library/socket.html#socket.socket.settimeout)
- [RFC 9110 - timeouts](https://www.rfc-editor.org/rfc/rfc9110.html)
