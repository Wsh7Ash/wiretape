---
name: request-target-forms
description: "Compare origin-form, absolute-form and path tricks because routers disagree about which one wins. Use when an endpoint is reachable through an edge that routes on the request line"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, routing, target]
---

# Request Target Forms

> Compare origin-form, absolute-form and path tricks because routers disagree about which one wins

**Use when:** an endpoint is reachable through an edge that routes on the request line

**Avoid when:** the service is a plain application server with no path based router in front

## Procedure

1. Capture the working origin-form request as the control
2. Author an absolute-form target naming the same host and compare the response
3. Author a target with a dot segment such as /v1/../admin and compare routing
4. Author a target with an encoded slash and compare which layer decodes it
5. Record the status and the body difference for each form
6. Keep only the variants that produced a routing difference as findings

## Signals

- one form returns an admin page while the other returns the public page
- a WAF rule matches the encoded form but not the plain one
- the origin logs a different path than the edge matched on
- a redirect reveals the canonical path the router expected

## Patterns

**1. Absolute form**

```text
GET https://internal.example.test/admin HTTP/1.1
```

**2. Dot segment**

```text
GET /v1/../admin/orders HTTP/1.1
```

**3. Encoded slash**

```text
GET /admin%2Forders HTTP/1.1
```

## Pitfalls

- Assuming the client preserved the unusual target when it rewrote it
- Testing path tricks against an origin that never sees the raw path
- Reporting a routing difference without proving the response body changed meaning

## Done when

- each target form is stored with the routing outcome it produced
- any difference is attributable to a named layer

## References

- [RFC 9112 - request target](https://www.rfc-editor.org/rfc/rfc9112.html)
- [OWASP - path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
