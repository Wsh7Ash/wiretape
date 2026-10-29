---
name: replay-connection-reuse
description: "Compare a fresh connection with a reused one, because per-connection state can change the answer. Use when testing authentication caching, connection scoped state or keep-alive behaviour"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, connection, state]
---

# Replay Connection Reuse

> Compare a fresh connection with a reused one, because per-connection state can change the answer

**Use when:** testing authentication caching, connection scoped state or keep-alive behaviour

**Avoid when:** the client cannot hold a connection open in a controlled way

## Procedure

1. Send the request on a fresh connection and store the result
2. Send two requests on one connection, changing identity between them
3. Record whether the second response reflects the second identity
4. Close and reopen, then repeat the first request to confirm the reset
5. Note any cached authorisation visible only on the reused connection
6. Keep both variants in the tape as separate steps

## Signals

- the second request on a reused connection returns the first identity's data
- a 401 appears only when the connection is fresh
- the server sends Connection close despite a keep-alive request
- an authentication challenge is skipped on a reused connection

## Patterns

**1. Fresh connection**

```text
TLS handshake, one request, response for identity A
```

**2. Reused connection**

```text
same socket, identity B, response still for identity A
```

**3. Reset check**

```text
new socket with identity B returns identity B correctly
```

## Pitfalls

- Assuming a library pools connections the way you expect without checking
- Reporting cross identity leakage that was actually a client side cache
- Holding a connection open long enough to trip server idle timeouts

## Done when

- both fresh and reused connection results are stored
- any state difference is attributed to the connection, not the identity

## References

- [RFC 9112 - persistent connections](https://www.rfc-editor.org/rfc/rfc9112.html)
- [OWASP - session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
