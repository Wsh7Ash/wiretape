# Security Policy

## Reporting a vulnerability in wiretape

Open a private advisory at
[github.com/Wsh7Ash/wiretape/security/advisories/new](https://github.com/Wsh7Ash/wiretape/security/advisories/new),
or email the maintainer address on the GitHub profile.

Include the version, a minimal tape or request, and the impact you expect.
Acknowledgement within seven days. Please do not open a public issue.

Areas worth probing:

- a tape that escapes the scope guard (host matching, IPv6 literals, trailing
  dots, userinfo in the origin URL);
- a shell step that runs without `--allow-shell`;
- an export path that emits a secret despite redaction;
- a parser that accepts a malformed message and then sends something different
  from what the author wrote.

## How the tool is meant to be used

wiretape sends HTTP requests and can run shell commands. Both are powerful and
both are gated, but the gates are policies, not permissions:

- **Scope is enforced, not advisory.** A request to a host outside `tape.scope`
  is refused before a socket opens. Do not patch that out; put the host in scope
  or do not run the tape.
- **Shell is opt-in.** `--allow-shell` runs commands as your user, with your
  filesystem access. Read the commands first. A tape is data, and data can come
  from someone else.
- **Redaction is applied on the way out**, not on the way in: captures keep what
  arrived so evidence is intact, and every printer, exporter and report redacts.

## Rules of engagement for users

1. Test only assets in scope for a program you have joined, or your own systems.
2. Respect program rules on automation and on malformed-traffic experiments.
   Framing tests (`content-length-authoring`) can affect shared edge
   infrastructure; do not run them where the program forbids it.
3. Keep the volume low. `replay-stability-sample` asks for five sends, not fifty.
4. Do not collect third party data. If a response contains it, record the fact
   and a count, not the records. The `assert-minimal-evidence` skill is the
   checklist.
5. Delete captures that contain credentials once the finding is written, and
   rotate any credential that was used during testing.
6. Report through the program's channel. Do not paste a tape containing an
   endpoint inventory into a public chat or gist.

## What wiretape does not protect you from

- A malicious tape you chose to run with `--allow-shell`.
- A target that is hostile to your client (very large bodies are read into
  memory; there is a per-step timeout but no body size cap).
- Traffic analysis on a network you do not control. Use TLS and verify it; only
  pass `--insecure` against a lab you own.

## Supported versions

| Version | Supported |
|---|---|
| 1.x | yes |
