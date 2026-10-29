---
name: replay-with-header-mutations
description: "Change one header per replay so a behaviour change can be attributed to that header alone. Use when testing trust in forwarded, override or content negotiation headers"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, headers, attribution]
---

# Replay With Header Mutations

> Change one header per replay so a behaviour change can be attributed to that header alone

**Use when:** testing trust in forwarded, override or content negotiation headers

**Avoid when:** the hypothesis needs a combination of headers that only works together

## Procedure

1. List the headers the application is likely to trust from an upstream
2. Pick one header and one value change for the first replay
3. Keep every other byte identical to the baseline
4. Record status, body digest and any reflected value
5. Repeat for the next header on a fresh baseline, not the mutated one
6. Only combine headers after each single change is understood

## Signals

- adding one header changes the identity the application believes it has
- a header is echoed into the response, proving it is read
- removing a security header changes caching or CORS behaviour
- the same header is ignored when the source address is untrusted

## Patterns

**1. Identity header**

```text
X-Forwarded-User: admin added to the baseline request
```

**2. Override header**

```text
X-HTTP-Method-Override: DELETE on a POST
```

**3. Negotiation**

```text
Accept: application/xml returns a different parser branch
```

## Pitfalls

- Changing three headers at once and reporting a combination you cannot isolate
- Testing forwarded headers from an address the edge overwrites
- Assuming the application reads a header because the proxy logs it

## Done when

- each mutation is a single header change against a stored baseline
- the behaviour change is attributed to that header in the notes

## References

- [MDN - X-Forwarded-For](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For)
- [OWASP - access control](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)
