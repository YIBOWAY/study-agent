from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SkillPackage:
    name: str
    description: str
    root: Path
    entrypoint: str
    references: tuple[str, ...] = ()
    scripts: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty("skill name", self.name)
        _require_non_empty("entrypoint", self.entrypoint)
        object.__setattr__(self, "root", self.root.resolve())
        object.__setattr__(self, "references", tuple(self.references))
        object.__setattr__(self, "scripts", tuple(self.scripts))
        object.__setattr__(self, "assets", tuple(self.assets))


class SkillRuntime:
    def load(self, path: str | Path) -> SkillPackage:
        root = Path(path).resolve()
        skill_file = root / "SKILL.md"
        if not skill_file.is_file():
            raise ValueError("SKILL.md is required")

        entrypoint = skill_file.read_text(encoding="utf-8")
        metadata = _parse_frontmatter(entrypoint)
        name = metadata.get("name", "").strip()
        description = metadata.get("description", "").strip()
        if not name:
            raise ValueError("skill name must not be empty")

        return SkillPackage(
            name=name,
            description=description,
            root=root,
            entrypoint=entrypoint,
            references=_discover(root, "references"),
            scripts=_discover(root, "scripts"),
            assets=_discover(root, "assets"),
        )

    def read_reference(self, package: SkillPackage, relative_path: str | Path) -> str:
        relative = Path(relative_path)
        if relative.is_absolute():
            raise ValueError("reference path must stay under references")
        root = package.root.resolve()
        references_root = (root / "references").resolve()
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(references_root):
            raise ValueError("reference path must stay under references")
        if not candidate.is_file():
            raise ValueError("reference file does not exist")
        return candidate.read_text(encoding="utf-8")


def _discover(root: Path, directory_name: str) -> tuple[str, ...]:
    directory = root / directory_name
    if not directory.is_dir():
        return ()
    return tuple(
        path.relative_to(root).as_posix()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    )


def _parse_frontmatter(content: str) -> dict[str, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return metadata
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
