---
name: assert-difference-between-roles
description: "Run one assertion set as two identities so a pass cannot come from the wrong principal. Use when testing authorisation, tenancy or role scoping where both outcomes return 200"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, authorization, roles]
---

# Assert Difference Between Roles

> Run one assertion set as two identities so a pass cannot come from the wrong principal

**Use when:** testing authorisation, tenancy or role scoping where both outcomes return 200

**Avoid when:** the endpoint has no notion of identity at all

## Procedure

1. Store the same request twice, once per identity, with distinct step ids
2. Extract each identity's own object id before the comparison
3. Assert the owner step returns the owner's data
4. Assert the other identity's step does not return that data
5. Confirm both assertions can fail by swapping the identities once
6. Keep the run as one tape so the comparison is not lost in notes

## Signals

- the owner gets 200 with their own object and the other role gets 403
- both get 200 but the second body contains the first tenant's fields
- the second role gets 200 with an empty body where 404 was expected
- swapping identities flips both results, proving the assertion is real

## Patterns

**1. Paired steps**

```text
read-order-as-owner and read-order-as-other
```

**2. Cross tenant fail**

```text
absent customer email in the second role's body
```

**3. Swap control**

```text
same requests with tokens exchanged produce mirrored results
```

## Pitfalls

- Testing one role and inferring what the other would see
- Comparing status codes only when both roles receive 200
- Using two accounts that share a team, so the authorisation boundary is not crossed

## Done when

- both identities have their own stored step and assertion
- the pair has been shown to fail when identities are swapped

## References

- [OWASP - access control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [PortSwigger - IDOR](https://portswigger.net/web-security/access-control/idor)
