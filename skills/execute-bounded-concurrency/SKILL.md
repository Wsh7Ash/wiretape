---
name: execute-bounded-concurrency
description: "Race two requests deliberately and rarely, because concurrency findings need a control and a budget. Use when testing a single use token, a coupon, a balance or any check that might not be atomic"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, concurrency, races]
---

# Execute Bounded Concurrency

> Race two requests deliberately and rarely, because concurrency findings need a control and a budget

**Use when:** testing a single use token, a coupon, a balance or any check that might not be atomic

**Avoid when:** the program forbids automated load, or the endpoint affects other tenants

## Procedure

1. Run the operation serially first and confirm the second attempt is rejected
2. Write the race as two steps fired together with a shared start signal
3. Keep the concurrency count at two until a race is suspected
4. Record both responses fully, including which one succeeded
5. Repeat a small number of times to separate a real race from noise
6. Report the serial control alongside the raced run

## Signals

- both concurrent requests succeed where the second serial one fails
- the balance decreases once while two credits appear
- the same single use token is accepted twice in the same millisecond window
- the serial control consistently rejects the duplicate

## Patterns

**1. Serial control**

```text
first redeem 200, second redeem 409
```

**2. Raced pair**

```text
two redeems started together, both returned 200
```

**3. Attempt budget**

```text
five attempts total, stop after the first reproducible pair
```

## Pitfalls

- Running fifty parallel requests at a production endpoint and calling it a test
- Reporting a race without the serial control that proves the guard exists
- Racing a destructive operation that cannot be undone

## Done when

- the serial control and the raced run are both stored
- the number of attempts stays within a stated budget

## References

- [OWASP - race conditions](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE-362](https://cwe.mitre.org/data/definitions/362.html)
