from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any


class ApprovalMode(StrEnum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    subject: str
    mode: ApprovalMode | str
    reason: str
    matched_rule: str = ""

    def __post_init__(self) -> None:
        _require_non_empty("subject", self.subject)
        _require_non_empty("reason", self.reason)
        try:
            mode = ApprovalMode(self.mode)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in ApprovalMode)
            raise ValueError(f"mode must be one of: {allowed}") from exc
        object.__setattr__(self, "mode", mode)

    @property
    def requires_review(self) -> bool:
        return self.mode is ApprovalMode.REQUIRE_APPROVAL

    def to_record(self) -> dict[str, str]:
        return {
            "subject": self.subject,
            "mode": self.mode.value,
            "reason": self.reason,
            "matched_rule": self.matched_rule,
        }


@dataclass(frozen=True, slots=True)
class ApprovalRule:
    tool_name_pattern: str
    mode: ApprovalMode | str
    reason: str

    def __post_init__(self) -> None:
        _require_non_empty("tool_name_pattern", self.tool_name_pattern)
        _require_non_empty("reason", self.reason)
        try:
            mode = ApprovalMode(self.mode)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in ApprovalMode)
            raise ValueError(f"mode must be one of: {allowed}") from exc
        object.__setattr__(self, "mode", mode)

    def matches(self, tool_name: str) -> bool:
        _require_non_empty("tool_name", tool_name)
        return fnmatchcase(tool_name, self.tool_name_pattern)


@dataclass(frozen=True, slots=True)
class ApprovalPolicy:
    rules: Sequence[ApprovalRule] = ()
    default_mode: ApprovalMode | str = ApprovalMode.REQUIRE_APPROVAL
    default_reason: str = "No approval rule matched."

    def __post_init__(self) -> None:
        rules = tuple(self.rules)
        if any(not isinstance(rule, ApprovalRule) for rule in rules):
            raise ValueError("rules must contain ApprovalRule objects")
        try:
            default_mode = ApprovalMode(self.default_mode)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in ApprovalMode)
            raise ValueError(f"default_mode must be one of: {allowed}") from exc
        _require_non_empty("default_reason", self.default_reason)
        object.__setattr__(self, "rules", rules)
        object.__setattr__(self, "default_mode", default_mode)

    def decide(self, subject: str) -> ApprovalDecision:
        _require_non_empty("subject", subject)
        for rule in self.rules:
            if rule.matches(subject):
                return ApprovalDecision(
                    subject=subject,
                    mode=rule.mode,
                    reason=rule.reason,
                    matched_rule=rule.tool_name_pattern,
                )
        return ApprovalDecision(
            subject=subject,
            mode=self.default_mode,
            reason=self.default_reason,
        )


@dataclass(frozen=True, slots=True)
class SandboxDecision:
    subject: str
    allowed: bool
    reason: str

    def __post_init__(self) -> None:
        _require_non_empty("subject", self.subject)
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be a boolean")
        _require_non_empty("reason", self.reason)

    def to_record(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "allowed": self.allowed,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    readable_paths: Sequence[str | Path] = ()
    writable_paths: Sequence[str | Path] = ()
    blocked_paths: Sequence[str | Path] = ()
    allow_network: bool = False
    max_runtime_seconds: int = 30

    def __post_init__(self) -> None:
        if not isinstance(self.allow_network, bool):
            raise ValueError("allow_network must be a boolean")
        if (
            not isinstance(self.max_runtime_seconds, int)
            or isinstance(self.max_runtime_seconds, bool)
            or self.max_runtime_seconds <= 0
        ):
            raise ValueError("max_runtime_seconds must be a positive integer")
        object.__setattr__(self, "readable_paths", _normalize_paths(self.readable_paths))
        object.__setattr__(self, "writable_paths", _normalize_paths(self.writable_paths))
        object.__setattr__(self, "blocked_paths", _normalize_paths(self.blocked_paths))

    def decide_path(self, path: str | Path, *, access: str) -> SandboxDecision:
        if access not in {"read", "write"}:
            raise ValueError("access must be one of: read, write")
        resolved_path = _resolve_path(path)
        subject = str(resolved_path)
        if any(_is_relative_to(resolved_path, blocked) for blocked in self.blocked_paths):
            return SandboxDecision(
                subject=subject,
                allowed=False,
                reason="path is blocked by sandbox policy",
            )
        allowed_roots = self.readable_paths if access == "read" else self.writable_paths
        if any(_is_relative_to(resolved_path, root) for root in allowed_roots):
            return SandboxDecision(
                subject=subject,
                allowed=True,
                reason=f"path is allowed for {access}",
            )
        return SandboxDecision(
            subject=subject,
            allowed=False,
            reason=f"path is not allowed for {access}",
        )

    def network_decision(self) -> SandboxDecision:
        if self.allow_network:
            return SandboxDecision(
                subject="network",
                allowed=True,
                reason="network access is enabled",
            )
        return SandboxDecision(
            subject="network",
            allowed=False,
            reason="network access is disabled",
        )


def _normalize_paths(paths: Sequence[str | Path]) -> tuple[Path, ...]:
    if isinstance(paths, (str, bytes, Path)):
        raise ValueError("paths must be a sequence of paths")
    return tuple(_resolve_path(path) for path in paths)


def _resolve_path(path: str | Path) -> Path:
    path_obj = Path(path)
    if not str(path_obj).strip():
        raise ValueError("path must not be empty")
    return path_obj.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
