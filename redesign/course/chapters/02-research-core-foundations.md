# Part 2: Research Core — 让回答有据可查

> 接 Part 1。你应该已经知道：不要只看 final answer，要看 event trail。Part 2 继续训练同一个习惯，只是这次检查的对象从 "Agent 有没有跑过工具" 变成 "报告里的 claim 有没有证据"。

预计时间：60 到 90 分钟。

## Learner Contract

- **Who this is for**: Beginner Track 和 Engineer Track 都适合。你需要会运行 Python shell，知道 `assert` 是检查条件。
- **Before you start**: 先完成 Part 1 的 Chapter 00、Chapter 01、Lab 01。
- **You will build**: 一个完全离线的证据链：本地 paper fixture -> `Source` -> `Evidence` -> `Claim` -> `Report` -> `ClaimSourceLink`。
- **You will be able to explain**: 为什么 `Source`、`Evidence`、`Claim` 不能混成一团；为什么 final report 不能替代证据链；为什么 `FakeRetriever` 对学习和测试更好。
- **You will prove it works by running**: `uv run pytest tests/research_core/test_research_retrieval.py tests/research_core/test_claim_source_mapping.py -q`。
- **Offline guarantee**: 所有资料都是本地字符串 fixture；检索使用 `FakeRetriever`，不需要搜索引擎、embedding、数据库或 API key。

## 你的本地论文研究助手现在需要：出处

Part 1 让助手会跑。现在研究员问：

> "帮我看一下这批论文里，RAG 评测为什么需要引用和 grounding。"

如果助手只回答：

> "RAG evaluation should track citation grounding."

这句话看起来像答案，但研究员会马上追问：这句话从哪篇论文来？证据是哪一句？如果这句话错了，我应该改 report，还是改 source，还是改 evidence extraction？

Part 2 解决的就是这个问题：让每一句研究结论都能回到本地资料里的证据。

> [BIG] **大局观**：Part 1 证明一次 run 发生过；Part 2 证明一次研究回答有出处。后面的 Memory 会记住研究历史，Delegation 会分派研究任务，Workbench 会把 source/evidence/report 展示给人看。

```text
Local Paper Research Assistant
  [x] Part 1: Agent Kernel, event trail
  [*] Part 2: Research Core, evidence chain
      [*] Source ingestion
      [*] Fake retrieval
      [*] Evidence -> Claim -> Report links
  [ ] Part 3: Memory and Skills
  [ ] Part 4: Delegation
  [ ] Part 5: Workbench UI
  [ ] Part 6: Framework comparison
  [ ] Part 7: Production readiness
```

## Section 1 [LIGHT Concept]: 这句话从哪来

### Problem Hook

想象你在给研究团队做一个本地论文助手。它读的是本地 paper fixture，不连外网。研究员不只要一个结论，他还要能点回原文。

没有 Research Core 时，系统里常见的糟糕形状是这样：

```text
Question -> Model -> "Citation grounding matters for RAG evaluation."
```

这不是研究报告，只是一句话。它缺了三件事：

- 看过哪些资料？
- 哪一句资料能当证据？
- 报告里的哪条 claim 被哪条证据支撑？

### 概念：侦探故事版

Part 2 可以先按侦探故事理解：

| Research Core object | 侦探故事里的角色 | 它回答的问题 |
| --- | --- | --- |
| `Source` | 案发现场 | 原始资料在哪里？标题和 URI 是什么？ |
| `Evidence` | 证物 | 哪一句原文能支撑判断？ |
| `Claim` | 结论 | 报告里到底说了什么？ |
| `Report` | 案件陈述 | 多个结论如何组织成研究输出？ |
| `ClaimSourceLink` | 证据链清单 | 这条结论能不能回到证物和现场？ |

> [CHECK] **检查一下**：如果你只能说出 claim，但说不出 evidence 和 source，这不是完整研究链路。请用自己的话解释：为什么漂亮 final answer 不能替代证据链？

### Inspect

Part 2 的核心数据流是：

```text
SourceInput
    |
    v
SourceIngestor  ->  Source
                      |
                      v
FakeRetriever  ->  SearchResult
                      |
                      v
Evidence  ->  Claim  ->  Report
                      |
                      v
             ClaimSourceLink
```

这条链路刻意很小。它不做真实搜索，不做自动论文解析，也不做模型生成 report。它先把研究对象的边界立住：资料、证据、结论、报告、引用链各自是什么。

> [DD] **设计决策**：为什么 Part 2 先用本地 fixture 和 `FakeRetriever`？
>
> **选了**：固定的本地 source 字符串，加确定性的 token/phrase scoring。
> **没选**：一开始就接真实搜索、embedding、rerank 或论文数据库。
> **因为**：这节课要训练的是证据链边界。真实检索会引入网络、索引质量、模型波动和外部数据变化，反而让新手分不清错的是 retrieval，还是 evidence/claim 关系。

## Section 2 [FULL Build]: Build The Evidence Chain

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

### Build

先准备 imports 和三篇本地 paper fixture：

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
        SourceInput(
            uri="paper://agent-memory-notes",
            title="Agent Memory Notes",
            content="Memory records can pollute an agent when write policy is missing.",
        ),
    ]
)

print([source.id for source in sources])
```

Expected output:

```text
['source_1', 'source_2', 'source_3']
```

`SourceInput` 是还没进入系统的原始资料。`SourceIngestor` 把它变成带稳定 ID 的 `Source`。稳定 ID 是后面引用和测试的锚点。

> [TRAP] **常见陷阱：source ID 不是装饰**
>
> 如果每次导入 source 都生成不可预测的 ID，`Evidence(source_id="...")` 和 report link 就很难测试。Part 2 的 deterministic ID 不是为了好看，而是为了让证据链可复现。

### L1 Follow 练习：从 search 到 cited report

继续粘贴：

```python
results = FakeRetriever(sources).search("citation grounding", limit=2)

print([(result.source_id, result.title, result.score) for result in results])

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

print(record["claim_id"])
print(record["source_uri"])
print(record["quote"])

assert record["claim_id"] == "claim_1"
assert record["evidence_id"] == "evidence_1"
assert record["source_id"] == "source_1"
assert record["source_uri"] == "paper://rag-evaluation-survey"
```

你应该看到 `claim_1` 能回到 `paper://rag-evaluation-survey`，并能看到 quote 原文。

#### Exercise Feedback - L1 Follow

**Common Errors**:

1. 把 `source_id` 写成 `source_0` - `SourceIngestor` 从 1 开始生成 ID。
2. 忘记给 `Claim` 填 `evidence_ids` - claim 会变成 unsupported claim。
3. 把 `Evidence.quote` 改成和 source content 完全无关的句子 - 当前 contract 不会做语义验证，但你的研究质量已经坏了。

**Failure Output Interpretation**: 如果报 `claim 'claim_1' references missing evidence 'evidence_1'`，说明 report 指向了不存在的 evidence。 如果报 `evidence 'evidence_1' references missing source 'source_1'`，说明 evidence 指向了不存在的 source。 如果 assert 的 `source_uri` 不对，先打印 `record`，看 link 走到了哪条 source。

**Where To Go Back**: 回到本节的数据流图，逐个说出 `SourceInput`、`Source`、`Evidence`、`Claim`、`Report`、`ClaimSourceLink` 的职责。

**Why Correct Answer Is Correct**: 这些 assert 不只是证明代码能跑。它们证明 report claim 能通过 `evidence_id` 回到 quote，再通过 `source_id` 回到 source URI。

### Inspect The Chain

现在把 link record 当成 Workbench 未来会消费的数据看：

```python
for key, value in record.items():
    print(f"{key}: {value}")
```

你应该看到类似：

```text
claim_id: claim_1
claim_text: RAG evaluation reports should preserve citation grounding.
evidence_id: evidence_1
source_id: source_1
source_title: RAG Evaluation Survey
source_uri: paper://rag-evaluation-survey
quote: RAG evaluation should report retrieval quality and citation grounding.
location: sentence 1
```

这里的每个字段都服务一个产品问题：

```text
Report panel claim
      |
      v
ClaimSourceLink
      |
      +--> Evidence quote shown in citation inspector
      |
      +--> Source title + URI shown in source panel
```

> [DD] **设计决策**：为什么不把 quote 直接塞进 `Claim.text`？
>
> **选了**：`Claim` 保存报告结论，`Evidence` 保存原文证据。
> **没选**：让 claim 文本同时承担结论和证据两个角色。
> **因为**：结论是你对资料的判断，证据是资料本身。混在一起以后，Workbench 无法清楚告诉研究员：哪部分是原文，哪部分是系统写出的判断。

### Modify: 换一个 query，预测 ranking

先预测：如果 query 从 `"citation grounding"` 改成 `"claim source"`，哪篇 source 会排第一？

运行：

```python
claim_results = FakeRetriever(sources).search("claim source", limit=1)

print(claim_results[0].source_id)
print(claim_results[0].title)
print(claim_results[0].score)

assert claim_results[0].source_id == "source_2"
```

`source_2` 会赢，因为它的 content 直接包含 `claim` 和 `source`。这不代表 `FakeRetriever` 聪明，它只是确定地执行 token matching。确定性正是课程和测试需要的。

> [TRAP] **常见陷阱：搜索排名不是证据链**
>
> `SearchResult` 只说明某个 source 和 query 匹配。它还不是 evidence。你仍然需要明确选出 quote，建 `Evidence`，再让 `Claim` 引用它。

### Break

现在故意写一个没有证据的 claim：

```python
bad_report = Report(
    id="bad_report",
    run_id="run_1",
    title="Bad Report",
    summary="This report has a claim but no evidence.",
    claims=[Claim(id="claim_bad", text="Citation grounding matters.")],
)

try:
    build_claim_source_links(bad_report, evidence=evidence, sources=sources)
except ValueError as exc:
    print(str(exc))
```

Expected output:

```text
claim 'claim_bad' must reference at least one evidence id
```

### Fix

修复不是“吞掉错误”，而是补上证据关系：

```python
fixed_report = Report(
    id="fixed_report",
    run_id="run_1",
    title="Fixed Report",
    summary="This report has a supported claim.",
    claims=[
        Claim(
            id="claim_fixed",
            text="Citation grounding matters for RAG evaluation.",
            evidence_ids=["evidence_1"],
        )
    ],
)

fixed_links = build_claim_source_links(fixed_report, evidence=evidence, sources=sources)
assert fixed_links[0].source_uri == "paper://rag-evaluation-survey"
```

### Reflect

用自己的话回答：

1. `FakeRetriever` 排第一的 source 为什么还不是 evidence？
2. unsupported claim 的错误保护了谁？
3. 修复时为什么要改 `Claim.evidence_ids`，而不是只改 `Report.summary`？

## Section 3 [LIGHT Inspection]: Read The Data Flow

把完整链路再压缩一下：

```text
[paper fixture string]
        |
        v
[SourceInput] --ingest_many--> [Source: id + uri + title + content]
        |
        v
[FakeRetriever search] ------> [SearchResult: source_id + score]
        |
        v
[Evidence: quote + source_id]
        |
        v
[Claim: text + evidence_ids] -> [Report: ordered claims]
        |
        v
[ClaimSourceLink: claim + evidence + source record]
```

如果你以后看到一个 report claim 出错，先问三层：

- Claim 有没有 evidence ID？
- Evidence ID 是否存在？
- Evidence 指向的 source ID 是否存在？

这三个问题都能由 `build_claim_source_links()` 在本地、确定性地检查。

> [DEEP] **深入一点**：当前 contract 不会验证 quote 是否真的逐字出现在 `Source.content` 里。那是后续 eval 或 evidence extraction 阶段可以加的质量检查。R2 不把它塞进基础 dataclass，是为了让初学者先学清楚引用关系，再学内容一致性。

## Section 4 [LIGHT Product]: 接入你的 Workbench

Workbench 需要 Part 2 的对象来回答用户最关心的问题：

| Workbench panel | 需要的 Part 2 数据 | 用户能看到什么 |
| --- | --- | --- |
| Source panel | `Source` | 论文标题、URI、正文片段 |
| Evidence panel | `Evidence` | 支撑判断的 quote 和位置 |
| Report editor | `Report` / `Claim` | 报告里的每条结论 |
| Citation inspector | `ClaimSourceLink` | 从 claim 跳回 quote 和 source |
| Eval panel | mapping errors | unsupported claim、missing evidence、missing source |

> [DD] **设计决策**：为什么 Workbench 消费 `ClaimSourceLink.to_record()` 这样的普通 record？
>
> **选了**：核心对象负责保持关系正确，产品层消费普通 JSON-compatible record。
> **没选**：让 React 组件自己在前端猜 claim、evidence、source 怎么连。
> **因为**：证据链是研究质量边界，不是 UI 小技巧。前端可以负责展示，但不应该发明引用规则。

## Section 5 [LIGHT Gate]: Eval Gate

### Passing Standard

你完成 Part 2 后，应该能证明：

- source ingestion 生成稳定 source IDs；
- fake retrieval 离线、确定、可测试；
- report claim 能回到 evidence 和 source；
- unsupported claim、missing evidence、missing source 会显式失败；
- Workbench 为什么需要 link record，而不是只要 final report。

### Commands

Run from `redesign/`:

```bash
uv run pytest tests/research_core/test_research_retrieval.py tests/research_core/test_claim_source_mapping.py -q
uv run ruff check packages/research_core/src/research_core/research tests/research_core/test_research_retrieval.py tests/research_core/test_claim_source_mapping.py
```

Full project gate:

```bash
uv run pytest -q
uv run ruff check .
```

### Failure Output Interpretation

- `query must not be empty`: 你传给 `FakeRetriever.search()` 的 query 是空白。
- `claim ... references missing evidence`: report 指向了不存在的 evidence ID。
- `evidence ... references missing source`: evidence 指向了不存在的 source ID。
- `claim ... must reference at least one evidence id`: 你写了 unsupported claim。

## Checkpoint

### L3 Design 预告

Lab 02 会让你自己设计一个新的本地 paper fixture，并写出一条能追溯的 claim。不要只让 final text 看起来对；你必须用 assert 证明：

- source ID 是你预期的；
- evidence quote 来自正确 source；
- claim 引用了正确 evidence；
- link record 能回到 source URI。

### Reflection

1. `SourceInput` 和 `Source` 为什么要分开？
2. `Evidence.quote` 和 `Claim.text` 为什么不是同一个东西？
3. 为什么 `FakeRetriever` 的确定性对课程比真实搜索更重要？
4. 如果 Workbench 只显示 final report，不显示 citation inspector，研究员会误判什么？

---

**完成 Part 2 后，你的本地论文研究助手现在可以把报告结论连回本地资料证据。**

**Next: Part 3 会遇到新的问题：助手查过一次资料以后，下一次完全不记得。接下来要让它学会 Memory 和 Skills。**
