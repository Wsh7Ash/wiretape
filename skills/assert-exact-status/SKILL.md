---
name: assert-exact-status
description: "Assert the status you expect rather than a class, so a silent downgrade to a handled error is visible. Use when a step's meaning depends on a specific code such as 200, 201 or 403"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, status, precision]
---

# Assert Exact Status

> Assert the status you expect rather than a class, so a silent downgrade to a handled error is visible

**Use when:** a step's meaning depends on a specific code such as 200, 201 or 403

**Avoid when:** the endpoint legitimately returns several success codes and the class is the point

## Procedure

1. Record the observed status on the baseline run
2. Write the expected status as the exact code, not a range
3. Run the tape and confirm the step passes with that code
4. Change the expectation to a neighbouring code and confirm the step fails
5. Restore the expectation and re-run to confirm the pass
6. Add a second allowed code only when the API documents both

## Signals

- the tape fails when the server returns 200 instead of the expected 201
- a handled 400 replaces a 500 and the assertion catches it
- the failure message states the observed and expected codes
- an undocumented second code appears during a rerun

## Patterns

**1. Exact expectation**

```text
expect status [201] on the create step
```

**2. Downgrade caught**

```text
observed 200, expected 201, step failed
```

**3. Documented pair**

```text
expect status [200, 204] where the API allows both
```

## Pitfalls

- Asserting 2xx and calling any success a pass
- Hard coding 200 on a create endpoint that documents 201
- Loosening the assertion after a failure instead of investigating the failure

## Done when

- every request step asserts an explicit status list
- a wrong code produces a failure naming both codes

## References

- [RFC 9110 - status codes](https://www.rfc-editor.org/rfc/rfc9110.html)
- [MDN - HTTP response status](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
