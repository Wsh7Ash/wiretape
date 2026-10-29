---
name: extract-created-id
description: "Take the identifier of the object you just created from the response, not from a guess. Use when a create step returns an id that later read, update and delete steps must target"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, id, objects]
---

# Extract Created Id

> Take the identifier of the object you just created from the response, not from a guess

**Use when:** a create step returns an id that later read, update and delete steps must target

**Avoid when:** the endpoint returns no identifier and the object must be found by listing

## Procedure

1. Create the object with a unique marker in a non-sensitive field
2. Extract the id from the body or from the Location header
3. Confirm the id resolves with a read before using it further
4. Use the id through a variable so every later step targets the same object
5. Delete or close the object at the end of the tape when the API allows it
6. Record the creation response digest as provenance for the id

## Signals

- the read of the extracted id returns the marker you sent
- Location ends in the same id the body contains
- the id is a predictable counter, which is itself worth noting
- a second create with the same marker returns a different id

## Patterns

**1. Body identifier**

```text
"id"\s*:\s*"([0-9a-f-]{36})"
```

**2. Location id**

```text
Location: /v1/orders/([0-9a-f-]{36})
```

**3. Provenance**

```text
create digest 71ab, read of the id returns marker wt-2026-10-29
```

## Pitfalls

- Guessing the next id after observing a counter, then testing an object you do not own
- Extracting the id from a list response and picking the wrong element
- Leaving created objects behind so the next run collides with them

## Done when

- the id used by later steps is the one the server returned
- the object is verified by read and cleaned up where possible

## References

- [RFC 9110 - Location](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP - IDOR](https://owasp.org/www-project-web-security-testing-guide/)
