---
name: execute-command-as-evidence
description: "Capture stdout, stderr and the exit code together, because a command's verdict is all three. Use when a shell step is used to prove something, such as a signature check or a parser result"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, evidence, exit-code]
---

# Execute Command as Evidence

> Capture stdout, stderr and the exit code together, because a command's verdict is all three

**Use when:** a shell step is used to prove something, such as a signature check or a parser result

**Avoid when:** the command is only a convenience that produces no evidence

## Procedure

1. Decide what the command proves and what a failure looks like
2. Run the command through the tape so its output is stored with the step
3. Store stdout, stderr, exit code and elapsed time together
4. Assert the exit code rather than grepping the output for the word error
5. Keep a copy of the input the command consumed, such as the captured response
6. Redact secrets from the stored output before export

## Signals

- a non-zero exit code fails the step even when stdout looks normal
- stderr contains a warning that explains a later step's behaviour
- the stored exit code matches what the report claims
- the command's input file is still beside the output for a recheck

## Patterns

**1. Full record**

```text
exit 2, stderr 'signature mismatch', 14 ms
```

**2. Assertion**

```text
expect returncode 0 on the verify-signature step
```

**3. Input kept**

```text
captures/order-create.response.http consumed by the verifier
```

## Pitfalls

- Piping output through a filter and losing the real exit status
- Storing stdout only and discarding the stderr that explained the failure
- Letting a warning on stderr pass as success because the code was zero

## Done when

- exit code, stdout and stderr are stored for every evidence command
- the step asserts the exit code rather than a text match

## References

- [POSIX - exit status](https://pubs.opengroup.org/onlinepubs/9699919799/)
- [GNU bash - exit status](https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html)
