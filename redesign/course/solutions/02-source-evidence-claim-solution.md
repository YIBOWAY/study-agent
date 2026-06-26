# Solution 02: Source, Evidence, Claim

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

所有 snippets 都从 `redesign/` 的 Python shell 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Imports

```python
from research_core.research import (
    Claim,
    Evidence,
    FakeRetriever,
    Report,
    SourceIngestor,
    SourceInput,
    build_claim_source_links,
)
```

## Exercise 1 Solution

```python
sources = SourceIngestor().ingest_many(
    [
        SourceInput(
            uri="memory://agent-evidence",
            title="Agent Evidence",
            content="Research agents need evidence and citation mapping.",
        ),
        SourceInput(
            uri="memory://memory-policy",
            title="Memory Policy",
            content="Memory records can pollute an agent without write policy.",
        ),
    ]
)

assert [source.id for source in sources] == ["source_1", "source_2"]
assert sources[0].uri == "memory://agent-evidence"
assert sources[1].title == "Memory Policy"
```

What this proves:

- `SourceIngestor` assigns deterministic source IDs.
- `SourceInput` becomes a stable `Source`.
- The lab does not need a database or web crawler.

## Exercise 2 Solution

```python
results = FakeRetriever(sources).search("evidence citation", limit=1)

assert results[0].source_id == "source_1"
assert results[0].title == "Agent Evidence"
assert results[0].score > 0
```

What this proves:

- Retrieval can be tested offline.
- Source ranking is deterministic for the same inputs.
- Search results carry enough source metadata for later UI panels.

## Exercise 3 Solution

```python
evidence = [
    Evidence(
        id="evidence_1",
        source_id="source_1",
        quote="Research agents need evidence and citation mapping.",
        location="sentence 1",
    )
]

report = Report(
    id="report_1",
    run_id="run_1",
    title="Research Agent Notes",
    summary="Evidence mapping keeps reports inspectable.",
    claims=[
        Claim(
            id="claim_1",
            text="Research-agent reports should preserve evidence links.",
            evidence_ids=["evidence_1"],
        )
    ],
)

links = build_claim_source_links(report, evidence=evidence, sources=sources)
record = links[0].to_record()

assert record == {
    "claim_id": "claim_1",
    "claim_text": "Research-agent reports should preserve evidence links.",
    "evidence_id": "evidence_1",
    "source_id": "source_1",
    "source_title": "Agent Evidence",
    "source_uri": "memory://agent-evidence",
    "quote": "Research agents need evidence and citation mapping.",
    "location": "sentence 1",
}
```

What this proves:

- A report claim can be traced back to a quote.
- The quote can be traced back to a source URI.
- `ClaimSourceLink` is a plain serializable record shape for product UI and evals.

## Exercise 4 Solution

```python
bad_report = Report(
    id="bad_report",
    run_id="run_1",
    title="Bad Report",
    summary="This report has an unsupported claim.",
    claims=[Claim(id="claim_bad", text="Unsupported claim.")],
)

try:
    build_claim_source_links(bad_report, evidence=[], sources=sources)
except ValueError as exc:
    error_message = str(exc)
else:
    raise AssertionError("Expected unsupported claim to fail")

assert error_message == "claim 'claim_bad' must reference at least one evidence id"
```

What this proves:

- Unsupported claims are rejected.
- The failure is explicit and inspectable.
- Research quality is protected by data contracts, not by trust in final prose.

## Final Takeaway

The important lesson is:

```text
A research agent should preserve the evidence path from report claim back to source.
```

This is the difference between a nice-looking answer and an auditable research artifact.
