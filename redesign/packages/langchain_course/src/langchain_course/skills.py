"""Part 3: progressive skill package loading for the LangChain track."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class SkillError(ValueError):
    """Raised when a skill package is invalid or a reference read is unsafe."""


_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass(frozen=True, slots=True)
class SkillManifest:
    name: str
    description: str
    entrypoint: str
    root: str
    references: tuple[str, ...] = ()
    scripts: tuple[str, ...] = ()
    body: str = ""

    def to_record(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "entrypoint": self.entrypoint,
            "root": self.root,
            "references": list(self.references),
            "scripts": list(self.scripts),
            "body": self.body,
        }


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    body = text[match.end() :]
    return meta, body


def _discover(root: Path, directory_name: str) -> tuple[str, ...]:
    folder = root / directory_name
    if not folder.is_dir():
        return ()
    names = sorted(
        path.name
        for path in folder.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )
    return tuple(names)


class SkillLoader:
    """Load skill packages with progressive disclosure.

    `load()` reads only SKILL.md (manifest + body). References are listed but
    not loaded until `read_reference()` is called explicitly.
    """

    def load(self, path: str | Path) -> SkillManifest:
        root = Path(path).resolve()
        if not root.is_dir():
            raise SkillError(f"skill path is not a directory: {root}")
        entry = root / "SKILL.md"
        if not entry.is_file():
            raise SkillError(f"missing SKILL.md in {root}")
        text = entry.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        name = (meta.get("name") or root.name).strip()
        description = (meta.get("description") or "").strip()
        if not name:
            raise SkillError("skill name must be non-empty")
        if not description:
            raise SkillError("skill description must be non-empty (frontmatter)")
        return SkillManifest(
            name=name,
            description=description,
            entrypoint="SKILL.md",
            root=str(root),
            references=_discover(root, "references"),
            scripts=_discover(root, "scripts"),
            body=body.strip(),
        )

    def read_reference(self, manifest: SkillManifest, relative_path: str | Path) -> str:
        rel = Path(relative_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise SkillError(f"unsafe reference path: {relative_path}")
        rel_str = rel.as_posix()
        if rel_str not in manifest.references and not rel_str.startswith("references/"):
            # allow either bare filename discovered under references/ or prefixed form
            bare = Path(rel_str).name
            if bare not in manifest.references:
                raise SkillError(
                    f"reference {relative_path!r} is not listed in skill manifest; "
                    "load() does not auto-read references"
                )
            rel = Path("references") / bare
        elif rel_str in manifest.references:
            rel = Path("references") / rel_str
        root = Path(manifest.root).resolve()
        target = (root / rel).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise SkillError(f"reference escapes skill root: {relative_path}") from exc
        if not target.is_file():
            raise SkillError(f"reference file not found: {relative_path}")
        return target.read_text(encoding="utf-8")
