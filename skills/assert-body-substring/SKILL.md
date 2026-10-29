---
name: assert-body-substring
description: "Prove the reply contains the value that makes it the right reply, not merely the right code. Use when two different outcomes share a status code and the body distinguishes them"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, body, content]
---

# Assert Body Substring

> Prove the reply contains the value that makes it the right reply, not merely the right code

**Use when:** two different outcomes share a status code and the body distinguishes them

**Avoid when:** the body is a binary payload where a substring check is meaningless

## Procedure

1. Identify the smallest string that could only appear in the expected outcome
2. Prefer an identifier you created over a generic word such as success
3. Add the substring to the step's expectation
4. Confirm the pass on a correct reply and the failure on a wrong one
5. Record the exact string in the tape so the assertion is auditable
6. Revisit the string when the API's wording changes

## Signals

- the response contains the unique marker sent in the request
- an empty list response fails because the marker is absent
- the assertion catches a permission error page served with 200
- a localised error message still fails the intended check

## Patterns

**1. Marker check**

```text
contains wt-2026-10-29-7f3a echoed in the created object
```

**2. 200 page problem**

```text
contains "order_id" fails on a login page served with 200
```

**3. Wording drift**

```text
contains "created" breaks when the API returns "accepted"
```

## Pitfalls

- Asserting on a word like success that appears on error pages too
- Asserting on a value you generated but sent in a header the server ignores
- Forgetting that the check is case sensitive and the API changed casing

## Done when

- the asserted substring appears only in the intended outcome
- the assertion has been observed to fail at least once

## References

- [OWASP - content spoofing](https://owasp.org/www-community/attacks/Content_Spoofing)
- [RFC 9110 - message content](https://www.rfc-editor.org/rfc/rfc9110.html)
