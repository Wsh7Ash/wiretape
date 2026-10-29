---
name: host-header-versus-origin
description: "Separate the three names a request carries, because the TLS name, Host header and connect address can disagree. Use when testing virtual host routing, password reset links or cache poisoning candidates"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, host, routing]
---

# Host Header Versus Origin

> Separate the three names a request carries, because the TLS name, Host header and connect address can disagree

**Use when:** testing virtual host routing, password reset links or cache poisoning candidates

**Avoid when:** the service is a single tenant host where all three names are identical by design

## Procedure

1. Record the connect address, the TLS server name and the Host header separately
2. Send the control where all three agree and store its digest
3. Change only the Host header and record the response and any absolute links
4. Change only the origin used to connect while keeping the Host header fixed
5. Look for the hostname reflected in redirects, links or cache keys
6. Report only the variants where the changed name changed behaviour

## Signals

- the response body contains the injected hostname in a link or form action
- a redirect points at the host you supplied rather than the canonical one
- two different Host values share a cache entry
- a 421 or 400 names the expected authority and reveals the routing rule

## Patterns

**1. Split names**

```text
connect 10.0.0.7, SNI api.example.test, Host evil.example.test
```

**2. Reflection**

```text
<form action="https://evil.example.test/reset">
```

**3. Cache key**

```text
same /v1/catalog response served for two Host values
```

## Pitfalls

- Changing the connect address and the Host header at the same time and losing attribution
- Calling any reflection a finding without a victim flow that follows the link
- Testing host routing on a service that terminates TLS at a shared edge

## Done when

- the three names are recorded separately for every variant
- behaviour change is attributed to exactly one changed name

## References

- [RFC 9110 - Host and authority](https://www.rfc-editor.org/rfc/rfc9110.html)
- [PortSwigger - host header attacks](https://portswigger.net/web-security/host-header)
