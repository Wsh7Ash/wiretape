---
name: export-har-archive
description: "Produce a HAR 1.2 file so the evidence opens in the tools a triager already has. Use when a run should be reviewable in browser devtools, Burp or any HAR reader"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, har, interop]
---

# Export HAR Archive

> Produce a HAR 1.2 file so the evidence opens in the tools a triager already has

**Use when:** a run should be reviewable in browser devtools, Burp or any HAR reader

**Avoid when:** the finding hinges on bytes a HAR cannot represent, such as a malformed framing

## Procedure

1. Export after a run so responses carry real status and content
2. Check that every request entry has an absolute URL and a method
3. Confirm header order and duplicates survived into the HAR arrays
4. Redact credentials before writing the file, not after sharing it
5. Open the HAR in a reader and confirm the entries render
6. Note in the report that the HAR is redacted, so nobody hunts for the real token

## Signals

- the HAR opens without warnings in a standard reader
- entry count matches the number of request steps
- each response has the status the run recorded
- the header list preserves duplicates rather than merging them

## Patterns

**1. Entry shape**

```text
request.url absolute, request.method DELETE, response.status 403
```

**2. Duplicate header**

```text
two X-Forwarded-For objects in the headers array
```

**3. Redaction**

```text
Authorization value is the placeholder in every entry
```

## Pitfalls

- Exporting before the run and shipping entries with status 0
- Letting a HAR writer merge duplicate headers and losing the bug
- Sharing a HAR that still contains a session cookie

## Done when

- the HAR opens in a reader and entry count matches the tape
- credentials are redacted in the exported file

## References

- [W3C - HAR 1.2 spec](https://w3c.github.io/web-performance/specs/HAR/Overview.html)
- [MDN - network panel](https://developer.mozilla.org/en-US/docs/Tools/Network_Monitor)
