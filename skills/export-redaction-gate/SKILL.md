---
name: export-redaction-gate
description: "Verify redaction on the exported artifact itself, because the exporter is code and code has gaps. Use when any export leaves the workspace, especially to a program, a chat or a commit"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, redaction, verification]
---

# Export Redaction Gate

> Verify redaction on the exported artifact itself, because the exporter is code and code has gaps

**Use when:** any export leaves the workspace, especially to a program, a chat or a commit

**Avoid when:** the export is a throwaway diff of two timings with no headers or bodies

## Procedure

1. Know which header names and parameters the redactor covers
2. Export the artifact to a file and read it in full before sharing
3. Search the file for the literal credential you know is in the tape
4. Check bodies as well as headers, since a token is often in both
5. Add any secret you find in plaintext to the redaction list before re-exporting
6. Record in the report that the artifact was checked, and how

## Signals

- searching for the known token returns nothing in the artifact
- Authorization, Cookie and Set-Cookie lines show the placeholder
- a body field such as access_token is replaced rather than printed
- the redaction check is repeatable and part of the export step

## Patterns

**1. Literal search**

```text
grep for the session value returns no match
```

**2. Covered header**

```text
Set-Cookie: <redacted> in the HAR entries
```

**3. Body coverage**

```text
"access_token": "<redacted>" inside the JSON body
```

## Pitfalls

- Trusting a redaction list that only covers Authorization headers
- Exporting to stdout and pasting terminal scrollback that predates redaction
- Assuming an unusual header such as X-Amz-Security-Token is covered

## Done when

- a literal search for a known credential finds nothing in the artifact
- bodies and headers were both checked, not just headers

## References

- [OWASP - secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [CWE-532](https://cwe.mitre.org/data/definitions/532.html)
