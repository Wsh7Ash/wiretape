---
name: assert-error-path-parity
description: "Assert the same protections on the failure path, because error handlers are where security headers and access checks go missing. Use when a success response has been checked for the headers and redaction the endpoint needs"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, errors, parity]
---

# Assert Error Path Parity

> Assert the same protections on the failure path, because error handlers are where security headers and access checks go missing

**Use when:** a success response has been checked for the headers and redaction the endpoint needs

**Avoid when:** the endpoint has no error path that returns a body, such as a 204 only endpoint

## Procedure

1. Choose an input that provokes a handled error, such as a missing required field
2. Capture the error response and compare its headers with the success response
3. Assert that the cache and security headers are not weaker on the error path
4. Look for stack traces, file paths and framework versions in the body
5. Repeat for an unauthenticated request so the 401 path is covered too
6. Record which handler produced the response, when a header or body reveals it

## Signals

- the error response lacks a no-store header the success response had
- a validation error echoes the internal field names of the model
- the 500 path returns a trace while the 400 path returns JSON
- the unauthenticated error names the expected token format

## Patterns

**1. Header parity**

```text
success has no-store, the 422 does not
```

**2. Trace leak**

```text
Traceback (most recent call last) in the 500 body
```

**3. Model echo**

```text
invalid value for field internal_pricing_tier
```

## Pitfalls

- Checking only the happy path because the feature works there
- Sending malformed input that the edge rejects before the application sees it
- Reporting a verbose error without the information it actually disclosed

## Done when

- success and error headers are compared for the same endpoint
- any disclosed internal detail is quoted in the note with its source

## References

- [OWASP - error handling](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html)
- [CWE-209](https://cwe.mitre.org/data/definitions/209.html)
