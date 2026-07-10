# Design: LangChain & LangGraph Parallel Teaching Tracks

> **Status:** Design approved (pending user review of this written spec)  
> **Date:** 2026-07-10  
> **Branch:** `codex/redesign-course-r7` (or successor teaching branch)  
> **Related:** handwritten course R1–R9 complete; Part 6 framework profiles remain deterministic records only

## 1. Problem

学习者已经完成（或可完成）handwritten `research_core` 主课，并理解「为何先手写、再选型」。下一步要**系统学习真实的 LangChain 与 LangGraph**，而不是只看 Part 6 的评分卡。

需求约束（已确认）：

| 决策 | 选择 |
| --- | --- |
| 范围 | 完整镜像轨：Parts 1–7 + Capstone，各有 chapter / lab / solution |
| 与主课关系 | **并行轨**：主课 R1–R9 不动；可三方对照 |
| 顺序 | 先整条 **LangChain**，再整条 **LangGraph**（LC 为 LG 前置） |
| 实现关系 | **完全框架原生重写**业务能力；不 import `research_core`；不混合 |
| 模型 | **默认真实 API**；DeepSeek（OpenAI-compatible） |
| 交付形态 | 独立教学包 + optional deps；主 CI 不强制装 LC/LG、不强制有 key |

## 2. Goals

1. 提供与主课能力对齐的 **LangChain 完整教学轨**（Parts 1–7 + Capstone）。
2. 在 LC 完成后，提供 **LangGraph 完整教学轨**（Parts 1–7 + Capstone）。
3. 每 Part 可与 handwritten 对照（场景、验收语义、概念映射），代码零共享。
4. 不污染 `research_core` 产品路径与主课 offline CI。
5. 分 phase（F0–F5）交付，使学习者可在 F1 起开始学 LC，不必等全部完成。

## 3. Non-Goals

- 不替换 handwritten 主线或默认 Beginner Track。
- 不把 LC/LG 做成产品默认 runtime（`apps/` 仍走 `research_core`）。
- 不在框架轨接入真实论文 API / 网络检索（仍用本地 paper fixture 语义）。
- 不做 CrewAI / LlamaIndex 等其它框架的完整镜像。
- 不把需要 API key 的 integration 测试默认并入主 CI 必跑项。
- 不在第一期完整重写 React Workbench UI（Part 5 以 API/snapshot 语义与薄演示为主）。

## 4. Architecture

### 4.1 Directory layout

```text
course/tracks/
  langchain/
    README.md
    chapters/          # 01..07 + 00 setup if needed
    labs/
    solutions/
    capstone/          # fixtures copy or shared path, starter, solution, rubric
    reference/         # LC 术语、排障、与 handwritten 映射总表
  langgraph/
    README.md
    chapters/
    labs/
    solutions/
    capstone/
    reference/

packages/
  langchain_course/    # 教学用可运行代码（非产品）
    pyproject or nested under redesign extras
    src/langchain_course/
  langgraph_course/
    src/langgraph_course/

docs/plans/            # F0–F5 executable plans
docs/progress/phases/  # phase-f0 .. phase-f5
```

命名约定：

- 课程材料：`course/tracks/{langchain|langgraph}/`
- 可运行包：`packages/langchain_course`、`packages/langgraph_course`
- **禁止**从 `research_core` import 这两包；**禁止**这两包 import `research_core`
- **禁止** `apps/api` / `apps/web` 依赖框架轨包

### 4.2 Dependency isolation

- 主 `pyproject` 通过 **optional extras** 安装框架轨依赖，例如：
  - `langchain-course` → `langchain`, `langchain-openai`（或等价 DeepSeek 兼容栈）, `langchain-core`, …
  - `langgraph-course` → `langgraph`, 以及 LG 轨需要的 LC 生态包
- 主 CI 默认 **不** install 这些 extras；现有 `pytest -q`（215）保持无 key 可绿。
- 框架轨测试路径独立（例如 `packages/langchain_course/tests`、`course/tracks/langchain/**/test_*.py`），不进入默认 `testpaths`，或用 marker 排除。

### 4.3 Shared semantics only

跨轨共享的是**语义**，不是代码：

| 共享语义 | 说明 |
| --- | --- |
| 产品故事 | 本地论文研究助手 |
| 研究问题 | 与 Capstone 同主题（可复制文本，不共享 Python 模块） |
| Paper fixtures | JSON 可复制到各轨 `capstone/paper_fixtures/`（允许内容相同，路径独立） |
| Rubric 维度 | 证据链、记忆/技能、委派、可检查产出、生产边界、reflection——用框架语言表述 |
| 对照表 | 每章 handwritten 概念 ↔ LC/LG 概念 |

## 5. Model configuration (DeepSeek)

| Item | Convention |
| --- | --- |
| Provider | DeepSeek via OpenAI-compatible API |
| Required env | `DEEPSEEK_API_KEY` |
| Optional env | `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` |
| LC wiring | Chat model factory using OpenAI-compatible client + base_url |
| LG wiring | Same chat model inside graph nodes |
| Secrets | Env / local `.env` (gitignored); never commit keys |
| Swap | Document how to point base_url/model at other compatible endpoints |

## 6. Content mapping

### 6.1 Delivery order

1. Complete **LangChain** Parts 1–7 + Capstone (phases F1–F3).  
2. Then complete **LangGraph** Parts 1–7 + Capstone (phases F4–F5).  
3. Learners may keep handwritten materials open for对照.

### 6.2 Part → framework focus

| Part | Handwritten focus | LangChain track | LangGraph track |
| --- | --- | --- | --- |
| 0 Setup | uv, primer | DeepSeek hello, LC env, package install | LG env, graph hello（依赖 LC 已完成） |
| 1 Kernel | AgentRunner, tools, events | AgentExecutor / LCEL tool-calling agent；中间步骤可观察 | StateGraph 最小 loop：model ↔ tool 节点 |
| 2 Research | Source→Evidence→Claim→Report | Document/loader、retriever、RAG 链；引用字段可检查 | 有状态研究图：retrieve → extract → claim 节点与状态 schema |
| 3 Memory/Skills | MemoryEngine, SkillRuntime | LC memory；prompt/tool 包或等价 skill 加载 | 状态内记忆 + 外部 store；条件边加载技能 |
| 4 Delegation | DelegationRuntime, budgets | 多 chain / 多 agent 协作模式 | 多 actor / subgraph；预算用步数或节点限制表达 |
| 5 Workbench | WorkbenchSnapshot, adapters | 导出 JSON snapshot 形状；可选薄 FastAPI | 从 graph state 投影 snapshot；可选 interrupt 展示 |
| 6 Comparisons | FrameworkProfile 评分 | 用真实 LC 体验回看 Part 6 决策 | 用真实 LG 体验解释 state_resume 高分 |
| 7 Production | Diagnostics, JSONL, approval, sandbox | 回调/tracing、持久化、人工审批钩子 | checkpoint、resume、interrupt、策略边界 |
| Capstone | 整合 Parts 1–7 | 完整 LC 版助手 + tests + reflection | 完整 LG 版助手 + checkpoint 演示 + reflection |

### 6.3 Per-Part artifact contract (mirror of main course)

Each rewritten Part in each track must include:

- Chapter with problem-first narrative and **handwritten ↔ framework 映射表**
- Lab: L1 Follow / L2 Modify / L3 Design（可按框架习惯微调，但三档保留）
- Solution with 参考实现要点与「为何这样对照 handwritten」
- Eval gate: 可运行命令（unit 无 key；integration 需 key 时文档标明）
- 至少若干 callout：`[DD]` / `[TRAP]` / `[CHECK]`（诚实边界：非确定性、费用、与 core 无关）
- Reflection：tradeoff，不是纯 recall

Capstone per track:

- README product brief（框架语境）
- Rubric（对齐六维语义）
- paper_fixtures
- starter + solution
- trajectory 或 run log 样例（API 非确定时允许「结构样例」）
- report + reflection（chose / rejected / because）

## 7. Testing strategy

| Layer | What | Needs key? |
| --- | --- | --- |
| Main CI | Existing redesign suite + ruff + docs freshness | No |
| Track unit | Import, config validation, pure helpers, static graph shape | No |
| Track integration | Live DeepSeek lab/capstone smoke | Yes; `@pytest.mark.integration`; skip unless `RUN_DEEPSEEK_TESTS=1` |
| Docs | Index links for track paths exist | No |

Assertion style for live labs:

- Prefer structure, tool-call occurrence, required fields, graph node visits
- Avoid exact full-string equality on model prose
- Document flaky-risk and retry policy (keep simple)

## 8. Honesty boundaries

- Live API output is **non-deterministic**.
- Framework tracks do **not** claim to replace `research_core` as product runtime.
-对照 is by **capability and scenario**, not identical `RunEvent` sequences.
- LC track must not require LangGraph packages for Parts 1–7 / Capstone.
- LG track may depend on LangChain ecosystem packages, but pedagogy is “after LC”.
- Role/tool/memory “declared but not enforced” class of lessons should be re-expressed honestly in each framework’s real behavior (do not invent fake auto-enforcement).

## 9. Delivery phases

| Phase | Deliverable | Learner can start |
| --- | --- | --- |
| **F0** | Scaffold: dirs, packages, optional deps, DeepSeek factory, track READMEs, plan/progress, course index entry | Env + hello DeepSeek |
| **F1** | LC Parts 1–2 | Systematic LC learning |
| **F2** | LC Parts 3–4 | |
| **F3** | LC Parts 5–7 + LC Capstone | Full LC track |
| **F4** | LG Parts 1–4 | Systematic LG learning |
| **F5** | LG Parts 5–7 + LG Capstone | Full LG track; three-way对照 complete |

Phase workflow (same discipline as R-phases):

1. Write phase plan + progress file  
2. Author materials + code  
3. Verify (unit always; integration when key present)  
4. Sync indexes / neat-freak  
5. Commit and push without requiring the user to run git  

## 10. Index and progress surfaces

When F0 lands, update at minimum:

- `course/README.md` — section「并行框架轨」（默认 Beginner Track 仍指向 handwritten）
- `docs/course/roadmap.md` — F0–F5 near-term work
- `docs/README.md` — link track entrypoints and this spec
- `docs/progress/overall.md` + `docs/progress/README.md` — phase rows
- Root `README.md` — short pointer to parallel tracks
- Optional: `AGENTS.md` boundary line: framework track packages are teaching-only

Do **not** rewrite R1–R9 status as replaced.

## 11. Recommended learner path

```text
(optional) handwritten Part 1 mental model
  → F0 DeepSeek hello
  → LC Parts 1→7 → LC Capstone
  → revisit handwritten Part 6 scoring with real LC experience
  → LG Parts 1→7 → LG Capstone
  → three-way Capstone对照: handwritten / LC / LG strengths
```

## 12. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Non-deterministic labs | Structural assertions; sample trajectories not golden prose |
| Upstream API churn | Pin dependency ranges; version matrix in F0 README |
| Scope explosion | Hard phase cuts F0–F5; no LG until F3 done |
| Cost / rate limits | Document expected calls; keep lab steps small |
| Learners skip handwritten | Entry text recommends Part 1 handwritten first; tracks still usable alone |

## 13. Success criteria (program complete)

1. LC mirror complete and runnable with DeepSeek.  
2. LG mirror complete and runnable; state/checkpoint (or equivalent resume demo) visible.  
3. Zero pollution of `research_core` / `apps` dependency direction.  
4. Main CI remains green without API key.  
5. Every Part has handwritten ↔ framework mapping.  
6. Config via env only; secrets never committed.  
7. F0–F5 plans/progress and indexes consistent.

## 14. First implementation slice (F0 preview only)

Out of scope for this design doc’s approval gate, but next plan should start with:

- Create `course/tracks/langchain` and `course/tracks/langgraph` skeletons + READMEs  
- Create `packages/langchain_course` with DeepSeek chat factory + hello test (integration marked)  
- Wire optional extras and pytest markers  
- One lab: configure DeepSeek and complete one chat round-trip  
- Index + progress for F0  

F0 does **not** implement Parts 1–7 content.

## 15. Design decisions summary

| ID | Decision | Why |
| --- | --- | --- |
| DD-T1 | Parallel tracks, not replace main course | Preserve offline handwritten baseline and product core |
| DD-T2 | Full mirror (not thin对照-only) | User goal is systematic LC then LG learning |
| DD-T3 | LC entire track before LG entire track | LC is pedagogical prerequisite for LG |
| DD-T4 | Framework-native rewrite, no `research_core` mix | Maximize framework idioms; avoid dual models |
| DD-T5 | Real DeepSeek by default | User has key; authentic learning path |
| DD-T6 | Optional deps + integration markers | Protect main CI and offline contributors |
| DD-T7 | Teaching packages under `packages/*_course` | Clear non-product boundary |
| DD-T8 | Phased F0–F5 delivery | Learnable incrementally; manageable reviews |

## 16. Open points deferred to implementation plans

These are intentionally **not** blocked on design approval; each phase plan will pin them:

- Exact pinned versions of `langchain` / `langgraph` stacks at F0 time  
- Whether Capstone fixtures are byte-identical copies or generated once and duplicated by script  
- Part 5 thin API surface: FastAPI app inside track package vs scripts only  
- Precise L1/L2/L3 rubrics per framework Part  

---

**Approval gate:** User reviews this file. After explicit approval, create F0 implementation plan via writing-plans skill; do not implement track content before that plan is approved.
