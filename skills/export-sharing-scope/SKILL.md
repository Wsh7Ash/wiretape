---
name: export-sharing-scope
description: "Decide who receives an export before making it, since a tape is a map of an organisation's endpoints. Use when a tape or run report leaves your machine, including into a program's report form"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, sharing, scope]
---

# Export Sharing Scope

> Decide who receives an export before making it, since a tape is a map of an organisation's endpoints

**Use when:** a tape or run report leaves your machine, including into a program's report form

**Avoid when:** the artifact stays local and will be deleted after reading

## Procedure

1. List what the export contains: hosts, paths, header names, extracts
2. Remove hosts and paths outside the program's scope before sharing
3. Prefer a single finding's steps over a whole reconnaissance tape
4. Send through the program's channel rather than a public paste service
5. Keep the full tape locally until the program asks for more detail
6. Record what was shared and when, in case the scope question is raised

## Signals

- the shared artifact contains only in-scope hosts
- the export is limited to the steps that prove the finding
- no unrelated endpoint inventory rides along with the evidence
- the sharing channel is the program's own submission form

## Patterns

**1. Scoped subset**

```text
markdown export of steps authz-* only, hosts in scope
```

**2. Sharing channel**

```text
submitted through the program form, not a public gist
```

**3. Share log**

```text
shared 3 steps on 2026-10-29 under report 12345
```

## Pitfalls

- Uploading a full discovery tape that maps internal services no one asked about
- Sharing a report that names a host from a different program
- Pasting evidence into a public chat to ask a quick question

## Done when

- the shared artifact contains no out-of-scope host
- only the steps needed to prove the finding are exported

## References

- [HackerOne - disclosure guidance](https://docs.hackerone.com/)
- [OWASP - responsible disclosure](https://owasp.org/www-project-vulnerability-disclosure-cheatsheet/)
