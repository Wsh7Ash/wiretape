---
name: replay-identical-bytes
description: "Resend the stored request unchanged before blaming the server for a difference. Use when a later result disagrees with the baseline or a report is about to be written"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, control, method]
---

# Replay Identical Bytes

> Resend the stored request unchanged before blaming the server for a difference

**Use when:** a later result disagrees with the baseline or a report is about to be written

**Avoid when:** the endpoint performs a non-idempotent action you already confirmed

## Procedure

1. Resend the stored baseline without editing any byte
2. Compare the response status, headers and body digest with the first send
3. Record which parts differ and which stay identical
4. If the digest differs, check for a nonce, timestamp or state change first
5. Only treat the replay as a control once it reproduces
6. Keep the replay result beside the original in the same tape run

## Signals

- the replay digest matches the baseline exactly
- a differing field is explained by a nonce or a mutated object
- the status flips between sends, which is itself a finding about state
- headers such as Date or Set-Cookie differ while the body digest does not

## Patterns

**1. Exact replay**

```text
byte-identical request, response digest 5c1e matches
```

**2. Expected drift**

```text
Date header differs, body digest is stable
```

**3. State drift**

```text
second send returns 409 because the object was already consumed
```

## Pitfalls

- Editing a header while trying to reproduce and calling the result an anomaly
- Comparing full header blocks and treating Date drift as a difference
- Replaying a destructive request against shared data without a cleanup plan

## Done when

- the replay is byte-identical and its result is recorded
- any drift is explained before it becomes a claim

## References

- [RFC 9110 - idempotent methods](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP WSTG - testing methodology](https://owasp.org/www-project-web-security-testing-guide/)
