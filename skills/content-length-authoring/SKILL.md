---
name: content-length-authoring
description: "Write a content length that disagrees with the body on purpose, and record what each layer believed. Use when testing how a server or intermediary frames a message body"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, framing, length]
---

# Content Length Authoring

> Write a content length that disagrees with the body on purpose, and record what each layer believed

**Use when:** testing how a server or intermediary frames a message body

**Avoid when:** the program forbids framing experiments or the endpoint is shared production

## Procedure

1. Start from a stored baseline whose content length matches its body
2. Author a variant whose content length is larger than the body actually sent
3. Author a second variant whose length is smaller than the body
4. Send each variant alone and record the status and how much body was read
5. Send a follow-up request on a fresh connection to see whether framing leaked
6. Record whether the server, an edge node or the application made the decision

## Signals

- the server waits for bytes that never arrive and the request times out
- the response body contains a truncated echo of the next request
- a 400 arrives from an edge layer while the origin never logs the request
- the response headers name a different length than the body you sent

## Patterns

**1. Oversized length**

```text
Content-Length: 100 with a 40 byte body
```

**2. Undersized length**

```text
Content-Length: 10 with a 40 byte body, remainder parsed as next
```

**3. Layer attribution**

```text
edge 400, origin has no access log entry for the request
```

## Pitfalls

- Sending a mismatched length at a shared edge and affecting other tenants
- Concluding smuggling from one desynchronised response without a second request
- Letting the client library recompute the length and erase the variant

## Done when

- each framing variant is stored with its observed status and body length
- the resolving layer is named in the notes, not guessed

## References

- [RFC 9112 - message body length](https://www.rfc-editor.org/rfc/rfc9112.html)
- [PortSwigger - request smuggling](https://portswigger.net/web-security/request-smuggling)
