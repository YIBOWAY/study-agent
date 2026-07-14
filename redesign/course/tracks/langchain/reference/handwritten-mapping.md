# Handwritten ↔ LangChain 映射（Parts 0–7 + Capstone）

| 主题 | Handwritten | LangChain 轨 | 备注 |
| --- | --- | --- | --- |
| 环境 | uv + pytest | uv group `langchain-course` + DeepSeek | key 放 `.env` |
| Hello | Lab 00 env check | Lab 00 DeepSeek hello | F0 |
| Agent loop | `AgentRunner` | `run_tool_calling_agent` | `bind_tools` 手写 loop |
| Tools | `ToolRuntime` | `@tool` / `BaseTool` | `tools_echo` |
| Trail | `RunEvent` / `event_type_sequence` | `AgentStep` / `step_kinds` | 语义对照非类型共享 |
| Model | `FakeModel` | deterministic `BaseChatModel` 或 `ChatOpenAI` | offline 不绕过 LC |
| Sources | `Source` / `SourceIngestor` | `PaperDoc` / `default_paper_docs` | 本地 fixture |
| Retrieve | `FakeRetriever` | `LangChainPaperRetriever(BaseRetriever)` | 返回 `Document`，非 embedding |
| Chain composition | 手写函数调用 | LCEL Runnable / `get_graph()` | 可 invoke/batch/inspect |
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
| Child runner | stub / FakeModel | deterministic/live LC agent loop | unit 离线 |
| Parallel workers | 自定义 delegation runtime | `RunnableParallel` | 不自动带总预算/回滚 |
| Session history | 显式 memory engine | `RunnableWithMessageHistory` | 当前版本提示迁往 LG persistence |
| Workbench | `research_core.product` | `langchain_course.workbench` | 九面板 shape 对齐 |
| Timeline adapter | `from_event(RunEvent)` | `from_step(AgentStep)` | |
| Comparisons | `course.framework_comparisons` | `langchain_course.comparisons` | profile 是记录非 wrapper |
| Baseline run | `run_handwritten_task` | `run_lc_baseline` | 真实 LC tool loop，确定性模型 |
| Diagnostics | `RunDiagnostics.from_events` | `RunDiagnostics.from_steps` | |
| Persistence | `JsonlRunEventStore` | `JsonlStepStore` | schema 独立 |
| Approval / sandbox | `ApprovalPolicy` / `SandboxPolicy` | approval 适配 `before_tool`；sandbox 仍需 adapter | control before effect |
| Framework tracing | `RunEvent` | `LangChainTraceRecorder` callback | 观察不等于控制 |
| Capstone | `course/capstone` | `course/tracks/langchain/capstone` | fixtures 可复制文本 |
| 产品 core | `packages/research_core` | **禁止**双向 import | 教学包独立 |
