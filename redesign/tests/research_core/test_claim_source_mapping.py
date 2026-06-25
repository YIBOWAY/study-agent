from research_core.research import (
    Claim,
    ClaimSourceLink,
    Evidence,
    Report,
    Source,
    build_claim_source_links,
)


def test_build_claim_source_links_returns_deterministic_links() -> None:
    source_1 = Source(
        id="source_1",
        uri="memory://source-1",
        title="Agent Evidence",
        content="Agents need evidence.",
    )
    source_2 = Source(
        id="source_2",
        uri="memory://source-2",
        title="Citation Mapping",
        content="Reports map claims to sources.",
    )
    evidence_1 = Evidence(
        id="evidence_1",
        source_id="source_1",
        quote="Agents need evidence.",
        location="p1",
    )
    evidence_2 = Evidence(
        id="evidence_2",
        source_id="source_2",
        quote="Reports map claims to sources.",
        location="p2",
    )
    report = Report(
        id="report_1",
        run_id="run_1",
        title="Report",
        summary="Summary.",
        claims=[
            Claim(id="claim_1", text="Agents need evidence.", evidence_ids=["evidence_1"]),
            Claim(id="claim_2", text="Reports need citations.", evidence_ids=["evidence_2"]),
        ],
    )

    links = build_claim_source_links(report, [evidence_2, evidence_1], [source_2, source_1])

    assert links == (
        ClaimSourceLink(
            claim_id="claim_1",
            claim_text="Agents need evidence.",
            evidence_id="evidence_1",
            source_id="source_1",
            source_title="Agent Evidence",
            source_uri="memory://source-1",
            quote="Agents need evidence.",
            location="p1",
        ),
        ClaimSourceLink(
            claim_id="claim_2",
            claim_text="Reports need citations.",
            evidence_id="evidence_2",
            source_id="source_2",
            source_title="Citation Mapping",
            source_uri="memory://source-2",
            quote="Reports map claims to sources.",
            location="p2",
        ),
    )


def test_claim_source_link_to_record_is_plain_serializable() -> None:
    link = ClaimSourceLink(
        claim_id="claim_1",
        claim_text="Agents need evidence.",
        evidence_id="evidence_1",
        source_id="source_1",
        source_title="Agent Evidence",
        source_uri="memory://source-1",
        quote="Agents need evidence.",
        location="p1",
    )

    assert link.to_record() == {
        "claim_id": "claim_1",
        "claim_text": "Agents need evidence.",
        "evidence_id": "evidence_1",
        "source_id": "source_1",
        "source_title": "Agent Evidence",
        "source_uri": "memory://source-1",
        "quote": "Agents need evidence.",
        "location": "p1",
    }


def test_build_claim_source_links_rejects_missing_evidence() -> None:
    report = Report(
        id="report_1",
        run_id="run_1",
        title="Report",
        summary="Summary.",
        claims=[Claim(id="claim_1", text="Missing evidence.", evidence_ids=["missing"])],
    )

    try:
        build_claim_source_links(report, evidence=[], sources=[])
    except ValueError as exc:
        assert "claim 'claim_1' references missing evidence 'missing'" in str(exc)
    else:
        raise AssertionError("Expected missing evidence to be rejected")


def test_build_claim_source_links_rejects_missing_source() -> None:
    report = Report(
        id="report_1",
        run_id="run_1",
        title="Report",
        summary="Summary.",
        claims=[Claim(id="claim_1", text="Missing source.", evidence_ids=["evidence_1"])],
    )
    evidence = [Evidence(id="evidence_1", source_id="missing", quote="Quote.")]

    try:
        build_claim_source_links(report, evidence=evidence, sources=[])
    except ValueError as exc:
        assert "evidence 'evidence_1' references missing source 'missing'" in str(exc)
    else:
        raise AssertionError("Expected missing source to be rejected")


def test_build_claim_source_links_rejects_claims_without_evidence() -> None:
    report = Report(
        id="report_1",
        run_id="run_1",
        title="Report",
        summary="Summary.",
        claims=[Claim(id="claim_1", text="Unsupported claim.")],
    )

    try:
        build_claim_source_links(report, evidence=[], sources=[])
    except ValueError as exc:
        assert "claim 'claim_1' must reference at least one evidence id" in str(exc)
    else:
        raise AssertionError("Expected unsupported claim to be rejected")
