---
name: replay-body-encodings
description: "Send the same logical body as JSON, form, multipart and XML to find the parser that validates least. Use when an endpoint accepts structured bodies and more than one content type"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [replay, parsing, content-type]
---

# Replay Body Encodings

> Send the same logical body as JSON, form, multipart and XML to find the parser that validates least

**Use when:** an endpoint accepts structured bodies and more than one content type

**Avoid when:** the endpoint rejects unknown content types before parsing, which the baseline already proves

## Procedure

1. Store the baseline body and its content type
2. Re-encode the same fields as form data and send with the form content type
3. Re-encode as multipart with the same field names and compare
4. Re-encode as XML if the service advertises it anywhere
5. Record which encoder each layer actually used, from errors and echoes
6. Report the variant that reached the widest code path

## Signals

- a type mismatch produces a stack trace naming a different parser
- the form variant bypasses validation the JSON branch enforced
- duplicate field names resolve differently between encodings
- an XML entity in a text field is resolved rather than escaped

## Patterns

**1. JSON to form**

```text
same keys, application/x-www-form-urlencoded, 200 instead of 422
```

**2. Multipart**

```text
field name repeated to test first versus last wins
```

**3. Type confusion**

```text
amount sent as a string where the JSON branch required a number
```

## Pitfalls

- Changing the body and the content type and the path in one replay
- Assuming a 415 means the parser is safe rather than unreachable
- Sending XML with external entities to a shared parser without permission

## Done when

- each encoding is stored with the parser the response implies
- any validation difference between encodings is documented with evidence

## References

- [MDN - content type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type)
- [OWASP - XXE prevention](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
