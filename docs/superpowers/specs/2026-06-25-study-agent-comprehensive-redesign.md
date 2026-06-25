# Study Agent Comprehensive Redesign

## Goal

把当前的 Research Agent Platform 重构为一个完整的学习型 Agent 工程项目：

- 它首先是课程：适合从基础 Python 起步，系统学习现代 Agent 工程。
- 它也是工程参考：展示 Agent loop、context、memory、skills、MCP、multi-agent、eval、observability、harness 的真实边界。
- 它最终形成一个作品级产品：Research Agent Workbench，而不是 chat + RAG demo。

项目目标不是追逐某个框架，而是让学习者先理解机制，再理解框架在什么条件下值得使用。

## Current Baseline

当前仓库已经是一个不错的 Agent 工程全景项目，但不是合格的从零学习课程。

已有优势：

- 手写 LLM HTTP 调用、tool loop、RAG、workflow、agent、agent_v2、multi-agent、eval、guardrails、tracing、MCP、前端和 CI。
- 代码量足够展示真实工程复杂度。
- 现有测试覆盖较多，具备继续演化的基础。

主要问题：

- 学习路径不连续，对初学者不友好。
- 课程层、产品层、实验层没有明确分离。
- 框架比较缺少统一任务和统一评价基准。
- memory、context compression、skills、harness、loop engineering、multi-agent delegation 还没有成为主线。
- 产品形态还不像专业研究工作台。
- 离线可运行性、fake model、trajectory regression 和文档 gate 需要重新设计。

最近一次基线验证结果：

- `compileall` 通过。
- `ruff check app tests` 通过。
- 全量 pytest 结果为 `261 passed, 2 failed, 1 warning`。
- 两个失败用例集中在 Windows MCP command/path 解析，原因是 POSIX `shlex` 会剥离 Windows 反斜杠。

## Approved Direction

本重构采用以下已经确认的方向：

1. 课程优先，同时兼顾工程参考和作品集展示。
2. 面向有基础 Python、但不熟 async、FastAPI、Agent 工程的学习者。
3. 允许破坏式重构，不要求原地兼容当前目录结构。
4. 使用双层仓库：课程/labs 层与最终产品层并存。
5. 默认离线可运行，不需要 API key。
6. 业务主题保持为 research assistant。
7. 最终产品必须是专业 standalone web app。
8. 每章必须有严格练习、测试和 eval gate。
9. 课程长度扩展到 24 周，优先保证完整度和丰富度。
10. 默认运行时以手写 Agent Runner 为主，框架作为对照实验。
11. Hermes 是主参考方向，Pi 是轻量内核参考。

## Reference Hierarchy

### Hermes: Primary Reference

Hermes 更接近本项目应该学习的现代 Agent 形态。重点参考：

- agent loop
- context assembly
- skills
- delegation
- isolated child contexts
- concurrent tool execution
- interrupt / cancellation
- iteration and budget controls
- context compression
- persistent memory
- harness engineering

项目不复制 Hermes，但学习它的问题分解方式：Agent 不只是 prompt 和 tool calling，而是一套可观测、可暂停、可恢复、可压缩、可委派的运行系统。

### Pi: Kernel Quality Reference

Pi 是 coding-agent harness，不是本项目的业务模板。它更适合作为底层工程风格参考：

- internal `AgentMessage` 与 provider LLM message 分离。
- event stream 是一等运行协议。
- JSONL session tree 支持 fork、branch、clone、labels、compaction。
- compaction 是被测试的算法，而不是临时摘要 prompt。
- resource loader 统一加载 context files、skills、prompts、extensions、trust state。
- extension hooks 给 runtime lifecycle 留出干净扩展点。

本项目应该吸收这些内核设计，但不能缩成 coding agent，也不能因此去掉 MCP、multi-agent、A2A、approval、sandbox 或 research product 能力。

### Frameworks: Controlled Comparisons

框架不作为产品主线，而作为课程对照实验。

纳入对照的候选：

- PydanticAI
- LlamaIndex Workflows
- LangGraph
- OpenAI Agents SDK
- CrewAI
- MCP / A2A protocol integrations

对照规则：

- 同一个任务。
- 同一套 fake model/search fixtures。
- 同一套 trajectory/eval metrics。
- 对比表达力、复杂度、可测试性、debuggability、state/resume 能力、团队协作成本。

LangGraph 只在 checkpoint、resume、human-in-the-loop、复杂状态图明显有价值时使用。普通教学主线不依赖它。

## Repository Architecture

采用双层仓库，保留一套共享核心：

```text
apps/
  api/
  web/
packages/
  research_core/
  model_providers/
  retrieval/
  observability/
  storage/
  protocol_adapters/
course/
  chapters/
  labs/
  solutions/
  framework_comparisons/
evals/
docs/
  architecture/
  course/
  product/
  adr/
infra/
```

### `packages/research_core`

纯 Python 核心，不依赖 FastAPI、React、具体数据库或具体模型提供商。

包含：

- Agent Runner
- AgentMessage / EventStream
- Context Engine
- Memory Engine
- Tool Runtime
- Skill Runtime
- Delegation Runtime
- Research Plan / Evidence / Report domain model
- Budget / cancellation / retry / failure policy

### `apps/api`

FastAPI 只是产品接口层。它依赖 `research_core`，但核心不能反向依赖 API。

职责：

- project/run/report/source/memory/skill/eval API。
- SSE 或 websocket 事件流。
- pause/resume/cancel/replay 入口。
- adapter wiring。

### `apps/web`

最终产品是 Research Agent Workbench。

它不是教学玩具页面，而是展示真正研究流程的工作台：

- Projects
- Research Runs
- Agent Team
- Delegations
- Sources
- Reports
- Memory
- Skills
- Evals
- Settings

前端建议采用 React + TypeScript + Vite 或同等级现代前端栈。它不能退回 Streamlit 级别的 demo，也不需要营销 landing page；打开后第一屏就是可操作的 workbench。

### `course`

课程层不直接等于产品代码。

每章都应包含：

- concept note
- handwritten lab
- failure lab
- product integration note
- framework comparison
- exercises
- eval gate
- solution

课程代码允许比产品代码更小、更教学化，但必须使用相同概念和相同 contracts，避免学习内容与最终工程脱节。

### `evals`

评估层是项目质量主轴。

包含：

- fake model scripts
- fake search corpus
- task datasets
- expected trajectories
- citation quality cases
- memory pollution cases
- multi-agent merge cases
- framework comparison reports

## Course Roadmap

课程周期为 24 周，分 8 个领域。

### Domain 1: Agent Engineering Foundations

目标：建立 LLM 与 Agent 的底层直觉。

内容：

- token、embedding、transformer inference、sampling、context window。
- SFT、RLHF、tool calling、structured output 的边界。
- prompt、message、role、system instruction、developer instruction。
- hallucination、grounding、evidence、deterministic fake model。
- 从一个最小 chat loop 过渡到 agent loop。

### Domain 2: Agent Kernel & Context Engine

目标：手写可测试 Agent 内核。

内容：

- AgentMessage vs provider message。
- event stream。
- tool registry。
- think-act-observe loop。
- budget、stop condition、retry、timeout。
- context builder。
- trajectory replay。
- context compression 初版。

### Domain 3: Memory & Stateful Agents

目标：把 memory 从“向量库技巧”提升为状态系统。

内容：

- working memory
- session memory
- episodic memory
- semantic memory
- procedural memory
- pinned/core memory
- recall policy
- write policy
- forgetting
- conflict handling
- pollution eval
- memory explainability

### Domain 4: Tools, Skills, MCP & Extensions

目标：理解工具、skills、插件和协议的边界。

内容：

- deterministic tools。
- LLM tool calling。
- tool schema and validation。
- approval and permission。
- skills folder with `SKILL.md`。
- progressive disclosure。
- skill assets/scripts/references。
- MCP server/client。
- extension hooks。
- tool calling -> MCP -> A2A 的协议光谱。

### Domain 5: Knowledge & Deep Research

目标：从 RAG 过渡到 research workflow。

内容：

- chunking、embedding、hybrid search、rerank。
- source ingestion。
- claim-source mapping。
- citation completeness。
- evidence graph。
- conflict detection。
- report synthesis。
- research planning and iterative search。

### Domain 6: Delegation & Multi-Agent Systems

目标：把 multi-agent 做成产品中的真实能力，而不是演示噱头。

内容：

- orchestrator-worker。
- planner/researcher/reader/critic/synthesizer roles。
- isolated child context。
- scoped tools and skills。
- parallel delegation。
- cancellation propagation。
- budget accounting。
- result merge。
- conflict resolution。
- child memory write restrictions。
- A2A remote agent adapter。

### Domain 7: Harness & Loop Engineering

目标：学习现代 Agent 项目真正难的工程部分。

内容：

- repo instructions。
- resource loader。
- context files。
- run logs。
- JSONL session storage。
- run tree and branch。
- compaction algorithm。
- trajectory diagnostics。
- eval feedback loop。
- agent-readable docs。
- worktree isolation。
- error taxonomy。

### Domain 8: Frameworks, Product & Production

目标：把机制转化为框架判断力和产品交付能力。

内容：

- PydanticAI comparison。
- LlamaIndex Workflows comparison。
- LangGraph comparison。
- OpenAI Agents SDK comparison。
- CrewAI / A2A comparison。
- FastAPI product API。
- web workbench。
- observability。
- security and sandboxing。
- deployment。
- docs maintenance。
- living landscape updates。

## Chapter Structure

每章采用六步结构：

1. Theory: 讲清概念和失败模式。
2. Handwritten implementation: 从零实现一个小机制。
3. Product integration: 接入 Research Agent Workbench。
4. Failure lab: 人为制造 bug、上下文污染、工具失败或评估失败。
5. Framework comparison: 用至少一个框架重做同一任务。
6. Eval gate: 必须通过测试、轨迹检查或质量评估。

这会让学习者同时获得三种能力：

- 能手写机制。
- 能读懂框架。
- 能把机制放进产品。

## Product Design

最终产品是 Research Agent Workbench。

### Product Purpose

用户提交一个研究问题，系统组织一个或多个 Agent 完成：

- question clarification
- research plan
- source discovery
- evidence extraction
- claim verification
- contradiction detection
- synthesis
- report generation
- memory update
- eval and replay

### Core Domain Entities

产品核心实体：

- Project: 一组研究主题、资料、记忆和报告的边界。
- ResearchRun: 一次可暂停、可恢复、可重放的研究任务。
- RunEvent: Agent 运行轨迹中的 append-only 事件。
- AgentProfile: role、prompt policy、tool scope、skill scope、memory policy。
- Delegation: parent agent 分配给 child agent 的任务。
- Source: 外部或本地资料来源。
- Evidence: 从 Source 中抽取的可引用证据片段。
- Claim: 报告中的可验证论断。
- Report: 研究输出和 claim-source mapping。
- MemoryRecord: 可召回、可解释、可冲突处理的记忆条目。
- Skill: 可被 runtime 加载的能力包。
- EvalResult: 针对 run/report/memory/delegation 的质量记录。

### Main Screens

首屏不是 landing page，而是工作台。

主要区域：

- Workspace navigation。
- Task Composer。
- Run Timeline。
- Delegation Tree。
- Agent Inspector。
- Source & Evidence Panel。
- Merge & Conflict Panel。
- Report Editor。
- Memory Panel。
- Skill Panel。
- Eval Panel。

### Multi-Agent Surface

Multi-agent 必须是一等产品能力，体现在 UI 和 runtime 两层。

UI 中必须能看到：

- Agent Team roster。
- Orchestrator 节点。
- Search Agent、Reader Agent、Analyst Agent、Critic Agent、Synthesizer Agent。
- 每个 child agent 的 isolated context、tool scope、skill scope、budget、status。
- delegation tree。
- cross-agent messages。
- merge decisions。
- conflicts and unresolved claims。

Runtime 中必须支持：

- single-agent baseline。
- orchestrator-worker delegation。
- parallel delegation。
- isolated context per child。
- memory policy per role。
- scoped tools/skills。
- cancellation and timeout propagation。
- result merge contract。
- A2A adapter for remote agents。

### Out of Product Scope

v1 不做：

- enterprise multi-tenant auth。
- team billing。
- mobile app。
- browser extension。
- unrestricted code execution。
- full model fine-tuning。
- four duplicated framework implementations inside product。

## Runtime Design

### AgentMessage

内部消息格式必须独立于 OpenAI、Anthropic 或其他 provider message。

原因：

- 便于支持 fake model。
- 便于记录 tool、skill、delegate、memory、compression events。
- 便于做 trajectory regression。
- 便于在 provider adapter 边界做转换。

### Event Stream

所有运行事件统一进入 event stream：

- model_request
- model_response
- tool_call
- tool_result
- skill_load
- skill_step
- memory_recall
- memory_write
- delegate_start
- delegate_event
- delegate_finish
- compaction_start
- compaction_finish
- eval_result
- error

event stream 同时服务：

- UI timeline。
- debugging。
- tests。
- replay。
- eval。
- docs examples。

### Session Storage

初版采用 JSONL session storage，后续可接 SQLite/Postgres。

必须支持：

- append-only event log。
- run tree。
- fork。
- branch label。
- compaction marker。
- model/provider changes。
- active tool/skill changes。
- replay。

### Context Compression

compression 不能只是“让模型总结一下历史”。

需要明确：

- trigger threshold。
- protected messages。
- evidence/source preservation。
- tool result preservation。
- previous summary update。
- lost information audit。
- compression eval。

### Skills

skills 采用 folder-based progressive disclosure：

```text
skills/
  deep-research/
    SKILL.md
    scripts/
    references/
    assets/
```

`SKILL.md` 只放入口说明和触发规则。大型参考资料、脚本和素材放到子目录，需要时再加载。

产品中 skills 是 Research Run 的扩展能力；课程中 skills 是学习 tool/plugin/harness 边界的核心材料。

## Documentation System

文档必须服务三类读者：

- 学习者。
- 工程维护者。
- Agent。

### Required Docs

必须建立：

- `README.md`: 项目定位、快速启动、课程入口、产品入口。
- `AGENTS.md`: 仓库操作协议、测试命令、写文档规则、agent safety rules。
- `docs/architecture/overview.md`: 双层架构和依赖方向。
- `docs/architecture/runtime.md`: agent loop、event stream、context、memory、delegation。
- `docs/architecture/data-model.md`: project、run、event、source、evidence、report、memory、skill。
- `docs/course/roadmap.md`: 24 周课程地图。
- `docs/course/chapter-template.md`: 每章固定结构。
- `docs/product/workbench.md`: 产品边界和页面说明。
- `docs/adr/`: 关键架构决策记录。
- `docs/glossary.md`: Agent、tool、skill、plugin、MCP、A2A、harness、memory 等术语。
- `docs/living-landscape.md`: 记录框架和协议变化，带日期，不混入稳定核心。

### Documentation Gates

每个重要实现必须同步：

- tests。
- docs。
- examples。
- eval fixture。

如果某章新增一个核心机制，却没有对应 failure lab 和 eval gate，则该章不算完成。

## Testing and Evaluation Strategy

### Offline First

默认测试不需要 API key。

必须提供：

- FakeModel。
- FakeSearch。
- FakeEmbedding。
- FakeMCPServer。
- deterministic clock/id generator。
- fixed datasets。

### Test Layers

测试分层：

- unit tests: core algorithms。
- contract tests: adapters。
- integration tests: API and storage。
- trajectory tests: event stream regression。
- eval tests: research quality metrics。
- Playwright E2E: workbench flows。
- docs tests: commands and examples stay valid。

### Eval Categories

至少覆盖：

- answer relevance。
- source recall。
- citation completeness。
- claim-source consistency。
- conflict detection。
- tool failure recovery。
- memory pollution。
- context compression loss。
- delegation merge quality。
- framework comparison metrics。

### Quality Gates

每章和每个产品 milestone 都要给出明确 gate：

- required tests。
- required eval dataset。
- expected output shape。
- allowed failure cases。
- debug checklist。

## Migration Strategy

采用 clean-room v2 重构。

### Why Not Incremental Refactor

当前仓库可以作为学习素材，但结构已经不适合直接长成双层课程/产品项目。

原地渐进式重构的风险：

- 旧边界拖住新架构。
- 课程层和产品层继续混在一起。
- 框架比较难以保持统一基准。
- 文档难以重新成为主干。

### Migration Shape

推荐步骤：

1. 保留当前 git history。
2. 新建 v2 package/app/course/evals/docs 骨架。
3. 先迁移有价值的 tests、fixtures、docs 片段，而不是迁移全部旧代码。
4. 先建立 `research_core` contracts。
5. 再实现课程前几章 lab。
6. 再把同一机制接入 product workbench。
7. 每个 milestone 都跑 offline tests 和 eval gates。

不要创建巨大的 `legacy/` 目录。需要参考旧代码时通过 git history 和有选择的迁移完成。

## Milestones

这些 milestones 是总体路线，不要求在一个实现计划或一个 PR 中全部完成。后续 writing-plans 阶段应把它们拆成可评审、可测试、可回滚的执行计划。

### Milestone 0: Redesign Scaffold

- 新目录结构。
- root README。
- AGENTS.md。
- glossary。
- architecture overview。
- fake model/search fixtures。
- test harness baseline。

### Milestone 1: Agent Kernel Course Spine

- Domain 1-2 前几章。
- AgentMessage。
- event stream。
- basic agent loop。
- tool runtime。
- context builder。
- trajectory tests。

### Milestone 2: Research Core

- source/evidence/report domain model。
- retrieval adapters。
- claim-source mapping。
- research planning。
- report synthesis。

### Milestone 3: Memory and Skills

- memory engine。
- recall/write policy。
- skill runtime。
- skill examples。
- memory pollution eval。

### Milestone 4: Multi-Agent and Delegation

- delegation runtime。
- parallel workers。
- isolated child context。
- role policies。
- merge contract。
- A2A adapter stub。
- multi-agent eval cases。

### Milestone 5: Workbench Product

- FastAPI app。
- web app。
- research run timeline。
- delegation tree。
- source/evidence panels。
- report editor。
- memory/skill/eval panels。

### Milestone 6: Framework Comparisons

- same task across handwritten runner and selected frameworks。
- reports under `course/framework_comparisons`。
- clear framework recommendation matrix。

### Milestone 7: Production Readiness

- observability。
- persistence hardening。
- auth/approval/sandbox policy。
- deployment docs。
- docs freshness checks。
- full course/product gate.

## Risks

### Scope Creep

24 周课程、完整产品和多框架比较很容易膨胀。

Mitigation:

- 每章只引入一个主要机制。
- 产品 v1 不做企业功能。
- 框架只做对照实验，不进入产品主路径。

### Framework Churn

Agent 框架和协议变化很快。

Mitigation:

- 稳定核心只讲机制。
- `docs/living-landscape.md` 记录日期化变化。
- framework comparison 可替换，不影响核心课程。

### Fake Model Overfitting

离线测试可能让代码只适配 fake fixtures。

Mitigation:

- contract tests 明确 provider boundary。
- 少量 optional live smoke tests。
- eval datasets 覆盖 failure modes。

### Multi-Agent Becoming Theater

Multi-agent 容易变成角色 prompt 表演。

Mitigation:

- 必须有 isolated context、budget、tool scope、parallelism、merge contract。
- 必须能在 UI 中看见 delegation tree 和 merge decisions。
- 必须用 eval 比较 single-agent 与 multi-agent 的质量/成本差异。

### Documentation Drift

课程和代码容易不同步。

Mitigation:

- chapter template 强制包含 product integration 和 eval gate。
- docs tests 检查命令和文件引用。
- 每个 milestone 完成时更新 glossary 和 architecture docs。

## Acceptance Criteria

本重构设计完成后，最终项目应满足：

- 新学习者能从 README 进入 24 周课程，不需要先理解旧项目历史。
- 无 API key 环境可以跑通核心课程测试和产品 smoke。
- 学习者能手写一个最小 Agent Runner，再理解框架如何封装它。
- memory、skills、MCP、multi-agent、harness、loop engineering 都是主线内容。
- Research Agent Workbench 明确展示 multi-agent delegation、memory、skills、eval 和 evidence workflow。
- 所有核心机制都有测试、failure lab 和 eval gate。
- Hermes 的现代 Agent 工程思想被吸收为方向，Pi 的轻量内核设计被吸收为实现质感，但项目不变成两者的复制品。

## References

- Hermes docs: `https://hermes-agent.nousresearch.com/docs/`
- Hermes architecture: `https://hermes-agent.nousresearch.com/docs/developer-guide/architecture`
- Hermes agent loop: `https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop`
- Hermes delegation: `https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation`
- Pi repository: `https://github.com/earendil-works/pi`
- Pi article: `https://lucumr.pocoo.org/2026/1/31/pi/`
- OpenClaw runtime architecture: `https://docs.openclaw.ai/agent-runtime-architecture`
- AI 编程绿皮书: `https://class.imooc.com/sale/aicodegb`
