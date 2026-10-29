---
name: replay-stability-sample
description: "Send the same request several times and measure which response properties actually vary. Use when a finding depends on a difference and you need to know the natural variance first"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, variance, measurement]
---

# Replay Stability Sample

> Send the same request several times and measure which response properties actually vary

**Use when:** a finding depends on a difference and you need to know the natural variance first

**Avoid when:** the request mutates server state or triggers a costly side effect per send

## Procedure

1. Choose a sample size that is small enough to stay polite, such as five sends
2. Send the request the same number of times with the same bytes
3. Record status, body length and body digest for every send
4. Compute how many distinct combinations appeared
5. Treat any property that varies across the control as unusable evidence
6. Compare the mutation against the observed variance, not against one baseline

## Signals

- body digest is stable while a request id changes every time
- two distinct response bodies appear under identical input
- status is stable but the object version increments per send
- a load balanced backend returns different server headers per send

## Patterns

**1. Stable control**

```text
5 sends, 1 distinct digest, status always 200
```

**2. Drifting control**

```text
5 sends, 2 distinct digests, same length
```

**3. Stability verdict**

```text
mutation differs outside the 2-digest control envelope
```

## Pitfalls

- Running fifty sends at a production endpoint to be statistically happy
- Comparing a single baseline with a single mutation and calling it variance
- Ignoring that concurrent sends may race on the same object

## Done when

- the control's natural variance is measured before the mutation is judged
- every distinct response variant is stored with its digest

## References

- [RFC 9110 - safe and idempotent methods](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP - automated scanning ethics](https://owasp.org/www-project-web-security-testing-guide/)
