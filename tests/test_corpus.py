"""Corpus rules, generated-file sync and the real CLI as a subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wiretape.corpus import PACK, SKILLS  # noqa: E402
from wiretape.model import REQUIRED_KEYS  # noqa: E402
from wiretape.render import render_skill, word_count  # noqa: E402
from wiretape.validate import (  # noqa: E402
    MAX_DESCRIPTION,
    MIN_DONE,
    MIN_PATTERNS,
    MIN_PITFALLS,
    MIN_SIGNALS,
    MIN_STEPS,
    MIN_WORDS,
    validate_pack,
)

ENV = {"PYTHONPATH": str(ROOT / "src"), "PATH": __import__("os").environ.get("PATH", "")}


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wiretape", *args],
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        text=True,
    )


# --------------------------------------------------------------------- shape


def test_pack_metadata_is_complete() -> None:
    assert PACK["expected_skills"] == 50
    assert len(SKILLS) == 50
    for key in ("name", "version", "category", "license", "runtime", "description"):
        assert PACK[key]
    assert PACK["meta_keys"] == ("phase",)


def test_every_skill_declares_required_keys() -> None:
    for skill in SKILLS:
        for key in REQUIRED_KEYS:
            assert getattr(skill, key), f"{skill.slug} missing {key}"


def test_slugs_and_titles_are_unique() -> None:
    assert len({skill.slug for skill in SKILLS}) == 50
    assert len({skill.title.lower() for skill in SKILLS}) == 50


def test_phase_coverage_is_balanced() -> None:
    counts = Counter(skill.meta_get("phase") for skill in SKILLS)
    assert set(counts) == {"capture", "replay", "extract", "assert", "execute", "export"}
    assert min(counts.values()) >= 8
    assert sum(counts.values()) == 50


def test_strength_floors_hold() -> None:
    for skill in SKILLS:
        assert len(skill.steps) >= MIN_STEPS
        assert len(skill.signals) >= MIN_SIGNALS
        assert len(skill.patterns) >= MIN_PATTERNS
        assert len(skill.pitfalls) >= MIN_PITFALLS
        assert len(skill.done_when) >= MIN_DONE


def test_every_skill_renders_above_word_floor() -> None:
    for skill in SKILLS:
        rendered = render_skill(PACK, skill)
        assert word_count(rendered) >= MIN_WORDS, skill.slug
        assert rendered.startswith("---\nname: ")
        assert f"pack: {PACK['name']}" in rendered
        for heading in ("## Procedure", "## Signals", "## Patterns", "## Pitfalls", "## Done when", "## References"):
            assert heading in rendered


def test_references_are_canonical_https() -> None:
    for skill in SKILLS:
        for ref in skill.refs:
            assert ref.startswith("[") and "](https://" in ref and ref.endswith(")")


def test_description_fits_front_matter_limit() -> None:
    from wiretape.render import render_description

    for skill in SKILLS:
        description = render_description(skill)
        assert 120 <= len(description) <= MAX_DESCRIPTION, skill.slug


def test_pack_validates_with_no_issues() -> None:
    assert validate_pack(PACK, SKILLS) == []


# ---------------------------------------------------------------------- disk


def test_generated_skills_match_the_corpus() -> None:
    for skill in SKILLS:
        path = ROOT / "skills" / skill.slug / "SKILL.md"
        assert path.exists(), f"{skill.slug} not generated"
        assert path.read_text(encoding="utf-8") == render_skill(PACK, skill), skill.slug


def test_pack_json_matches_corpus() -> None:
    manifest = json.loads((ROOT / "pack.json").read_text(encoding="utf-8"))
    assert manifest["skill_count"] == 50
    assert len(manifest["skills"]) == 50
    assert [entry["slug"] for entry in manifest["skills"]] == [skill.slug for skill in SKILLS]


def test_validation_report_is_green() -> None:
    report = json.loads((ROOT / "results" / "validation.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["valid"] == 50


# ----------------------------------------------------------------------- cli


def test_cli_validate_passes() -> None:
    result = cli("validate")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "50/50 skills valid" in result.stdout


def test_cli_list_and_show() -> None:
    listed = cli("list", "--phase", "export")
    assert listed.returncode == 0
    assert "-- 8 skills" in listed.stdout
    shown = cli("show", "export-curl-reproduction")
    assert shown.returncode == 0
    assert "# Export Curl Reproduction" in shown.stdout
    missing = cli("show", "does-not-exist")
    assert missing.returncode == 1


def test_cli_search_ranks() -> None:
    result = cli("search", "redaction")
    assert result.returncode == 0
    assert "redaction" in result.stdout


def test_cli_lint_and_steps_on_a_real_tape() -> None:
    linted = cli("lint", "examples/demo.tape.json")
    assert linted.returncode == 0, linted.stdout + linted.stderr
    steps = cli("steps", "examples/demo.tape.json")
    assert steps.returncode == 0
    assert "login" in steps.stdout


def test_cli_export_curl_is_redacted() -> None:
    result = cli("export", "examples/demo.tape.json", "--to", "curl")
    assert result.returncode == 0
    assert "--path-as-is" in result.stdout
    assert "Authorization: <redacted>" in result.stdout
    assert "Bearer {{token}}" not in result.stdout


def test_cli_run_refuses_shell_without_flag() -> None:
    result = cli("run", "examples/demo.tape.json", "--dry-run")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
