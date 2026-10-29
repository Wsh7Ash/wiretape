---
name: export-curl-reproduction
description: "Emit a curl command a triager can paste and run, with the origin absolute and the body quoted once. Use when a finding needs a one line reproduction that does not depend on your tools"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, curl, reproduction]
---

# Export Curl Reproduction

> Emit a curl command a triager can paste and run, with the origin absolute and the body quoted once

**Use when:** a finding needs a one line reproduction that does not depend on your tools

**Avoid when:** the request depends on state your tape produces and a single command cannot express it

## Procedure

1. Export the request with its headers in the authored order
2. Keep the method explicit rather than relying on the body to imply it
3. Quote the body exactly once so shell expansion cannot alter it
4. Redact credentials and tell the reader where to supply them
5. Run the exported command yourself against a lab and confirm it works
6. Paste the verified command into the report, not the untested draft

## Signals

- the exported command runs unchanged in a clean shell
- the request line path matches the path in the tape
- the redaction placeholder is visible where a credential belongs
- the response from the exported command matches the tape's recorded status

## Patterns

**1. Runnable line**

```text
curl --path-as-is --request DELETE 'https://api.example.test/v1/orders/1'
```

**2. Body quoting**

```text
--data-raw '{"amount":1}' with no shell expansion
```

**3. Credential note**

```text
--header 'Authorization: <redacted>' supplied from your environment
```

## Pitfalls

- Exporting a command that relies on a cookie left in your shell history
- Double quoting the body so the server receives literal backslashes
- Publishing a command containing a live token because the export looked tidy

## Done when

- the exported command has been run once and matched the recorded result
- no credential appears in the exported text

## References

- [curl - command line options](https://curl.se/docs/manpage.html)
- [RFC 9112 - request line](https://www.rfc-editor.org/rfc/rfc9112.html)
