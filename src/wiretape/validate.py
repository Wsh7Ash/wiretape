"""Validation rules for the skill corpus.

``validate`` is the gate that "50/50 skills valid" refers to: every rule below
is enforced on every run, and the CLI exits non-zero when any rule fails.
Rules cover structure (front-matter, required sections), strength (step,
signal, pattern and word-count floors) and hygiene (no placeholders, no
machine-local paths, canonical https references).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .model import Skill
from .render import render_description, render_skill, word_count

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REF_RE = re.compile(r"^\[[^\]]+\]\(https://[^)\s]+\)$")
TAG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FORBIDDEN_RE = re.compile(
    r"\b(TODO|FIXME|TBD|lorem ipsum|coming soon|your text here|placeholder text)\b",
    re.IGNORECASE,
)
LOCAL_PATH_RE = re.compile(r"(C:\\|F:/|/Users/|/home/|/private/)")

# Strength floors.
MIN_STEPS = 6
MIN_SIGNALS = 4
MIN_PATTERNS = 3
MIN_PITFALLS = 3
MIN_DONE = 2
MIN_REFS = 1
MIN_TAGS = 2
MIN_WORDS = 180
MIN_SUMMARY = 40
MIN_CLAUSE = 30
MIN_DESCRIPTION = 120
MAX_DESCRIPTION = 1024
MIN_STEP_LEN = 25
MIN_SIGNAL_LEN = 15
MIN_PATTERN_LABEL = 8
MIN_PATTERN_CODE = 20
MIN_PITFALL_LEN = 30
MIN_DONE_LEN = 20


@dataclass(frozen=True)
class Issue:
    slug: str
    rule: str
    message: str

    def __str__(self) -> str:
        where = self.slug or "<pack>"
        return f"{where}: {self.rule}: {self.message}"


def skill_issues(pack: dict[str, Any], skill: Skill, rendered: str) -> list[Issue]:
    """Structural, strength and hygiene rules for a single skill."""
    issues: list[Issue] = []

    def add(rule: str, message: str) -> None:
        issues.append(Issue(skill.slug, rule, message))

    if not SLUG_RE.match(skill.slug):
        add("slug-format", f"{skill.slug!r} must be lowercase kebab-case")
    if not skill.title or skill.title.lower() == skill.title:
        add("title-case", "title must be present and start with a capital")
    if len(skill.summary) < MIN_SUMMARY:
        add("summary-length", f"summary must be at least {MIN_SUMMARY} chars")
    if len(skill.use_when) < MIN_CLAUSE:
        add("use-when", f"use_when must be at least {MIN_CLAUSE} chars")
    if len(skill.avoid_when) < MIN_CLAUSE:
        add("avoid-when", f"avoid_when must be at least {MIN_CLAUSE} chars")

    description = render_description(skill)
    if not MIN_DESCRIPTION <= len(description) <= MAX_DESCRIPTION:
        add(
            "description-length",
            f"description must be {MIN_DESCRIPTION}-{MAX_DESCRIPTION} chars, got {len(description)}",
        )

    if len(skill.tags) < MIN_TAGS:
        add("tags-count", f"at least {MIN_TAGS} tags required")
    if len(set(skill.tags)) != len(skill.tags):
        add("tags-unique", "tags must be unique")
    for tag in skill.tags:
        if not TAG_RE.match(tag):
            add("tags-format", f"tag {tag!r} must be lowercase kebab-case")

    if len(skill.steps) < MIN_STEPS:
        add("steps-count", f"at least {MIN_STEPS} steps required, got {len(skill.steps)}")
    for step in skill.steps:
        if len(step) < MIN_STEP_LEN:
            add("step-length", f"step too short to be actionable: {step[:60]!r}")
            break

    if len(skill.signals) < MIN_SIGNALS:
        add("signals-count", f"at least {MIN_SIGNALS} signals required")
    for signal in skill.signals:
        if len(signal) < MIN_SIGNAL_LEN:
            add("signal-length", f"signal too short: {signal[:60]!r}")
            break

    if len(skill.patterns) < MIN_PATTERNS:
        add("patterns-count", f"at least {MIN_PATTERNS} patterns required")
    for label, code in skill.patterns:
        if len(label) < MIN_PATTERN_LABEL:
            add("pattern-label", f"pattern label too short: {label!r}")
        if len(code) < MIN_PATTERN_CODE:
            add("pattern-code", f"pattern {label!r} is too thin to be useful")
        if "```" in code:
            add("pattern-fence", f"pattern {label!r} must not contain code fences")

    if len(skill.pitfalls) < MIN_PITFALLS:
        add("pitfalls-count", f"at least {MIN_PITFALLS} pitfalls required")
    for pitfall in skill.pitfalls:
        if len(pitfall) < MIN_PITFALL_LEN:
            add("pitfall-length", f"pitfall too short: {pitfall[:60]!r}")
            break

    if len(skill.done_when) < MIN_DONE:
        add("done-count", f"at least {MIN_DONE} done-when criteria required")
    for item in skill.done_when:
        if len(item) < MIN_DONE_LEN:
            add("done-length", f"done-when item too short: {item[:60]!r}")
            break

    if len(skill.refs) < MIN_REFS:
        add("refs-count", f"at least {MIN_REFS} reference required")
    for ref in skill.refs:
        if not REF_RE.match(ref):
            add("refs-format", f"reference must be [label](https://...): {ref!r}")

    for key in pack.get("meta_keys", ()):
        if not skill.meta.get(key):
            add("meta-key", f"missing required meta field {key!r}")

    if pack.get("requires_verification"):
        if not skill.verify_present and not skill.verify_absent:
            add("verification", "pack requires verify_present/verify_absent patterns")
        for pattern in (*skill.verify_present, *skill.verify_absent):
            try:
                re.compile(pattern)
            except re.error as exc:
                add("verification-regex", f"invalid regex {pattern!r}: {exc}")

    words = word_count(rendered)
    if words < MIN_WORDS:
        add("word-count", f"rendered skill must be >= {MIN_WORDS} words, got {words}")

    match = FORBIDDEN_RE.search(rendered)
    if match:
        add("placeholder", f"forbidden placeholder token: {match.group(0)!r}")
    match = LOCAL_PATH_RE.search(rendered)
    if match:
        add("local-path", f"machine-local path must not be published: {match.group(0)!r}")

    return issues


def pack_issues(pack: dict[str, Any], skills: list[Skill]) -> list[Issue]:
    """Pack-level rules: exact count, unique slugs and titles, meta keys."""
    issues: list[Issue] = []
    expected = pack.get("expected_skills", len(skills))
    if len(skills) != expected:
        issues.append(
            Issue("", "skill-count", f"expected {expected} skills, found {len(skills)}")
        )

    seen_slugs: dict[str, int] = {}
    seen_titles: dict[str, str] = {}
    for skill in skills:
        seen_slugs[skill.slug] = seen_slugs.get(skill.slug, 0) + 1
        key = skill.title.lower()
        if key in seen_titles:
            issues.append(
                Issue(skill.slug, "title-unique", f"duplicates title of {seen_titles[key]}")
            )
        seen_titles[key] = skill.slug
    for slug, count in seen_slugs.items():
        if count > 1:
            issues.append(Issue(slug, "slug-unique", f"slug appears {count} times"))

    if pack.get("requires_verification") and not any(
        skill.verify_present for skill in skills
    ):
        issues.append(Issue("", "verification-present", "no skill defines verify_present"))

    return issues


def validate_pack(pack: dict[str, Any], skills: list[Skill]) -> list[Issue]:
    """Run every rule; empty list means the pack is valid."""
    issues = pack_issues(pack, skills)
    for skill in skills:
        rendered = render_skill(pack, skill)
        issues.extend(skill_issues(pack, skill, rendered))
    return issues