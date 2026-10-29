---
name: capture-response-octets
description: "Store the response as it arrived with a digest, so a claim about bytes can be rechecked without the server. Use when a response will be cited as evidence in a report or a retest"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, evidence, digest]
---

# Capture Response Octets

> Store the response as it arrived with a digest, so a claim about bytes can be rechecked without the server

**Use when:** a response will be cited as evidence in a report or a retest

**Avoid when:** the exchange is a throwaway connectivity check with no evidentiary value

## Procedure

1. Write the received bytes to a file before any decoding or parsing
2. Compute a SHA-256 over those bytes and store it with the step result
3. Record the status line, header block and body length as separate facts
4. Note where the body was truncated, if a display limit applied
5. Keep the capture directory beside the tape so a reader can recheck it
6. Re-derive the digest when exporting to prove the export matches the capture

## Signals

- the stored digest recomputes from the stored file
- the body length in the record matches the bytes on disk
- a conflicting header and body length is visible in the stored octets
- the exported evidence cites the same digest as the run report

## Patterns

**1. Stored octets**

```text
captures/order-read.response.http with 812 bytes
```

**2. Digest record**

```text
response_sha256 2f9a01c4bd53e71a
```

**3. Truncation note**

```text
display truncated at 2000 chars, capture is complete
```

## Pitfalls

- Storing a re-serialised response and calling it the server's bytes
- Recording a digest of decoded text rather than of the received octets
- Deleting the capture directory and keeping only a screenshot of it

## Done when

- the response octets and their digest are stored together
- the digest recomputes from the stored file at export time

## References

- [RFC 9110 - message content](https://www.rfc-editor.org/rfc/rfc9110.html)
- [NIST - evidence handling](https://csrc.nist.gov/pubs/sp/800/86/final)
