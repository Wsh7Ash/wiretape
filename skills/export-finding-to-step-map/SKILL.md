---
name: export-finding-to-step-map
description: "Write the index that pairs each finding with the steps that prove it, so a retest is mechanical. Use when a program asks for a retest or a report contains more than one finding"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, index, retest]
---

# Export Finding to Step Map

> Write the index that pairs each finding with the steps that prove it, so a retest is mechanical

**Use when:** a program asks for a retest or a report contains more than one finding

**Avoid when:** the report covers a single step that speaks for itself

## Procedure

1. List each finding with a stable identifier of your own
2. Name the baseline step and the failing step for each finding
3. Record the expectation that should flip when the bug is fixed
4. Store the map beside the tapes so a retest can run the exact steps
5. Re-run the map after a patch and report each finding as fixed, open or changed
6. Keep the map in the report so a triager can reproduce one finding at a time

## Signals

- every finding maps to at least one failing step
- a retest run produces a per finding verdict without re-reading the report
- a fixed finding flips its step from fail to pass with no tape edits
- the map names the baseline used for comparison

## Patterns

**1. Map entry**

```text
idor-orders: baseline read-order-as-owner, failing read-order-as-other
```

**2. Retest verdict**

```text
idor-orders fixed: step now returns 403 as expected
```

**3. Stable id**

```text
html-injection-search-query, unchanged across two reports
```

## Pitfalls

- Writing findings that reference no step and cannot be retested
- Changing step ids during a retest so the map no longer matches
- Reporting a finding as fixed without running the mapped step again

## Done when

- each finding has a baseline step and a failing step in the map
- a retest produces one verdict per finding from the map alone

## References

- [HackerOne - retesting](https://docs.hackerone.com/)
- [OWASP - reporting](https://owasp.org/www-project-web-security-testing-guide/)
