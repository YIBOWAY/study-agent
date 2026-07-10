# Design Decisions Index

本页索引课程中所有重要的 **`[DD]` 设计决策** 与配套 **`[TRAP]` 诚实边界**。  
用途：复习时按主题跳转；写 Capstone reflection 时对照 “chose / rejected / because”。

图例：

- **DD** = 为什么这样设计
- **TRAP** = 容易误读成“框架已经自动做了”的边界

---

## Part 0 / Setup — 心智模型

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | `AgentMessage` 不是 provider message | `chapters/00-before-agent-kernel.md` | 内部消息模型与 OpenAI/Anthropic 解耦，换 provider 不掀桌 |
| DD | 学习阶段先用 `FakeModel` | 同上 | 离线、确定、可测；先学协议再学模型智商 |

---

## Part 1 — Agent Kernel

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | 自定义 JSON tool-call 格式，而非直接绑 OpenAI function calling | `chapters/01-agent-kernel-foundations.md` | 最小协议讲清 think-act-observe；provider 格式是 adapter 的事 |
| DD | `AgentRunner` 不在调用前把工具存在性预先吞掉 | 同上 | 失败应进入可观察路径，而不是静默“没发生” |
| TRAP | FakeModel 的 tool call 是 JSON 字符串，不是 Python dict | 同上 | `content=json.dumps(...)` |
| TRAP | tool result ≠ model response | 同上 | tool 是观察；final answer 是后续 model 文本 |
| TRAP | `records[i]["payload"]` 与 `events[i].payload` 不是同一种索引对象 | `labs/01-agent-runner-lab.md` | 先对齐结构再比字段 |

---

## Part 2 — Research Core

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | 先用本地 fixture 与 `FakeRetriever` | `chapters/02-research-core-foundations.md` | 证据链可测优先于“真的联网搜到论文” |
| DD | 不把 quote 直接塞进 `Claim.text` | 同上 | 主张与摘录分层，映射可审计 |
| DD | Workbench 消费 `ClaimSourceLink.to_record()` 这类普通 record | 同上 | 产品层吃 JSON-compatible 记录，不吃私有对象图 |
| TRAP | source ID 不是装饰 | 同上 | ID 是引用完整性的键 |
| TRAP | 搜索排名不是证据链 | 同上 | hit score ≠ cited evidence |

---

## Part 3 — Memory & Skills

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | 先做确定性本地 memory 与 folder skill runtime | `chapters/03-memory-and-skills.md` | 先看清 write/recall/load 边界，再谈 DB / marketplace |
| TRAP | MEMORY_*/SKILL_* 枚举存在但不会自动发射 | 同上 | Engine/Runtime 独立；要进 trail 需显式 append |
| TRAP | list 和 recall 不是一回事 | 同上 | recall 受 policy 过滤 |

---

## Part 4 — Multi-Agent Delegation

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | 不做真实并发 / 远程 worker，先本地 deterministic contract | `chapters/04-multi-agent-delegation.md` | 边界不清时上 async 只会放大混乱 |
| TRAP | `tool_names` / `skill_names` / `memory_kinds` 不自动 enforce | 同上 | 真 enforce：`max_steps` + budget；工具需 `filter_tools_for_role` |
| TRAP | `task.metadata` 存在 ≠ child 可见 | 同上 | 看 `compile_child_prompt` / child MODEL_REQUEST |

---

## Part 5 — Workbench Product

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | `research_core` 不能 import FastAPI 或 React | `chapters/05-workbench-product.md` | 产品契约在 `research_core.product`；web 是可替换外壳 |
| DD | fallback fixture 必须与 API record 同形 | 同上 | UI 依赖形状契约，不是某一份假数据 |
| TRAP | 不要手搓面板项绕过 `from_*` | 同上 | 手搓 = 发明第二套数据模型 |
| TRAP | lab 再次强调手搓 `WorkbenchEvidenceItem` 的失败模式 | `labs/05-workbench-product-lab.md` | 与 chapter TRAP 同一条 |

---

## Part 6 — Framework Comparisons

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | `FrameworkProfile` 是 deterministic 记录，不是第三方 wrapper | `chapters/06-framework-comparisons.md` | 不把 LangGraph/CrewAI 拖进依赖树也能练判断 |
| DD | 比较代码留在课程目录；真接入是独立 phase | 同上 | adapter 住 core 外，自带测试与文档 |
| TRAP | strengths ≠ “分数最高的几科” | 同上 | 需 ≥0.80 **且** 在 weights 里 |

---

## Part 7 — Production Readiness

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| DD | production contract 先做本地离线 Python 对象 | `chapters/07-production-readiness.md` | 云日志/DB/网页审批应包住 contract，而不是藏规则 |
| DD | production contract 仍不 import FastAPI/React/DB/云 SDK | 同上 | 纯 Python 测试必须能跑通 |
| TRAP | `RunDiagnostics` 不是替代 event trail | 同上 | 它是目录与摘要 |
| （延伸 TRAP） | `max_runtime_seconds` inspectable only | Capstone + production API | 必须 `runtime_decision`；runner 不自动 kill |

---

## Capstone

| 类型 | 标题 | 位置 | 一句话 |
| --- | --- | --- | --- |
| TRAP | Skill/memory role fields are not auto-enforced | `capstone/README.md` | 工厂显式接线 |
| TRAP | MEMORY_*/SKILL_* events are not automatic | 同上 | 不伪造 event |
| TRAP | max_runtime_seconds is inspectable, not auto-killed | 同上 | 调用 `runtime_decision` |
| DD | Capstone stays on handwritten research_core contracts | 同上 | 教学整合，不是新产品包 |
| Reflection 模型 | chose / rejected / because | `capstone/solution/reflection.md` | 决策叙事模板 |

### Capstone 与 Parts 的决策映射（写 reflection 时用）

| 你想证明的能力 | 应对齐的 DD/TRAP |
| --- | --- |
| 可观察 loop | Part 1 DD/TRAP |
| 引用可审计 | Part 2 DD：quote≠claim；排名≠证据 |
| 记忆不污染 | Part 3 write policy；非自动 event |
| 委派不越权 | Part 4 filter_tools_for_role；metadata 不可见性 |
| UI 不发明模型 | Part 5 from_*；fixture 同形 |
| 选型可复现 | Part 6 pinned harness |
| 可回放可审批 | Part 7 diagnostics/JSONL/approval/sandbox + runtime_decision |
| 组合而非复制 | Capstone DD：public contracts only |

---

## Cross-cutting Themes

把分散的 DD 收成五条主线，便于口头解释整个项目：

1. **离线确定性优先**  
   FakeModel、FakeRetriever、FrameworkProfile、本地 production 对象。

2. **可观察性优先于“看起来聪明”**  
   RunEvent、error 不静默、diagnostics 不替代 trail。

3. **分层与映射，不把概念揉成一坨**  
   Message≠provider message；Search≠Evidence；Claim≠quote；list≠recall；diagnostics≠events。

4. **声明 ≠ 执行**  
   role 字段、skill_names、memory_kinds、max_runtime 配置，都要问：谁 enforce？

5. **依赖方向单向向下**  
   core ← product adapters ← API/UI；比较/Capstone 代码不污染 core。

---

## How to use this index in study

1. 每学完一个 Part，用本页核对自己能否用一句话复述该 Part 的 DD。  
2. 做 lab Break 题时，先猜会踩哪条 TRAP，再跑代码验证。  
3. Capstone reflection 至少覆盖 3 条跨 Part 决策，并显式写出 rejected 方案。  
4. 若文档与代码冲突，以**测试与当前 public API**为准，并开 issue/改文档（neat-freak）。

更多模式级总结见 [common-patterns.md](common-patterns.md)；排障见 [troubleshooting.md](troubleshooting.md)；讨论题与参考答案见 [discussion-prompts.md](discussion-prompts.md)。
