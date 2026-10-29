---
name: preserve-header-order-and-duplicates
description: "Keep repeated and oddly ordered headers intact, because collapsing them hides the bug you are hunting. Use when the request contains duplicate headers or an order that a proxy might normalise"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, headers, fidelity]
---

# Preserve Header Order and Duplicates

> Keep repeated and oddly ordered headers intact, because collapsing them hides the bug you are hunting

**Use when:** the request contains duplicate headers or an order that a proxy might normalise

**Avoid when:** the exchange is a plain GET with one instance of every header

## Procedure

1. Store headers as an ordered list of pairs rather than a map
2. Allow the same name twice and keep both values in their original positions
3. Record which duplicates are deliberate, such as two X-Forwarded-For values
4. Send the duplicated request and compare the response with the single-header control
5. Note the parsing difference between a comma-joined value and two separate lines
6. Keep both variants in the tape so the difference is reproducible later

## Signals

- the sent bytes contain both header lines in the authored order
- the response differs from the single-value control in status or body
- a proxy or server joins duplicates with a comma you did not write
- the last duplicate wins in application logic, giving a different identity

## Patterns

**1. Duplicate pair**

```text
X-Forwarded-For: 10.0.0.1 then X-Forwarded-For: 127.0.0.1
```

**2. Split identity**

```text
two Authorization lines lead to a 200 for a different user
```

**3. Order control**

```text
same headers sorted alphabetically as the comparison case
```

## Pitfalls

- Storing headers in a JSON object and silently keeping only the last duplicate
- Assuming the server concatenates duplicates the way the RFC suggests it may
- Testing duplicates only on a header the application never reads

## Done when

- duplicate headers survive the round trip into the sent bytes
- the duplicate and single-header responses are both recorded

## References

- [RFC 9110 - field lines and combining](https://www.rfc-editor.org/rfc/rfc9110.html)
- [PortSwigger - HTTP request smuggling](https://portswigger.net/web-security/request-smuggling)
