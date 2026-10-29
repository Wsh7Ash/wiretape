"""Corpus data model.

A skill is authored as a plain dict inside ``wiretape.corpus`` and loaded
into the immutable-ish :class:`Skill` shape used by the renderer, the
validator and every CLI command.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REQUIRED_KEYS = (
    "slug",
    "title",
    "summary",
    "use_when",
    "avoid_when",
    "tags",
    "steps",
    "signals",
    "patterns",
    "pitfalls",
    "done_when",
    "refs",
)


@dataclass(frozen=True)
class Skill:
    """One skill: a self-contained, testable procedure for a recon task."""

    slug: str
    title: str
    summary: str
    use_when: str
    avoid_when: str
    tags: tuple[str, ...]
    steps: tuple[str, ...]
    signals: tuple[str, ...]
    patterns: tuple[tuple[str, str], ...]
    pitfalls: tuple[str, ...]
    done_when: tuple[str, ...]
    refs: tuple[str, ...]
    # Domain metadata declared by the pack (e.g. phase, cwe, threat id).
    meta: dict[str, str] = field(default_factory=dict)
    # Optional verification regexes used by packs whose CLI checks patched code.
    verify_absent: tuple[str, ...] = ()
    verify_present: tuple[str, ...] = ()

    def meta_get(self, key: str, default: str = "") -> str:
        return self.meta.get(key, default)


def _strings(value: Any, label: str, slug: str = "?") -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{slug}: {label} must be a list of strings")
    out = tuple(str(item).strip() for item in value)
    if any(not item for item in out):
        raise ValueError(f"{slug}: {label} contains an empty entry")
    return out


def skill_from_dict(raw: dict[str, Any]) -> Skill:
    """Build a :class:`Skill` from its authoring dict, validating the shape."""
    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ValueError(f"{raw.get('slug', '?')}: missing keys {missing}")

    patterns: list[tuple[str, str]] = []
    for item in raw["patterns"]:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            patterns.append((str(item[0]).strip(), str(item[1]).strip()))
        else:
            raise ValueError(
                f"{raw['slug']}: pattern entries must be (label, code) pairs"
            )

    meta = {str(k): str(v) for k, v in dict(raw.get("meta", {})).items()}

    return Skill(
        slug=str(raw["slug"]).strip(),
        title=str(raw["title"]).strip(),
        summary=str(raw["summary"]).strip(),
        use_when=str(raw["use_when"]).strip(),
        avoid_when=str(raw["avoid_when"]).strip(),
        tags=_strings(raw["tags"], "tags", str(raw["slug"])),
        steps=_strings(raw["steps"], "steps", str(raw["slug"])),
        signals=_strings(raw["signals"], "signals", str(raw["slug"])),
        patterns=tuple(patterns),
        pitfalls=_strings(raw["pitfalls"], "pitfalls", str(raw["slug"])),
        done_when=_strings(raw["done_when"], "done_when", str(raw["slug"])),
        refs=_strings(raw["refs"], "refs", str(raw["slug"])),
        meta=meta,
        verify_absent=_strings(raw.get("verify_absent", ()), "verify_absent", str(raw["slug"])),
        verify_present=_strings(raw.get("verify_present", ()), "verify_present", str(raw["slug"])),
    )