---
name: execute-local-lab-first
description: "Rehearse a destructive or frame sensitive tape against a local service before it ever touches scope. Use when the tape sends malformed framing, destructive verbs or high volume"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, lab, rehearsal]
---

# Execute Local Lab First

> Rehearse a destructive or frame sensitive tape against a local service before it ever touches scope

**Use when:** the tape sends malformed framing, destructive verbs or high volume

**Avoid when:** the tape is a single read against a documented staging host

## Procedure

1. Start a local server that implements the minimum behaviour you need
2. Point the tape's origin at the loopback address and add it to scope
3. Run the tape and confirm every step's expectations behave as intended
4. Break the lab server deliberately to confirm the assertions fail correctly
5. Only then switch the origin to the authorised host and re-run
6. Record both runs so the rehearsal is part of the evidence

## Signals

- the tape passes locally and fails as expected when the lab is broken
- no request left the machine during the rehearsal
- the first scoped run behaves the same as the rehearsal
- a framing variant that kills the lab server is caught before production

## Patterns

**1. Loopback origin**

```text
origin http://127.0.0.1:8080 with scope [127.0.0.1]
```

**2. Broken lab**

```text
server returns 200 for everything, the 403 assertion fails
```

**3. Promotion**

```text
same tape, origin switched to the staging host
```

## Pitfalls

- Skipping the rehearsal because the test looks harmless
- Building a lab server so permissive that every assertion passes
- Leaving the lab origin in the tape when promoting it to a real target

## Done when

- the tape has run end to end against a local server
- the assertions have been shown to fail on a deliberately broken lab

## References

- [Python - http.server](https://docs.python.org/3/library/http.server.html)
- [OWASP - testing environment](https://owasp.org/www-project-web-security-testing-guide/)
