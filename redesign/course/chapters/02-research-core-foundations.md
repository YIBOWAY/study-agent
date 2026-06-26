# Chapter 02: Research Core Foundations

## Goal

这一章补上 Phase 2 的学习路径：一个研究型 Agent 不能只会“回答”，还要能说清楚答案来自哪里。

学完以后，你应该能看懂这条主线：

```text
SourceInput
  -> SourceIngestor
  -> FakeRetriever
  -> Evidence
  -> Claim
  -> Report
  -> ClaimSourceLink
```

预计时间：45 到 60 分钟。

## Before You Start

请先完成：

- `00-before-agent-kernel.md`
- `01-agent-kernel-foundations.md`
- `../labs/01-agent-runner-lab.md`

这一章不需要真实搜索引擎、数据库、embedding 或 API key。所有材料都在本地构造，重点是理解研究对象之间的边界。

## The Idea In Plain Language

Research Core 解决的不是“怎么让模型更会写”，而是“怎么让研究过程可检查”。

如果一个报告里有一句 claim，却找不到对应 evidence 和 source，这个报告就很难被信任。Phase 2 先不做复杂搜索，也不做自动写报告，只建立最小的证据链：

- `Source`: 原始资料。
- `Evidence`: 从资料里摘出来、可以支撑判断的一段话。
- `Claim`: 报告里的判断。
- `Report`: 一组 claim 组成的结果。
- `ClaimSourceLink`: 把 claim、evidence、source 串起来的引用记录。

这套结构让未来的 Workbench 可以问一个很简单的问题：这句话的证据在哪里？

## Core Objects

| Object | Plain Meaning | Why It Exists |
| --- | --- | --- |
| `SourceInput` | 等待导入的原始资料 | 让导入前的数据也有清楚形状 |
| `SourceIngestor` | 本地导入器 | 给 source 生成确定的 ID，方便测试和引用 |
| `Source` | 已导入资料 | 保存 URI、标题、正文和 metadata |
| `FakeRetriever` | 离线检索器 | 用确定的 token/phrase scoring 模拟搜索，不依赖网络 |
| `Evidence` | 证据片段 | 记录 quote、source_id 和位置 |
| `Claim` | 报告里的判断 | 必须引用 evidence 才算可追踪 |
| `Report` | 研究输出 | 把多个 claim 组织起来 |
| `ClaimSourceLink` | 引用链 | 让 claim 可以回到 evidence 和 source |

## Minimal Example

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴：

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

results = FakeRetriever(sources).search("evidence citation", limit=1)
print(results[0].source_id)
print(results[0].score)
```

你应该看到第一条结果来自 `source_1`。它为什么排第一？因为 title 和 content 都命中了 evidence/citation 相关 token。

继续粘贴：

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
print(links[0].to_record())
```

你应该看到一条普通 dict，里面同时有 `claim_id`、`evidence_id`、`source_id`、`source_uri` 和 `quote`。

## Why This Matters

只保存 final report 不够。一个研究型 Agent 至少要保留三层事实：

1. 它看过哪些 source。
2. 它拿哪些 evidence 支撑判断。
3. 它把哪些 claim 写进 report。

这三层拆开以后，后面的 eval 才能检查：

- claim 是否引用了不存在的 evidence；
- evidence 是否指向不存在的 source；
- report 是否有 unsupported claim；
- UI 是否能从一句 claim 跳回原始资料。

## Failure Lab Preview

故意写一个没有 evidence 的 claim：

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
```

你应该看到：

```text
claim 'claim_bad' must reference at least one evidence id
```

这个错误不是烦人的限制。它是在保护研究质量：没有证据的 claim 不应该悄悄进入可发布报告。

## Product Integration

Phase 5 的 Workbench 会需要这些对象：

- source/evidence panel 显示 `Source` 和 `Evidence`。
- report editor 显示 `Report` 和 `Claim`。
- citation inspector 使用 `ClaimSourceLink` 从 claim 跳回 quote。
- eval panel 检查 missing evidence、missing source 和 unsupported claim。

所以 Phase 2 不是“先写几个 dataclass”。它是在给研究产品定义可验证的数据骨架。

## Eval Gate

项目级检查：

```bash
uv run pytest tests/research_core/test_research_retrieval.py tests/research_core/test_claim_source_mapping.py -q
uv run ruff check packages/research_core/src/research_core/research tests/research_core/test_research_retrieval.py tests/research_core/test_claim_source_mapping.py
```

核心自查：

```python
assert links[0].claim_id == "claim_1"
assert links[0].source_uri == "memory://agent-evidence"
```

## Checkpoint

继续后面的章节前，用自己的话回答：

1. `SourceInput` 和 `Source` 为什么要分开？
2. `FakeRetriever` 为什么比真实搜索更适合入门课和测试？
3. `Evidence` 为什么保存 `source_id`？
4. 为什么 `Claim` 不能没有 evidence？
5. Workbench 里点击 claim 回到 quote，靠的是哪个对象？
