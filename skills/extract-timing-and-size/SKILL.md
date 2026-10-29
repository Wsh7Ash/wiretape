---
name: extract-timing-and-size
description: "Record elapsed time and body size as observations, so a blind finding can be argued with numbers. Use when testing blind injection, existence oracles or enumeration where the body is identical"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, timing, oracles]
---

# Extract Timing and Size

> Record elapsed time and body size as observations, so a blind finding can be argued with numbers

**Use when:** testing blind injection, existence oracles or enumeration where the body is identical

**Avoid when:** the response body already differs clearly between the two cases

## Procedure

1. Measure the baseline latency several times and record the spread
2. Measure the candidate condition the same number of times
3. Compare medians rather than single samples
4. Record body sizes for both cases even when the bytes look identical
5. Look for a size difference that a status code does not reveal
6. Report a timing claim only when the difference exceeds the observed spread

## Signals

- the candidate median is several times the baseline median
- body sizes differ by a constant amount across repeats
- one case consistently returns a marginally larger payload
- the spread within a case is small enough for the difference to mean something

## Patterns

**1. Median compare**

```text
baseline 42 ms, candidate 610 ms over five sends each
```

**2. Size oracle**

```text
403 with 211 bytes versus 403 with 213 bytes
```

**3. Spread guard**

```text
within-case spread 6 ms, observed difference 568 ms
```

## Pitfalls

- Reporting a single slow response as a timing oracle
- Ignoring network jitter on a mobile or cross region path
- Publishing timings without the sample count that produced them

## Done when

- both cases have a recorded sample count and spread
- the claim is larger than the noise in the data

## References

- [OWASP - blind injection](https://owasp.org/www-project-web-security-testing-guide/)
- [PortSwigger - blind SQL injection](https://portswigger.net/web-security/sql-injection/blind)
