---
name: export-digest-provenance
description: "Attach request and response digests to every exported claim, so a later reader can prove what was captured. Use when an export will be cited in a report, a retest or a dispute with a triager"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [export, provenance, digest]
---

# Export Digest Provenance

> Attach request and response digests to every exported claim, so a later reader can prove what was captured

**Use when:** an export will be cited in a report, a retest or a dispute with a triager

**Avoid when:** the export is an internal note that will never be referenced again

## Procedure

1. Record a digest of the sent bytes and the received bytes per step
2. Keep the capture files beside the tape under the same step id
3. Include the digests in the run report and the markdown table
4. State the digest algorithm alongside the value, not just the hex
5. Recompute the digest from the stored capture when the export is made
6. Refuse to export a claim whose digest no longer matches its capture

## Signals

- the digest in the report recomputes from the stored capture
- a changed capture produces a visible digest mismatch
- the algorithm and truncation length are stated with the value
- two exports of the same run carry identical digests

## Patterns

**1. Pair of digests**

```text
request_sha256 5c1e, response_sha256 9f2a
```

**2. Algorithm note**

```text
SHA-256 of the received octets, first 16 hex characters
```

**3. Mismatch**

```text
capture digest 9f2a does not match the report value 9f2b
```

## Pitfalls

- Publishing a digest of decoded text rather than the received bytes
- Truncating a digest without saying so and confusing a later comparison
- Letting a capture be overwritten while an export still cites it

## Done when

- every exported claim carries a digest and an algorithm
- the digests recompute from the stored captures at export time

## References

- [NIST - hash functions](https://csrc.nist.gov/pubs/fips/180-4/final)
- [NIST - evidence handling](https://csrc.nist.gov/pubs/sp/800/86/final)
