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
    (skill / "references" / "hidden.md").write_text("nope", encoding="utf-8")
    # recreate listing without hidden by only having checklist in dir... actually discover lists all
    # remove checklist and only hidden? better: request a name not present
    loader = SkillLoader()
    manifest = loader.load(skill)
    with pytest.raises(SkillError, match="not listed"):
        loader.read_reference(manifest, "missing.md")
