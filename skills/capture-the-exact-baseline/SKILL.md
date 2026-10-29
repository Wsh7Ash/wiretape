---
name: capture-the-exact-baseline
description: "Save the bytes you are about to send before you change anything, so every later mutation has a control. Use when you are about to test a hypothesis against an endpoint and have not yet stored a working baseline"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [capture, baseline, method]
---

# Capture the Exact Baseline

> Save the bytes you are about to send before you change anything, so every later mutation has a control

**Use when:** you are about to test a hypothesis against an endpoint and have not yet stored a working baseline

**Avoid when:** the request is already stored in a tape with its capture digest and a passing run

## Procedure

1. Send the request exactly as the application sent it, with no edits at all
2. Store the request bytes and the response bytes in separate files named after the step
3. Record the status, content type and body digest of the response
4. Confirm the exchange reproduces: send it again and compare digests
5. Only after the control reproduces, author the first mutation against it
6. Keep the baseline step in the tape so a regression is visible later

## Signals

- the baseline response digest repeats across two sends
- the stored request is byte-identical to the captured original
- the status and content type are recorded as facts, not expectations
- every mutation step in the tape names the baseline it differs from

## Patterns

**1. Stored pair**

```text
captures/order-read.request.http and order-read.response.http
```

**2. Control digest**

```text
response_sha256 9f2c41d0 matches on the second send
```

**3. Mutation reference**

```text
step order-id-swap derives from order-read baseline
```

## Pitfalls

- Editing the header order while capturing and losing the control you needed
- Trusting a status code without storing the body digest that came with it
- Capturing once and assuming the response is stable across sends

## Done when

- the baseline request and response bytes are stored under stable names
- a second send reproduces the baseline response digest

## References

- [RFC 9110 - HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP WSTG - testing methodology](https://owasp.org/www-project-web-security-testing-guide/)
