# Agent Kernel Glossary

这页用人话解释课程会遇到的词。先有感觉，再看代码。  
Part 1 术语在前；Parts 2–7 与 Capstone 术语按主题接在后面。

相关材料：[common-patterns.md](common-patterns.md) · [design-decisions-index.md](design-decisions-index.md) · [troubleshooting.md](troubleshooting.md) · [discussion-prompts.md](discussion-prompts.md)

---

## Part 1 — Kernel

### Agent

Agent 不是一个神秘的大脑。这里的 Agent 是一段 runtime：它把用户问题交给 model，必要时调用 tool，把结果再交回 model，最后产出答案。

本项目里，Agent 的核心不是“聪明”，而是“可观察、可测试、可复盘”。

### Model

Model 是生成文本的东西。真实项目里它可能是 OpenAI、Anthropic、本地模型或别的 provider。课程里先不用真实模型，而是用 `FakeModel`。

### FakeModel

`FakeModel` 是一个离线模型替身。你提前告诉它第一步返回什么、第二步返回什么，它就照着返回。

这让课程和测试不依赖网络、不依赖 API key，也不会因为真实模型输出漂移而得到不同答案。

### Message / AgentMessage

Message 是对话里的一个片段。代码里用 `AgentMessage` 表示**内部** message。它不是 OpenAI message，也不是 Anthropic message。这样以后换 provider 时，核心 runtime 不需要跟着大改。

### Role（message role）

Role 表示一条 message 的身份：

- `system`: 系统规则。
- `user`: 用户输入。
- `assistant`: 模型或 Agent 的回复。
- `tool`: tool 执行后的观察结果。

（注意：Part 4 的 `AgentRolePolicy` 是**另一个“角色”概念**——委派工牌，不是 message role。）

### System Prompt

System prompt 是系统给 Agent 的最高层指令。`ContextBuilder` 会保证 system prompt 只能从一个入口进入，避免调用方偷偷塞第二条 system message。

### Context / ContextBuilder

Context 是一次 model request 看到的全部 message。`ContextBuilder` 负责组装它。

### Tool / ToolDefinition / ToolRuntime

Tool 是 Agent 可以调用的函数。`ToolDefinition` 描述名字与 handler；`ToolRuntime` 负责注册与执行。

### Tool Call

Model 发出的“我要调用这个工具”的请求。课程约定 content 为 JSON 字符串：

```json
{
  "tool_call": {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"}
  }
}
```

这不是所有框架通用的格式，而是本课程的最小协议。

### Tool Result

Tool 执行后的结果。AgentRunner 会把它追加成 `tool` message，供下一次 model request 观察。它**不是**最终答案。

### RunEvent / Event Sequence / Trajectory

- `RunEvent`：中间发生了什么（model_request、tool_call、error…）。
- Event sequence：事件类型顺序；比只看最终答案更可靠。
- Trajectory：一次 run 的行车记录（顺序 + 关键 payload）。

### JSON-Compatible

数据能安全变成 JSON：str/number/bool/list/dict 通常可以；`set` 不行。Tool args、event payload、Workbench record 都要尽量 JSON-compatible。

### Immutable

创建后不应随便改。message、event、tool call/result 倾向 immutable，轨迹才像证据。

### Eval Gate

每章用来证明“机制还正常”的检查（测试命令、event sequence、docs freshness 等）。

### AgentRunner

编排 think-act-observe 循环的核心对象：请求 model、解析 tool call、执行 tool、写 events、产出最终消息。

---

## Part 2 — Research Core

### Source / SourceInput / SourceIngestor

- `SourceInput`：待摄入的原始输入（本地 fixture 路径、元数据等）。
- `SourceIngestor`：把输入变成稳定的 `Source`（含 id、title、uri 等）。
- `Source`：证据链的根节点之一。

### FakeRetriever / SearchResult

离线检索替身。返回的 `SearchResult` 带排名信息，**只是检索视图**，不是证据本身。

### Evidence

带 `quote`、`source_id`、`location`（等）的摘录对象。证明“原文哪里说过”。

### Claim

研究报告中的**主张**，通过 `evidence_ids` 指向证据，而不是把原文 paste 进 `text`。

### Report

Claims 的集合/容器，面向“写给用户看的研究结论结构”。

### ClaimSourceLink

把 claim 映射回 source 的可序列化记录（常经 `build_claim_source_links` 生成）。Workbench 与审计吃这种 record。

### Evidence Chain

`Source → Evidence → Claim → Report → ClaimSourceLink` 的完整可审计路径。

---

## Part 3 — Memory & Skills

### MemoryEngine

本地确定性记忆引擎：write / list / recall 等。不自动往 AgentRunner 塞 RunEvent。

### MemoryRecord

一条记忆的数据对象（kind、content、importance、metadata…）。

### MemoryWritePolicy / MemoryRecallPolicy

写与召回前的策略对象：allowlist、过滤、限制。Policy 决策后，Engine 才动作。

### list vs recall

- `list`：notebook 式枚举/查看。  
- `recall`：按 policy 过滤后的“想起来的子集”。

### Skill package / SKILL.md / manifest

文件夹形态的技能包：manifest 描述技能，细节在 references 里。

### SkillRuntime

`load` 技能包；`read_reference` 按需读取细则。**Progressive disclosure**：先目录后正文。

### MEMORY_* / SKILL_* event types

`RunEventType` 枚举里的名字。存在 ≠ 自动发射。要进 trail 需编排层显式 append。

---

## Part 4 — Delegation

### AgentRolePolicy

Child/parent 的“工牌”：可声明 `tool_names`、`skill_names`、`memory_kinds`、`max_steps` 等。  
**声明 ≠ 全部自动 enforce。**

### filter_tools_for_role

按角色 allowlist 过滤工具名的辅助函数。工厂必须用它的结果去 `register`，否则 child 仍可能拿到多余工具。

### DelegationTask / compile_child_prompt

委派任务对象；compiler 生成 child 真正可见的 prompt/context。`task.metadata` 存在不代表 child 可见。

### DelegationBudget

限制 child runs / per-child steps / total steps。超预算应失败可见。

### DelegationRuntime

执行委派、记账、写 parent 侧 `delegate_*` 事件的 runtime。当前课程路径是**本地 deterministic**，不是真实并发集群。

### Parent / Child run

Parent 编排；Child 是隔离的一次（或多次）子 run。用 event trail 证明边界。

---

## Part 5 — Workbench Product

### Workbench

产品界面：FastAPI 提供 snapshot API，React 渲染多面板（timeline、evidence、report、memory、skills、delegation、eval…）。

### WorkbenchSnapshot

一次可展示的产品状态快照：由 adapters 组装，带引用完整性校验，再 `to_record()` 成 JSON。

### from_* adapters

如 `from_event`、`from_source`、`from_evidence`、`from_report`、`from_memory_record`…  
唯一推荐的 domain → 面板项路径。手搓面板项 = 第二套数据模型。

### Referential integrity

Snapshot 内 ID 交叉引用必须完整（无孤儿 claim/evidence/run）。

### summary_row / to_record

面向 UI/API 的投影与序列化。UI 应依赖 record 形状，而不是 Python 对象图。

### Fallback fixture

API 不可用时 UI 使用的本地假数据；**必须与真实 API record 同形**。

---

## Part 6 — Framework Comparisons

### FrameworkProfile

某候选框架/方案的 **deterministic 能力画像记录**，不是第三方 SDK wrapper。

### Pinned harness

固定 task + fixture + metrics，使比较可复现。

### Weighted score / strengths / tradeoffs

透明权重下的得分；`strengths` 通常要求高分阈值（如 ≥0.80）**且**该维在 weights 中；弱项记 tradeoffs。

### Build vs adopt

自研 handwritten runner 基线 vs 采用外部框架的决策过程；课程练的是方法，不是安利某一家。

---

## Part 7 — Production Readiness

### RunDiagnostics

从 events 汇总的目录/摘要（计数、标志）。**不是**完整 trail 的替代品。

### JsonlRunEventStore

把 events 以 JSONL 落盘，支持按 run 回放与 `list_run_ids`。

### ApprovalPolicy / ApprovalDecision

按工具名等规则给出 allow / deny / require_approval 等**决策**；调用方负责执行。

### SandboxPolicy

路径、网络、runtime 等边界策略。提供 `path_decision` / `network_decision` / `runtime_decision` 等。

### runtime_decision / max_runtime_seconds

`max_runtime_seconds` 是可检查上限；`runtime_decision(elapsed)` 返回是否允许继续。  
**AgentRunner 不会自动 kill。**

### Docs freshness

文档索引链接的路径必须真实存在；课程用测试门禁防止“文档指向幽灵文件”。

### Local-first production contract

先本地纯 Python 对象证明回放与边界，再让云/DB/网页审批包住这些 contract。

---

## Capstone

### Capstone

Parts 1–7 的整合项目：完整离线本地论文研究助手。材料在 `course/capstone/`（fixtures、starter、solution、rubric、reflection…）。

### Starter / Solution

- Starter：学员填写的脚手架（测试可 skip-until-implemented）。  
- Solution：参考实现 + 诚实边界示范。

### Rubric

评分维度：证据链、memory/skill、delegation（若用）、Workbench、production trust evidence、reflection 等。

### production_boundary

Capstone 中显式收集 diagnostics、JSONL、approval、sandbox、`runtime_decision` 等信任证据的步骤/返回结构。

### Reflection（chose / rejected / because）

决策叙事模板：选了什么、否决了什么、为什么。用于证明工程判断，而不只是代码能跑。

### Honesty boundary

文档/实现必须承认的限制：角色字段不自动 enforce、MEMORY/SKILL event 不自动、max_runtime 仅 inspectable 等。禁止用假 event 粉饰。

---

## Workbench（产品名，跨 Part）

Workbench 是这个项目的产品界面。Phase 5 起有本地版本：FastAPI `/api/workbench/snapshot` + React 面板。底层 timeline 仍来自 Part 1 的 `RunEvent`；Part 5 解释如何变成 snapshot record；Part 7 的 production 证据也可被面板消费。

---

## 易混词对照

| 词 A | 词 B | 差别一句话 |
| --- | --- | --- |
| Message role | AgentRolePolicy | 对话身份 vs 委派工牌 |
| Tool result | Final answer | 中间观察 vs 最终 assistant 文本 |
| SearchResult | Evidence | 排名命中 vs 带出处摘录 |
| Claim.text | Evidence.quote | 主张 vs 原文摘录 |
| list | recall | 全本浏览 vs 策略过滤召回 |
| skill_names 声明 | SkillRuntime.load | 工牌标签 vs 真加载 |
| RunDiagnostics | RunEvent trail | 目录摘要 vs 完整过程 |
| max_runtime_seconds | 自动超时杀进程 | 配置上限 vs 需 runtime_decision + 编排执行 |
| FrameworkProfile | 第三方 SDK | 选型记录 vs 真依赖 |
| Hand-built Workbench item | from_* | 第二套模型 vs 唯一适配路径 |
