# Solution 02: Evidence Chain Lab

这份 solution 用来校准理解，不是用来跳过 lab。先自己完成 Lab 02，再看这里。

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
    Source,
    SourceIngestor,
    SourceInput,
    build_claim_source_links,
)
```

## Exercise 1 Solution: Build The Smallest Supported Claim

### What This Proves

这一题证明最小证据链成立：

- `SourceIngestor` 生成稳定 source IDs。
- `FakeRetriever` 能离线找到相关 source。
- `Claim.evidence_ids` 能把 report claim 连到 evidence。
- `ClaimSourceLink.to_record()` 能把 claim、evidence、source 合成产品和 eval 可消费的普通 record。

### Runnable Solution

```python
sources = SourceIngestor().ingest_many(
    [
        SourceInput(
            uri="paper://rag-evaluation-survey",
            title="RAG Evaluation Survey",
            content=(
                "RAG evaluation should report retrieval quality and citation "
                "grounding. Evidence links help readers audit generated claims."
            ),
        ),
        SourceInput(
            uri="paper://citation-mapping",
            title="Citation Mapping for Research Assistants",
            content=(
                "Citation mapping connects every report claim to a quote, "
                "source URI, and paper title."
            ),
        ),
    ]
)

results = FakeRetriever(sources).search("citation grounding", limit=2)

evidence = [
    Evidence(
        id="evidence_1",
        source_id="source_1",
        quote=(
            "RAG evaluation should report retrieval quality and citation "
            "grounding."
        ),
        location="sentence 1",
    )
]

report = Report(
    id="report_1",
    run_id="run_1",
    title="RAG Evaluation Notes",
    summary="Citation grounding keeps generated research reports auditable.",
    claims=[
        Claim(
            id="claim_1",
            text="RAG evaluation reports should preserve citation grounding.",
            evidence_ids=["evidence_1"],
        )
    ],
)

links = build_claim_source_links(report, evidence=evidence, sources=sources)
record = links[0].to_record()

assert [source.id for source in sources] == ["source_1", "source_2"]
assert results[0].source_id == "source_1"
assert record == {
    "claim_id": "claim_1",
    "claim_text": "RAG evaluation reports should preserve citation grounding.",
    "evidence_id": "evidence_1",
    "source_id": "source_1",
    "source_title": "RAG Evaluation Survey",
    "source_uri": "paper://rag-evaluation-survey",
    "quote": "RAG evaluation should report retrieval quality and citation grounding.",
    "location": "sentence 1",
}
```

### Why This Design

Final answer 在研究场景里不够。这个 solution 检查的是引用链：report claim 能回到 evidence quote，quote 能回到 source URI。后面的 Workbench citation inspector 就靠这种 record 让研究员追溯报告出处。

## Exercise 2 Solution: Move The Claim To Different Evidence

### What This Proves

这一题证明证据链不是靠文字相似度猜出来的，而是由 `Claim.evidence_ids` 明确决定。

### Runnable Solution

```python
evidence = [
    Evidence(
        id="evidence_1",
        source_id="source_1",
        quote=(
            "RAG evaluation should report retrieval quality and citation "
            "grounding."
        ),
        location="sentence 1",
    ),
    Evidence(
        id="evidence_2",
        source_id="source_2",
        quote=(
            "Citation mapping connects every report claim to a quote, "
            "source URI, and paper title."
        ),
        location="sentence 1",
    ),
]

report = Report(
    id="report_2",
    run_id="run_1",
    title="Citation Mapping Notes",
    summary="Citation mapping keeps report claims connected to sources.",
    claims=[
        Claim(
            id="claim_2",
            text="A cited report should map each claim back to a source.",
            evidence_ids=["evidence_2"],
        )
    ],
)

links = build_claim_source_links(report, evidence=evidence, sources=sources)
record = links[0].to_record()

assert record["claim_id"] == "claim_2"
assert record["evidence_id"] == "evidence_2"
assert record["source_id"] == "source_2"
assert record["source_uri"] == "paper://citation-mapping"
assert "report claim" in record["quote"]

claim_results = FakeRetriever(sources).search("claim source", limit=1)
assert claim_results[0].source_id == "source_2"
```

### Why This Design

`FakeRetriever` 可以帮你找到候选 source，但它不会自动创建 evidence，也不会自动改 claim 的引用。这个边界很重要：retrieval 是发现资料，evidence chain 是报告质量控制。

如果以后真实检索接进来，这个原则也不变。真实检索可以更强，但 claim 仍然必须显式引用 evidence。

## Exercise 3 Solution: Diagnose Broken Links

### What This Proves

这题证明三类错误有不同含义：

- unsupported claim: claim 没有任何 evidence ID；
- missing evidence: claim 引用了不存在的 evidence ID；
- missing source: evidence 引用了不存在的 source ID。

### Runnable Solution

```python
unsupported_report = Report(
    id="unsupported_report",
    run_id="run_1",
    title="Unsupported Report",
    summary="This report skips evidence.",
    claims=[Claim(id="claim_bad", text="Citation grounding matters.")],
)

try:
    build_claim_source_links(unsupported_report, evidence=evidence, sources=sources)
except ValueError as exc:
    unsupported_error = str(exc)
else:
    raise AssertionError("Expected unsupported claim to fail")

assert unsupported_error == "claim 'claim_bad' must reference at least one evidence id"

missing_evidence_report = Report(
    id="missing_evidence_report",
    run_id="run_1",
    title="Missing Evidence Report",
    summary="This report references an evidence id that does not exist.",
    claims=[
        Claim(
            id="claim_missing_evidence",
            text="This claim points to missing evidence.",
            evidence_ids=["missing_evidence"],
        )
    ],
)

try:
    build_claim_source_links(missing_evidence_report, evidence=evidence, sources=sources)
except ValueError as exc:
    missing_evidence_error = str(exc)
else:
    raise AssertionError("Expected missing evidence to fail")

assert (
    missing_evidence_error
    == "claim 'claim_missing_evidence' references missing evidence 'missing_evidence'"
)

orphan_evidence = [
    Evidence(
        id="orphan_evidence",
        source_id="source_missing",
        quote="This quote points to a source that is not loaded.",
    )
]

orphan_report = Report(
    id="orphan_report",
    run_id="run_1",
    title="Orphan Evidence Report",
    summary="This report references evidence with a missing source.",
    claims=[
        Claim(
            id="claim_orphan",
            text="This claim points to orphan evidence.",
            evidence_ids=["orphan_evidence"],
        )
    ],
)

try:
    build_claim_source_links(orphan_report, evidence=orphan_evidence, sources=sources)
except ValueError as exc:
    missing_source_error = str(exc)
else:
    raise AssertionError("Expected missing source to fail")

assert (
    missing_source_error
    == "evidence 'orphan_evidence' references missing source 'source_missing'"
)

fixed_report = Report(
    id="fixed_report",
    run_id="run_1",
    title="Fixed Evidence Report",
    summary="This report references existing evidence.",
    claims=[
        Claim(
            id="claim_fixed",
            text="Citation mapping keeps report claims connected to sources.",
            evidence_ids=["evidence_2"],
        )
    ],
)

fixed_links = build_claim_source_links(fixed_report, evidence=evidence, sources=sources)
fixed_record = fixed_links[0].to_record()

assert fixed_record["source_uri"] == "paper://citation-mapping"
```

### Why This Design

这些错误信息让失败可诊断。生产里的研究助手不应该悄悄发布 unsupported claim；课程里的学习者也不应该只看到一个模糊的 "bad report"。错误明确到 claim/evidence/source 哪一层，才知道该修哪里。

## Exercise 4 Solution: Design A New Evidence Chain

### What This Proves

这一题证明你能从需求出发自己设计证据链，而不是只复制单 claim 示例：

- 自定义 `id_prefix`；
- 多 source；
- 多 evidence；
- 多 claim；
- link record 顺序跟 report claim 顺序一致。

### Runnable Solution

```python
sources = SourceIngestor(id_prefix="paper").ingest_many(
    [
        SourceInput(
            uri="paper://eval-loop",
            title="Evaluation Loop For Agents",
            content=(
                "Agent evaluation loops compare expected records with actual "
                "run outputs so regressions can be caught offline."
            ),
        ),
        SourceInput(
            uri="paper://citation-audit",
            title="Citation Audit For Research Assistants",
            content=(
                "Citation audits check that every research claim links to "
                "evidence, source URI, and paper title."
            ),
        ),
    ]
)

evidence = [
    Evidence(
        id="evidence_eval",
        source_id="paper_1",
        quote=(
            "Agent evaluation loops compare expected records with actual "
            "run outputs so regressions can be caught offline."
        ),
        location="abstract",
    ),
    Evidence(
        id="evidence_citation",
        source_id="paper_2",
        quote=(
            "Citation audits check that every research claim links to "
            "evidence, source URI, and paper title."
        ),
        location="section 2",
    ),
]

report = Report(
    id="report_eval_citation",
    run_id="run_eval_citation",
    title="Evaluation And Citation Checks",
    summary="Local research assistants need both regression checks and citations.",
    claims=[
        Claim(
            id="claim_eval",
            text="Evaluation loops help catch regressions offline.",
            evidence_ids=["evidence_eval"],
        ),
        Claim(
            id="claim_citation",
            text="Citation audits connect research claims back to source metadata.",
            evidence_ids=["evidence_citation"],
        ),
    ],
)

links = build_claim_source_links(report, evidence=evidence, sources=sources)

assert [source.id for source in sources] == ["paper_1", "paper_2"]
assert [link.source_uri for link in links] == [
    "paper://eval-loop",
    "paper://citation-audit",
]
assert [link.evidence_id for link in links] == ["evidence_eval", "evidence_citation"]
assert [link.claim_id for link in links] == ["claim_eval", "claim_citation"]
```

### Why This Design

The order of `links` follows the order of `report.claims`, not the order of `sources` or `evidence`. That makes report rendering deterministic: Workbench can show citations in the same order that the report presents claims.

The two source URIs also prove that a report can combine evidence from multiple local papers without blurring where each claim came from.

## Final Takeaway

Part 2 的核心不是 dataclass 名字，而是一个研究质量习惯：

```text
Every report claim needs a path back to evidence and source.
```

以后 Part 3 增加 Memory 时，memory 不能污染这个证据链。Part 4 增加 Delegation 时，child agent 的结果也要能并回可检查的 evidence。Part 5 做 Workbench 时，citation inspector 要让研究员点回 quote。Part 7 做 diagnostics 时，失败报告要能说清楚断在 claim、evidence 还是 source。
