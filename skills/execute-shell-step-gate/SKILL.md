---
name: execute-shell-step-gate
description: "Treat a tape as data that cannot run commands until a human enables it, and say so out loud. Use when a tape contains shell steps that process captures, sign requests or start a local service"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [execute, shell, safety]
---

# Execute Shell Step Gate

> Treat a tape as data that cannot run commands until a human enables it, and say so out loud

**Use when:** a tape contains shell steps that process captures, sign requests or start a local service

**Avoid when:** the tape contains only request and wait steps

## Procedure

1. Read every shell step before enabling execution, including substituted variables
2. Check whether any variable in the command comes from a remote response
3. Enable shell execution only for this run, never by default in a shared config
4. Print a warning naming the fact that commands will run as your user
5. Run with a timeout so a hanging command cannot stall the tape
6. Disable shell execution again for any tape you did not author

## Signals

- a run without the flag refuses the shell step and continues with the rest
- the refusal message names the step and says how to enable it
- the warning appears before the first command runs
- a command that exceeds its timeout is reported as a timeout, not a pass

## Patterns

**1. Gate refusal**

```text
shell step refused: pass --allow-shell to run commands
```

**2. Enablement warning**

```text
warning: --allow-shell executes commands from the tape as your user
```

**3. Command timeout**

```text
command timed out after 15s on step sign-request
```

## Pitfalls

- Enabling shell execution in a wrapper script so every tape runs commands
- Substituting a response value into a command without quoting it
- Treating a non-zero exit as a pass because the command printed something useful

## Done when

- shell steps are refused unless explicitly enabled for that run
- the enablement warning and the timeout are both observed

## References

- [Python - subprocess security](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [OWASP - command injection](https://owasp.org/www-community/attacks/Command_Injection)
