---
name: assert-structured-regex
description: "Use a regex assertion when the reply must have a shape, such as an id at a known position. Use when the reply's meaning depends on a format, ordering or field presence rule"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, regex, structure]
---

# Assert Structured Regex

> Use a regex assertion when the reply must have a shape, such as an id at a known position

**Use when:** the reply's meaning depends on a format, ordering or field presence rule

**Avoid when:** a plain substring already distinguishes the outcomes without ambiguity

## Procedure

1. Write the smallest regex that expresses the required shape
2. Keep it anchored to the key or tag it belongs to rather than the whole body
3. Test the pattern against one passing and one failing stored response
4. Add it to the step expectation and confirm the pass
5. Record why the shape matters, since a future reader cannot infer intent
6. Narrow the pattern when it starts matching error pages

## Signals

- the pattern matches the success body and not the error body
- the field order in the response does not affect the match
- a missing field fails the step with the pattern printed
- the pattern tolerates whitespace differences in pretty printed JSON

## Patterns

**1. Order shape**

```text
\{"order_id":"[0-9a-f-]{36}","status":"(created|pending)"
```

**2. Header shape**

```text
Location: /v1/orders/[0-9a-f-]{36}\r?\n
```

**3. Tolerant match**

```text
"status"\s*:\s*"created" matches compact and pretty JSON
```

## Pitfalls

- Writing a pattern that matches the whole document and therefore always passes
- Assuming field order is stable when the server serialises from a map
- Using a regex where a substring would state intent more plainly

## Done when

- the pattern has been shown to reject a real error response
- the intent of the shape check is written beside the pattern

## References

- [Python - re module](https://docs.python.org/3/library/re.html)
- [RFC 8259 - JSON grammar](https://www.rfc-editor.org/rfc/rfc8259.html)
