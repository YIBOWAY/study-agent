"""Part 7: offline production-readiness contracts for the LangChain track.

Diagnostics, JSONL step persistence, approval, and sandbox policies operate on
AgentStep trails — not research_core.RunEvent. No cloud, auth, or network I/O.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from langchain_course.agent_kernel import AgentStep, BeforeToolHook, ToolGateDecision


class ProductionError(ValueError):
    """Raised when production contracts receive invalid input."""


class LangChainTraceRecorder(BaseCallbackHandler):
    """Small local callback handler that exposes real LC lifecycle events."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, Any]] = []

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self.records.append(
            {
                "kind": "chat_model_start",
                "run_id": str(run_id),
                "batch_count": len(messages),
                "tags": list(kwargs.get("tags") or ()),
                "name": serialized.get("name"),
            }
        )

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del response, kwargs
        self.records.append({"kind": "llm_end", "run_id": str(run_id)})

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del kwargs
        self.records.append(
            {
                "kind": "tool_start",
                "run_id": str(run_id),
                "name": serialized.get("name"),
                "input": input_str,
            }
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        del kwargs
        self.records.append(
            {"kind": "tool_end", "run_id": str(run_id), "output": str(output)}
        )


JSONL_STEP_LOG_SCHEMA_VERSION = "lc.agent_step_log.v1"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProductionError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class RunDiagnostics:
    run_id: str
    event_count: int
    event_type_counts: Mapping[str, int]
    error_summaries: Sequence[Mapping[str, Any]]

    def __post_init__(self) -> None:
        _require_non_empty("run_id", self.run_id)
        if (
            not isinstance(self.event_count, int)
            or isinstance(self.event_count, bool)
            or self.event_count < 0
        ):
            raise ProductionError("event_count must be a non-negative integer")
        object.__setattr__(self, "event_type_counts", dict(self.event_type_counts))
        object.__setattr__(self, "error_summaries", tuple(self.error_summaries))

    @classmethod
    def from_steps(cls, run_id: str, steps: Sequence[AgentStep]) -> RunDiagnostics:
        _require_non_empty("run_id", run_id)
        step_tuple = tuple(steps)
        if not step_tuple:
            raise ProductionError("steps must not be empty")
        if any(not isinstance(step, AgentStep) for step in step_tuple):
            raise ProductionError("steps must contain AgentStep objects")
        counts = Counter(step.kind for step in step_tuple)
        errors = tuple(
            {
                "index": index,
                "kind": step.payload.get("error_kind", "error"),
                "message": str(step.payload.get("message", step.payload.get("error", ""))),
            }
            for index, step in enumerate(step_tuple)
            if step.kind == "error"
        )
        return cls(
            run_id=run_id,
            event_count=len(step_tuple),
            event_type_counts=dict(sorted(counts.items())),
            error_summaries=errors,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event_count": self.event_count,
            "event_type_counts": dict(self.event_type_counts),
            "error_summaries": [dict(item) for item in self.error_summaries],
        }


def step_to_record(step: AgentStep, *, run_id: str, index: int) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "index": index,
        "kind": step.kind,
        "payload": dict(step.payload),
    }


def step_from_record(record: Mapping[str, Any]) -> AgentStep:
    kind = record.get("kind")
    payload = record.get("payload", {})
    if not isinstance(kind, str) or not kind.strip():
        raise ProductionError("step record kind must be a non-empty string")
    if not isinstance(payload, Mapping):
        raise ProductionError("step record payload must be an object")
    return AgentStep(kind=kind, payload=dict(payload))


class JsonlStepStore:
    """Append-only JSONL store for AgentStep trails (one step per line)."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if self._path.exists() and self._path.is_dir():
            raise ProductionError("path must be a file path")
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append_steps(self, run_id: str, steps: Sequence[AgentStep]) -> None:
        _require_non_empty("run_id", run_id)
        with self._path.open("a", encoding="utf-8") as handle:
            for index, step in enumerate(steps):
                if not isinstance(step, AgentStep):
                    raise ProductionError("steps must contain AgentStep objects")
                line = {
                    "schema_version": JSONL_STEP_LOG_SCHEMA_VERSION,
                    "step": step_to_record(step, run_id=run_id, index=index),
                }
                handle.write(json.dumps(line, sort_keys=True))
                handle.write("\n")

    def read_run(self, run_id: str) -> tuple[AgentStep, ...]:
        _require_non_empty("run_id", run_id)
        return tuple(
            step
            for step_run_id, step in self._read_all_with_ids()
            if step_run_id == run_id
        )

    def list_run_ids(self) -> tuple[str, ...]:
        run_ids: list[str] = []
        seen: set[str] = set()
        for run_id, _step in self._read_all_with_ids():
            if run_id in seen:
                continue
            seen.add(run_id)
            run_ids.append(run_id)
        return tuple(run_ids)

    def _read_all_with_ids(self) -> list[tuple[str, AgentStep]]:
        if not self._path.exists():
            return []
        rows: list[tuple[str, AgentStep]] = []
        for line_number, line in enumerate(
            self._path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProductionError(
                    f"invalid JSON step log at line {line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise ProductionError(f"step log line {line_number} must be an object")
            if record.get("schema_version") != JSONL_STEP_LOG_SCHEMA_VERSION:
                raise ProductionError(
                    f"unsupported step log schema at line {line_number}"
                )
            raw_step = record.get("step")
            if not isinstance(raw_step, dict):
                raise ProductionError(
                    f"step log line {line_number} must contain step object"
                )
            run_id = raw_step.get("run_id")
            if not isinstance(run_id, str) or not run_id.strip():
                raise ProductionError(
                    f"step log line {line_number} missing run_id"
                )
            rows.append((run_id, step_from_record(raw_step)))
        return rows


class ApprovalMode(StrEnum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    subject: str
    mode: ApprovalMode
    reason: str
    matched_rule: str = ""

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
    mode: ApprovalMode
    reason: str

    def matches(self, tool_name: str) -> bool:
        _require_non_empty("tool_name", tool_name)
        return fnmatchcase(tool_name, self.tool_name_pattern)


@dataclass(frozen=True, slots=True)
class ApprovalPolicy:
    rules: Sequence[ApprovalRule] = ()
    default_mode: ApprovalMode = ApprovalMode.REQUIRE_APPROVAL
    default_reason: str = "No approval rule matched."

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))
        _require_non_empty("default_reason", self.default_reason)

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


def build_approval_hook(
    policy: ApprovalPolicy,
    *,
    approved_tools: set[str] | frozenset[str] = frozenset(),
) -> BeforeToolHook:
    """Adapt approval policy to the agent kernel's pre-execution tool hook."""
    approved = frozenset(approved_tools)

    def _before_tool(tool_name: str, _args: Mapping[str, Any]) -> ToolGateDecision:
        decision = policy.decide(tool_name)
        allowed = decision.mode is ApprovalMode.ALLOW or (
            decision.mode is ApprovalMode.REQUIRE_APPROVAL and tool_name in approved
        )
        reason = decision.reason
        if decision.requires_review and tool_name in approved:
            reason = f"human approval recorded; {reason}"
        return ToolGateDecision(
            allowed=allowed,
            mode=decision.mode.value,
            reason=reason,
        )

    return _before_tool


@dataclass(frozen=True, slots=True)
class SandboxDecision:
    subject: str
    allowed: bool
    reason: str

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
            raise ProductionError("allow_network must be a boolean")
        if (
            not isinstance(self.max_runtime_seconds, int)
            or isinstance(self.max_runtime_seconds, bool)
            or self.max_runtime_seconds <= 0
        ):
            raise ProductionError("max_runtime_seconds must be a positive integer")
        object.__setattr__(self, "readable_paths", _normalize_paths(self.readable_paths))
        object.__setattr__(self, "writable_paths", _normalize_paths(self.writable_paths))
        object.__setattr__(self, "blocked_paths", _normalize_paths(self.blocked_paths))

    def decide_path(self, path: str | Path, *, access: str) -> SandboxDecision:
        if access not in {"read", "write"}:
            raise ProductionError("access must be one of: read, write")
        resolved = _resolve_path(path)
        subject = str(resolved)
        if any(_is_relative_to(resolved, blocked) for blocked in self.blocked_paths):
            return SandboxDecision(
                subject=subject,
                allowed=False,
                reason="path is blocked by sandbox policy",
            )
        allowed_roots = self.readable_paths if access == "read" else self.writable_paths
        if any(_is_relative_to(resolved, root) for root in allowed_roots):
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

    def runtime_decision(self, elapsed_seconds: float) -> SandboxDecision:
        if (
            not isinstance(elapsed_seconds, (int, float))
            or isinstance(elapsed_seconds, bool)
            or elapsed_seconds < 0
        ):
            raise ProductionError("elapsed_seconds must be a non-negative number")
        if elapsed_seconds <= self.max_runtime_seconds:
            return SandboxDecision(
                subject="runtime",
                allowed=True,
                reason=(
                    f"elapsed runtime {elapsed_seconds}s is within "
                    f"max_runtime_seconds {self.max_runtime_seconds}"
                ),
            )
        return SandboxDecision(
            subject="runtime",
            allowed=False,
            reason=(
                f"elapsed runtime {elapsed_seconds}s exceeds "
                f"max_runtime_seconds {self.max_runtime_seconds}"
            ),
        )


def _normalize_paths(paths: Sequence[str | Path]) -> tuple[Path, ...]:
    if isinstance(paths, (str, bytes, Path)):
        raise ProductionError("paths must be a sequence of paths")
    return tuple(_resolve_path(path) for path in paths)


def _resolve_path(path: str | Path) -> Path:
    path_obj = Path(path)
    if not str(path_obj).strip():
        raise ProductionError("path must not be empty")
    return path_obj.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
