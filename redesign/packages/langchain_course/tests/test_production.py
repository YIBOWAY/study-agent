from __future__ import annotations

from pathlib import Path

import pytest
from langchain_course.agent_kernel import AgentStep
from langchain_course.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    JsonlStepStore,
    ProductionError,
    RunDiagnostics,
    SandboxPolicy,
)


def test_run_diagnostics_from_steps() -> None:
    steps = (
        AgentStep(kind="model_request", payload={"step": "plan"}),
        AgentStep(kind="tool_call", payload={"tool": "search"}),
        AgentStep(
            kind="error",
            payload={"error_kind": "tool_error", "message": "fixture missing"},
        ),
        AgentStep(kind="final", payload={"text": "partial"}),
    )
    diag = RunDiagnostics.from_steps("run_7", steps)
    rec = diag.to_record()
    assert rec["run_id"] == "run_7"
    assert rec["event_count"] == 4
    assert rec["event_type_counts"]["error"] == 1
    assert rec["error_summaries"][0]["message"] == "fixture missing"


def test_run_diagnostics_rejects_empty() -> None:
    with pytest.raises(ProductionError, match="empty"):
        RunDiagnostics.from_steps("run_x", [])


def test_jsonl_step_store_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "steps.jsonl"
    store = JsonlStepStore(path)
    steps = (
        AgentStep(kind="model_request", payload={"n": 1}),
        AgentStep(kind="final", payload={"text": "ok"}),
    )
    store.append_steps("run_a", steps)
    store.append_steps("run_b", (AgentStep(kind="error", payload={"message": "x"}),))
    assert store.list_run_ids() == ("run_a", "run_b")
    replay = store.read_run("run_a")
    assert len(replay) == 2
    assert replay[0].kind == "model_request"
    assert replay[1].payload["text"] == "ok"
    assert store.read_run("missing") == ()


def test_approval_policy_patterns() -> None:
    policy = ApprovalPolicy(
        rules=(
            ApprovalRule(
                tool_name_pattern="keyword_*",
                mode=ApprovalMode.ALLOW,
                reason="local retrieval is allowed",
            ),
            ApprovalRule(
                tool_name_pattern="shell_*",
                mode=ApprovalMode.DENY,
                reason="shell tools are blocked",
            ),
        ),
        default_mode=ApprovalMode.REQUIRE_APPROVAL,
    )
    allow = policy.decide("keyword_search")
    assert allow.mode is ApprovalMode.ALLOW
    assert allow.matched_rule == "keyword_*"
    deny = policy.decide("shell_rm")
    assert deny.mode is ApprovalMode.DENY
    review = policy.decide("unknown_tool")
    assert review.requires_review is True
    assert review.to_record()["mode"] == "require_approval"


def test_sandbox_policy_paths_and_network(tmp_path: Path) -> None:
    allowed = tmp_path / "workspace"
    allowed.mkdir()
    blocked = tmp_path / "secrets"
    blocked.mkdir()
    policy = SandboxPolicy(
        readable_paths=(allowed,),
        writable_paths=(allowed,),
        blocked_paths=(blocked,),
        allow_network=False,
        max_runtime_seconds=10,
    )
    ok = policy.decide_path(allowed / "paper.json", access="read")
    assert ok.allowed is True
    no = policy.decide_path(tmp_path / "elsewhere" / "x", access="write")
    assert no.allowed is False
    blocked_decision = policy.decide_path(blocked / "key", access="read")
    assert blocked_decision.allowed is False
    net = policy.network_decision()
    assert net.allowed is False
    assert policy.runtime_decision(5).allowed is True
    assert policy.runtime_decision(11).allowed is False
