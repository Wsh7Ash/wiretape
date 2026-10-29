---
name: replay-against-a-new-origin
description: "Retarget a tape to a second environment while keeping the request identical everywhere else. Use when the same test must run against staging, a second region or a duplicate host"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, retarget, scope]
---

# Replay Against a New Origin

> Retarget a tape to a second environment while keeping the request identical everywhere else

**Use when:** the same test must run against staging, a second region or a duplicate host

**Avoid when:** the second origin is not in the agreed scope or is production when staging exists

## Procedure

1. Add the new host to the tape's scope list explicitly
2. Set the origin per run rather than editing each request's host header
3. Keep any Host header that was part of the original test as an authored value
4. Run the tape and compare responses across origins with digests
5. Note origin specific differences such as auth requirements or editions
6. Record which origin produced which evidence in the report

## Signals

- the same request bytes reach both origins except for routing names
- a difference between origins is explained by configuration, not by the tool
- the tape refuses an origin host missing from scope
- each stored result states the origin it came from

## Patterns

**1. Scoped origin**

```text
scope [api.staging.example.test, api.example.test]
```

**2. Run override**

```text
--origin https://api.staging.example.test, request bytes unchanged
```

**3. Cross origin note**

```text
staging returns 200, production returns 401 for the same role
```

## Pitfalls

- Editing request files to change hosts and losing the ability to compare
- Forgetting that cookies scoped to one host will not be sent to the other
- Treating a staging-only weakness as a production finding without a shared cause

## Done when

- every origin used is declared in the tape scope
- cross origin results are stored separately and labelled

## References

- [HackerOne - scope handling](https://docs.hackerone.com/)
- [RFC 6265 - cookies and host scoping](https://www.rfc-editor.org/rfc/rfc6265.html)
