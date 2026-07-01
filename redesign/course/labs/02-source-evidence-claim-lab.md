# Lab 02: Build A Traceable Evidence Chain

这个 lab 接 Part 2 Chapter 02。你要亲手证明一件事：本地论文研究助手写出的 claim，必须能回到本地 source 里的 evidence。

预计时间：60 到 90 分钟。

## Setup

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴 imports：

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

## Exercise 1 (L1 Follow): Build The Smallest Supported Claim

目标：跟着代码建立一条最小证据链。

粘贴：

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
print([(result.source_id, result.score) for result in results])

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

print(record)
```

Self-check：

```python
assert [source.id for source in sources] == ["source_1", "source_2"]
assert results[0].source_id == "source_1"
assert record["claim_id"] == "claim_1"
assert record["evidence_id"] == "evidence_1"
assert record["source_id"] == "source_1"
assert record["source_uri"] == "paper://rag-evaluation-survey"
assert "citation grounding" in record["quote"]
```

### Exercise Feedback - L1 Follow

**Common Errors**:

1. `ModuleNotFoundError: No module named 'research_core'` - 你可能没有从 `redesign/` 运行，或没有使用 `PYTHONPATH=packages/research_core/src uv run python`。
2. `source_1` 写成 `source_0` - `SourceIngestor` 默认从 1 开始编号。
3. 忘记 `evidence_ids=["evidence_1"]` - claim 会变成没有证据的结论。

**Failure Output Interpretation**: 如果 `record["source_uri"]` 不对，打印 `record`，看 claim 最终连到了哪条 source。 如果 `results[0].source_id` 不对，检查 query 和 source content 是否和示例一致。 如果 `build_claim_source_links(...)` 抛错，优先看错误里提到的是 missing evidence、missing source，还是 unsupported claim。

**Where To Go Back**: 回到 Chapter 02 的 "Build The Evidence Chain"，重新看 `SourceInput -> Source -> Evidence -> Claim -> Report -> ClaimSourceLink` 图。

**Why Correct Answer Is Correct**: 这些 assert 证明了完整引用路径：claim 指向 evidence，evidence 指向 source，link record 能给出 source URI 和 quote。

## Exercise 2 (L2 Modify): Move The Claim To Different Evidence

目标：改一条证据，先预测 link record 会怎么变，再运行验证。

这次新增第二条 evidence，来自 `source_2`：

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
```

先预测：如果 claim 的 `evidence_ids` 从 `["evidence_1"]` 改成 `["evidence_2"]`，`source_uri` 会变成什么？

然后粘贴：

```python
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

print(record["source_uri"])
print(record["quote"])
```

Self-check：

```python
assert record["claim_id"] == "claim_2"
assert record["evidence_id"] == "evidence_2"
assert record["source_id"] == "source_2"
assert record["source_uri"] == "paper://citation-mapping"
assert "report claim" in record["quote"]
```

现在再试一个 retrieval 修改：

```python
claim_results = FakeRetriever(sources).search("claim source", limit=1)

print(claim_results[0].source_id)
print(claim_results[0].title)

assert claim_results[0].source_id == "source_2"
```

### Exercise Feedback - L2 Modify

**Common Errors**:

1. 只改了 `Claim.text`，没改 `evidence_ids` - link record 不会因为文字像另一条证据就自动换 source。
2. 新增 `Evidence(id="evidence_2", source_id="source_3", ...)` - 但当前只有两条 source，会变成 missing source。
3. 以为 retrieval 排名会自动决定 claim 的证据 - search result 和 evidence link 是两件事。

**Failure Output Interpretation**: 如果 `source_uri` 仍然是 `paper://rag-evaluation-survey`，说明 claim 还在引用 `evidence_1`。 如果报 missing source，检查 `Evidence.source_id` 是否存在于 `sources`。 如果 `claim_results[0]` 不是 `source_2`，检查 query 是否是 `"claim source"`。

**Where To Go Back**: 回到 Chapter 02 的 `[TRAP] 搜索排名不是证据链`，确认 `SearchResult` 和 `Evidence` 的边界。

**Why Correct Answer Is Correct**: 正确结果证明 link record 由 `Claim.evidence_ids` 决定，而不是由 claim 文本、retrieval ranking 或 report summary 猜出来。

## Exercise 3 (Break/Fix): Diagnose Broken Links

目标：故意打坏三种关系，并读懂错误。

### Break 1: Unsupported Claim

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
    print(unsupported_error)

assert unsupported_error == "claim 'claim_bad' must reference at least one evidence id"
```

### Break 2: Missing Evidence

```python
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
    print(missing_evidence_error)

assert (
    missing_evidence_error
    == "claim 'claim_missing_evidence' references missing evidence 'missing_evidence'"
)
```

### Break 3: Missing Source

```python
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
    print(missing_source_error)

assert (
    missing_source_error
    == "evidence 'orphan_evidence' references missing source 'source_missing'"
)
```

### Fix

选择 Break 2 来修。做法是把 claim 指回真实存在的 `evidence_2`：

```python
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

### Exercise Feedback - Break/Fix

**Common Errors**:

1. 在 `try` block 里没有给错误变量赋值 - 如果没有抛错，后面的 assert 会变成变量未定义。
2. 修 missing evidence 时新建了 evidence，但忘记把它放进 `evidence=[...]` 参数。
3. 修 missing source 时只改 claim，没改 orphan evidence 的 `source_id`。

**Failure Output Interpretation**: unsupported claim 指向 `Claim.evidence_ids` 为空；missing evidence 指向 report 引用了不存在的 evidence ID；missing source 指向 evidence 引用了不存在的 source ID。

**Where To Go Back**: 回到 Chapter 02 的 Section 3，按三层问题排查：claim 有没有 evidence ID？evidence ID 是否存在？evidence 的 source ID 是否存在？

**Why Correct Answer Is Correct**: Break/Fix 证明错误不是随机失败，而是引用链每一层都有明确边界。修复时必须修对应边界，不能只改 final text。

## Exercise 4 (L3 Design): Design A New Evidence Chain

目标：不给 skeleton，自己设计一条新证据链。

需求：

- 使用 `SourceIngestor(id_prefix="paper")`。
- 至少创建 2 条 `SourceInput`。
- 研究问题是：本地论文助手为什么需要 evaluation 和 citation 两种检查？
- 至少创建 2 条 `Evidence`，来自不同 source。
- 创建一个 `Report`，里面至少有 2 条 `Claim`。
- 每条 claim 都必须引用一条 evidence。
- 使用 `build_claim_source_links(...)` 生成 links。
- 自查必须证明 links 的 source URI 顺序是 `["paper://eval-loop", "paper://citation-audit"]`。

你可以用这两个 source 方向：

```text
paper://eval-loop        -> 讲 evaluation loop / regression checks
paper://citation-audit   -> 讲 citation audit / evidence links
```

先自己写 10 到 15 分钟，再去看 solution。

最低自查形状如下。注意：这段依赖你自己在 L3 里创建的 `sources` 和 `links`，所以它是自查模板，不是直接粘贴运行的完整示例；可运行参考答案在 solution 里。

```text
assert [source.id for source in sources] == ["paper_1", "paper_2"]
assert [link.source_uri for link in links] == [
    "paper://eval-loop",
    "paper://citation-audit",
]
assert [link.evidence_id for link in links] == ["evidence_eval", "evidence_citation"]
```

### Exercise Feedback - L3 Design

**Common Errors**:

1. 忘记 `id_prefix="paper"` - source IDs 会是 `source_1`、`source_2`，不符合需求。
2. 两条 evidence 都指向同一条 source - 没有证明你能跨 source 维护证据链。
3. 只写一条 claim - 没有覆盖“多条 report claim 保持顺序”的要求。
4. 只检查 final report title - final text 不能证明 evidence chain 正确。

**Failure Output Interpretation**: source ID 断言失败通常说明 `SourceIngestor` 参数不对。 source URI 顺序断言失败通常说明 report claim 顺序或 evidence ID 引用顺序不对。 missing evidence/source 错误按 Exercise 3 的三层法排查。

**Where To Go Back**: 回到 Exercise 1 的最小支持 claim，再回到 Exercise 2 看如何让不同 claim 指向不同 evidence。

**Why Correct Answer Is Correct**: 正确设计证明你能从需求出发，自己建立 source、evidence、claim、report、link 的完整关系，而不是只复制单 claim 示例。

## Reflection

完成 lab 后，用自己的话回答：

1. `FakeRetriever` 找到 source 之后，为什么你还要手动建立 `Evidence`？
2. `Claim.text`、`Evidence.quote`、`Source.content` 分别代表什么？
3. 如果 Workbench 只显示 `Report.summary`，它会漏掉什么风险？
4. 你排查 broken link 时，最先看哪一层？为什么？
