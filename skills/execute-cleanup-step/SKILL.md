---
name: execute-cleanup-step
description: "End every tape that creates state with a cleanup step, so the next run starts from the same world. Use when the tape creates objects, uploads files or changes settings on the target"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, cleanup, hygiene]
---

# Execute Cleanup Step

> End every tape that creates state with a cleanup step, so the next run starts from the same world

**Use when:** the tape creates objects, uploads files or changes settings on the target

**Avoid when:** the created object is itself the evidence the program wants to inspect

## Procedure

1. List everything the tape creates or mutates
2. Add a delete or revert step for each, targeting the extracted ids
3. Make cleanup tolerate an already deleted object without failing the run
4. Order cleanup last, and keep it out of fail-fast so it still runs after a failure
5. Verify the cleanup with a read that returns 404 or the original value
6. Note in the report anything that could not be cleaned up, and why

## Signals

- a second run of the tape passes without collisions
- the cleanup step returns 204 or 404 rather than a server error
- the target's listing no longer contains the test marker
- cleanup runs even when an earlier step failed

## Patterns

**1. Delete by id**

```text
DELETE /v1/orders/{{order_id}} expecting 204
```

**2. Tolerant cleanup**

```text
404 accepted as already cleaned
```

**3. Verification**

```text
read of {{order_id}} returns 404 after cleanup
```

## Pitfalls

- Leaving test accounts behind that later trip rate limits or quota checks
- Deleting a production object that predated the test
- Making cleanup part of the fail-fast chain so a failure leaves debris

## Done when

- every created object has a corresponding cleanup step
- a repeat run starts clean and passes

## References

- [RFC 9110 - DELETE](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP - testing cleanup](https://owasp.org/www-project-web-security-testing-guide/)
