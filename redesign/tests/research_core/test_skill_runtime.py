from pathlib import Path

from research_core.skills import SkillRuntime


def _write_skill(root: Path) -> Path:
    skill_dir = root / "deep-research"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "scripts").mkdir()
    (skill_dir / "assets").mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: deep-research
description: Find and ground research sources.
---
# Deep Research

Load references only when the task needs them.
""",
        encoding="utf-8",
    )
    (skill_dir / "references" / "guide.md").write_text(
        "REFERENCE SECRET: cite every claim.",
        encoding="utf-8",
    )
    (skill_dir / "scripts" / "collect.py").write_text("print('collect')", encoding="utf-8")
    (skill_dir / "assets" / "diagram.txt").write_text("asset", encoding="utf-8")
    return skill_dir


def test_skill_runtime_loads_entrypoint_metadata_and_discovers_resources(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)

    package = SkillRuntime().load(skill_dir)

    assert package.name == "deep-research"
    assert package.description == "Find and ground research sources."
    assert "# Deep Research" in package.entrypoint
    assert "REFERENCE SECRET" not in package.entrypoint
    assert package.references == ("references/guide.md",)
    assert package.scripts == ("scripts/collect.py",)
    assert package.assets == ("assets/diagram.txt",)


def test_skill_runtime_rejects_missing_skill_file(tmp_path: Path) -> None:
    skill_dir = tmp_path / "empty-skill"
    skill_dir.mkdir()

    try:
        SkillRuntime().load(skill_dir)
    except ValueError as exc:
        assert "SKILL.md is required" in str(exc)
    else:
        raise AssertionError("Expected missing SKILL.md to be rejected")


def test_skill_runtime_rejects_blank_skill_name(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name:
description: Missing name.
---
# Bad Skill
""",
        encoding="utf-8",
    )

    try:
        SkillRuntime().load(skill_dir)
    except ValueError as exc:
        assert "skill name must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank skill name to be rejected")


def test_skill_runtime_reads_reference_only_when_requested(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    runtime = SkillRuntime()
    package = runtime.load(skill_dir)

    content = runtime.read_reference(package, "references/guide.md")

    assert content == "REFERENCE SECRET: cite every claim."


def test_skill_runtime_rejects_path_traversal_and_non_reference_reads(tmp_path: Path) -> None:
    skill_dir = _write_skill(tmp_path)
    runtime = SkillRuntime()
    package = runtime.load(skill_dir)

    for relative_path in ("../SKILL.md", "scripts/collect.py"):
        try:
            runtime.read_reference(package, relative_path)
        except ValueError as exc:
            assert "reference path must stay under references" in str(exc)
        else:
            raise AssertionError(f"Expected {relative_path} to be rejected")


def test_skill_package_is_immutable(tmp_path: Path) -> None:
    package = SkillRuntime().load(_write_skill(tmp_path))

    try:
        package.references += ("references/other.md",)
    except AttributeError:
        pass
    else:
        raise AssertionError("Expected skill package to be immutable")
