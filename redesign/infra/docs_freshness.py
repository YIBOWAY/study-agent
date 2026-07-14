from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_CODE_SPAN_PATTERN = re.compile(r"`([^`]+\.md)`")
_MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+\.md(?:#[^)]+)?)\)")


@dataclass(frozen=True, slots=True)
class DocsFreshnessReport:
    checked_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]

    def raise_for_missing(self) -> None:
        if self.missing_paths:
            missing = ", ".join(self.missing_paths)
            raise ValueError(f"missing indexed docs paths: {missing}")


def validate_docs_freshness(project_root: str | Path) -> DocsFreshnessReport:
    root = Path(project_root)
    return validate_index_paths(
        root,
        (
            root / "README.md",
            root / "docs" / "README.md",
            root / "docs" / "course" / "roadmap.md",
            root / "docs" / "plans" / "2026-06-25-redesign-execution-roadmap.md",
            root / "course" / "README.md",
            root / "course" / "tracks" / "langchain" / "README.md",
        ),
    )


def validate_index_paths(
    project_root: str | Path,
    index_paths: Sequence[str | Path],
) -> DocsFreshnessReport:
    root = Path(project_root).resolve(strict=False)
    checked: set[str] = set()
    missing: set[str] = set()
    for raw_index_path in index_paths:
        index_path = Path(raw_index_path).resolve(strict=False)
        for token in _markdown_code_spans(index_path):
            resolved = _resolve_index_token(root, index_path, token)
            relative = _relative_to_root(root, resolved)
            checked.add(relative)
            if not resolved.exists():
                missing.add(relative)
    return DocsFreshnessReport(
        checked_paths=tuple(sorted(checked)),
        missing_paths=tuple(sorted(missing)),
    )


def _markdown_code_spans(index_path: Path) -> tuple[str, ...]:
    if not index_path.exists():
        raise ValueError(f"index path does not exist: {index_path}")
    content = index_path.read_text(encoding="utf-8")
    tokens = list(_CODE_SPAN_PATTERN.findall(content))
    tokens.extend(
        target.split("#", 1)[0]
        for target in _MARKDOWN_LINK_PATTERN.findall(content)
        if "://" not in target
    )
    return tuple(token for token in tokens if not _is_placeholder_path(token))


def _resolve_index_token(root: Path, index_path: Path, token: str) -> Path:
    if token.startswith("redesign/"):
        return root / token.removeprefix("redesign/")
    local_path = (index_path.parent / token).resolve(strict=False)
    if local_path.exists():
        return local_path
    if token.startswith(("apps/", "course/", "docs/", "evals/", "infra/", "packages/")):
        return root / token
    if token in {"AGENTS.md", "README.md"}:
        return root / token
    return local_path


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_placeholder_path(token: str) -> bool:
    if token.startswith("path/") or token.startswith("example/"):
        return True
    return token == "SKILL.md" or "phase-N" in token
