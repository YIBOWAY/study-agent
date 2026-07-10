import json

import pytest
from research_core.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    SandboxPolicy,
)


def test_approval_policy_returns_first_matching_rule_decision() -> None:
    policy = ApprovalPolicy(
        default_mode=ApprovalMode.REQUIRE_APPROVAL,
        default_reason="Unknown tools need review.",
        rules=(
            ApprovalRule(
                tool_name_pattern="retriever.*",
                mode=ApprovalMode.ALLOW,
                reason="Read-only retrieval is allowed.",
            ),
            ApprovalRule(
                tool_name_pattern="shell.*",
                mode=ApprovalMode.DENY,
                reason="Shell commands are blocked in this lesson.",
            ),
        ),
    )

    allowed = policy.decide("retriever.search")
    denied = policy.decide("shell.exec")
    review = policy.decide("email.send")

    assert allowed.mode is ApprovalMode.ALLOW
    assert allowed.requires_review is False
    assert allowed.to_record() == {
        "subject": "retriever.search",
        "mode": "allow",
        "reason": "Read-only retrieval is allowed.",
        "matched_rule": "retriever.*",
    }
    assert denied.mode is ApprovalMode.DENY
    assert denied.requires_review is False
    assert review.mode is ApprovalMode.REQUIRE_APPROVAL
    assert review.requires_review is True
    assert review.matched_rule == ""
    assert json.loads(json.dumps(review.to_record(), allow_nan=False)) == (
        review.to_record()
    )


def test_approval_policy_rejects_blank_patterns_and_subjects() -> None:
    with pytest.raises(ValueError, match="tool_name_pattern must not be empty"):
        ApprovalRule(tool_name_pattern=" ", mode=ApprovalMode.ALLOW, reason="Allowed.")

    policy = ApprovalPolicy()
    with pytest.raises(ValueError, match="subject must not be empty"):
        policy.decide("")


def test_sandbox_policy_allows_explicit_paths_and_blocks_sensitive_paths(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    output = workspace / "outputs" / "report.md"
    secret = workspace / "secrets" / "token.txt"
    outside = tmp_path / "outside.txt"
    policy = SandboxPolicy(
        readable_paths=(workspace,),
        writable_paths=(workspace / "outputs",),
        blocked_paths=(workspace / "secrets",),
        allow_network=False,
        max_runtime_seconds=15,
    )

    assert policy.decide_path(output, access="read").allowed is True
    assert policy.decide_path(output, access="write").allowed is True
    assert policy.decide_path(secret, access="read").to_record() == {
        "subject": str(secret),
        "allowed": False,
        "reason": "path is blocked by sandbox policy",
    }
    assert policy.decide_path(outside, access="read").allowed is False
    assert policy.network_decision().to_record() == {
        "subject": "network",
        "allowed": False,
        "reason": "network access is disabled",
    }


def test_sandbox_policy_rejects_invalid_limits_and_access_names(tmp_path) -> None:
    with pytest.raises(ValueError, match="max_runtime_seconds must be a positive integer"):
        SandboxPolicy(max_runtime_seconds=0)

    policy = SandboxPolicy(readable_paths=(tmp_path,))
    with pytest.raises(ValueError, match="access must be one of"):
        policy.decide_path(tmp_path / "file.txt", access="execute")


def test_sandbox_runtime_decision_uses_max_runtime_seconds(tmp_path) -> None:
    sandbox = SandboxPolicy(
        readable_paths=(tmp_path,),
        max_runtime_seconds=15,
    )

    allowed = sandbox.runtime_decision(5)
    denied = sandbox.runtime_decision(20)

    assert allowed.allowed is True
    assert denied.allowed is False
    assert "exceeds max_runtime_seconds 15" in denied.reason
