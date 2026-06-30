# Course Teaching Redesign: From Module Docs to Project-Driven Learning

> **Status:** Design approved; Phase R1 complete; R2-R9 planned
> **Date:** 2026-06-30
> **Branch:** codex/redesign-course-r1

## Problem Statement

当前 v1 baseline 的课程内容（8 chapters, 8 labs, 8 solutions）从工程角度看是完整和正确的——架构清晰、测试通过、离线运行。但从教学角度看，它更接近于**技术文档的好版本**而非真正的**教学设计**。具体问题：

1. **信息密度过高**：每章在 60-90 分钟内要求理解 8-10 个新对象，初学者看完 Core Objects 表格就已信息过载
2. **Labs 是验证而非探索**：所有 lab 都是 "paste → assert"，学习者没有写代码、犯错、诊断的过程
3. **缺少叙事线**：每章独立，没有一条贯穿始终的项目故事
4. **没有设计思维训练**：Checkpoint 问题多是 recall 型，不教学习者做工程决策
5. **太干**：全程文字+代码，无架构图、event flow 时间线、对象关系图
6. **太浅**：跑通了代码，但学完不知道如何自己设计 Agent 系统
7. **无终点**：没有 capstone 把各章能力串成完整作品

## Vision

把课程从 **"先学概念，再用代码验证"** 翻转为 **"为了给项目加一个能力而学概念"**。

学习者从 Part 1 就知道最终目标：**做一个能 cite source、有 memory、能 delegate subtask、有 workbench UI 的本地论文研究助手**。每部分不是 "学一个模块"，而是 "给这个 assistant 加上一种新能力"。

> **Naming note**: 叙事线里的 "论文研究助手" 灵感来自 Semantic Scholar 的产品形态（论文搜索 + 引用追踪 + 文献综述），但它是**完全离线的本地教学项目**。所有检索使用静态 paper fixture 和 `FakeRetriever`，不调用真实 Semantic Scholar API 或任何外部服务。这样既给了学习者一个具体的、有实感的业务场景（而不是"通用 Agent 平台"），又不违背项目的离线优先原则。

## Teaching Principles

### 1. Problem-First, Not Concept-First

每一部分以一个问题开头（"你的 Agent 说了一句听起来对但找不到出处的话——你怎么知道它是真的还是编的？"），然后用概念和代码回答这个问题。

### 2. Build → Inspect → Break → Fix → Reflect

整个 Part 必须完整经历一次这个循环。循环的强度按 Section type 分级：

```
Problem (why this matters)
  → Explore (试一下现有方案，感受痛点)
  → Build (写最小可用版本)
  → Inspect (看 event trail / data flow)
  → Break (故意弄坏，看它怎么失败)
  → Fix (诊断并修复)
  → Connect (这个能力和前后 Part 的关系)
  → Reflect (设计决策问题)
```

**循环强度分级**：
- **Build Section / Break & Fix Section**：必须完整走完 8 步循环。这是教学的核心发动机。
- **Concept Section / Inspection Section**：侧重 Problem → Explore → Inspect → Connect，Build/Break/Fix 可放到下一个 Build Section。
- **Product Section / Gate Section**：侧重 Inspect → Connect → Reflect，Build/Break/Fix 交给前面 Section 已完成。

### 3. Tell-Show-Do-Reflect 节奏

- **Tell** (~15%)：概念和心智模型，配合图表
- **Show** (~20%)：运行示例代码，观察输出
- **Do** (~50%)：三阶练习 — Follow → Modify → Design
- **Reflect** (~15%)：Checkpoint 问题 + Design Decision 思考

### 4. Concrete Before Abstract

先给具体例子感受，再抽象成概念。不是先列 9 个对象再给例子，而是先给一个跑起来的 10 行代码，再从这 10 行里提取出概念。

### 5. Design Decisions Are Taught, Not Assumed

每次做一个工程选择，明确标注这是一个 Design Decision，并给出替代方案和取舍理由。目标是让学习者学会"像设计者一样思考"。

## Course Restructuring

### From Chapters to Parts

现有 8 个独立 Chapter → 重新组织为 8 个 Part，每个 Part 服务于本地理工论文研究助手的一个新能力。文件名保留 `chapters/00-07`，不改名为 `parts/`，避免大面积链接 churn。

| Part | 项目能力 | 文件 | 核心交付物 |
|------|---------|------|-----------|
| Part 1 | 让 Agent 跑起来，并且能看懂它做了什么 | `chapters/00`, `chapters/01` | 最小 AgentRunner + event trail |
| Part 2 | 让 Agent 的回答有据可查 | `chapters/02` | Source → Evidence → Claim → Report 证据链 |
| Part 3 | 让 Agent 有记忆和技能 | `chapters/03` | MemoryEngine + SkillRuntime |
| Part 4 | 让 Agent 能派活给子 Agent | `chapters/04` | DelegationRuntime + child context isolation |
| Part 5 | 给 Agent 做一个研究工作台界面 | `chapters/05` | WorkbenchSnapshot + FastAPI + React |
| Part 6 | 学会对比和选择框架 | `chapters/06` | Framework comparison reports |
| Part 7 | 让 Agent 达到生产可用标准 | `chapters/07` | Diagnostics + Persistence + Policy |
| Capstone | 整合所有能力，做一个可展示的作品 | 新增 `course/capstone/` | 完整本地论文研究助手 |

### Part Internal Structure

每个 Part 拆成 3-5 个 Section。Section types 和各自的循环强度：

| Section Type | 循环强度 | 核心活动 |
|-------------|---------|---------|
| Concept Section | 轻量：Problem → Explore → Inspect → Connect | 引入 2-3 个新概念，通过具体例子建立直觉 |
| Build Section | 完整：全部 8 步 | 写代码实现新能力，L1/L2/L3 练习 |
| Inspection Section | 轻量：Inspect → Connect → Reflect | 看 event trail / data flow / architecture |
| Break & Fix Section | 完整：Break → Fix → Inspect → Reflect | 故意破坏 + 诊断修复 |
| Product Section | 轻量：Inspect → Connect → Reflect | 把新能力接入 Workbench UI |
| Gate Section | 轻量：Reflect → Connect | Eval gate + checkpoint 问题 |

### Exercise Three-Tier System

每个 Build Section 包含三阶练习：

| 阶梯 | 名称 | 描述 | 学习者做什么 |
|------|------|------|------------|
| L1 | Follow | 跟着教程写代码，确认能跑 | Copy-type 关键代码，观察输出 |
| L2 | Modify | 改一行/一个参数，预测结果，验证 | 预测 → 修改 → 观察 → 比较 |
| L3 | Design | 给需求描述，自己写实现 | 理解需求 → 设计实现 → 通过 eval gate |

L1 确保不会掉队；L2 训练因果推理；L3 训练设计能力。

**每个 L1/L2/L3 练习必须包含反馈闭环**：

1. **Common Errors**: 列出该练习最常见的 2-3 个错误及原因
2. **Failure Output Interpretation**: 如果输出不对，错误信息应该长什么样，从哪里开始排查
3. **Where To Go Back**: 如果卡住了，应该回到正文的哪一段重新理解
4. **Why Correct Answer Is Correct**: Solution 里不只给正确答案，还要解释"这个答案排除了哪些错误理解"

### Visual Aid Types

每个 Part 标配以下图表（ASCII art，可离线显示，git diff 友好）：

1. **Architecture Map**: 当前 Part 在整个系统中的位置
2. **Object Relationship Diagram**: 核心对象的输入/输出/依赖关系
3. **Event Flow Timeline**: 一次 run 的事件序列时间线
4. **Data Flow Diagram**: 数据在对象之间的流转路径

### Sidebar System

在章节正文中穿插以下 callout。主标记用 ASCII tag，emoji 作为可选视觉增强：

| Callout | 主标记 | Emoji 增强 | 目的 |
|---------|--------|-----------|------|
| Design Decision | `[DD]` | `💡` | 解释为什么选择这个接口/边界，替代方案是什么 |
| Common Trap | `[TRAP]` | `⚠️` | 初学者容易误解的地方 |
| Mental Checkpoint | `[CHECK]` | `🧠` | 要求学习者在继续前用自己的话解释 |
| Big Picture | `[BIG]` | `🔗` | 当前概念和前后 Part 的关系 |
| Deep Dive | `[DEEP]` | `🔬` | 可选的高级内容，初学者可跳过 |

在 terminal 和纯文本环境中，`[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` 作为稳定的可检索标记。在支持 emoji 的渲染环境（GitHub、VS Code preview）中可追加 emoji 增强可读性。

```markdown
> [DD] **设计决策**：为什么 ToolRuntime 不接受 async handler？
> 
> Phase 1 的工具都是同步函数。async 会引入 event loop 管理、cancellation propagation 和测试复杂度，对初学者是额外负担。未来 Phase 如果有真实的网络工具需要 async，可以在 ToolDefinition 上加 `is_async: bool` 而不破坏现有 contract。
```

## Narrative Thread: 本地论文研究助手

### The Story

你在为一个研究团队构建一个**本地论文研究助手**——一个能基于本地论文 fixture 搜索文献、整理证据、写出可溯源的文献综述、还能把任务分派给子 Agent 的 AI 研究助手。

这条叙事线的好处：
- 每个 Part 的能力是"研究者真正需要的"
- 工程决策有了业务上下文（"为什么 Evidence 必须引用 Source？因为研究者要能点回去看原文"）
- Capstone 是一个完整的研究助手，有展示价值
- 全部离线：所有 paper 数据是静态 fixture，检索用 `FakeRetriever`，模型用 `FakeModel`

### How the Narrative Flows

```
Part 1: "研究者说'帮我查一下 attention mechanism 的最新进展'——你的 Agent 连跑都跑不起来。先让它能动。"
Part 2: "它跑起来了，但说'Transformer 在 2025 年被 XXX 超越'——这句话的证据在哪？"
Part 3: "上次它查过 attention mechanism，这次又问——它完全不记得。让它有记忆。"
Part 4: "一篇综述要查 5 个方向——它一个人做太慢。让它能派活。"
Part 5: "研究者看不懂代码——给它做个界面。"
Part 6: "别人用 LangChain 做同样的事——你手写的版本和它比，谁好？"
Part 7: "研究者要把你的 Agent 部署到团队服务器——它现在能安全上线吗？"
Capstone: "把你 7 个 Part 的工作整合，做一个能演示的本地论文研究助手。"
```

## Capstone Project Design

### Goal

学习者用 7 个 Part 积累的代码和能力，构建一个完整的**本地论文研究助手**，包含：

1. 接收研究问题 → AgentRunner 执行 research plan
2. 基于本地 paper fixture 检索 source → 提取 evidence → 生成 cited report
3. Memory 记住之前的搜索结果
4. 复杂问题 delegation 给 child agent
5. Workbench UI 展示 timeline + sources + report + eval
6. Production diagnostics 可复盘任何一次 run

全部离线运行，使用 `FakeModel` + `FakeRetriever` + 静态 paper fixture。

### Deliverables

```
course/capstone/
├── README.md              # 需求文档：模拟真实产品需求
├── rubric.md              # 评分标准（6 个 success criteria）
├── paper_fixtures/        # 离线 paper 数据集（JSON fixture）
├── starter/               # 教学 starter code（基于前 7 Part 积累）
│   ├── agent_starter.py
│   └── test_starter.py
├── solution/              # 参考 solution（完整可运行的 capstone agent）
│   ├── agent.py
│   ├── test_run.py
│   ├── trajectory.jsonl
│   ├── report.md          # Agent 产出的示例研究报告
│   └── reflection.md      # 复盘：学到了什么，哪些设计决策会改
```

### Teaching Artifacts Rule

**不改 runtime/product 代码**（`packages/research_core`、`apps/api`、`apps/web` 保持原样），但**允许**在 `course/capstone/starter/` 和 `course/capstone/solution/` 下创建教学用的 Python 示例代码。这些代码是课程材料的一部分，不是产品代码。

### Success Criteria

- [ ] 能从至少 3 个 source 中提取 evidence（使用本地 paper fixture）
- [ ] Report 中所有 claim 都能追溯到 evidence
- [ ] 至少使用 1 个 skill 和 1 个 memory policy
- [ ] Timeline 在 Workbench UI 中可查看
- [ ] 运行 `uv run pytest -q` 全绿
- [ ] 写一份 reflection 解释 3 个关键设计决策

## Implementation Phases

### Phase R1: Part 1 Restructuring (Ch00 + Ch01)

**Files to rewrite:**
- `course/README.md` — 重写为项目驱动的学习指南
- `course/chapters/00-before-agent-kernel.md` — 重写为 Part 1 Section 1：心智模型
- `course/chapters/01-agent-kernel-foundations.md` — 重写为 Part 1 Section 2-5
- `course/labs/01-agent-runner-lab.md` — 改为三阶练习 + 反馈闭环
- `course/solutions/01-agent-runner-solution.md` — 增加设计决策解释 + "为什么对"
- `docs/course/roadmap.md` — 更新 roadmap 到新的 Part 结构
- `docs/course/chapter-template.md` — 替换为新 template
- `docs/README.md` — 更新文档索引

**New files:**
- `course/capstone/README.md` — Capstone 项目说明（先建占位）
- `docs/specs/2026-06-30-course-teaching-redesign.md` — 本 spec

**Key changes:**
- 引入叙事线："本地论文研究助手"
- 拆散 Core Objects 表格，改为边写代码边引入对象
- Lab 从粘贴验证改为 Follow → Modify → Design + 反馈闭环
- 增加 event flow timeline ASCII 图
- 增加 `[DD]` / `[TRAP]` / `[BIG]` callout

### Phase R2: Part 2 Restructuring (Ch02)

**Files to rewrite:**
- `course/chapters/02-research-core-foundations.md`
- `course/labs/02-source-evidence-claim-lab.md`
- `course/solutions/02-source-evidence-claim-solution.md`

**Key changes:**
- Problem hook: "Agent 说的话找不到出处"
- 证据链作为侦探故事讲述（Source = 案发现场，Evidence = 证物，Claim = 结论）
- 三阶练习 + 反馈闭环：L1（构建证据链）→ L2（加入假 evidence）→ L3（给论文 fixture，自己建 source/evidence/claim）
- 加入 Data Flow Diagram（SourceInput → Source → Evidence → Claim → Report → ClaimSourceLink）

### Phase R3: Part 3 Restructuring (Ch03)

**Files to rewrite:**
- `course/chapters/03-memory-and-skills.md`
- `course/labs/03-memory-skill-runtime-lab.md`
- `course/solutions/03-memory-skill-runtime-solution.md`

**Key changes:**
- Problem hook: "Agent 不记得上次查过什么"
- Memory 用"Agent 的笔记本"类比，Skills 用"Agent 的技能包"类比
- 三阶练习中 L3 要求设计一个 memory policy
- 增加 Memory flow diagram

### Phase R4: Part 4 Restructuring (Ch04)

**Files to rewrite:**
- `course/chapters/04-multi-agent-delegation.md`
- `course/labs/04-delegation-runtime-lab.md`
- `course/solutions/04-delegation-runtime-solution.md`

**Key changes:**
- Problem hook: "一篇综述需要查 5 个方向，Agent 一个人太慢"
- Delegation 用"主编把任务分给记者"类比
- 重点教 child context isolation 的设计逻辑
- L3：给需求，自己设计 delegation task 和 role

### Phase R5: Part 5 Restructuring (Ch05)

**Files to rewrite:**
- `course/chapters/05-workbench-product.md`
- `course/labs/05-workbench-product-lab.md`
- `course/solutions/05-workbench-product-solution.md`

**Key changes:**
- Problem hook: "研究者说'我看不懂代码，给我一个界面'"
- Workbench UI 作为"研究者的仪表盘"讲述
- 强调 product adapter 的设计决策（为什么不把 FastAPI 塞进 runtime）
- L3：给 Workbench 加一个新 panel

### Phase R6: Part 6 Restructuring (Ch06)

**Files to rewrite:**
- `course/chapters/06-framework-comparisons.md`
- `course/labs/06-framework-comparisons-lab.md`
- `course/solutions/06-framework-comparisons-solution.md`

**Key changes:**
- Problem hook: "别人问你'为什么不用 LangChain'——你怎么回答？"
- 框架对比作为"你在做技术选型"的场景
- Comparison matrix 作为决策工具讲授

### Phase R7: Part 7 Restructuring (Ch07)

**Files to rewrite:**
- `course/chapters/07-production-readiness.md`
- `course/labs/07-production-readiness-lab.md`
- `course/solutions/07-production-readiness-solution.md`

**Key changes:**
- Problem hook: "你的 Agent 要在团队服务器上跑了——它安全吗？"
- Production readiness 作为"上线前的检查清单"讲述
- Policy decisions 作为"安全守门人"类比

### Phase R8: Capstone Project

**New files:**
- `course/capstone/README.md` — 模拟真实产品需求文档
- `course/capstone/rubric.md` — 6 个 success criteria 的评分标准
- `course/capstone/paper_fixtures/` — 离线论文数据集（JSON）
- `course/capstone/starter/agent_starter.py` — 教学 starter code
- `course/capstone/starter/test_starter.py` — starter 的测试骨架
- `course/capstone/solution/agent.py` — 完整参考 solution
- `course/capstone/solution/test_run.py` — 一次完整运行的脚本
- `course/capstone/solution/trajectory.jsonl` — 示例运行轨迹
- `course/capstone/solution/report.md` — Agent 产出的示例研究报告
- `course/capstone/solution/reflection.md` — 设计决策复盘

### Phase R9: Reference & Support Materials

**New files:**
- `course/reference/common-patterns.md` — 常见 Agent 设计模式
- `course/reference/troubleshooting.md` — 常见错误和修复指南
- `course/reference/design-decisions-index.md` — 所有 `[DD]` callout 的索引
- `course/reference/discussion-prompts.md` — 每章的讨论题（self-study 或团队用）

**Updates:**
- `course/reference/agent-kernel-glossary.md` — 补充新引入的术语

## Design Decisions For This Redesign

### DD1: Rewrite teaching layer only; no runtime/product code changes

**Decision**: 本次改造不改动 `packages/research_core`、`apps/api`、`apps/web` 中的任何代码。只改 `course/` 下的 markdown 文件和 `docs/` 下的文档。教学示例代码（如 capstone starter/solution）放在 `course/capstone/` 下，作为课程材料而非产品代码。

**Why**: Runtime/product 代码已经通过测试且架构正确。问题是教法不是实现。分离关注点，避免引入新的 bug。Capstone 的 starter/solution 代码是课程交付物的一部分——就像 lab solution 里一直有代码示例一样——但它们是教学 artifact，不进入 `packages/` 或 `apps/` 的产品路径。

### DD2: Narrative is "本地论文研究助手" not "generic Agent platform"

**Decision**: 用一个具体的业务场景（论文研究助手）贯穿始终。场景灵感来自 Semantic Scholar 的产品形态（论文搜索 + 引用追踪 + 文献综述），但**完全离线运行**——所有 paper 数据是静态 JSON fixture，检索使用 `FakeRetriever`，模型使用 `FakeModel`，不调用任何外部 API。

**Why**: 通用平台没有故事张力。论文研究助手是一个真实的、有价值的、能展示的用例。同时和现有代码（`research_core`）完全对齐。明确的"离线本地"限定避免了学习者误以为需要 API key 或真实论文数据库。

### DD3: ASCII diagrams over image files

**Decision**: 所有图表使用 ASCII art，不引入图片。

**Why**: 保持离线可运行、git-friendly（diff 可见）、terminal 友好。ASCII art 的"简陋"反而降低了学习者自己画图的障碍——他们会觉得"我也可以画"。

### DD4: Three-tier exercises, not progressive difficulty per chapter

**Decision**: 每章内部有三阶练习（Follow/Modify/Design），而不是"前面的章节简单，后面的难"。

**Why**: 不同背景的学习者可以在同一章找到合适的难度。纯新手做 L1，有经验的做 L2-L3。这也让同一章可以服务 Beginner Track 和 Engineer Track。

### DD5: Sidebar callouts inline, with ASCII tag as primary marker

**Decision**: Design Decision、Common Trap 等用 markdown blockquote 内联在正文中。主标记使用 ASCII tag（`[DD]`、`[TRAP]`、`[CHECK]`、`[BIG]`、`[DEEP]`），emoji 作为可选视觉增强。

**Why**: 单独文件会增加跳转成本，inline 让阅读流不断。ASCII tag 在 terminal、git diff、纯文本编辑器中都是稳定可检索的标记。Emoji 在 GitHub/VS Code 等渲染环境中提升可读性，但不应成为唯一的标记方式。

### DD6: Files keep chapter/ naming, content uses Part/ naming

**Decision**: 文件名保留 `chapters/00-07` 不变；文档内标题和引用使用 "Part 1" 到 "Part 7"。

**Why**: 重命名文件会造成大范围的 import、链接、index 更新，纯 churn。内容和结构的逻辑重组不需要通过文件名体现。

## Quality Gates

改造完成后，每个 Phase 需要通过以下 gate：

1. **Teaching flow gate**: Part 是否完整经历了一次 Problem → Build → Inspect → Break → Fix → Reflect 循环？Build/Break Section 是否走了全部 8 步？
2. **Exercise gate**: 每个 Part 是否有 L1/L2/L3 三个阶梯的练习？每个练习是否有 Common Errors / Failure Output / Where To Go Back / Why Correct？
3. **Narrative gate**: 是否能清晰解释该 Part 如何推进本地论文研究助手的能力？
4. **Visual gate**: 是否有至少 2 个 ASCII 图表？
5. **Sidebar gate**: 是否有至少 3 个 `[DD]` / `[TRAP]` callout？
6. **Docs sync gate**: 是否更新了 `course/README.md`、`docs/course/roadmap.md`、`docs/README.md` 和 `docs/progress/` 中相关条目？如果没有改，是否有明确的 deferral 记录？
7. **Test gate**: `uv run pytest -q` 和 `uv run ruff check .` 通过
8. **Offline gate**: 所有示例无需 API key 可运行

## Appendix: Chapter Template (New)

替换现有的 `docs/course/chapter-template.md`：

```markdown
# Part N: [能力名称]

## 你的本地论文研究助手现在需要 [新能力]

[一句话描述这个 Part 解决什么问题，在叙事线中的位置]

> [BIG] **大局观**：[这个 Part 在整个系统中的位置]

```
[ASCII Architecture Map — 当前 Part 高亮]
```

## Section 1: [概念名称] — 为什么需要这个

### Problem Hook
[具体场景，让学习者先感受痛点]

### Explore
[试一下现有方案，看它哪里不够]

### 概念：人话版
[2-3 个新概念，用类比解释]

> [CHECK] **检查一下**：[用自己的话解释]

### 你的第一个 [概念]
[最小可运行代码，学习者 L1 Follow]

### Inspect The Trail
[看 event sequence / data flow]

> [DD] **设计决策**：为什么选择这个接口/边界？
>
> **选了**：[描述]
> **没选**：[替代方案]
> **因为**：[取舍理由]

## Section 2: [更深的概念]

### Build: [实现某个具体机制]

> L1 Follow 练习

[代码骨架，学习者填入关键部分]

#### 🔍 练习反馈

**常见错误**：
1. [错误 1] — 原因：[...]
2. [错误 2] — 原因：[...]

**如果输出不对**：检查 event sequence 的第二项是不是 `model_response`。如果不是，回到 Section 1 的 "Inspect The Trail"。

**卡住了？**回到正文 "[具体段落名]" 重读 [具体概念]。

### Modify: [改一行，预测结果]

> L2 Modify 练习

[修改任务]

> [TRAP] **常见陷阱**：[初学者在这里容易犯的错]

#### 🔍 练习反馈

**如果输出和预期不一样**：[排查步骤]

**正确答案为什么对**：[排除了哪种错误理解]

### Break It
[故意弄坏 — 具体的破坏指令]

### Fix It
[诊断和修复 — 不给答案，给方向]

#### 🔍 练习反馈

**如果还是不对**：[回到正文哪一段]

## Section 3: 接入你的 Workbench

[这个能力在 UI 上如何体现]

## Section N: Eval Gate

[通过标准]
[具体命令]

## Checkpoint

> L3 Design 练习

[给需求描述，不给代码骨架]

#### 🔍 练习反馈

**常见设计错误**：
1. [设计错误 1] — 为什么它看起来对但其实有问题：[...]

**自查**：你的实现是否通过了 eval gate 的所有 assert？

### Reflection

[2-3 个设计决策相关的开放问题]
[1-2 个 discussion 问题，适合 self-study 或团队讨论]

---

**完成这个 Part 后，你的本地论文研究助手现在可以 [新能力]。**

**Next: [下一个 Part 的 teaser — 一句话预告下一个痛点]**
```

## Summary

这次改造的核心是一个公式：

```
现有课程 = 正确的技术内容 + 错误的教学方式
改造     = 相同的 runtime/product 代码 + 项目驱动的教学方式
         + 三阶练习 + 反馈闭环 + 视觉化 + 设计决策教学 + 叙事线 + Capstone
```

9 个 implementation phase（R1-R9）：
- R1-R7 重写现有 8 个 chapter 为 7 个 Part（Ch00+01 合并为 Part 1）
- R8 新建 capstone 项目
- R9 补充参考材料

不改动 `packages/` 和 `apps/` 下的产品代码。教学用示例代码（capstone starter/solution）放在 `course/capstone/` 下。改造完成后，课程从 "能学到东西的技术文档" 升级为 "真的能教会人的 Agent 工程课程"。
