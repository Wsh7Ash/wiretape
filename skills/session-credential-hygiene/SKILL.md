---
name: session-credential-hygiene
description: "Keep live cookies and tokens out of tapes, commits and exports while still reproducing the request. Use when the request under test carries a session cookie, bearer token or API key"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, secrets, hygiene]
---

# Session Credential Hygiene

> Keep live cookies and tokens out of tapes, commits and exports while still reproducing the request

**Use when:** the request under test carries a session cookie, bearer token or API key

**Avoid when:** the credential is a lab value minted for a throwaway local account

## Procedure

1. Replace the live value with a variable reference such as {{session}}
2. Keep the real value in an environment file that is gitignored
3. Confirm the tape runs with the variable supplied and fails clearly without it
4. Check the export path redacts the header rather than printing the value
5. Mint a separate low privilege account for capture, not your primary one
6. Rotate the credential after the engagement if it was ever written to disk

## Signals

- no committed file contains a value that grants access
- running without the variable fails with a named missing variable
- the curl export shows the redaction placeholder in the header
- a second account with fewer roles produces a different but usable tape

## Patterns

**1. Variable reference**

```text
Cookie: session={{session}}
```

**2. Environment hold**

```text
.env.local with WIRETAPE_SESSION, gitignored
```

**3. Export view**

```text
Authorization: <redacted> in the generated curl
```

## Pitfalls

- Committing a tape captured with a live cookie and deleting it later
- Putting the token in the tape's variables block as a default value
- Testing with an administrator session and missing the role question

## Done when

- every credential in the tape is a variable, not a literal
- the redaction is verified on an actual export, not assumed

## References

- [OWASP - secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub - ignoring files](https://docs.github.com/en/get-started/git-basics/ignoring-files)
