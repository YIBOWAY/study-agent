# Discussion Prompts（含参考答案与解析）

用法：

- **自学**：先自己写答案，再对参考答案。
- **小组**：一人主答，一人当“诚实边界检查员”，专挑神话（自动 kill、自动 MEMORY event 等）。
- **评分**：不要求与参考答案字面一致；要求抓住机制、诚实边界与常见错法。

相关材料：[design-decisions-index.md](design-decisions-index.md) · [common-patterns.md](common-patterns.md) · [troubleshooting.md](troubleshooting.md)

每题结构：**题干 → 参考答案 → 解析**。

---

## Part 1 — Agent Kernel

### Q1.1 为什么最终答案正确，仍可能判定这次 Agent run 失败？

**参考答案**  
因为课程用 **event trail / trajectory** 证明过程，不只信 final message。例如：工具名拼错后靠硬编码文本“碰巧”答对；或 tool 根本没跑、中间 error 被吞掉。只要 sequence 不是期望的 `model_request → model_response → tool_call → tool_result → …`，工程上仍算失败。

**解析**  
- 对应 Pattern：Event Trail as Evidence。  
- 常见错法：只 `assert result.message.content == "期望字符串"`。  
- 关联 DD/TRAP：AgentRunner 不静默预吞未知 tool；tool result ≠ final answer。

### Q1.2 FakeModel 的 tool call 为什么必须是 JSON 字符串而不是 Python dict？

**参考答案**  
课程协议把 tool call 放在 **assistant message 的 content 文本**里，形状是 `{"tool_call": {...}}` 的 JSON。`FakeModel` 模拟的是“模型返回字符串”，不是直接返回 Python 对象。传 dict 会绕过真实序列化/解析路径，测试会绿、上线真模型会碎。

**解析**  
- 常见错法：`FakeModelResponse(content={"tool_call": ...})`。  
- 正确：`content=json.dumps({...})`。  
- 关联 TRAP：FakeModel tool call 是 JSON 字符串。

### Q1.3 `AgentMessage` 与 OpenAI/Anthropic message 为什么要分开？

**参考答案**  
内部消息模型应与 provider 解耦。Kernel 只认识 `system/user/assistant/tool` 与 content 协议；provider adapter 负责双向翻译。否则换模型供应商就要改 AgentRunner。

**解析**  
- DD：AgentMessage 不是 provider message。  
- 延伸：tool-call JSON 也是“教学最小协议”，不是绑死某一家 function calling API。

### Q1.4 未知工具名时，为什么不在调用前静默 return，而要让失败进入 event？

**参考答案**  
静默失败会让调用方只看到“没有答案/空结果”，无法审计。让 `ToolRuntime` 在调用时失败并留下 `error` event（或挂在异常的 `events` 上），才符合 fail-closed + 可观察。

**解析**  
- DD：不预吞工具存在性。  
- 排障：见 troubleshooting B4。

---

## Part 2 — Research Core

### Q2.1 搜索结果第一名是否等于报告里的证据？为什么？

**参考答案**  
不等于。`SearchResult` / ranking 只是检索视图；证据是带 `source_id`、`quote`、`location` 的 `Evidence`。报告中的 `Claim` 必须通过 `evidence_ids` 映射，再经 `ClaimSourceLink` 连回 source。

**解析**  
- TRAP：搜索排名不是证据链。  
- 常见错法：把 hit 标题直接当 claim，或把 quote 写进 `Claim.text`。

### Q2.2 为什么不能把 quote 直接塞进 `Claim.text`？

**参考答案**  
Claim 是**主张**，Evidence 是**摘录**。混在一起会丢失：同一 claim 多证据、同一 quote 支撑多 claim、出处审计与改写边界。映射层 `build_claim_source_links` 需要分层才能 fail-closed 检查缺失 ID。

**解析**  
- DD：不把 quote 塞进 Claim.text。  
- Capstone L2 要求能从 claim 反查 source。

### Q2.3 为什么 source ID “不是装饰”？

**参考答案**  
下游 evidence / claim / link / Workbench 全部用 ID 做引用完整性。ID 变了，整条链断裂；测试与 UI 会出现孤儿引用。

**解析**  
- TRAP：source ID 不是装饰。  
- 实践：fixture 固定 id；ingest 策略要稳定。

### Q2.4 为什么 Part 2 坚持 FakeRetriever + 本地 paper fixtures？

**参考答案**  
先证明**证据链协议**可测、可复盘。真联网检索的噪声、配额、抖动会掩盖映射 bug。真检索应是 core 外的 adapter。

**解析**  
- DD：先用本地 fixture。  
- 与 Part 1 FakeModel 同一条“离线确定性优先”主线。

---

## Part 3 — Memory & Skills

### Q3.1 为什么 `list` 有记录，`recall` 可能为空？

**参考答案**  
`list` 是 notebook 视图；`recall` 受 `MemoryRecallPolicy`（kind、query、limit、importance 等）过滤。两者职责不同，不能互相替代。

**解析**  
- TRAP：list ≠ recall。  
- 常见错法：用 list 结果假装“Agent 已经想起了”。

### Q3.2 写了 memory，为什么 event trail 里没有 `memory_write`？

**参考答案**  
`MemoryEngine` 是独立组件；`RunEventType` 里有 MEMORY_* **不等于自动发射**。要进 trail 必须由编排层显式 append。Capstone 诚实要求：**不要伪造**这些 event。

**解析**  
- TRAP：MEMORY_*/SKILL_* 不自动。  
- 神话清单第一名：看到枚举就以为 runtime 已接线。

### Q3.3 Progressive disclosure 解决什么问题？Skill 会自动灌进 child 吗？

**参考答案**  
解决“整本手册塞 system prompt”的成本与不可测。正确路径：`SkillRuntime.load` → 需要时 `read_reference`。`AgentRolePolicy.skill_names` **不会**自动 load skill。

**解析**  
- Pattern：Progressive Disclosure Skills。  
- Capstone：citation-check skill 需显式接线。

### Q3.4 `MemoryWritePolicy` 拒绝写入时，应该“放宽到全开”吗？

**参考答案**  
一般不应。应理解拒绝原因（kind allowlist、importance、长度、forbidden phrase），在**保留防护**的前提下调整 policy 或清洗 content。全开等于取消 Part 3 的课。

**解析**  
- Pattern：Policy Before Side Effect。  
- 产品上：污染记忆比少记一条更贵。

---

## Part 4 — Multi-Agent Delegation

### Q4.1 角色工牌写了 `tool_names=("retriever.search",)`，child 是否自动只能用这些工具？

**参考答案**  
**不会自动。** `DelegationRuntime` 不按 `tool_names` 过滤 ToolRuntime。工厂必须 `filter_tools_for_role(...)` 后再 `register`。当前真正 enforce 的主要是 `max_steps` 与 `DelegationBudget`；`skill_names` / `memory_kinds` 仍是声明。

**解析**  
- TRAP：role 字段不自动 enforce。  
- Capstone solution 的 child_factory 是标准答案形状。

### Q4.2 为什么不能把 parent 的完整 transcript 丢给 child？

**参考答案**  
会泄漏 parent-only system 规则、预算外工具线索、无关噪声，破坏隔离与审计边界。child 可见输入应由 `compile_child_prompt`（或等价 compiler）显式产生。

**解析**  
- Pattern：Child Context Isolation。  
- Break 练习：故意泄漏后看 child 是否遵循 parent-only 规则。

### Q4.3 `task.metadata` 里的字段 child 一定看得到吗？

**参考答案**  
不一定。metadata 是否进入 child 取决于 compiler。判断可见性应检查 **compiled prompt / child MODEL_REQUEST payload**，而不是“字段在 task 对象上存在”。

**解析**  
- TRAP：metadata 存在 ≠ 可见。  
- 常见错法：把关键指令只塞 metadata，却从不编译进去。

### Q4.4 为什么 Part 4 先不做真实并发 / 远程 worker？

**参考答案**  
边界（隔离、预算、事件、冲突可见性）未清时，async 只会放大混乱与 flaky。先本地 deterministic contract，再谈并发。

**解析**  
- DD：先本地 deterministic。  
- 与“离线确定性优先”一致。

---

## Part 5 — Workbench Product

### Q5.1 为什么禁止手搓 `WorkbenchEvidenceItem(...)` 绕过 `from_*`？

**参考答案**  
手搓等于发明**第二套数据模型**，ID/字段极易与 domain 不一致，破坏 referential integrity，UI 会“看起来有数据”却不可审计。正确路径：domain → `from_*` → `WorkbenchSnapshot` → `to_record()`。

**解析**  
- TRAP：不要手搓面板项。  
- Pattern：Adapter-only Product Surface。

### Q5.2 为什么 `research_core` 不能 import FastAPI 或 React？

**参考答案**  
保持依赖方向：core ← product adapters ← API/UI。core 保持可离线测试；web 是可替换外壳。规则散进框架 import 后，课程与 CI 无法纯 Python 证明边界。

**解析**  
- DD：core 不 import web 框架。  
- 同 Part 7 production contracts。

### Q5.3 fallback fixture 与 API record 为什么必须同形？

**参考答案**  
UI 依赖**形状契约**。fixture 字段名/嵌套与 `/api/workbench/snapshot` 不一致时，离线 UI 正常、接 API 全崩（或反过来）。

**解析**  
- DD：fixture 与 API 同形。  
- 排障 F1。

### Q5.4 Snapshot 的 referential integrity 在防什么？

**参考答案**  
防孤儿引用：timeline 指向不存在的 run、claim 指向不存在的 evidence/source。校验失败应在组装时暴露，而不是到 React 里 undefined。

**解析**  
- Pattern：Snapshot Referential Integrity。  
- Capstone 用同一批 domain 对象适配。

---

## Part 6 — Framework Comparisons

### Q6.1 为什么 `FrameworkProfile` 不是“把 LangGraph 包一层”？

**参考答案**  
课程要练的是**可复现的选型判断**，不是安装第三方 SDK。Profile 是 deterministic 记录：固定 task/fixture/metric + 透明权重。真接入是独立 phase，adapter 在 core 外。

**解析**  
- DD：Profile 不是 wrapper。  
- 避免依赖膨胀与离线失败。

### Q6.2 某候选在未加权维度上拿了 0.95，为什么可能不进 `strengths`？

**参考答案**  
`strengths` 要求 **score ≥ 0.80 且该维出现在 weights**。没进入本场考试权重的高分，不记为 strength——避免“这场不考的科目刷存在感”。

**解析**  
- TRAP：strengths 的双条件。  
- 讨论价值：权重本身就是产品决策，应透明。

### Q6.3 没有 pinned task/fixture/metric 的“框架更强”争论有什么问题？

**参考答案**  
不可复现、不可审计，最后变成印象分与营销页对比。工程选型需要同一 harness 下的分数与 tradeoffs。

**解析**  
- Pattern：Pinned Comparison Harness。  
- 与 Part 1 “用 sequence 证明过程”同构：都反对只看最终口号。

---

## Part 7 — Production Readiness

### Q7.1 配置了 `max_runtime_seconds=30`，超时任务为什么仍可能跑完？

**参考答案**  
该字段是 **inspectable limit**，不是 AgentRunner 的自动 kill 开关。必须调用 `sandbox.runtime_decision(elapsed)`；`allowed=False` 时由**编排层**决定拒绝/中止/告警。Runner 当前不会读取 SandboxPolicy。

**解析**  
- 延伸 TRAP / Capstone honesty。  
- 常见神话：设了数字就等于生产超时。

### Q7.2 `RunDiagnostics` 能否替代完整 event trail？

**参考答案**  
不能。Diagnostics 是目录与摘要（counts、flags）；审计细节仍要 events / JSONL。

**解析**  
- TRAP：Diagnostics ≠ trail。  
- Pattern：Local Production Contracts First。

### Q7.3 为什么 production contracts 要先做本地 Python 对象，而不是直接上云日志？

**参考答案**  
规则应可单测、可离线证明。云/DB/网页审批应**包住** `ApprovalPolicy` / `SandboxPolicy` / `JsonlRunEventStore`，而不是把边界藏进平台配置后无法在 CI 复现。

**解析**  
- DD：本地离线对象优先。  
- 与 core 不 import 云 SDK 一致。

### Q7.4 ApprovalPolicy 写了 shell 规则，为何 `shell.exec` 仍 allow？

**参考答案**  
可能 pattern 不匹配，或只构造了 policy 从未 `decide`。Approval 同样是“决策对象”，不自动劫持 ToolRuntime。

**解析**  
- 与 runtime_decision 同一类“声明 vs 执行”。  
- 确认：`approval.decide("shell.exec").mode`。

---

## Capstone — 整合

### Q8.1 Capstone 的目标是“再写一个 research_core 模块”吗？

**参考答案**  
不是。目标是**组合公开 contracts** 成完整离线论文研究助手，放在 `course/capstone/`，用 reflection 记录 chose/rejected/because。不要新建 `research_core.capstone` mega-module，也不要抄私有 helper。

**解析**  
- Capstone DD：handwritten contracts / public API only。  
- 评分看整合与诚实，不看重新发明轮子。

### Q8.2 列出至少三条 Capstone 必须诚实面对的边界，并说明如何在代码里“做对”。

**参考答案（示例）**  
1. **Role 字段不自动 enforce** → child_factory 用 `filter_tools_for_role` 再 register。  
2. **MEMORY_*/SKILL_* 不自动** → 不伪造 event；需要 skill 就显式 `SkillRuntime`。  
3. **max_runtime inspectable only** → 显式 `runtime_decision(under)` 与 `runtime_decision(over)`，写入 production 证据。

**解析**  
- 对应 Capstone README traps + solution `production_boundary`。  
- 只拼报告、不做 production 证据 → rubric 缺口。

### Q8.3 为什么 starter 测试可以长期 skip？这和“课程完整”矛盾吗？

**参考答案**  
不矛盾。Starter 是**学习脚手架**（skip-until-implemented）；solution 与 rubric 提供完整标准。完整性体现在 materials + solution 可验证，而不是强迫空 starter 假绿。

**解析**  
- 工程诚实：假绿比 skip 更糟。  
- 学员路径：先独立填 starter，再对照 solution。

### Q8.4 用 chose / rejected / because 写一条跨 Part 决策示例。

**参考答案（示例）**  
- **Chose**：证据链用 Claim + Evidence + ClaimSourceLink，而不是把引用写进 prose。  
- **Rejected**：Markdown 脚注字符串拼接。  
- **Because**：Part 2 要求可映射、可 fail-closed；Workbench/Capstone 需要 ID 级审计（Part 5/7）。

**解析**  
- Reflection 模板见 `capstone/solution/reflection.md`。  
- 好 reflection 至少 3 条跨 Part，且每条有 rejected。

### Q8.5 Capstone 若为了“trail 好看”手动 append 假的 `memory_write` event，问题在哪？

**参考答案**  
破坏可观察性的可信度：trail 应反映 runtime 真实接线。伪造 event 会让 diagnostics/JSONL/审计全部建立在谎言上，与课程核心价值观相反。

**解析**  
- Capstone TRAP：events are not automatic — 也不应假造。  
- 正确做法：在 reflection 写明 declarative vs enforced。

---

## 跨章综合题

### Q9.1 用一句话串起 Parts 1–7 的“同一条主线”。

**参考答案**  
先有可观察的 think-act-observe 与 event trail，再长出可审计证据链、受控记忆/技能、隔离委派、adapter 产品面、可复现选型，最后用本地 production contracts 把回放与边界决策钉住——全程离线可测。

**解析**  
- 对应 design-decisions-index 的五条 cross-cutting themes。  
- Capstone 是这条主线的期末考试，不是新故事。

### Q9.2 举三个“配置了 ≠ 生效了”的例子。

**参考答案**  
1. `tool_names` 未经过 `filter_tools_for_role`。  
2. `skill_names` / `memory_kinds` 未显式 load/write 接线。  
3. `max_runtime_seconds` 未调用 `runtime_decision`。  
（加分：ApprovalPolicy 未 `decide`。）

**解析**  
- 主题：声明 ≠ 执行。  
- 面试/答辩极高频。

### Q9.3 若只能保留一种“证明手段”给评审看，你选什么？为什么？

**参考答案（推荐）**  
**Event trail +（Part 7）JSONL 回放**，辅以 evidence links 与 production decision records。因为最终答案可伪造，过程与映射更难撒谎；diagnostics 只作目录。

**解析**  
- 若答“只看 UI 截图”：弱，可手搓数据。  
- 若答“只看 final report”：Part 1/2 已否定。

---

## 自检清单（讨论后）

- [ ] 没有声称 AgentRunner 会自动按 SandboxPolicy kill  
- [ ] 没有声称 Memory/Skill 会自动进 RunEvent  
- [ ] 没有声称 role 字段自动过滤工具  
- [ ] 能区分 Search / Evidence / Claim  
- [ ] 能区分 list / recall  
- [ ] 能区分 diagnostics / events  
- [ ] 能说明 Workbench 只走 `from_*`  
- [ ] Capstone 决策用了 chose / rejected / because  

未勾选项：回对应 Part 的 chapter `[TRAP]` 与 [troubleshooting.md](troubleshooting.md)。
