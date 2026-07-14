from pathlib import Path

import pytest

from infra.docs_freshness import validate_docs_freshness, validate_index_paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_docs_freshness_validates_current_course_and_docs_indexes() -> None:
    report = validate_docs_freshness(PROJECT_ROOT)

    assert report.missing_paths == ()
    assert "docs/plans/2026-06-30-phase-7-production-readiness.md" in (
        report.checked_paths
    )
    assert "course/solutions/00-environment-check-solution.md" in report.checked_paths


def test_docs_freshness_reports_missing_indexed_markdown_paths(tmp_path) -> None:
    index = tmp_path / "docs" / "index.md"
    index.parent.mkdir()
    index.write_text("Read `missing.md` and `../course/lesson.md`.\n", encoding="utf-8")
    (tmp_path / "course").mkdir()
    (tmp_path / "course" / "lesson.md").write_text("ok\n", encoding="utf-8")

    report = validate_index_paths(tmp_path, (index,))

    assert report.checked_paths == ("course/lesson.md", "docs/missing.md")
    assert report.missing_paths == ("docs/missing.md",)
    with pytest.raises(ValueError, match="missing indexed docs paths"):
        report.raise_for_missing()


def test_docs_freshness_ignores_non_markdown_code_spans(tmp_path) -> None:
    index = tmp_path / "README.md"
    index.write_text("Run `uv run pytest -q` and inspect `RunEvent`.\n", encoding="utf-8")

    report = validate_index_paths(tmp_path, (index,))

    assert report.checked_paths == ()
    assert report.missing_paths == ()


def test_docs_freshness_checks_relative_markdown_links(tmp_path) -> None:
    index = tmp_path / "course" / "README.md"
    index.parent.mkdir()
    index.write_text(
        "Read [good](chapters/good.md) and [bad](labs/missing.md#step).\n",
        encoding="utf-8",
    )
    (tmp_path / "course" / "chapters").mkdir()
    (tmp_path / "course" / "chapters" / "good.md").write_text("ok\n", encoding="utf-8")

    report = validate_index_paths(tmp_path, (index,))

    assert "course/chapters/good.md" in report.checked_paths
    assert report.missing_paths == ("course/labs/missing.md",)
