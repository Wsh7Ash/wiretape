---
name: capture-naming-for-correlation
description: "Name every step after the question it answers so a report can point at the exact exchange. Use when a tape will hold more than a handful of steps or feed a written report"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, naming, reporting]
---

# Capture Naming for Correlation

> Name every step after the question it answers so a report can point at the exact exchange

**Use when:** a tape will hold more than a handful of steps or feed a written report

**Avoid when:** the tape is a single throwaway request you will delete immediately

## Procedure

1. Name step ids after the behaviour under test, not after the endpoint
2. Keep one hypothesis per step so a failure is unambiguous
3. Prefix variants with the baseline they derive from
4. Record the hypothesis in the step note, not only in your head
5. Reference the step id in the finding so the evidence is one lookup away
6. Rename a step when the hypothesis changes rather than reusing the id

## Signals

- a reader can tell what each step proved from its id alone
- variant ids share the baseline prefix and differ by the mutation
- every finding cites at least one step id
- no step id appears twice with different meanings across tapes

## Patterns

**1. Hypothesis id**

```text
authz-read-other-tenant-order
```

**2. Variant pair**

```text
cache-baseline and cache-no-vary-header
```

**3. Finding link**

```text
finding: idor-orders, steps authz-* in tape orders-2026-10-29
```

## Pitfalls

- Naming steps after HTTP verbs so three different tests share one id
- Bundling several mutations into one step and losing attribution
- Renaming steps after a report is written and breaking its references

## Done when

- each step id states the behaviour it tests
- every finding in the report cites concrete step ids

## References

- [OWASP - reporting](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST - security testing](https://csrc.nist.gov/pubs/sp/800/115/final)
