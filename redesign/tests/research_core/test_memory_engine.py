from dataclasses import FrozenInstanceError

from research_core.memory import (
    MemoryEngine,
    MemoryKind,
    MemoryRecallPolicy,
    MemoryRecord,
    MemoryWritePolicy,
)


def test_memory_record_rejects_blank_id_and_content() -> None:
    try:
        MemoryRecord(id="", kind=MemoryKind.SEMANTIC, content="User prefers citations.")
    except ValueError as exc:
        assert "id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank id to be rejected")

    try:
        MemoryRecord(id="mem_1", kind=MemoryKind.SEMANTIC, content=" ")
    except ValueError as exc:
        assert "content must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank content to be rejected")


def test_memory_record_normalizes_kind_from_string() -> None:
    record = MemoryRecord(id="mem_1", kind="pinned", content="Always cite sources.")

    assert record.kind is MemoryKind.PINNED


def test_memory_record_rejects_invalid_kind_and_importance() -> None:
    try:
        MemoryRecord(id="mem_1", kind="global", content="User prefers citations.")
    except ValueError as exc:
        assert "kind must be one of" in str(exc)
    else:
        raise AssertionError("Expected invalid kind to be rejected")

    for value in (-0.1, 1.1, True):
        try:
            MemoryRecord(
                id="mem_1",
                kind=MemoryKind.SEMANTIC,
                content="User prefers citations.",
                importance=value,
            )
        except ValueError as exc:
            assert "importance must be a number between 0 and 1" in str(exc)
        else:
            raise AssertionError("Expected invalid importance to be rejected")


def test_memory_record_tags_and_metadata_are_copied_and_read_only() -> None:
    tags = ["citation"]
    metadata = {"source": {"run_id": "run_1"}}
    record = MemoryRecord(
        id="mem_1",
        kind=MemoryKind.SEMANTIC,
        content="User prefers citation-backed answers.",
        tags=tags,
        metadata=metadata,
    )

    tags.append("mutated")
    metadata["source"]["run_id"] = "mutated"

    assert record.tags == ("citation",)
    assert record.metadata["source"]["run_id"] == "run_1"

    try:
        record.tags += ("new",)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Expected tags to be immutable")

    try:
        record.metadata["source"]["run_id"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected metadata to be read-only")


def test_memory_write_policy_rejects_disallowed_low_value_overlong_and_forbidden_writes() -> None:
    policy = MemoryWritePolicy(
        allowed_kinds=[MemoryKind.SEMANTIC],
        min_importance=0.5,
        max_content_chars=32,
        forbidden_phrases=["remember everything"],
    )

    cases = [
        (
            MemoryRecord(
                id="mem_1",
                kind=MemoryKind.WORKING,
                content="Temporary scratch note.",
                importance=0.9,
            ),
            "kind 'working' is not allowed",
        ),
        (
            MemoryRecord(
                id="mem_2",
                kind=MemoryKind.SEMANTIC,
                content="Low-value preference.",
                importance=0.1,
            ),
            "importance is below policy minimum",
        ),
        (
            MemoryRecord(
                id="mem_3",
                kind=MemoryKind.SEMANTIC,
                content="This content is intentionally longer than the policy allows.",
                importance=0.9,
            ),
            "content exceeds policy maximum",
        ),
        (
            MemoryRecord(
                id="mem_4",
                kind=MemoryKind.SEMANTIC,
                content="Remember everything the user says.",
                importance=0.9,
            ),
            "content contains forbidden phrase",
        ),
    ]

    for record, expected_message in cases:
        try:
            policy.validate(record)
        except ValueError as exc:
            assert expected_message in str(exc)
        else:
            raise AssertionError(f"Expected policy to reject {record.id}")


def test_memory_engine_writes_and_recalls_deterministic_pinned_first_matches() -> None:
    engine = MemoryEngine(
        write_policy=MemoryWritePolicy(
            allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
            min_importance=0.2,
        )
    )
    semantic = engine.write(
        MemoryRecord(
            id="mem_1",
            kind=MemoryKind.SEMANTIC,
            content="The user prefers citation-backed agent answers.",
            tags=["preference"],
            importance=0.8,
        )
    )
    pinned = engine.write(
        MemoryRecord(
            id="mem_2",
            kind=MemoryKind.PINNED,
            content="Always preserve source evidence in research answers.",
            tags=["rule"],
            importance=0.7,
        )
    )
    engine.write(
        MemoryRecord(
            id="mem_3",
            kind=MemoryKind.SEMANTIC,
            content="The project uses deterministic fake models.",
            tags=["project"],
            importance=0.9,
        )
    )

    recalled = engine.recall(MemoryRecallPolicy(query="agent evidence answers", limit=2))

    assert recalled == (pinned, semantic)


def test_memory_recall_policy_rejects_empty_query_and_invalid_limit() -> None:
    try:
        MemoryRecallPolicy(query=" ")
    except ValueError as exc:
        assert "query must not be empty" in str(exc)
    else:
        raise AssertionError("Expected empty query to be rejected")

    for limit in (0, -1, True):
        try:
            MemoryRecallPolicy(query="agent", limit=limit)
        except ValueError as exc:
            assert "limit must be a positive integer" in str(exc)
        else:
            raise AssertionError("Expected invalid limit to be rejected")


def test_memory_engine_recall_filters_allowed_kinds() -> None:
    engine = MemoryEngine()
    engine.write(
        MemoryRecord(
            id="mem_1",
            kind=MemoryKind.SESSION,
            content="Session says agent memory should be temporary.",
        )
    )
    semantic = engine.write(
        MemoryRecord(
            id="mem_2",
            kind=MemoryKind.SEMANTIC,
            content="Semantic memory stores durable agent preferences.",
        )
    )

    recalled = engine.recall(
        MemoryRecallPolicy(query="agent memory", allowed_kinds=[MemoryKind.SEMANTIC])
    )

    assert recalled == (semantic,)
