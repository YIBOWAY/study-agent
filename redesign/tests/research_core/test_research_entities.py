from dataclasses import FrozenInstanceError

from research_core.research import (
    Claim,
    Evidence,
    Project,
    Report,
    ResearchRun,
    ResearchRunStatus,
    Source,
)


def test_project_rejects_blank_id_and_name() -> None:
    try:
        Project(id="", name="Research")
    except ValueError as exc:
        assert "id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank id to be rejected")

    try:
        Project(id="project_1", name=" ")
    except ValueError as exc:
        assert "name must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank name to be rejected")


def test_project_metadata_is_copied_and_read_only() -> None:
    metadata = {"tags": ["agent"], "nested": {"priority": 1}}
    project = Project(id="project_1", name="Research", metadata=metadata)

    metadata["tags"].append("mutated")
    metadata["nested"]["priority"] = 2

    assert project.metadata["tags"] == ("agent",)
    assert project.metadata["nested"]["priority"] == 1

    try:
        project.metadata["nested"]["priority"] = 3
    except TypeError:
        pass
    else:
        raise AssertionError("Expected nested metadata to be read-only")


def test_metadata_rejects_non_json_compatible_values() -> None:
    try:
        Source(
            id="source_1",
            uri="memory://source",
            title="Source",
            content="content",
            metadata={"flags": {"cached"}},
        )
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible metadata to be rejected")


def test_research_run_status_accepts_string_values() -> None:
    run = ResearchRun(
        id="run_1",
        project_id="project_1",
        question="What changed?",
        status="running",
    )

    assert run.status is ResearchRunStatus.RUNNING


def test_research_run_status_rejects_unsupported_values() -> None:
    try:
        ResearchRun(
            id="run_1",
            project_id="project_1",
            question="What changed?",
            status="paused",
        )
    except ValueError as exc:
        assert "status must be one of" in str(exc)
    else:
        raise AssertionError("Expected unsupported status to be rejected")


def test_source_and_evidence_require_research_text_fields() -> None:
    try:
        Source(id="source_1", uri="", title="Source", content="content")
    except ValueError as exc:
        assert "uri must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank uri to be rejected")

    try:
        Evidence(id="evidence_1", source_id="source_1", quote="")
    except ValueError as exc:
        assert "quote must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank quote to be rejected")


def test_claim_evidence_ids_are_copied_and_immutable() -> None:
    evidence_ids = ["evidence_1"]
    claim = Claim(id="claim_1", text="Agents need evidence.", evidence_ids=evidence_ids)

    evidence_ids.append("evidence_2")

    assert claim.evidence_ids == ("evidence_1",)

    try:
        claim.evidence_ids += ("evidence_3",)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Expected claim evidence ids to be immutable")


def test_claim_rejects_blank_evidence_ids_when_supplied() -> None:
    try:
        Claim(id="claim_1", text="Agents need evidence.", evidence_ids=[" "])
    except ValueError as exc:
        assert "evidence_ids must not contain blank values" in str(exc)
    else:
        raise AssertionError("Expected blank evidence id to be rejected")


def test_report_claims_are_copied_immutable_and_ordered() -> None:
    first = Claim(id="claim_1", text="First claim.", evidence_ids=["evidence_1"])
    second = Claim(id="claim_2", text="Second claim.", evidence_ids=["evidence_2"])
    claims = [first, second]
    report = Report(
        id="report_1",
        run_id="run_1",
        title="Report",
        summary="Summary.",
        claims=claims,
    )

    claims.reverse()

    assert report.claims == (first, second)

    try:
        report.claims += (first,)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Expected report claims to be immutable")


def test_entity_contracts_are_frozen_and_slotted() -> None:
    project = Project(id="project_1", name="Research")
    source = Source(id="source_1", uri="memory://source", title="Source", content="content")

    for entity in (project, source):
        assert not hasattr(entity, "__dict__")
        try:
            entity.id = "mutated"
        except (AttributeError, FrozenInstanceError):
            pass
        else:
            raise AssertionError("Expected entity to be frozen")
