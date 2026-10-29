---
name: keep-redirects-as-evidence
description: "Do not follow a 302 while capturing, because the redirect itself is often the observable. Use when the endpoint answers with a redirect whose Location carries the interesting value"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, redirects, evidence]
---

# Keep Redirects as Evidence

> Do not follow a 302 while capturing, because the redirect itself is often the observable

**Use when:** the endpoint answers with a redirect whose Location carries the interesting value

**Avoid when:** you are only checking reachability of a final page and the redirect is irrelevant

## Procedure

1. Disable redirect following for the capture
2. Store the status, the Location header and any body of the redirect itself
3. Inspect Location for host, scheme and parameter injection opportunities
4. Follow exactly one redirect deliberately as a separate step
5. Compare the followed result with the unfollowed record
6. Report the redirect response, never a re-rendered final page

## Signals

- Location points at a host you supplied rather than the canonical host
- the redirect body contains a link that the browser would render before following
- status is 307 and the method is preserved, unlike the 303 variant
- a redirect chain crosses from https to http

## Patterns

**1. Unfollowed record**

```text
302 Location: https://evil.example.test/landing
```

**2. Deliberate follow**

```text
step follows once with a fresh GET to /landing
```

**3. Scheme downgrade**

```text
301 from https origin to an http Location
```

## Pitfalls

- Letting the client follow redirects and logging only the final 200
- Missing an open redirect because the final page looked normal
- Following a redirect to a host outside scope

## Done when

- the redirect response is stored unfollowed with its Location
- any follow is a separate, deliberate step

## References

- [RFC 9110 - redirection](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP - open redirect](https://owasp.org/www-community/attacks/Unvalidated_Redirects_and_Forwards_Cheat_Sheet)
