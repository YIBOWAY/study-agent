# Lab 02: Source, Evidence, Claim

## Goal

这个 lab 会带你亲手跑三种情况：

1. 把本地资料导入成确定 ID 的 `Source`。
2. 用 `FakeRetriever` 离线检索资料。
3. 把 `Claim` 连接回 `Evidence` 和 `Source`。
4. 故意写一个没有 evidence 的 claim，观察错误。

预计时间：45 到 60 分钟。

## Setup

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

保持这个 shell 打开，后面的练习会复用前面创建的变量。

先粘贴 imports：

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

## Exercise 1: Ingest Local Sources

粘贴：

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

print([source.id for source in sources])
print(sources[0].title)
```

你应该看到：

```text
['source_1', 'source_2']
Agent Evidence
```

自查：

```python
assert [source.id for source in sources] == ["source_1", "source_2"]
assert sources[0].uri == "memory://agent-evidence"
```

## Exercise 2: Search With FakeRetriever

粘贴：

```python
results = FakeRetriever(sources).search("evidence citation", limit=1)

print(results[0].source_id)
print(results[0].title)
print(results[0].score)
```

你应该看到第一条结果是 `source_1`。分数只要是正整数即可。

自查：

```python
assert results[0].source_id == "source_1"
assert results[0].score > 0
```

## Exercise 3: Build Claim-Source Links

粘贴：

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

print(record["claim_id"])
print(record["source_uri"])
print(record["quote"])
```

你应该看到：

```text
claim_1
memory://agent-evidence
Research agents need evidence and citation mapping.
```

自查：

```python
assert record["claim_id"] == "claim_1"
assert record["evidence_id"] == "evidence_1"
assert record["source_id"] == "source_1"
assert record["source_uri"] == "memory://agent-evidence"
```

## Exercise 4: Break The Evidence Link

现在故意写一个没有 evidence 的 claim。

粘贴：

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
    print(str(exc))
else:
    raise AssertionError("Expected unsupported claim to fail")
```

你应该看到：

```text
claim 'claim_bad' must reference at least one evidence id
```

## Reflection

做完以后，回答：

1. 为什么 `SourceIngestor` 要给 source 生成确定 ID？
2. `FakeRetriever` 在课程里替代了什么真实系统？
3. `Evidence.quote` 和 `Claim.text` 为什么不是同一个东西？
4. `build_claim_source_links()` 拒绝 unsupported claim 保护了什么？
5. 如果 Workbench 要从 report 句子跳回原文，它需要哪条 record？
