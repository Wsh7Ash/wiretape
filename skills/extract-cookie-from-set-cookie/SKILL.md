---
name: extract-cookie-from-set-cookie
description: "Read the session value from a set-cookie header without swallowing its attributes. Use when the session arrives in a Set-Cookie header and must be replayed in a Cookie header"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, cookies, session]
---

# Extract Cookie From Set Cookie

> Read the session value from a set-cookie header without swallowing its attributes

**Use when:** the session arrives in a Set-Cookie header and must be replayed in a Cookie header

**Avoid when:** the service authenticates with a bearer token in the body instead

## Procedure

1. Store the complete Set-Cookie value, including attributes
2. Capture only the name equals value pair for the Cookie header
3. Note the attributes: HttpOnly, Secure, SameSite, Domain and Path
4. Send the pair back in a Cookie header and confirm the identity it grants
5. Test whether the attributes match how the cookie is actually enforced
6. Record any attribute that is missing where it should have been set

## Signals

- the replayed cookie authenticates the same principal as the browser
- HttpOnly is absent on a session cookie that scripts could read
- SameSite is None without Secure, which browsers may still send
- Domain is broader than the host that issued it

## Patterns

**1. Full header**

```text
Set-Cookie: sid=abc123; Path=/; Secure; HttpOnly; SameSite=Lax
```

**2. Replay pair**

```text
Cookie: sid=abc123; other=value-from-response
```

**3. Attribute gap**

```text
Set-Cookie without HttpOnly on an authenticated session
```

## Pitfalls

- Copying the whole Set-Cookie value into the Cookie header with its attributes
- Assuming SameSite is enforced by the API rather than by the browser
- Losing a second Set-Cookie line when the response set two cookies

## Done when

- the replay cookie is the name and value pair only
- cookie attributes are recorded and any gap is noted

## References

- [RFC 6265 - cookies](https://www.rfc-editor.org/rfc/rfc6265.html)
- [OWASP - session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
