---
name: assert-absent-for-negatives
description: "Prove a negative by asserting the forbidden content is missing, not by trusting a status code. Use when the hypothesis is that data is not returned, such as cross tenant or redacted fields"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [assert, negative, access]
---

# Assert Absent for Negatives

> Prove a negative by asserting the forbidden content is missing, not by trusting a status code

**Use when:** the hypothesis is that data is not returned, such as cross tenant or redacted fields

**Avoid when:** the response is a binary stream where absence cannot be expressed as text

## Procedure

1. Decide the exact string that must never appear in the response
2. Prefer a value belonging to the other principal, such as their email or id
3. Add an absent assertion to the step
4. Run the step and confirm it passes when the value is genuinely missing
5. Run a control that does return the value to prove the assertion can fail
6. Store both runs so the absence claim has a witness

## Signals

- the forbidden value is missing from a 200 response body
- the control step returns the value and fails the absent check as expected
- the absence holds across a second send and a second identity
- the response contains a placeholder instead of the value

## Patterns

**1. Forbidden value**

```text
absent tenant-b-customer-email in a 200 response
```

**2. Witness control**

```text
control step for the owning tenant returns that email
```

**3. Placeholder**

```text
field present as null rather than omitted entirely
```

## Pitfalls

- Asserting absence only on the status code, which can be 200 for a permission page
- Choosing a value that the endpoint never returns in any case
- Assuming absence in one representation means absence in every representation

## Done when

- the forbidden value has a control that proves the assertion can fail
- absence is checked on the body, not only on the status

## References

- [OWASP - broken access control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [NIST - access control](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
