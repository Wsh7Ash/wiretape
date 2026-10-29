---
name: export-markdown-report
description: "Turn a run into a table plus per step evidence, so the report is generated from the facts not retyped. Use when a finding is ready to write up and the tape already contains every exchange"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, report, markdown]
---

# Export Markdown Report

> Turn a run into a table plus per step evidence, so the report is generated from the facts not retyped

**Use when:** a finding is ready to write up and the tape already contains every exchange

**Avoid when:** the finding needs narrative reasoning that no generated table can carry

## Procedure

1. Export the markdown report from the finished run
2. Read it as a whole and add the narrative: what was expected versus observed
3. Keep the generated table and paste it rather than retyping statuses
4. Add the impact paragraph above the table, since triagers read the top first
5. Check that every claim in the prose points at a step id
6. Attach the redacted run report JSON beside the markdown

## Signals

- every status in the report matches the run report exactly
- failures section lists only the steps that actually failed
- the extracted variables table shows placeholders for secrets
- prose claims cite step ids rather than vague references

## Patterns

**1. Table row**

```text
authz-read-other 403 /v1/orders/42 FAIL
```

**2. Failure entry**

```text
body lacks 'order' after a 403 permission page
```

**3. Attachment**

```text
run.json redacted, 6 steps, 2 failures
```

## Pitfalls

- Retyping statuses into a report and introducing numbers the run never produced
- Exporting before the run finished so the table says not run
- Publishing the table with live tokens in the extracted variables

## Done when

- every factual claim in the report is traceable to a step id
- the exported table matches the run report without manual edits

## References

- [HackerOne - report writing](https://docs.hackerone.com/)
- [OWASP - reporting](https://owasp.org/www-project-web-security-testing-guide/)
