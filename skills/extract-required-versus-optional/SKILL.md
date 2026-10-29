---
name: extract-required-versus-optional
description: "Mark an extraction required only when a missing value should stop the tape. Use when a tape extracts several values that differ in how critical they are"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, failure, design]
---

# Extract Required Versus Optional

> Mark an extraction required only when a missing value should stop the tape

**Use when:** a tape extracts several values that differ in how critical they are

**Avoid when:** every extracted value is essential and the distinction adds nothing

## Procedure

1. List every extracted value and what breaks if it is missing
2. Mark values the next step cannot run without as required
3. Mark diagnostic values such as a request id as optional
4. Confirm an optional miss is recorded but does not fail the step
5. Confirm a required miss fails with the extraction name in the message
6. Re-read the tape when a required value becomes optional to avoid stale strictness

## Signals

- a required miss stops the tape with a named extraction failure
- an optional miss appears in the result without a failure verdict
- the next step never receives an empty substituted value
- the tape's failure message says which value was missing

## Patterns

**1. Required**

```text
token: {from body, regex ..., required true}
```

**2. Optional**

```text
request_id: {from header X-Request-Id, required false}
```

**3. Failure verdict**

```text
step failed: could not extract 'token'
```

## Pitfalls

- Making everything required so one absent diagnostic value fails the run
- Making everything optional so an unauthenticated request is sent quietly
- Treating a present but empty value as a successful extraction

## Done when

- each extraction states whether a miss is fatal
- both failure modes are exercised at least once

## References

- [RFC 9110 - response header fields](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP - testing methodology](https://owasp.org/www-project-web-security-testing-guide/)
