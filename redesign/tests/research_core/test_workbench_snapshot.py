import json
from dataclasses import replace

import pytest
from research_core.product import (
    WorkbenchDelegationNode,
    WorkbenchEvalItem,
    WorkbenchEvidenceItem,
    WorkbenchMemoryItem,
    WorkbenchProject,
    WorkbenchReport,
    WorkbenchRun,
    WorkbenchSkillItem,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
    WorkbenchTimelineItem,
    build_demo_workbench_snapshot,
)


def test_required_public_workbench_names_are_exported() -> None:
    assert WorkbenchProject.__name__ == "WorkbenchProject"
    assert WorkbenchRun.__name__ == "WorkbenchRun"
    assert WorkbenchTimelineItem.__name__ == "WorkbenchTimelineItem"
    assert WorkbenchDelegationNode.__name__ == "WorkbenchDelegationNode"
    assert WorkbenchEvidenceItem.__name__ == "WorkbenchEvidenceItem"
    assert WorkbenchSourceItem.__name__ == "WorkbenchSourceItem"
    assert WorkbenchReport.__name__ == "WorkbenchReport"
    assert WorkbenchMemoryItem.__name__ == "WorkbenchMemoryItem"
    assert WorkbenchSkillItem.__name__ == "WorkbenchSkillItem"
    assert WorkbenchEvalItem.__name__ == "WorkbenchEvalItem"
    assert WorkbenchSnapshot.__name__ == "WorkbenchSnapshot"
    assert build_demo_workbench_snapshot.__name__ == "build_demo_workbench_snapshot"


def test_demo_workbench_snapshot_record_is_plain_json_contract() -> None:
    snapshot = build_demo_workbench_snapshot()

    record = snapshot.to_record()

    assert set(record) == {
        "project",
        "run",
        "timeline",
        "delegation",
        "sources",
        "report",
        "memory",
        "skills",
        "evals",
    }
    assert record["project"]["id"] == "project_workbench_demo"
    assert record["run"]["project_id"] == "project_workbench_demo"
    assert record["report"]["run_id"] == record["run"]["id"]
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_timeline_preserves_stable_runtime_event_order() -> None:
    snapshot = build_demo_workbench_snapshot()

    record = snapshot.to_record()

    assert [item["type"] for item in record["timeline"]] == [
        "model_request",
        "tool_call",
        "delegate_start",
        "delegate_finish",
    ]
    assert [item["id"] for item in record["timeline"]] == [
        "evt_model_request",
        "evt_tool_call",
        "evt_delegate_start",
        "evt_delegate_finish",
    ]


def test_sources_and_report_preserve_claim_source_links() -> None:
    snapshot = build_demo_workbench_snapshot()

    record = snapshot.to_record()

    first_source = record["sources"][0]
    first_evidence = first_source["evidence"][0]
    first_link = record["report"]["claim_source_links"][0]

    assert first_evidence["claim_ids"] == [first_link["claim_id"]]
    assert first_link == {
        "claim_id": "claim_1",
        "claim_text": "Citation-backed workbench snapshots make research auditable.",
        "evidence_id": first_evidence["id"],
        "source_id": first_source["id"],
        "source_title": first_source["title"],
        "source_uri": first_source["uri"],
        "quote": first_evidence["quote"],
        "location": first_evidence["location"],
    }


def test_memory_skill_and_eval_panels_expose_deterministic_summary_rows() -> None:
    snapshot = build_demo_workbench_snapshot()

    record = snapshot.to_record()

    assert [item["summary_row"] for item in record["memory"]] == [
        {
            "id": "mem_citation_rule",
            "title": "Citation rule",
            "kind": "pinned",
            "importance": 0.95,
            "tags": ["citation", "reporting"],
        },
        {
            "id": "mem_workbench_preference",
            "title": "Workbench preference",
            "kind": "semantic",
            "importance": 0.8,
            "tags": ["product"],
        },
    ]
    assert [item["summary_row"] for item in record["skills"]] == [
        {
            "id": "skill_source_mapping",
            "title": "Source mapping",
            "name": "source-mapping",
            "status": "loaded",
            "resource_count": 2,
        }
    ]
    assert [item["summary_row"] for item in record["evals"]] == [
        {
            "id": "eval_claim_links",
            "title": "Claim links",
            "metric": "claim_source_coverage",
            "status": "passed",
            "score": 1.0,
        }
    ]


def test_to_record_returns_independent_plain_copies() -> None:
    snapshot = build_demo_workbench_snapshot()

    record = snapshot.to_record()
    record["timeline"][0]["metadata"]["tokens"]["prompt"] = 999
    record["sources"][0]["evidence"][0]["claim_ids"].append("mutated")
    record["report"]["claim_source_links"][0]["quote"] = "mutated"
    record["memory"][0]["summary_row"]["tags"].append("mutated")

    fresh_record = snapshot.to_record()
    assert fresh_record["timeline"][0]["metadata"]["tokens"]["prompt"] == 128
    assert fresh_record["sources"][0]["evidence"][0]["claim_ids"] == ["claim_1"]
    assert (
        fresh_record["report"]["claim_source_links"][0]["quote"]
        == "Every report claim keeps an evidence link back to a source."
    )
    assert fresh_record["memory"][0]["summary_row"]["tags"] == [
        "citation",
        "reporting",
    ]


def test_snapshot_contract_rejects_blank_ids_titles_and_bad_metadata() -> None:
    invalid_cases = [
        (
            lambda: WorkbenchProject(id=" ", title="Workbench"),
            "id must not be empty",
        ),
        (
            lambda: WorkbenchRun(
                id="run_1",
                project_id="project_1",
                title=" ",
                question="What changed?",
            ),
            "title must not be empty",
        ),
        (
            lambda: WorkbenchTimelineItem(
                id="evt_1",
                run_id="run_1",
                type="model_request",
                title=" ",
            ),
            "title must not be empty",
        ),
        (
            lambda: WorkbenchSourceItem(
                id="source_1",
                title=" ",
                uri="memory://source",
            ),
            "title must not be empty",
        ),
        (
            lambda: WorkbenchReport(
                id="report_1",
                run_id="run_1",
                title=" ",
                summary="Summary.",
            ),
            "title must not be empty",
        ),
        (
            lambda: WorkbenchTimelineItem(
                id="evt_1",
                run_id="run_1",
                type="model_request",
                title="Model request",
                metadata={"flags": {"cached"}},
            ),
            "payload values must be JSON-compatible",
        ),
        (
            lambda: WorkbenchSnapshot(
                project=WorkbenchProject(id="project_1", title="Project"),
                run=WorkbenchRun(
                    id="run_1",
                    project_id="project_1",
                    title="Run",
                    question="What changed?",
                ),
                memory=[
                    build_demo_workbench_snapshot().memory[0].__class__(
                        id="mem_bad",
                        title="Bad memory",
                        kind="semantic",
                        content="Bad importance.",
                        importance=1.5,
                    )
                ],
            ),
            "importance must be a number between 0 and 1",
        ),
        (
            lambda: build_demo_workbench_snapshot().evals[0].__class__(
                id="eval_bad",
                title="Bad eval",
                metric="coverage",
                status="passed",
                score=-0.1,
            ),
            "score must be a number between 0 and 1",
        ),
    ]

    for build_invalid, expected_message in invalid_cases:
        try:
            build_invalid()
        except ValueError as exc:
            assert expected_message in str(exc)
        else:
            raise AssertionError(f"Expected invalid workbench contract: {expected_message}")


def test_snapshot_requires_panel_contract_objects() -> None:
    snapshot = build_demo_workbench_snapshot()

    try:
        WorkbenchSnapshot(
            project=snapshot.project,
            run=snapshot.run,
            timeline=[object()],
            delegation=snapshot.delegation,
            sources=snapshot.sources,
            report=snapshot.report,
            memory=snapshot.memory,
            skills=snapshot.skills,
            evals=snapshot.evals,
        )
    except ValueError as exc:
        assert "timeline must contain WorkbenchTimelineItem objects" in str(exc)
    else:
        raise AssertionError("Expected non-workbench timeline items to be rejected")


def test_snapshot_rejects_cross_field_reference_mismatches() -> None:
    snapshot = build_demo_workbench_snapshot()
    invalid_cases = [
        (
            lambda: _copy_snapshot(
                snapshot,
                run=replace(snapshot.run, project_id="other_project"),
            ),
            "run project_id must match project id",
        ),
        (
            lambda: _copy_snapshot(
                snapshot,
                timeline=(replace(snapshot.timeline[0], run_id="other_run"),),
            ),
            "timeline run_id must match run id",
        ),
        (
            lambda: _copy_snapshot(
                snapshot,
                report=replace(snapshot.report, run_id="other_run"),
            ),
            "report run_id must match run id",
        ),
        (
            lambda: _copy_snapshot(
                snapshot,
                sources=(
                    WorkbenchSourceItem(
                        id="source_1",
                        title="Source",
                        uri="memory://source",
                        evidence=(
                            WorkbenchEvidenceItem(
                                id="evidence_1",
                                source_id="other_source",
                                quote="Evidence quote.",
                            ),
                        ),
                    ),
                ),
                report=None,
            ),
            "source evidence source_id must match source id",
        ),
        (
            lambda: _copy_snapshot(
                snapshot,
                report=replace(
                    snapshot.report,
                    claim_source_links=(
                        replace(
                            snapshot.report.claim_source_links[0],
                            evidence_id="missing_evidence",
                        ),
                    ),
                ),
            ),
            "report claim_source_links evidence_id must reference snapshot evidence",
        ),
    ]

    for build_invalid, expected_message in invalid_cases:
        with pytest.raises(ValueError, match=expected_message):
            build_invalid()


def test_snapshot_rejects_invalid_delegation_tree_relationships() -> None:
    snapshot = build_demo_workbench_snapshot()

    with pytest.raises(ValueError, match="delegation node ids must be unique"):
        _copy_snapshot(
            snapshot,
            delegation=(
                WorkbenchDelegationNode(
                    id="task_duplicate",
                    title="First",
                    role="reviewer",
                    status="completed",
                    run_id="run_child_1",
                ),
                WorkbenchDelegationNode(
                    id="task_duplicate",
                    title="Second",
                    role="reviewer",
                    status="completed",
                    run_id="run_child_2",
                ),
            ),
        )

    with pytest.raises(
        ValueError,
        match="delegation parent_id must reference another delegation node",
    ):
        _copy_snapshot(
            snapshot,
            delegation=(
                WorkbenchDelegationNode(
                    id="task_orphan",
                    title="Orphan",
                    role="reviewer",
                    status="completed",
                    run_id="run_child_orphan",
                    parent_id="missing_parent",
                ),
            ),
        )

    with pytest.raises(
        ValueError,
        match="delegation child parent_id must match parent node id",
    ):
        _copy_snapshot(
            snapshot,
            delegation=(
                WorkbenchDelegationNode(
                    id="task_parent",
                    title="Parent",
                    role="lead",
                    status="completed",
                    run_id="run_child_parent",
                    children=(
                        WorkbenchDelegationNode(
                            id="task_child",
                            title="Child",
                            role="reviewer",
                            status="completed",
                            run_id="run_child_nested",
                            parent_id="task_sibling",
                        ),
                    ),
                ),
                WorkbenchDelegationNode(
                    id="task_sibling",
                    title="Sibling",
                    role="reviewer",
                    status="completed",
                    run_id="run_child_sibling",
                ),
            ),
        )


def _copy_snapshot(snapshot: WorkbenchSnapshot, **overrides: object) -> WorkbenchSnapshot:
    values = {
        "project": snapshot.project,
        "run": snapshot.run,
        "timeline": snapshot.timeline,
        "delegation": snapshot.delegation,
        "sources": snapshot.sources,
        "report": snapshot.report,
        "memory": snapshot.memory,
        "skills": snapshot.skills,
        "evals": snapshot.evals,
    }
    values.update(overrides)
    return WorkbenchSnapshot(**values)
