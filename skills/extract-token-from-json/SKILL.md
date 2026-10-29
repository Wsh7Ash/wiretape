---
name: extract-token-from-json
description: "Pull a token out of a JSON body with an anchored pattern instead of splitting the string. Use when a login or create response returns a token that later steps must present"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, json, token]
---

# Extract Token From Json

> Pull a token out of a JSON body with an anchored pattern instead of splitting the string

**Use when:** a login or create response returns a token that later steps must present

**Avoid when:** the token is already in a response header that can be read directly

## Procedure

1. Inspect the raw body once and note the exact key and its quoting
2. Write a regex that matches the key and captures the value as one group
3. Anchor the pattern on the key, not on position, so field order does not matter
4. Mark the extraction required so a missing token fails the step
5. Use the token in the next request as a variable reference, never by hand
6. Print the extracted value redacted when confirming the run

## Signals

- the extracted value is non-empty and the next step authenticates
- the pattern still matches when the response reorders its keys
- a missing token fails with a named extraction rather than an empty header
- the token is absent from logs and exports after redaction

## Patterns

**1. Anchored capture**

```text
"access_token"\s*:\s*"([^"]+)"
```

**2. Nested key**

```text
"data"\s*:\s*\{[^}]*"token"\s*:\s*"([^"]+)"
```

**3. Extraction failure**

```text
could not extract 'token' for step auth-login
```

## Pitfalls

- Splitting on a colon and taking the next slice, which breaks on escaped quotes
- Making the extraction optional so an empty header is sent silently
- Logging the extracted value in full while debugging and forgetting to remove it

## Done when

- a later step consumes the token through a variable reference
- a response without the token fails the step by name

## References

- [MDN - JSON](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON)
- [RFC 8259 - JSON](https://www.rfc-editor.org/rfc/rfc8259.html)
