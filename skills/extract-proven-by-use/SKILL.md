---
name: extract-proven-by-use
description: "Treat an extraction as valid only when a later step authenticates or succeeds with it. Use when a question turns on whether a value is genuinely accepted by the server"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, verification, method]
---

# Extract Proven by Use

> Treat an extraction as valid only when a later step authenticates or succeeds with it

**Use when:** a question turns on whether a value is genuinely accepted by the server

**Avoid when:** the value is diagnostic and never intended for reuse

## Procedure

1. Identify the step that will consume the extracted value
2. Add an expectation to the consumer that only succeeds with a valid value
3. Run the tape and confirm the consumer passes with the extraction
4. Break the value deliberately, for example truncate it, and confirm the failure
5. Restore the value and re-run to confirm the pass returns
6. Record the paired run as proof that the extraction matters

## Signals

- the consumer returns 200 with the extracted value and 401 with a truncated one
- the failure message names the authentication step, not the extraction
- the object read returns data only when the value was accepted
- restoring the value restores the pass without other edits

## Patterns

**1. Paired run**

```text
valid token 200, truncated token 401
```

**2. Consumer check**

```text
expect status [200] on the step that uses {{token}}
```

**3. Restored value**

```text
third run with the original value passes again
```

## Pitfalls

- Declaring success because the extraction printed a long string
- Testing the consumer against an endpoint that ignores authentication
- Leaving the deliberately broken variant in the tape as the last run

## Done when

- a later step passes only because the value was extracted correctly
- the negative variant is stored as evidence, not deleted

## References

- [OWASP - authentication testing](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST - security testing](https://csrc.nist.gov/pubs/sp/800/115/final)
