from pathlib import Path

import pytest

from infra.markdown_python_blocks import (
    MarkdownPythonBlockError,
    validate_markdown_python_blocks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PART3_MARKDOWN_PATHS = (
    PROJECT_ROOT / "course" / "chapters" / "03-memory-and-skills.md",
    PROJECT_ROOT / "course" / "labs" / "03-memory-skill-runtime-lab.md",
    PROJECT_ROOT / "course" / "solutions" / "03-memory-skill-runtime-solution.md",
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


def test_part3_course_python_blocks_stay_executable() -> None:
    report = validate_markdown_python_blocks(PART3_MARKDOWN_PATHS, PROJECT_ROOT)

    expected_files = tuple(path.resolve(strict=False) for path in PART3_MARKDOWN_PATHS)
    assert report.checked_files == expected_files
    assert report.executed_blocks > 0
