---
name: export-raw-http-bundle
description: "Ship the exchange as raw HTTP text so another researcher can import the exact bytes. Use when the finding depends on framing, header order or exact body bytes"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, raw, fidelity]
---

# Export Raw HTTP Bundle

> Ship the exchange as raw HTTP text so another researcher can import the exact bytes

**Use when:** the finding depends on framing, header order or exact body bytes

**Avoid when:** the audience only needs a summary and a curl command

## Procedure

1. Export the captured request and response octets as text
2. Keep the request line, header order and blank line exactly as captured
3. Include the capture digest beside the bundle so it can be rechecked
4. Strip nothing except credentials, and mark where values were removed
5. Confirm the bundle parses back into the same request and response
6. Attach the bundle rather than pasting a screenshot of it

## Signals

- the bundle parses back to the same method, target and header list
- the body digest of the parsed response matches the recorded digest
- an unusual header line survives the round trip unchanged
- the file opens in a plain text editor without mojibake

## Patterns

**1. Bundle head**

```text
DELETE /v1/orders/42 HTTP/1.1 followed by the authored headers
```

**2. Digest line**

```text
# response_sha256 71abcd, 812 bytes
```

**3. Round trip**

```text
parse the exported text and compare with the stored capture
```

## Pitfalls

- Saving a re-serialised response and calling it raw
- Letting an editor convert line endings and changing the wire format
- Removing a header that looked like noise and thereby erasing the evidence

## Done when

- the exported text parses back to the same exchange
- the bundle states which values were redacted

## References

- [RFC 9112 - message format](https://www.rfc-editor.org/rfc/rfc9112.html)
- [NIST - evidence integrity](https://csrc.nist.gov/pubs/sp/800/86/final)
