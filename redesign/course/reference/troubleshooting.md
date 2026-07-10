# Troubleshooting

按症状查找。每条给出：**现象 → 可能原因 → 怎么确认 → 修法 → 相关 Part**。

先确认环境：

```bash
# 在 redesign/ 根目录
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
```

Capstone 不在默认 `testpaths` 里，需要显式跑：

```bash
PYTHONPATH=packages/research_core/src uv run pytest \
  course/capstone/solution/test_run.py \
  course/capstone/starter/test_starter.py -q
```

系统 Python 若是 3.9，可能缺 `StrEnum` 等语法；请用项目 `uv` 管理的 3.11+。

---

## A. 环境与导入

### A1. `ModuleNotFoundError: research_core`

| | |
| --- | --- |
| 现象 | import research_core 失败 |
| 原因 | 未设置 `PYTHONPATH=packages/research_core/src`，或不在 redesign 根目录 |
| 确认 | `pwd`；`ls packages/research_core/src/research_core` |
| 修法 | 所有 pytest / 脚本前加 `PYTHONPATH=packages/research_core/src` |
| Part | Setup / 00 |

### A2. `uv` cache / sandbox `Operation not permitted`

| | |
| --- | --- |
| 现象 | `uv run` 写 cache 失败 |
| 原因 | 沙箱限制默认 cache 路径 |
| 修法 | `UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run ...` |
| Part | Setup |

### A3. Capstone 在 3.9 上报 `StrEnum` / typing 错误

| | |
| --- | --- |
| 现象 | 系统 python3 跑 capstone 失败 |
| 原因 | 项目目标 3.11+ |
| 修法 | 只用 `uv run`，不要 `python3 course/capstone/...` 裸跑 |
| Part | Capstone |

### A4. Docs freshness 失败：missing indexed paths

| | |
| --- | --- |
| 现象 | `tests/course/test_docs_freshness.py` 报 missing paths |
| 原因 | README / roadmap 链到了不存在的 markdown |
| 确认 | 读失败信息里的 path |
| 修法 | 创建文件，或改索引链接；索引里的 `` `path.md` `` 必须真实存在 |
| Part | 全课程文档 |

---

## B. Part 1 — Agent Kernel

### B1. FakeModel 报 “no more responses” / 队列用尽

| | |
| --- | --- |
| 现象 | run 中途异常，或 steps 不够 |
| 原因 | `FakeModel([...])` 预置条数少于实际 model 调用次数 |
| 确认 | 数 event 里 `model_request` 次数 vs FakeModel 队列长度 |
| 修法 | tool 路径通常需要：tool_call 响应 + 最终文本响应（至少 2 条） |
| Part | 1 |

### B2. tool call 解析失败 / 不调用工具

| | |
| --- | --- |
| 现象 | 模型“说了要调工具”但没有 `tool_call` event |
| 原因 | content 不是约定的 JSON 字符串；或传了 Python dict 当 content |
| 确认 | `FakeModelResponse(content=json.dumps({...}))` |
| 修法 | 使用课程 JSON 协议；`json.dumps` 后再放入 content |
| Part | 1；见 [TRAP] FakeModel tool call 是 JSON 字符串 |

### B3. 把 tool result 当成 final answer

| | |
| --- | --- |
| 现象 | 测试断言 final message 等于 tool 返回值，失败 |
| 原因 | tool result 是中间观察；final 是后续 model 文本 |
| 确认 | sequence 是否在 `tool_result` 后还有 `model_request/response` |
| 修法 | 断言 final 看最后一条 assistant；断言过程看 events |
| Part | 1 |

### B4. 未知工具没有留下线索

| | |
| --- | --- |
| 现象 | 调错工具名，只看到异常，没有 event |
| 原因 | 过早吞掉异常，或没跑完整 runner |
| 确认 | `exc.events` 或 result 中是否有 `error` |
| 修法 | 让失败走 runner 记录路径；Part 1 故意不在调用前静默预检 |
| Part | 1 |

### B5. `records[i]["payload"]` 与 `events[i].payload` 对不上

| | |
| --- | --- |
| 现象 | lab 里索引错位 |
| 原因 | record 是序列化视图；event 是对象；过滤后的 list 与全量 events 索引不同 |
| 修法 | 先对**同一种结构**取序列，再比 payload；见 lab 01 [TRAP] |
| Part | 1 lab |

---

## C. Part 2 — Research Core

### C1. claim 有了，但 `build_claim_source_links` 失败

| | |
| --- | --- |
| 现象 | mapping 抛错或 links 为空 |
| 原因 | `evidence_ids` 指向不存在的 evidence；或 source_id 对不上 |
| 确认 | 打印 `claim.evidence_ids` 与 `evidence.id` 集合 |
| 修法 | 先修 ID 引用，再写报告 prose |
| Part | 2 |

### C2. 搜索第一名被当成“证据”

| | |
| --- | --- |
| 现象 | 报告只有 ranking，没有 quote/location |
| 原因 | 混淆 `SearchResult` 与 `Evidence` |
| 修法 | hit 只指导你去读哪篇；证据必须是带 `source_id` 的 quote |
| Part | 2；[TRAP] 搜索排名不是证据链 |

### C3. 把 quote 写进 `Claim.text`

| | |
| --- | --- |
| 现象 | 结构上“能跑”，但无法区分主张与摘录 |
| 原因 | 违反分层 |
| 修法 | Claim = 主张；Evidence = 摘录；Link = 映射 |
| Part | 2 |

### C4. source ID 变了，下游全断

| | |
| --- | --- |
| 现象 | 改 ingest 后 evidence 全失效 |
| 原因 | source id 是引用键 |
| 修法 | 稳定 id 策略；测试固定 fixture；不要把 id 当展示文案随意改 |
| Part | 2 |

### C5. Capstone topics 变成单字符

| | |
| --- | --- |
| 现象 | metadata topics 是 `('a','b',...)` 字符元组 |
| 原因 | 对字符串做了 `tuple("a,b")` |
| 修法 | 仅当 topics 是 list/tuple 时转换；字符串要先 split 或忽略 |
| Part | Capstone / 2 |

---

## D. Part 3 — Memory & Skills

### D1. 写了 memory，event trail 没有 `memory_write`

| | |
| --- | --- |
| 现象 | 期望自动出现 MEMORY_* event |
| 原因 | **诚实边界**：`MemoryEngine` 不自动 append RunEvent |
| 确认 | 枚举值存在 ≠ 自动发射 |
| 修法 | 若需要进 trail，在编排层显式 append；Capstone 不要伪造 event |
| Part | 3, Capstone |

### D2. `list` 有记录，`recall` 为空

| | |
| --- | --- |
| 现象 | notebook 里看得到，召回没有 |
| 原因 | recall policy 的 kind / query / limit / importance 过滤更严 |
| 确认 | 分别调用 list 与 recall，打印 policy |
| 修法 | 放宽 `MemoryRecallPolicy`；理解 list ≠ recall |
| Part | 3 |

### D3. write 被拒绝

| | |
| --- | --- |
| 现象 | `write` 失败或记录未进入 |
| 原因 | kind 不在 allowlist、importance 过低、超长、命中 forbidden phrase |
| 确认 | `MemoryWritePolicy` 字段 |
| 修法 | 调整 policy 或清洗 content（不要为了过测关掉所有防护） |
| Part | 3 |

### D4. skill reference 读不到 / 路径错误

| | |
| --- | --- |
| 现象 | `read_reference` 失败 |
| 原因 | 路径必须相对 package 内资源；progressive disclosure 不会自动预加载全部文件 |
| 修法 | 先 `load`，再读 manifest 声明的 reference 路径 |
| Part | 3 |

### D5. 角色上写了 `skill_names`，skill 没加载

| | |
| --- | --- |
| 现象 | Capstone / delegation child 没有 skill 内容 |
| 原因 | `skill_names` 是声明式标签 |
| 修法 | 显式 `SkillRuntime.load(...)`；见 Capstone honesty notes |
| Part | 4, Capstone |

---

## E. Part 4 — Delegation

### E1. child 仍能调用不该有的工具

| | |
| --- | --- |
| 现象 | `tool_names` 写了 allowlist，但 child 注册了更多 tool |
| 原因 | `DelegationRuntime` **不**自动按 `tool_names` 过滤 ToolRuntime |
| 修法 | factory 内 `filter_tools_for_role` 后再 register |
| Part | 4, Capstone |

### E2. child 看不到 `task.metadata` 里的字段

| | |
| --- | --- |
| 现象 | 把关键指令塞进 metadata，child 行为不变 |
| 原因 | 可见性由 `compile_child_prompt` 决定，不是 metadata 自动注入 |
| 确认 | 打印 compiled prompt / child MODEL_REQUEST |
| 修法 | 把必要信息放进 objective / 编译路径允许的字段 |
| Part | 4 |

### E3. budget 溢出但“好像跑完了”

| | |
| --- | --- |
| 现象 | status 失败或 parent trail 有错误，却仍有部分输出 |
| 原因 | 观察步数与角色 max_steps / budget 冲突 |
| 确认 | `DelegationBudget` 与 child `max_steps`；parent events |
| 修法 | 收紧角色与预算，使失败形状可预期 |
| Part | 4 |

### E4. duplicate child run id

| | |
| --- | --- |
| 现象 | 第二次委派失败 |
| 原因 | child_run_id 必须唯一（同一 accounting 范围） |
| 修法 | 每次任务新 id |
| Part | 4 |

### E5. system message 泄漏到 child

| | |
| --- | --- |
| 现象 | child 遵循了 parent-only 规则 |
| 原因 | 错误地把 parent messages 整包转发 |
| 修法 | 只用 compiler 产出的 child context；跑 Break 练习验证 |
| Part | 4 |

---

## F. Part 5 — Workbench

### F1. UI 用 fixture 正常，接 API 崩

| | |
| --- | --- |
| 现象 | 字段 undefined / 面板空白 |
| 原因 | fallback fixture 与 `/api/workbench/snapshot` record **不同形** |
| 修法 | 九个面板字段名与 record 对齐；fixture 复制真实 `to_record()` 形状 |
| Part | 5 |

### F2. 手搓 `WorkbenchEvidenceItem(...)` 后 ID 对不齐

| | |
| --- | --- |
| 现象 | 校验失败或 UI 显示孤儿引用 |
| 原因 | 绕过 `from_*` 发明第二套模型 |
| 修法 | `from_evidence` / `from_source` / `from_event` / `from_report` / `from_memory_record` |
| Part | 5 |

### F3. snapshot 校验 referential integrity 失败

| | |
| --- | --- |
| 现象 | 创建 snapshot 抛错 |
| 原因 | claim/evidence/source/run id 交叉引用断裂 |
| 修法 | 从同一批 domain 对象适配；先修 core 链再适配 |
| Part | 5 |

### F4. FastAPI 或 React 想 import 深层 core 私有结构

| | |
| --- | --- |
| 现象 | 循环依赖或测试难跑 |
| 原因 | 依赖方向反了 |
| 修法 | 只消费 record / 公开 product 契约；core 不 import web 框架 |
| Part | 5 |

---

## G. Part 6 — Framework Comparisons

### G1. strengths 列表“少了很强的维度”

| | |
| --- | --- |
| 现象 | 某候选单科很高却不进 strengths |
| 原因 | strengths 要求 **score ≥ 0.80 且该维在 weights 中** |
| 修法 | 调整权重或接受“这场考试不考那科” |
| Part | 6 |

### G2. 想直接 pip 进 LangGraph 做比较

| | |
| --- | --- |
| 现象 | 依赖膨胀、离线失败 |
| 原因 | 课程比较用 deterministic `FrameworkProfile`，不是 wrapper |
| 修法 | 先写 profile 记录；真接入是独立 phase + adapter 在 core 外 |
| Part | 6 |

---

## H. Part 7 — Production Readiness

### H1. 设了 `max_runtime_seconds` 但超时任务仍跑完

| | |
| --- | --- |
| 现象 | 期望自动 kill，没有 |
| 原因 | **inspectable only**；`AgentRunner` 不自动读 SandboxPolicy |
| 修法 | 调用 `sandbox.runtime_decision(elapsed)`；由编排层执行决策 |
| Part | 7, Capstone |

### H2. diagnostics 有了，但无法审计细节

| | |
| --- | --- |
| 现象 | 只有 count / 摘要 |
| 原因 | 把 diagnostics 当成完整 trail |
| 修法 | 同时保留 events 与 JSONL；diagnostics 是目录 |
| Part | 7 |

### H3. approval 对 shell 仍是 allow

| | |
| --- | --- |
| 现象 | 规则不生效 |
| 原因 | pattern 不匹配；或只构造了 policy 从未 `decide` |
| 确认 | `approval.decide("shell.exec").mode` |
| 修法 | 规则顺序 / pattern；显式 decide 后再执行 |
| Part | 7 |

### H4. JSONL 读回 run_ids 为空

| | |
| --- | --- |
| 现象 | `list_run_ids()` 空 |
| 原因 | 未 `append_many`；路径被清空后未重写；读了错误 path |
| 修法 | 写后立刻 list；Capstone solution 会先 unlink 再写干净文件 |
| Part | 7 |

### H5. network_decision 与直觉不符

| | |
| --- | --- |
| 现象 | 以为默认能上网 |
| 原因 | Capstone / 课程 sandbox 常 `allow_network=False` |
| 修法 | 读 `SandboxPolicy` 构造参数；用 `network_decision()` 验证 |
| Part | 7 |

---

## I. Capstone 整合

### I1. starter 测试全部 skip

| | |
| --- | --- |
| 现象 | `1 skipped` |
| 原因 | starter 设计为 skip-until-implemented |
| 修法 | 实现后再改 skip 条件；对照 solution 不要先抄答案 |
| Part | Capstone |

### I2. solution 绿但自己的 agent 缺 production 字段

| | |
| --- | --- |
| 现象 | 缺 `runtime_under_budget` / approval 等 |
| 原因 | 只拼了报告，没做 production_boundary |
| 修法 | 按 rubric：diagnostics + JSONL + approval + sandbox + **runtime_decision** |
| Part | Capstone |

### I3. 伪造 MEMORY_*/SKILL_* 事件“显得完整”

| | |
| --- | --- |
| 现象 | trail 看起来更满，但与 runtime 能力不符 |
| 原因 | 违反 honesty notes |
| 修法 | 不写假 event；reflection 写明 declarative vs enforced |
| Part | Capstone |

### I4. 模块名冲突 `agent` / `agent_starter`

| | |
| --- | --- |
| 现象 | pytest 收集怪异 |
| 原因 | Capstone 在默认 testpaths 外，且模块名通用 |
| 修法 | 显式路径跑测；不要把 capstone 塞进全局 testpaths 除非改名 |
| Part | Capstone |

---

## J. 快速决策树

```text
失败发生在 import/环境？ → 章节 A
只有最终答案不对、过程未知？ → 先打 event sequence（B/H）
论文出处问题？ → C
记忆/技能“写了但看不见”？ → D（先问：list/recall/event/role 哪一层）
多 agent 越权或泄漏？ → E
UI/API 形状问题？ → F
选型分数奇怪？ → G
超时/审批/落盘？ → H
Capstone 整合缺项？ → I + rubric.md
```

仍卡住时：回到对应 chapter 的 `[TRAP]` / `[DD]`，并查 [design-decisions-index.md](design-decisions-index.md)。
