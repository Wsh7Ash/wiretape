---
name: execute-on-captured-output
description: "Feed a captured response into a local command instead of re-fetching, so the analysis is reproducible offline. Use when a response needs parsing, signature checking or decoding by another program"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, capture, offline]
---

# Execute on Captured Output

> Feed a captured response into a local command instead of re-fetching, so the analysis is reproducible offline

**Use when:** a response needs parsing, signature checking or decoding by another program

**Avoid when:** the analysis depends on live state that the capture no longer reflects

## Procedure

1. Capture the response to a file as part of the request step
2. Point the command at the captured file rather than at a URL
3. Keep the command's output beside the capture it consumed
4. Record the capture digest in the command step's note
5. Re-run the command later without network access to prove the analysis still holds
6. Replace the capture only when a new run supersedes it, and label the version

## Signals

- the command succeeds with networking disabled
- the output cites the capture digest it was derived from
- re-running on the same capture produces identical output
- a stale capture produces an obviously mismatched analysis

## Patterns

**1. File input**

```text
verify-signature captures/order-create.response.http
```

**2. Digest link**

```text
analysis of response_sha256 71abcd, captured 2026-10-29
```

**3. Offline rerun**

```text
same output with network access disabled
```

## Pitfalls

- Re-fetching inside the command and silently analysing a different response
- Overwriting a capture while a report still cites its digest
- Assuming a capture is complete when the body was truncated for display

## Done when

- the analysis consumes a stored capture, not a live request
- the command output is reproducible without network access

## References

- [NIST - evidence handling](https://csrc.nist.gov/pubs/sp/800/86/final)
- [OWASP - testing methodology](https://owasp.org/www-project-web-security-testing-guide/)
