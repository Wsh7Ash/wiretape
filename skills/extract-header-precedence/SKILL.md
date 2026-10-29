---
name: extract-header-precedence
description: "Decide whether a value comes from a header or the body by testing which one the server obeys. Use when the same value appears in both a header and the body of a response"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, headers, precedence]
---

# Extract Header Precedence

> Decide whether a value comes from a header or the body by testing which one the server obeys

**Use when:** the same value appears in both a header and the body of a response

**Avoid when:** only one of the two carries the value, so there is no conflict to resolve

## Procedure

1. Record both copies of the value and confirm they match on the baseline
2. Send a follow-up request that contradicts one copy deliberately
3. Observe which copy the server acted on
4. Use that source in the tape's extraction so replay follows reality
5. Note any endpoint that behaves differently from the rest
6. Document the precedence rule where the tape is stored

## Signals

- a body value is ignored while the header value is enforced
- contradicting the body changes the response for one endpoint only
- the server accepts a header value that no client ever sends
- a signed header wins over an unsigned body field

## Patterns

**1. Contradiction**

```text
header says tenant A, body says tenant B, response is A
```

**2. Source choice**

```text
extract tenant from X-Tenant header, not the body
```

**3. Per endpoint note**

```text
the export endpoint reads the body, the API reads the header
```

## Pitfalls

- Extracting from the prettier source rather than the enforced one
- Assuming precedence is global when only one endpoint was tested
- Changing two conflicting values at once and losing attribution

## Done when

- the obeyed source is identified by a contradicting request
- the extraction uses the enforced source

## References

- [RFC 9110 - representation metadata](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OWASP - parameter pollution](https://owasp.org/www-project-web-security-testing-guide/)
