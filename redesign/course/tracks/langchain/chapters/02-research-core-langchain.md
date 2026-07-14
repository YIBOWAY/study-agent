# Part 2: Research Core / 证据链（LangChain 轨）

> 接 Part 1。Part 1 证明 loop 可观察；Part 2 证明**研究结论有出处**。

预计时间：60–90 分钟。

## Learner Contract

- **你会构建**：`PaperDoc` → LangChain `Document` → `BaseRetriever` → LCEL
  Runnable → Evidence → Claim → ClaimLink。
- **你会解释**：为什么漂亮 final answer 不能替代证据链。
- **验收**：`uv run pytest packages/langchain_course/tests/test_research.py -q`。
- **诚实边界**：本轨检索是 **keyword**，不是 embedding RAG；LangChain
  负责组合和生命周期，引用正确性仍由课程合同校验。

## 与 handwritten 对照

| Handwritten | 本轨 |
| --- | --- |
| `Source` / `SourceIngestor` | `PaperDoc` → LangChain `Document` |
| `FakeRetriever` | `LangChainPaperRetriever(BaseRetriever)` |
| `Evidence` / `Claim` / `Report` | `EvidenceItem` / `ClaimItem` / `ResearchReport` |
| `build_claim_source_links` | `build_claim_links` |
| 禁止缺链 | `ResearchChainError` |

> [DD] **零 import `research_core`**：类型名刻意不同，避免“看似同一对象却两套语义”。对照靠场景与验收，不靠共享类。

## Section 1：问题钩子

助手只回答：

> “RAG evaluation should track citation grounding.”

研究员会问：哪篇论文？哪句原文？本轨强制 claim 绑定 `evidence_ids`，link 时校验 source 存在。

```text
PaperDoc fixtures
   -> KeywordRetriever.search
   -> EvidenceItem(quote, source_id)
   -> ClaimItem(evidence_ids)
   -> ResearchReport
   -> build_claim_links -> ClaimLink records
```

## Section 2 [BUILD]：检索

```python
from langchain_course.paper_fixtures import default_paper_docs
from langchain_course.research import KeywordRetriever

docs = default_paper_docs()
hits = KeywordRetriever(docs).search("citation grounding", limit=2)
print([(h.source_id, h.score) for h in hits])
assert hits[0].source_id == "paper_1"
```

> [CHECK] score 是 token overlap 比例，不是语义相似度。

## Section 3 [BUILD / INSPECT]：跨进 LangChain 边界

上一段的 `KeywordRetriever` 是便于理解算法的纯 Python 版本。真正进入
LangChain 组合面时，使用 `Document`、`BaseRetriever` 和 LCEL Runnable：

```python
from langchain_core.documents import Document
from langchain_course.research import (
    LangChainPaperRetriever,
    build_research_context_runnable,
    paper_docs_to_documents,
)

lc_documents = paper_docs_to_documents(docs)
assert isinstance(lc_documents[0], Document)
assert lc_documents[0].metadata["source_id"] == "paper_1"

lc_retriever = LangChainPaperRetriever.from_papers(docs, k=2)
research_chain = build_research_context_runnable(lc_retriever)
context_result = research_chain.invoke({"question": "citation grounding"})
print([doc.metadata["source_id"] for doc in context_result["documents"]])
assert "RAG Evaluation Survey" in context_result["context"]
```

检查链的形状，而不只检查最终字符串：

```python
graph = research_chain.get_graph()
print(len(graph.nodes), len(graph.edges))
assert len(graph.nodes) >= 3
assert context_result["question"] == "citation grounding"
```

> [DD] `PaperDoc` 是课程稳定记录；`Document` 是进入 LangChain Retriever /
> Runnable 的框架值。边界转换比把所有业务字段都塞进 `Document.metadata`
> 更容易演进。

## Section 4 [BUILD]：最小可支撑 claim

```python
from langchain_course.research import (
    ClaimItem,
    EvidenceItem,
    ResearchReport,
    build_claim_links,
)

evidence = [
    EvidenceItem(
        id="evidence_1",
        source_id="paper_1",
        quote="RAG evaluation should report retrieval quality and citation grounding.",
        location="sentence 1",
    )
]
report = ResearchReport(
    id="report_1",
    title="RAG Evaluation Notes",
    summary="Citation grounding keeps reports auditable.",
    claims=[
        ClaimItem(
            id="claim_1",
            text="RAG evaluation reports should preserve citation grounding.",
            evidence_ids=["evidence_1"],
        )
    ],
)
links = build_claim_links(report, evidence=evidence, docs=docs)
print(links[0].to_record())
assert links[0].source_uri.startswith("paper://")
```

## Section 5 [BREAK / FIX]

1. `evidence_ids=["missing"]` → `ResearchChainError: missing evidence`
2. `evidence_ids=[]` → `ResearchChainError: no evidence_ids`（unsupported claim）
3. `invoke({"query": ...})` → 缺少 `question`；修复调用合同，而不是在链里
   猜测任意字段名。
4. 删除 `Document.metadata["source_id"]` → 后续无法稳定回链；修复
   `paper_docs_to_documents()` 的边界映射。

> [TRAP] 用 LLM 直接写 report 却跳过 `build_claim_links`，等于回到“散文式研究助手”。Lab 要求**先 link 再展示**。

## Section 6 [FIX]：给 chat 的 context（可选）

```python
from langchain_course.research import format_context_block
print(format_context_block(docs[:2])[:200])
```

Live 时可以把 context 塞进 system/user prompt，再让 model 起草 claim；**仍然**要用 `build_claim_links` 验收，而不是相信模型说“已引用”。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_research.py -q
```

## Reflection

1. keyword retriever 与 embedding RAG 各适合什么教学/产品阶段？
2. 若 claim 引用了正确 evidence id 但 quote 被改写，link 还能发现吗？还缺什么检查？
3. 主课 `ClaimSourceLink` 与本轨 `ClaimLink` 字段差异反映了什么边界选择？

## 下一步

- Lab：[labs/02-evidence-chain-lab.md](../labs/02-evidence-chain-lab.md)
- Solution：[solutions/02-evidence-chain-solution.md](../solutions/02-evidence-chain-solution.md)
