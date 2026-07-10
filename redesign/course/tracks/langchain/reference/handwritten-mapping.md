# Handwritten ↔ LangChain 映射（Parts 0–2）

| 主题 | Handwritten | LangChain 轨 | 备注 |
| --- | --- | --- | --- |
| 环境 | uv + offline | uv group `langchain-course` + DeepSeek | key 放 `.env` |
| Hello | Lab 00 env check | Lab 00 DeepSeek hello | F0 |
| Agent loop | `AgentRunner` | `run_tool_calling_agent` | `bind_tools` 手写 loop |
| Tools | `ToolRuntime` | `@tool` / `BaseTool` | `tools_echo` |
| Trail | `RunEvent` / `event_type_sequence` | `AgentStep` / `step_kinds` | 语义对照非类型共享 |
| Model | `FakeModel` | Scripted fake 或 `ChatOpenAI` | unit 默认 scripted |
| Sources | `Source` / `SourceIngestor` | `PaperDoc` / `default_paper_docs` | 本地 fixture |
| Retrieve | `FakeRetriever` | `KeywordRetriever` | 非 embedding |
| Evidence/Claim | `Evidence` / `Claim` / `Report` | `EvidenceItem` / `ClaimItem` / `ResearchReport` | 命名隔离 |
| Links | `build_claim_source_links` | `build_claim_links` | 缺链 raise |
| 产品 core | `packages/research_core` | **禁止**双向 import | 教学包独立 |

Parts 3+ 在 F2/F3 追加行。
