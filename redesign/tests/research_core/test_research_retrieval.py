from dataclasses import FrozenInstanceError

import pytest
from research_core.research import FakeRetriever, SearchResult, Source, SourceIngestor, SourceInput


def test_source_input_rejects_blank_uri_title_and_content() -> None:
    try:
        SourceInput(uri="", title="Source", content="content")
    except ValueError as exc:
        assert "uri must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank uri to be rejected")

    try:
        SourceInput(uri="memory://source", title=" ", content="content")
    except ValueError as exc:
        assert "title must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank title to be rejected")

    try:
        SourceInput(uri="memory://source", title="Source", content="")
    except ValueError as exc:
        assert "content must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank content to be rejected")


def test_source_input_metadata_is_copied_and_read_only() -> None:
    metadata = {"tags": ["fixture"]}
    source_input = SourceInput(
        uri="memory://source",
        title="Source",
        content="content",
        metadata=metadata,
    )

    metadata["tags"].append("mutated")

    assert source_input.metadata["tags"] == ("fixture",)

    try:
        source_input.metadata["tags"] = ("changed",)
    except TypeError:
        pass
    else:
        raise AssertionError("Expected metadata to be read-only")


def test_source_ingestor_assigns_deterministic_ids_and_preserves_metadata() -> None:
    ingestor = SourceIngestor(id_prefix="doc")

    sources = ingestor.ingest_many(
        [
            SourceInput(
                uri="memory://first",
                title="First",
                content="First content.",
                metadata={"kind": "note"},
            ),
            SourceInput(uri="memory://second", title="Second", content="Second content."),
        ]
    )

    assert [source.id for source in sources] == ["doc_1", "doc_2"]
    assert sources[0].uri == "memory://first"
    assert sources[0].metadata["kind"] == "note"
    assert sources[1].content == "Second content."


def test_fake_retriever_returns_matching_sources_sorted_by_score_then_source_order() -> None:
    sources = SourceIngestor().ingest_many(
        [
            SourceInput(
                uri="memory://agent-evidence",
                title="Agent Evidence",
                content="Agent runs need evidence and citation mapping.",
            ),
            SourceInput(
                uri="memory://memory",
                title="Memory Policy",
                content="Memory records can pollute agents without policy.",
            ),
            SourceInput(
                uri="memory://evidence-graph",
                title="Evidence Graph",
                content="Claim evidence mapping keeps reports grounded.",
            ),
        ]
    )
    retriever = FakeRetriever(sources)

    results = retriever.search("evidence mapping", limit=2)

    assert [result.source_id for result in results] == ["source_3", "source_1"]
    assert [result.score for result in results] == [4, 3]
    assert results[0].title == "Evidence Graph"
    assert results[0].snippet == "Claim evidence mapping keeps reports grounded."
    assert results[0].metadata["uri"] == "memory://evidence-graph"


def test_fake_retriever_returns_empty_tuple_for_no_matches() -> None:
    sources = SourceIngestor().ingest_many(
        [SourceInput(uri="memory://source", title="Source", content="Only local content.")]
    )

    assert FakeRetriever(sources).search("delegation") == ()


def test_fake_retriever_rejects_empty_queries_and_invalid_limits() -> None:
    retriever = FakeRetriever(())

    try:
        retriever.search(" ")
    except ValueError as exc:
        assert "query must not be empty" in str(exc)
    else:
        raise AssertionError("Expected empty query to be rejected")

    for limit in (0, -1, True):
        try:
            retriever.search("agent", limit=limit)
        except ValueError as exc:
            assert "limit must be a positive integer" in str(exc)
        else:
            raise AssertionError("Expected invalid limit to be rejected")


def test_search_result_contract_is_frozen_slotted_and_metadata_is_read_only() -> None:
    result = SearchResult(
        source_id="source_1",
        title="Source",
        snippet="Snippet",
        score=1,
        metadata={"uri": "memory://source"},
    )

    assert not hasattr(result, "__dict__")
    assert result.metadata["uri"] == "memory://source"

    try:
        result.title = "mutated"
    except (AttributeError, FrozenInstanceError):
        pass
    else:
        raise AssertionError("Expected search result to be frozen")

    try:
        result.metadata["uri"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected search result metadata to be read-only")


def test_fake_retriever_matches_chinese_query() -> None:
    source = Source(
        id="src_cjk",
        uri="memory://cjk",
        title="研究笔记",
        content="本地论文研究助手需要证据链。",
    )
    retriever = FakeRetriever([source])

    results = retriever.search("论文证据")

    assert [item.source_id for item in results] == ["src_cjk"]


def test_fake_retriever_rejects_duplicate_source_ids() -> None:
    source = Source(
        id="src_dup",
        uri="memory://a",
        title="A",
        content="alpha beta",
    )
    duplicate = Source(
        id="src_dup",
        uri="memory://b",
        title="B",
        content="gamma delta",
    )
    with pytest.raises(ValueError, match="duplicate source id"):
        FakeRetriever([source, duplicate])
