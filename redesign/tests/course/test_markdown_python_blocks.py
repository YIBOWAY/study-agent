import sys
from pathlib import Path

import pytest

from infra.markdown_python_blocks import (
    MarkdownPythonBlockError,
    validate_markdown_python_blocks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COURSE_MARKDOWN_PATHS = (
    PROJECT_ROOT / "course" / "chapters" / "00-before-agent-kernel.md",
    PROJECT_ROOT / "course" / "labs" / "00-environment-check.md",
    PROJECT_ROOT / "course" / "solutions" / "00-environment-check-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "01-agent-kernel-foundations.md",
    PROJECT_ROOT / "course" / "labs" / "01-agent-runner-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "01-agent-runner-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "02-research-core-foundations.md",
    PROJECT_ROOT / "course" / "labs" / "02-source-evidence-claim-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "02-source-evidence-claim-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "03-memory-and-skills.md",
    PROJECT_ROOT / "course" / "labs" / "03-memory-skill-runtime-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "03-memory-skill-runtime-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "04-multi-agent-delegation.md",
    PROJECT_ROOT / "course" / "labs" / "04-delegation-runtime-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "04-delegation-runtime-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "05-workbench-product.md",
    PROJECT_ROOT / "course" / "labs" / "05-workbench-product-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "05-workbench-product-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "06-framework-comparisons.md",
    PROJECT_ROOT / "course" / "labs" / "06-framework-comparisons-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "06-framework-comparisons-solution.md",
    PROJECT_ROOT / "course" / "chapters" / "07-production-readiness.md",
    PROJECT_ROOT / "course" / "labs" / "07-production-readiness-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "07-production-readiness-solution.md",
)
LANGCHAIN_TRACK_ROOT = PROJECT_ROOT / "course" / "tracks" / "langchain"
LANGCHAIN_COURSE_MARKDOWN_PATHS = (
    tuple(sorted((LANGCHAIN_TRACK_ROOT / "chapters").glob("*.md")))
    + tuple(sorted((LANGCHAIN_TRACK_ROOT / "labs").glob("*.md")))
    + tuple(sorted((LANGCHAIN_TRACK_ROOT / "solutions").glob("*.md")))
)


def test_markdown_python_blocks_execute_with_shared_namespace_and_expected_output(
    tmp_path,
) -> None:
    markdown_path = tmp_path / "lesson.md"
    markdown_path.write_text(
        """# Lesson

```python
from research_core.memory import MemoryKind

kind_name = MemoryKind.SEMANTIC.value
print(kind_name)
```

Expected output:

```text
semantic
```

```python
print(kind_name.upper())
```

Expected output:

```text
SEMANTIC
```
""",
        encoding="utf-8",
    )

    report = validate_markdown_python_blocks((markdown_path,), PROJECT_ROOT)

    assert report.checked_files == (markdown_path,)
    assert report.executed_blocks == 2
    assert report.expected_outputs_checked == 2


def test_markdown_python_blocks_report_stdout_mismatches_with_file_and_line(
    tmp_path,
) -> None:
    markdown_path = tmp_path / "broken.md"
    markdown_path.write_text(
        """# Broken

```python
print("actual")
```

Expected output:

```text
expected
```
""",
        encoding="utf-8",
    )

    with pytest.raises(MarkdownPythonBlockError) as excinfo:
        validate_markdown_python_blocks((markdown_path,), PROJECT_ROOT)

    message = str(excinfo.value)
    assert "broken.md:3" in message
    assert "expected stdout mismatch" in message
    assert "expected" in message
    assert "actual" in message


def test_markdown_python_blocks_execute_blocks_without_expected_output(tmp_path) -> None:
    markdown_path = tmp_path / "silent.md"
    markdown_path.write_text(
        """# Silent

```python
value = 41 + 1
assert value == 42
```
""",
        encoding="utf-8",
    )

    report = validate_markdown_python_blocks((markdown_path,), PROJECT_ROOT)

    assert report.executed_blocks == 1
    assert report.expected_outputs_checked == 0


def test_markdown_python_blocks_can_import_apps_api_modules(tmp_path, monkeypatch) -> None:
    # Isolate sys.path so the helper under test is the only supplier of
    # ``apps/api/src`` (pytest's configured ``pythonpath`` would otherwise mask it).
    apps_api_src = (PROJECT_ROOT / "apps" / "api" / "src").as_posix()
    monkeypatch.setattr(
        sys, "path", [entry for entry in sys.path if Path(entry).as_posix() != apps_api_src]
    )
    for module_name in [name for name in sys.modules if name.split(".")[0] == "research_api"]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    markdown_path = tmp_path / "workbench.md"
    markdown_path.write_text(
        """# Workbench

```python
from research_api.main import create_app

app = create_app()
print(app.title)
```

Expected output:

```text
Research Workbench API
```
""",
        encoding="utf-8",
    )

    report = validate_markdown_python_blocks((markdown_path,), PROJECT_ROOT)

    assert report.executed_blocks == 1
    assert report.expected_outputs_checked == 1


def test_course_python_blocks_for_parts_0_through_7_stay_executable() -> None:
    report = validate_markdown_python_blocks(COURSE_MARKDOWN_PATHS, PROJECT_ROOT)

    expected_files = tuple(path.resolve(strict=False) for path in COURSE_MARKDOWN_PATHS)
    assert report.checked_files == expected_files
    assert report.executed_blocks > 0


def test_langchain_track_python_blocks_stay_offline_executable() -> None:
    assert len(LANGCHAIN_COURSE_MARKDOWN_PATHS) == 23
    report = validate_markdown_python_blocks(
        LANGCHAIN_COURSE_MARKDOWN_PATHS,
        PROJECT_ROOT,
    )
    expected_files = tuple(
        path.resolve(strict=False) for path in LANGCHAIN_COURSE_MARKDOWN_PATHS
    )
    assert report.checked_files == expected_files
    assert report.executed_blocks >= 46
