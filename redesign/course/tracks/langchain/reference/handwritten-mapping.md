# Handwritten ↔ LangChain 映射（Parts 0–4）

| 主题 | Handwritten | LangChain 轨 | 备注 |
| --- | --- | --- | --- |
| 环境 | uv + pytest | uv group `langchain-course` + DeepSeek | key 放 `.env` |
| Hello | Lab 00 env check | Lab 00 DeepSeek hello | F0 |
| Agent loop | `AgentRunner` | `run_tool_calling_agent` | `bind_tools` 手写 loop |
| Tools | `ToolRuntime` | `@tool` / `BaseTool` | `tools_echo` |
| Trail | `RunEvent` / `event_type_sequence` | `AgentStep` / `step_kinds` | 语义对照非类型共享 |
| Model | `FakeModel` | Scripted fake 或 `ChatOpenAI` | unit 默认 scripted |
| Sources | `Source` / `SourceIngestor` | `PaperDoc` / `default_paper_docs` | 本地 fixture |
| Retrieve | `FakeRetriever` | `KeywordRetriever` | 非 embedding |
| Evidence/Claim | `Evidence` / `Claim` / `Report` | `EvidenceItem` / `ClaimItem` / `ResearchReport` | 命名隔离 |
| Links | `build_claim_source_links` | `build_claim_links` | 缺链 raise |
| Memory record | `MemoryRecord` | `MemoryNote` | kinds 对齐教学语义 |
| Memory engine | `MemoryEngine` | `Notebook` | write/recall policy |
| Write/recall policy | `MemoryWritePolicy` / `MemoryRecallPolicy` | 同名教学类型 | 非向量库 |
| Skill package | `SkillPackage` / `SkillRuntime` | `SkillManifest` / `SkillLoader` | progressive disclosure |
| Skill references | `read_reference` 显式 | `SkillLoader.read_reference` | 路径安全 |
| Role / task | `AgentRolePolicy` / `DelegationTask` | `WorkerRole` / `WorkerTask` | 顺序委派 |
| Budget | `DelegationBudget` | `WorkerBudget` | 按 model_request 计 |
| Runtime | `DelegationRuntime` | `DelegationCoordinator` | parent trail |
| Parent events | `delegate_*` | `delegate_start` / `delegate_finish` | 记在 `AgentStep` |
| Merge | `DelegationMergeResult` | `MergeResult` | conflicts 可见 |
| Child runner | stub / FakeModel | `scripted_runner` / live agent | unit 离线 |
| 产品 core | `packages/research_core` | **禁止**双向 import | 教学包独立 |

Parts 5+（workbench / comparisons / production / Capstone）在 F3 追加行。
