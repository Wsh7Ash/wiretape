---
name: replay-stateful-sequences
description: "Capture the order a flow depends on, because a request that works alone can fail in sequence. Use when the endpoint participates in a multi step flow such as create then confirm"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, state, sequence]
---

# Replay Stateful Sequences

> Capture the order a flow depends on, because a request that works alone can fail in sequence

**Use when:** the endpoint participates in a multi step flow such as create then confirm

**Avoid when:** the endpoint is stateless and each request stands alone

## Procedure

1. Record the flow as ordered steps with the values each step produced
2. Identify which values are state tokens versus ordinary inputs
3. Replay the sequence in order and confirm every step passes
4. Remove one step and record which later step fails and how
5. Replay the steps out of order to learn what the server enforces
6. Keep the negative sequences as steps so the ordering claim is reproducible

## Signals

- a later step returns 409 or 400 when an earlier step is skipped
- the state token is single use and the second replay fails
- out of order execution succeeds, which suggests missing state validation
- a confirmation step accepts an object id that was never created by this session

## Patterns

**1. Ordered flow**

```text
create order, then confirm order with the returned id
```

**2. Skipped step**

```text
confirm called directly after create, no payment step
```

**3. Out of order**

```text
confirm before create, server still returns 200
```

## Pitfalls

- Replaying steps from a saved flow whose state tokens already expired
- Concluding a race exists from a sequence that was simply out of order
- Leaving created objects behind and polluting the tenant you are testing

## Done when

- the positive sequence replays end to end
- at least one negative ordering case is stored with its outcome

## References

- [OWASP - business logic flaws](https://owasp.org/www-project-web-security-testing-guide/)
- [RFC 9110 - state changing methods](https://www.rfc-editor.org/rfc/rfc9110.html)
