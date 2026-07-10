from __future__ import annotations

from pathlib import Path

import pytest
from langchain_course.skills import SkillError, SkillLoader


def _write_skill(root: Path) -> Path:
    skill = root / "deep-research"
    (skill / "references").mkdir(parents=True)
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: deep-research\n"
        "description: Structured deep research checklist\n"
        "---\n"
        "\n"
        "# Deep Research\n"
        "\n"
        "Start with the checklist. Read references only when needed.\n",
        encoding="utf-8",
    )
    (skill / "references" / "checklist.md").write_text(
        "# Checklist\n\n1. Collect sources\n2. Extract evidence\n",
        encoding="utf-8",
    )
    (skill / "scripts" / "noop.py").write_text("print('noop')\n", encoding="utf-8")
    return skill


def test_load_manifest_without_reading_reference_body(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path)
    manifest = SkillLoader().load(skill)
    assert manifest.name == "deep-research"
    assert "checklist.md" in manifest.references
    assert "noop.py" in manifest.scripts
    assert "Start with the checklist" in manifest.body
    # load must not require opening references content beyond listing names
    assert "Collect sources" not in manifest.body


def test_read_reference_explicit(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path)
    loader = SkillLoader()
    manifest = loader.load(skill)
    text = loader.read_reference(manifest, "checklist.md")
    assert "Collect sources" in text


def test_read_reference_rejects_path_traversal(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path)
    loader = SkillLoader()
    manifest = loader.load(skill)
    with pytest.raises(SkillError, match="unsafe"):
        loader.read_reference(manifest, "../secrets.txt")


def test_read_unlisted_reference_fails(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path)
    loader = SkillLoader()
    manifest = loader.load(skill)
    with pytest.raises(SkillError, match="not listed"):
        loader.read_reference(manifest, "missing.md")


def test_read_unlisted_but_present_bare_name_fails(tmp_path: Path) -> None:
    """Bare basename that exists on disk but is absent from the load-time list."""
    skill = _write_skill(tmp_path)
    loader = SkillLoader()
    manifest = loader.load(skill)
    assert "hidden.md" not in manifest.references
    (skill / "references" / "hidden.md").write_text("nope", encoding="utf-8")
    with pytest.raises(SkillError, match="not listed"):
        loader.read_reference(manifest, "hidden.md")


def test_read_reference_rejects_unlisted_references_prefix_even_if_file_exists(
    tmp_path: Path,
) -> None:
    """Allowlist must apply to "references/<name>" form, not only bare basenames.

    Files added after load (or otherwise absent from manifest.references) must
    not be readable just because the caller prefixes references/.
    """
    skill = _write_skill(tmp_path)
    loader = SkillLoader()
    manifest = loader.load(skill)
    assert "hidden.md" not in manifest.references

    # Added after load so discover never listed it; file exists on disk.
    (skill / "references" / "hidden.md").write_text("secret unlisted", encoding="utf-8")

    with pytest.raises(SkillError, match="not listed"):
        loader.read_reference(manifest, "references/hidden.md")


def test_read_reference_accepts_prefixed_listed_name(tmp_path: Path) -> None:
    """Prefixed form "references/<name>" is allowed when <name> is listed."""
    skill = _write_skill(tmp_path)
    loader = SkillLoader()
    manifest = loader.load(skill)
    assert "checklist.md" in manifest.references

    text = loader.read_reference(manifest, "references/checklist.md")
    assert "Collect sources" in text
