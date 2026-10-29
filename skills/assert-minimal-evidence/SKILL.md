---
name: assert-minimal-evidence
description: "Assert only what the finding needs, so a passing run never stores another person's data. Use when the step touches a response that could contain personal or customer data"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, evidence, privacy]
---

# Assert Minimal Evidence

> Assert only what the finding needs, so a passing run never stores another person's data

**Use when:** the step touches a response that could contain personal or customer data

**Avoid when:** the response is a fixture you own end to end

## Procedure

1. Decide the smallest observable that proves the behaviour: a status, a field name, a length
2. Assert a field's presence rather than its value where the value is sensitive
3. Keep only a redacted excerpt in the report, not the full body
4. Avoid storing a whole customer record even when the response includes it
5. Record how many records were visible rather than their contents
6. Delete any capture that contains third party data once the count is proven

## Signals

- the passing run names a field and a count but stores no record body
- the exported report contains the placeholder where values were
- the assertion would fail if the endpoint returned nothing at all
- the evidence is enough for a triager to reproduce without seeing customer data

## Patterns

**1. Field presence**

```text
contains "email" and contains "customer_id"
```

**2. Count only**

```text
response lists 37 records, none stored
```

**3. Redacted excerpt**

```text
"email": "<redacted>", "tenant_id": "other-tenant"
```

## Pitfalls

- Screenshotting a full record to make the report look convincing
- Asserting a specific email value, which then lives in the tape forever
- Keeping the raw capture directory after the count was proven

## Done when

- no third party value is stored in the tape or the export
- the assertion still proves the behaviour without the data

## References

- [OWASP - privacy risks](https://owasp.org/www-project-top-10-privacy-risks/)
- [HackerOne - report quality](https://docs.hackerone.com/)
