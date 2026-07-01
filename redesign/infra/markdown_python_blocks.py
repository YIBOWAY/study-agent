from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Sequence
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MarkdownPythonBlockError(ValueError):
    """Raised when an executable markdown Python block fails validation."""


@dataclass(frozen=True, slots=True)
class MarkdownPythonCheckReport:
    checked_files: tuple[Path, ...]
    executed_blocks: int
    expected_outputs_checked: int


@dataclass(frozen=True, slots=True)
class _Fence:
    language: str
    content: str
    start_line: int
    previous_non_empty_line: str


@dataclass(frozen=True, slots=True)
class _PythonBlock:
    content: str
    start_line: int
    expected_output: str | None = None


_PYTHON_LANGUAGES = {"python", "py", "python3"}
_TEXT_LANGUAGES = {"text", "txt"}
_EXPECTED_OUTPUT_MARKERS = {"expected output:", "expected:"}


def validate_markdown_python_blocks(
    markdown_paths: Sequence[str | Path],
    project_root: str | Path,
) -> MarkdownPythonCheckReport:
    root = Path(project_root).resolve(strict=False)
    _ensure_source_paths(root)
    checked_files = tuple(Path(path).resolve(strict=False) for path in markdown_paths)

    executed_blocks = 0
    expected_outputs_checked = 0
    for markdown_path in checked_files:
        if not markdown_path.is_file():
            raise MarkdownPythonBlockError(f"markdown file does not exist: {markdown_path}")
        namespace: dict[str, Any] = {
            "__builtins__": __builtins__,
            "__file__": str(markdown_path),
            "__name__": "__markdown_python_block__",
        }
        for block in _python_blocks(markdown_path):
            output = _execute_python_block(markdown_path, block, namespace)
            executed_blocks += 1
            if block.expected_output is not None:
                expected_outputs_checked += 1
                _assert_stdout_matches(markdown_path, block, output)

    return MarkdownPythonCheckReport(
        checked_files=checked_files,
        executed_blocks=executed_blocks,
        expected_outputs_checked=expected_outputs_checked,
    )


def _ensure_source_paths(root: Path) -> None:
    source_dirs = (
        root / "packages" / "research_core" / "src",
        root / "apps" / "api" / "src",
    )
    for source_dir in source_dirs:
        if source_dir.is_dir():
            path_text = source_dir.as_posix()
            if path_text not in sys.path:
                sys.path.insert(0, path_text)


def _python_blocks(markdown_path: Path) -> tuple[_PythonBlock, ...]:
    fences = _fences(markdown_path)
    blocks: list[_PythonBlock] = []
    for index, fence in enumerate(fences):
        if fence.language not in _PYTHON_LANGUAGES:
            continue
        expected_output = _expected_output_after(fences, index)
        blocks.append(
            _PythonBlock(
                content=fence.content,
                start_line=fence.start_line,
                expected_output=expected_output,
            )
        )
    return tuple(blocks)


def _fences(markdown_path: Path) -> tuple[_Fence, ...]:
    fences: list[_Fence] = []
    in_fence = False
    fence_language = ""
    fence_start_line = 0
    fence_previous_non_empty_line = ""
    content_lines: list[str] = []
    previous_non_empty_line = ""

    lines = markdown_path.read_text(encoding="utf-8").splitlines(True)
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_fence:
                fences.append(
                    _Fence(
                        language=fence_language,
                        content="".join(content_lines),
                        start_line=fence_start_line,
                        previous_non_empty_line=fence_previous_non_empty_line,
                    )
                )
                in_fence = False
                content_lines = []
            else:
                in_fence = True
                language = stripped.removeprefix("```").strip()
                language_parts = language.split(maxsplit=1)
                fence_language = language_parts[0].casefold() if language_parts else ""
                fence_start_line = line_number
                fence_previous_non_empty_line = previous_non_empty_line
            previous_non_empty_line = stripped
            continue

        if in_fence:
            content_lines.append(line)
            continue

        if stripped:
            previous_non_empty_line = stripped

    if in_fence:
        raise MarkdownPythonBlockError(f"{markdown_path}: unclosed fenced code block")
    return tuple(fences)


def _expected_output_after(fences: tuple[_Fence, ...], index: int) -> str | None:
    if index + 1 >= len(fences):
        return None
    next_fence = fences[index + 1]
    if next_fence.language not in _TEXT_LANGUAGES:
        return None
    marker = next_fence.previous_non_empty_line.casefold()
    if marker not in _EXPECTED_OUTPUT_MARKERS:
        return None
    return next_fence.content


def _execute_python_block(
    markdown_path: Path,
    block: _PythonBlock,
    namespace: dict[str, Any],
) -> str:
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            exec(compile(block.content, f"{markdown_path}:{block.start_line}", "exec"), namespace)
    except Exception as exc:
        raise MarkdownPythonBlockError(
            f"{markdown_path.name}:{block.start_line}: python block failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    return output.getvalue()


def _assert_stdout_matches(markdown_path: Path, block: _PythonBlock, actual_output: str) -> None:
    expected_output = block.expected_output
    if expected_output == actual_output:
        return
    raise MarkdownPythonBlockError(
        f"{markdown_path.name}:{block.start_line}: expected stdout mismatch\n"
        f"Expected:\n{expected_output}"
        f"Actual:\n{actual_output}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute fenced python blocks in markdown and compare marked output blocks.",
    )
    parser.add_argument("paths", nargs="+", help="Markdown files to validate.")
    parser.add_argument(
        "--project-root",
        default=Path.cwd(),
        help="Project root used to add packages/research_core/src to sys.path.",
    )
    args = parser.parse_args(argv)

    try:
        report = validate_markdown_python_blocks(args.paths, args.project_root)
    except MarkdownPythonBlockError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(
        "checked "
        f"{report.executed_blocks} python blocks in {len(report.checked_files)} files; "
        f"{report.expected_outputs_checked} expected outputs matched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
