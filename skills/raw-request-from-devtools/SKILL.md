---
name: raw-request-from-devtools
description: "Turn a browser's Copy as cURL into a replayable raw request without inheriting its normalisations. Use when the starting point is a request observed in a browser and you need it as portable bytes"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, browser, authoring]
---

# Raw Request From DevTools

> Turn a browser's Copy as cURL into a replayable raw request without inheriting its normalisations

**Use when:** the starting point is a request observed in a browser and you need it as portable bytes

**Avoid when:** the request is already available as a raw capture from another tool

## Procedure

1. Copy the request as cURL from the network panel, not as a fetch snippet
2. Rewrite the target into origin-form such as /v1/orders/42 rather than an absolute URL
3. Keep headers in the copied order, including ones a browser marks as forbidden
4. Move the body into the request file exactly as sent, byte for byte where it is text
5. Drop the shell quoting that curl added and keep the values verbatim
6. Send the authored request and diff the response digest against the browser's own

## Signals

- the authored target is a path, and the host lives in the origin setting
- the header list matches the copied order rather than alphabetical order
- the response digest matches what the browser received
- no cookie value was rewritten by a shell escape during the copy

## Patterns

**1. Origin-form line**

```text
POST /v1/orders/42 HTTP/1.1
```

**2. Copied header order**

```text
Host, Cookie, Content-Type, X-Requested-With, Accept
```

**3. Body fidelity**

```text
JSON body kept on one line exactly as the browser sent it
```

## Pitfalls

- Leaving the absolute URL in the request line and then changing the origin flag
- Letting a shell expand $TOKEN inside the copied curl command before it is stored
- Dropping headers the browser hides, such as Origin or content length

## Done when

- the request replays from the file with no shell interpretation
- the response digest matches the browser's captured response

## References

- [MDN - HTTP headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers)
- [RFC 9112 - HTTP/1.1 message syntax](https://www.rfc-editor.org/rfc/rfc9112.html)
