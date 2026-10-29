---
name: extract-csrf-from-markup
description: "Find the anti-forgery token in the page the server actually rendered for this session. Use when a state changing form or API call requires a token embedded in markup"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, csrf, markup]
---

# Extract Csrf From Markup

> Find the anti-forgery token in the page the server actually rendered for this session

**Use when:** a state changing form or API call requires a token embedded in markup

**Avoid when:** the service uses a double submit cookie pattern with no server side token

## Procedure

1. Fetch the form page as the same identity that will submit it
2. Search the body for hidden inputs, meta tags and inline script assignments
3. Write a capture that matches the token by its name attribute
4. Submit the form with the extracted token and confirm acceptance
5. Reuse the token a second time to learn whether it is single use
6. Note whether the token is bound to the session or to the form only

## Signals

- the token differs per session, proving it is bound to the principal
- the same token is accepted twice, which weakens replay protection
- the token appears in a meta tag that client code reads
- a token from another session is rejected with a specific error

## Patterns

**1. Hidden input**

```text
<input type="hidden" name="csrf_token" value="([^"]+)"
```

**2. Meta tag**

```text
<meta name="csrf-token" content="([^"]+)">
```

**3. Binding check**

```text
same token submitted from a second session returns 403
```

## Pitfalls

- Scraping a token from a cached page rendered for a different session
- Reusing one token across a batch of submissions when it is single use
- Assuming a token in markup protects an endpoint that never verifies it

## Done when

- the extracted token is accepted by the state changing request
- token reuse and session binding are both recorded

## References

- [OWASP - CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN - SameSite cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
