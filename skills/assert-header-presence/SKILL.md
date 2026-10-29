---
name: assert-header-presence
description: "Assert the security and caching headers a reply must carry, because their absence is the finding. Use when testing cache behaviour, CORS, transport security or information leakage in headers"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, headers, security]
---

# Assert Header Presence

> Assert the security and caching headers a reply must carry, because their absence is the finding

**Use when:** testing cache behaviour, CORS, transport security or information leakage in headers

**Avoid when:** the endpoint is a health check with no user data behind it

## Procedure

1. List the headers the endpoint must send for its stated behaviour
2. Distinguish headers that must be present from those that must be absent
3. Add a presence check for each required header on the relevant step
4. Capture the exact value, such as a wildcard origin or a long cache age
5. Test the same headers on an error response, which is often less protected
6. Report the header fact together with the behaviour it enables

## Signals

- a cache header allows a shared cache to store an authenticated response
- a CORS origin is reflected with credentials allowed
- a server header names a version the vendor retired years ago
- an error response lacks the no-store header the success response had

## Patterns

**1. Cache risk**

```text
Cache-Control: public, max-age=6000 on an authenticated response
```

**2. CORS reflection**

```text
Access-Control-Allow-Origin: https://evil.example.test with credentials
```

**3. Version leak**

```text
Server: nginx/1.14.0 on a host that should not advertise it
```

## Pitfalls

- Treating a missing header as a finding without the behaviour it enables
- Checking only the success path and never the error path
- Reading the header from a proxy's synthetic response rather than the origin's

## Done when

- required and forbidden headers are both asserted explicitly
- each header finding names the concrete consequence

## References

- [OWASP - secure headers](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html)
- [MDN - Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
