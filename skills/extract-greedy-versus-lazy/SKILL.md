---
name: extract-greedy-versus-lazy
description: "Choose the quantifier deliberately so a capture stops at the value instead of the document end. Use when a regex capture returns far more text than the value you wanted"
pack: wiretape
version: 1.0.0
category: http-security-tooling
tags: [extract, regex, precision]
---

# Extract Greedy Versus Lazy

> Choose the quantifier deliberately so a capture stops at the value instead of the document end

**Use when:** a regex capture returns far more text than the value you wanted

**Avoid when:** the pattern is already anchored by a closing quote or a fixed delimiter

## Procedure

1. Run the pattern against a stored body and inspect the captured group
2. Replace a greedy dot star with a negated character class where possible
3. Anchor the capture with the literal characters that end the value
4. Test the pattern against a body containing two candidate matches
5. Confirm the first match is the intended one, or add an anchor to disambiguate
6. Store the corrected pattern in the tape so the extraction is reproducible

## Signals

- the captured group is exactly the value length you expected
- the pattern matches once rather than many times
- a second run of the same pattern yields the same value
- the capture fails loudly when the value is absent

## Patterns

**1. Greedy mistake**

```text
"token":"(.*)" captures the rest of the document
```

**2. Bounded capture**

```text
"token":"([^"]+)" stops at the closing quote
```

**3. Disambiguated**

```text
"data":\{[^}]*"id":"([^"]+)"
```

## Pitfalls

- Using dot star across newlines without enabling multiline thinking
- Assuming the first match is the right one when the body repeats the key
- Rewriting the pattern per run instead of storing the working version

## Done when

- the capture is bounded by a literal delimiter or a negated class
- the pattern is verified against a body with two candidates

## References

- [Python - regular expression syntax](https://docs.python.org/3/library/re.html)
- [MDN - quantifiers](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions/Cheatsheet)
