---
name: execute-continue-versus-fail-fast
description: "Decide per run whether a failure should stop the tape, so you neither miss evidence nor waste sends. Use when a tape has independent steps or a destructive step that later steps depend on"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, failure, flow]
---

# Execute Continue Versus Fail Fast

> Decide per run whether a failure should stop the tape, so you neither miss evidence nor waste sends

**Use when:** a tape has independent steps or a destructive step that later steps depend on

**Avoid when:** the tape is a single step, where the question does not arise

## Procedure

1. Group steps into independent and dependent runs
2. Use fail fast for dependent flows, where a broken prerequisite invalidates the rest
3. Use continue for exploratory sweeps that gather independent observations
4. Mark skipped steps explicitly so a reader does not read them as passes
5. Record the mode in the run report
6. Re-run only the failed step after a fix, rather than repeating destructive ones

## Signals

- the report distinguishes failed, passed and skipped steps
- a destructive step failure prevents later steps from firing
- an exploratory sweep still reports the steps that ran after a failure
- the run mode is visible in the exported report

## Patterns

**1. Fail fast**

```text
create failed, confirm and cleanup skipped with a reason
```

**2. Continue**

```text
header sweep reports 3 passes and 2 failures in one run
```

**3. Skip label**

```text
skipped: earlier step failed (fail-fast)
```

## Pitfalls

- Continuing past a failed authentication so ten steps report misleading 401s
- Using fail fast on a sweep and concluding the untested steps were clean
- Re-running a whole tape to retest one step and duplicating side effects

## Done when

- the run mode is chosen deliberately and recorded
- skipped steps are labelled rather than silently absent

## References

- [OWASP - testing methodology](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST - security testing](https://csrc.nist.gov/pubs/sp/800/115/final)
