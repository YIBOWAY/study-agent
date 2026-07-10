# Common Patterns

这是本地论文研究助手课程里反复出现的**可复用模式**。它们不是第三方框架教条，而是 `research_core` 与 Parts 1–7 / Capstone 里已经落地的工程习惯。

读法建议：

1. 先按 Part 顺序扫一遍，知道“这招在哪一章练过”。
2. 写 Capstone 或自己的扩展时，用本页当检查清单。
3. 每个模式都附诚实边界：不要把“模式”误读成“runtime 已自动替你做”。

相关材料：

- [design-decisions-index.md](design-decisions-index.md)
- [troubleshooting.md](troubleshooting.md)
- [discussion-prompts.md](discussion-prompts.md)
- [agent-kernel-glossary.md](agent-kernel-glossary.md)

---

## Pattern Map

| Pattern | 主要 Part | 一句话 |
| --- | --- | --- |
| Offline-first Fake Provider | 1 | 用 `FakeModel` / fixture 把网络和 API key 从测试路径里拿掉 |
| Think–Act–Observe Loop | 1 | model request → tool call → tool result → 再请求 model |
| Event Trail as Evidence | 1, 7 | 用 `RunEvent` 序列证明过程，而不是只信最终答案 |
| Fail Closed, Surface Error Events | 1, 4 | 失败写进 trail / result，而不是静默吞掉 |
| Evidence Chain, Not Search Ranking | 2 | `Source → Evidence → Claim → Report → ClaimSourceLink` |
| Policy Before Side Effect | 3, 7 | write / recall / approve / sandbox 先决策再动作 |
| Progressive Disclosure Skills | 3 | skill 先 manifest，再按需读 reference，不一次灌满 context |
| Explicit Role Enforcement at Factory | 4 | `filter_tools_for_role` 等工厂侧 enforce，角色字段本身不是魔法 |
| Child Context Isolation | 4 | child prompt 由 compiler 显式编译，不默认继承 parent 全部上下文 |
| Budget Accounting | 4 | `DelegationBudget` 数 child runs / steps，超预算失败可见 |
| Adapter-only Product Surface | 5 | domain → `from_*` → `WorkbenchSnapshot` → API/UI |
| Snapshot Referential Integrity | 5 | snapshot 校验 ID 引用完整，禁止孤儿 claim/evidence |
| Pinned Comparison Harness | 6 | 固定 task/fixture/metric + 透明权重，再谈 build vs adopt |
| Local Production Contracts First | 7 | diagnostics / JSONL / approval / sandbox 先本地对象，后接云 |
| Inspectable Limits ≠ Auto Kill | 7, Capstone | `max_runtime_seconds` 需 `runtime_decision`；runner 不自动杀 |
| Compose Public Contracts in Capstone | Capstone | Capstone 组合公开 API，不新建 mega-module 也不抄私有 helper |

---

## 1. Offline-first Fake Provider

**问题：** 真实 model / 检索 API 会让测试抖动、需要密钥、难复盘。

**做法：**

- Kernel 用 `FakeModel` + 预置 `FakeModelResponse` 队列。
- Research 用本地 `paper_fixtures` + `FakeRetriever`。
- Capstone 全程离线：fixture + fake，不连 Semantic Scholar / provider。

**何时用：** 课程、单测、CI、本地 demo、公平评分。

**诚实边界：** Fake 证明的是**协议与边界**，不是模型智力或检索召回质量。上线真模型时，adapter 应包在 core 外，而不是把 SDK 拖进 `research_core`。

---

## 2. Think–Act–Observe Loop

**问题：** “Agent” 若只是一次 chat completion，就无法调用工具、也无从审计。

**做法：**

```text
ContextBuilder 组装 messages
  -> model.complete(...)
  -> 若 content 是 tool_call JSON：ToolRuntime 执行
  -> 追加 tool message
  -> 再次 model.complete(...)
  -> 最终 assistant message
```

**检查点：**

- tool call 是 **JSON 字符串**，不是 Python dict。
- tool result 是 **tool role message**，不是又一次 assistant 回答。
- event sequence 至少能解释每一步。

---

## 3. Event Trail as Evidence

**问题：** 最终答案可能碰巧正确，但路径已坏（错工具、漏步骤、静默失败）。

**做法：**

- 每次 run 留下 `RunEvent` 列表。
- 用 `event_type_sequence(events)` 做 gate。
- Part 7 用 `RunDiagnostics.from_events` 做摘要目录，用 `JsonlRunEventStore` 做可回放存档。

**检查点：** diagnostics 是目录，不是替代原始 trail。审计时仍要读 events / JSONL。

---

## 4. Fail Closed, Surface Error Events

**问题：** 预校验把错误吞掉后，调用方只看到“没有答案”，无法定位。

**做法：**

- 未知 tool：让 `ToolRuntime` 在调用时失败，并留下 `error` event（Part 1 设计决策）。
- Delegation：预算溢出、duplicate child run id、编译泄漏等都变成可见 status / error，而不是半成功。
- Research mapping：缺 evidence id 时 fail closed，不让 narrative 补洞。

**反模式：** try/except 后 `return ""` 或伪造成功 event。

---

## 5. Evidence Chain, Not Search Ranking

**问题：** 搜索 hit 排名高 ≠ 报告里的 claim 有出处。

**做法：**

```text
SourceInput -> SourceIngestor -> Source
FakeRetriever.search -> SearchResult (排名只是检索视图)
Evidence(quote, source_id, location)
Claim(text, evidence_ids)
Report(claims...)
build_claim_source_links(...) -> ClaimSourceLink records
```

**检查点：**

- quote 不直接塞进 `Claim.text`。
- source id 是引用键，不是装饰。
- Capstone / L2 必须能从 claim 反查到 source URI / title。

---

## 6. Policy Before Side Effect

**问题：** memory 污染、危险 tool、越权写盘，往往发生在“先做再想”的路径上。

**做法：**

| 领域 | Policy | 动作 |
| --- | --- | --- |
| Memory write | `MemoryWritePolicy` | `MemoryEngine.write` |
| Memory recall | `MemoryRecallPolicy` | `MemoryEngine.recall` |
| Tool approval | `ApprovalPolicy.decide` | 是否允许执行某 tool |
| Sandbox | `SandboxPolicy.*_decision` | 路径 / 网络 / runtime 是否允许 |

**检查点：** policy 返回的是**决策对象**（allowed / mode / reason），调用方负责是否执行。不要假设 policy 对象自己会拦截 AgentRunner。

---

## 7. Progressive Disclosure Skills

**问题：** 把整本手册塞进 system prompt，既贵又难测。

**做法：**

1. `SkillRuntime.load(path)` 读 package / manifest。
2. 需要细则时再 `read_reference(package, "references/...")`。
3. Capstone 的 `citation-check` skill 演示：先知道有 skill，再读 citation rules。

**诚实边界：** `skill_names` 写在 `AgentRolePolicy` 上**不会**自动 load skill；工厂或编排层必须显式调用 `SkillRuntime`。

---

## 8. Explicit Role Enforcement at Factory

**问题：** 角色工牌上写了 `tool_names=("retriever.search",)`，开发者以为 child 自动只能用这些 tool。

**做法（Capstone solution 的正确形状）：**

```python
allowed = filter_tools_for_role(child_role, ("retriever.search",))
tools = ToolRuntime()
for tool_name in allowed:
    tools.register(ToolDefinition(name=tool_name, ...))
return AgentRunner(model=model, tools=tools, max_steps=child_role.max_steps)
```

**当前真正 enforced：**

- `max_steps`（runner）
- `DelegationBudget`（delegation runtime）

**仍是声明式标签：** `skill_names` / `memory_kinds`（直到你显式接线）。

---

## 9. Child Context Isolation

**问题：** parent 把完整 transcript 丢给 child，会泄漏 system 规则、预算外工具线索或无关噪声。

**做法：**

- `compile_child_prompt(task)`（或等价 compiler）生成 child 可见输入。
- 用 parent trail 的 `delegate_start` / `delegate_finish` 证明委派边界。
- 判断 child 看到了什么时，检查 **compiled prompt / child MODEL_REQUEST payload**，不要猜 `task.metadata` 是否“自动可见”。

---

## 10. Budget Accounting

**问题：** 多 agent 很容易无限分叉。

**做法：**

- `DelegationBudget(max_child_runs, max_steps_per_child, max_total_steps)`。
- 超预算 → 失败状态可见，而不是悄悄多跑。
- Capstone 用小预算（例如 1 child run / 2 steps）演示“够用且可审计”。

---

## 11. Adapter-only Product Surface

**问题：** UI / FastAPI 若直接 import 领域对象私有字段，产品与 core 互相绑死。

**做法：**

```text
research_core domain objects
  -> Workbench*Item.from_* adapters
  -> WorkbenchSnapshot
  -> snapshot.to_record()
  -> FastAPI JSON
  -> React panels
```

**硬规则：**

- `research_core` 不 import FastAPI / React。
- 不要手搓 `WorkbenchEvidenceItem(...)` 绕过 `from_*`（会发明第二套数据模型）。
- fallback fixture 必须与 API record **同形**。

---

## 12. Snapshot Referential Integrity

**问题：** timeline 指向不存在的 run、claim 指向不存在的 evidence，UI 会“看起来有数据”但不可审计。

**做法：** 组装 `WorkbenchSnapshot` 时做引用完整性校验（lab / core 验证路径）。Capstone 用 `from_event` / `from_source` / `from_report` / `from_memory_record` 保持 ID 对齐。

---

## 13. Pinned Comparison Harness

**问题：** “LangGraph 更强”这类争论如果没有固定任务，就会变成印象分。

**做法：**

- 固定 task + fixture + metrics。
- 透明权重；`strengths` 需要 **得分 ≥ 0.80 且该维在 weights 里**。
- 比较代码放在课程目录；候选是 deterministic `FrameworkProfile` 记录，不把第三方 SDK 拖进依赖树。

---

## 14. Local Production Contracts First

**问题：** 一上来接云日志 / 网页审批，边界规则会散落在平台配置里，课程与测试无法离线证明。

**做法：**

- `RunDiagnostics`、`JsonlRunEventStore`、`ApprovalPolicy`、`SandboxPolicy` 都是本地 Python 对象。
- Workbench 可以展示它们的 record；云 / DB 应**包住**这些 contract，而不是替换它们。

---

## 15. Inspectable Limits ≠ Auto Kill

**问题：** 配置了 `max_runtime_seconds=30`，就以为 AgentRunner 会自动超时终止。

**正确用法：**

```python
sandbox = SandboxPolicy(..., max_runtime_seconds=30)
under = sandbox.runtime_decision(5.0)   # allowed True
over = sandbox.runtime_decision(45.0)   # allowed False
# 调用方根据 decision 决定是否继续 / 拒绝 / 告警
```

**诚实边界：** 当前 `AgentRunner` **不会**读取 `SandboxPolicy` 并自动 kill。Capstone 必须显式调用 `runtime_decision` 才能算“练到了 Part 7 陷阱”。

---

## 16. Compose Public Contracts in Capstone

**问题：** Capstone 若复制一份私有实现或新建 `research_core.capstone`，就变成了产品功能而不是整合考试。

**做法：**

- 代码放在 `course/capstone/solution/`（教学产物）。
- 只 import 公开 `research_core` API。
- 用 reflection 记录 chose / rejected / because。

---

## Mini Checklist（写代码前 60 秒）

1. 这次改动能不能离线测？
2. 失败会不会进入 event trail / 明确 status？
3. 有没有把排名、quote、claim 混成一坨？
4. policy / role 字段是**声明**还是**已 enforce**？
5. 产品层是否只通过 adapter / record 消费？
6. 生产边界是 inspectable decision，还是误以为自动拦截？

若有一条答不上来，先回对应 Part 的 chapter + lab，再查 [troubleshooting.md](troubleshooting.md)。
