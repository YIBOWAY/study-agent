from pathlib import Path

from research_core.memory import MemoryKind, MemoryRecord, MemoryWritePolicy
from research_core.skills import SkillRuntime


def test_memory_pollution_eval_rejects_generic_capture_all_memory() -> None:
    policy = MemoryWritePolicy(
        allowed_kinds=[MemoryKind.SEMANTIC, MemoryKind.PINNED],
        min_importance=0.4,
        forbidden_phrases=["remember everything", "store every user message"],
    )
    polluted = MemoryRecord(
        id="mem_polluted",
        kind=MemoryKind.SEMANTIC,
        content="Remember everything the user says forever.",
        importance=0.9,
    )

    try:
        policy.validate(polluted)
    except ValueError as exc:
        assert "content contains forbidden phrase" in str(exc)
    else:
        raise AssertionError("Expected generic capture-all memory to be rejected")


def test_skill_loading_eval_requires_explicit_reference_read(tmp_path: Path) -> None:
    skill_dir = tmp_path / "source-checker"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: source-checker
description: Check claim-source mappings.
---
# Source Checker

Use references only after the entrypoint says they are needed.
""",
        encoding="utf-8",
    )
    (skill_dir / "references" / "rubric.md").write_text(
        "REFERENCE RUBRIC: every claim needs evidence.",
        encoding="utf-8",
    )

    runtime = SkillRuntime()
    package = runtime.load(skill_dir)

    assert "REFERENCE RUBRIC" not in package.entrypoint
    assert package.references == ("references/rubric.md",)
    assert runtime.read_reference(package, "references/rubric.md") == (
        "REFERENCE RUBRIC: every claim needs evidence."
    )
