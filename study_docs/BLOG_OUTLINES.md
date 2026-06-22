# 技术博客大纲（3 篇起步，可扩展到 5 篇）

> 学习方案 D.5 要求 3-5 篇技术博客。下列大纲可直接当目录用。
> 写作建议：每篇 2000-3500 字，包含 1 张架构图 + 2-3 段代码 + 1 个 trade-off 表 + 1 段"踩坑记录"。

---

## 博客 1：从 ReAct 到 Multi-Agent：用 LangGraph 编排你的研究流

### 适合发布：知乎 / 公众号 / Medium / 掘金

### 目标读者
- 已经会 OpenAI Function Calling
- 听说过 LangGraph 但没自己写过的工程师

### 大纲

1. **引子：单 Agent 的尽头**
   - 一段 ReAct 循环的代码，看着干净；
   - 接到一个"写一份某某行业调研报告"的任务，开始失控：
     - 一会儿想搜索，一会儿想写作，反复修订
     - 上下文超 4k token
     - 没有"反思"角色，错的也写出来。

2. **为什么不是 if-else**
   - 朴素状态机的代码爆炸；
   - LangGraph 的 graph + state 模型简介；
   - 节点 / 边 / 条件边 / END 四个核心概念。

3. **本项目里的 5 节点 Multi-Agent**
   - 配图：plan → research → analyze → write → review 流程图；
   - 共享 `MultiAgentState` 的字段设计（topic / queries / search_results / draft / feedback / iterations / revisions）；
   - 关键代码片段（来自 `app/services/multi_agent/graph.py`）。

4. **路由的两个分叉点**
   - `route_after_analysis`：是否还要继续搜索？看 confidence；
   - `route_after_review`：reviewer 判 ok / 重写；
   - 都加了硬上限（max_iterations / max_revisions）防失控。

5. **怎么测试一个 graph**
   - 单元测试每个节点纯函数化；
   - 集成测试用 mock LLM 回固定响应；
   - 端到端用 `agent_evaluator` 跑批。

6. **trade-offs 表**
   | 维度 | ReAct | Multi-Agent |
   |------|-------|-------------|
   | 复杂度 | 低 | 中-高 |
   | 成本 | 低 | 2-3x |
   | 可控性 | 中 | 高 |
   | 适用场景 | 工具调用 | 长报告/批判任务 |

7. **踩坑**
   - 节点共享状态时 mutate vs return 新对象的坑；
   - 条件边里漏掉 END 路径导致编译失败；
   - reviewer 总是说 ok 怎么办（提示词加角色压力 + 结构化输出）。

8. **下一步：人类介入 (HITL)**
   - 在 reviewer 节点暂停 → wait for human → resume；
   - LangGraph 的 `interrupt_before` 用法。

### 文末资源
- 项目 GitHub
- LangGraph 官方文档关键章节链接

---

## 博客 2：MCP 实战：让 Agent 工具"一次写好，到处可用"

### 适合发布：掘金 / Medium / dev.to

### 目标读者
- 在用 OpenAI / Anthropic / 国内 LLM 自定义 function calling 时苦于"每家协议不一样"的工程师。

### 大纲

1. **引子：function calling 的多协议地狱**
   - OpenAI tools schema、Anthropic tool_use、Gemini function declaration —— 三套不同；
   - 工具想跨厂商复用？把 schema 重写一遍，runtime 也重写。

2. **MCP 是什么**
   - Anthropic 牵头的 Model Context Protocol；
   - 把"工具"独立成 **server 进程**，client（LLM 驱动 / IDE / agent）通过 stdio 或 SSE 与之 RPC；
   - 协议是 JSON-RPC + 一组标准方法（tools/list、tools/call、resources/list、prompts/list）。

3. **怎么自己写一个 MCP server**
   - 项目里 `app/services/mcp/server.py` 用 mcp Python SDK；
   - 用 `@server.list_tools` / `@server.call_tool` 注册；
   - 关键：**call_tool 出错时返回 `CallToolResult(isError=True)` 而不是 raise**，否则 server 循环挂掉。

4. **怎么集成外部 MCP server**
   - Anthropic 官方的 filesystem / fetch；
   - 我们 `MCPRuntime` 拉起子进程、`tools/list` 拉清单、call 时按 `mcp__server__tool` namespacing；
   - 多 server 同名工具怎么办：namespace 隔离。

5. **超时与稳定性**
   - `asyncio.wait_for(call_tool, timeout=...)` 必须有，否则一个慢 server 拖垮整个 agent；
   - shlex 解析命令行：Windows 必须 `posix=False`。

6. **MCP 与 Function Calling 不是二选一**
   - 我们项目里 MCP 工具 + 本地工具用同一个 ToolRegistry；
   - LLM 端只看到统一的 OpenAI tools schema；
   - 内部转发：local 直接 invoke，mcp 走 runtime。

7. **何时不该用 MCP**
   - 工具只会被一个进程用；
   - 工具非常吃内存（多进程开销大）；
   - 网络隔离严格的内网；

8. **踩坑实录**
   - npx 在 slim Docker 没 node；
   - stdio 子进程 stdin/stdout 编码 Windows / Linux 不一致；
   - 工具 schema 字段 type 漏了 description LLM 表现下降。

### 文末资源
- mcp.so 官方
- 项目 GitHub /mcp 模块

---

## 博客 3：Production-Grade Agent 的工程化三件套：Eval、Guardrails、Tracing

### 适合发布：infoq / 公众号 / Medium

### 目标读者
- 有 Agent demo 但不知道"再做点什么才像生产"的工程师；
- 求职者准备讲项目时提升说服力。

### 大纲

1. **引子：80% 的 Agent demo 没法上线**
   - 给一个反例：能跑通 chat，但没法回答"准吗"、"安全吗"、"贵吗"；
   - 这三个问题对应 Eval / Guardrails / Tracing。

2. **Eval：怎么把"看上去不错"量化**
   - RAG 三大指标的定义与计算（Faithfulness / Context Precision / Answer Relevance）；
   - LLM-as-judge 的实现：固定格式 prompt + `response_format=json_object`；
   - Agent eval 的指标族：success_rate / iterations_used / latency / keyword_coverage；
   - 项目代码 walkthrough：`scripts/run_rag_eval.py` + `scripts/run_agent_eval.py`；
   - 单 judge 的 bias 与缓解（panel + bootstrap）。

3. **Guardrails：三层兜底**
   - 输入层：prompt injection 关键词正则 + 风险等级；
   - 输出层：PII 正则脱敏（手机/邮箱/身份证）；
   - 工具层：whitelist + 危险参数检测（`rm -rf` / SQL 关键字）；
   - 关键设计：guardrails 单点失败可关，便于 A/B；
   - 局限：obfuscated injection、跨语言、社会工程，需要 LLM-based moderation 叠加。

4. **Tracing：把每次 LLM 调用的"成本与因果"留下来**
   - 为什么不直接用 LangSmith：耦合 / 出墙 / 锁厂商；
   - 自己做一个：`asynccontextmanager trace()` + `ContextVar _CURRENT_TRACE_ID`；
   - 每个节点写 SQLite 一行（trace_id / parent_id / name / status / metadata / token / cost）；
   - 端点 `/observability/traces/{id}` 渲染嵌套树；
   - 之后可以平滑迁移 OpenTelemetry。

5. **CostCalculator**
   - 单价表 → 每次调用结束累加；
   - `/observability/cost-summary?days=7`；
   - 成本控制策略清单：cache、降模型、max_tokens、迭代上限。

6. **三件套合体**
   - 一次 multi_agent 调用产生：5 个 trace 节点 + 每个节点的 cost + guardrails 入口/出口都有 trace + 评估端点能离线跑；
   - 截图建议：`/observability/traces` 树状渲染。

7. **怎么把这套搬到自己的项目里**
   - 最小代码量：tracing 一个文件 + guardrails 一个文件 + eval 两个 cli；
   - 不破坏既有架构：用 contextmanager 注入而非签名改造。

8. **下一步**
   - 多模型 judge panel + 置信区间；
   - LLM-based moderation；
   - OpenTelemetry exporter；
   - 真实计费表 + budget alert。

### 文末资源
- 项目 GitHub / Phase 7 文档链接

---

## 博客 4（可选）：用 LangGraph 0.6 + FastAPI + SSE 实现实时研究流

### 大纲速览
1. SSE vs WebSocket：为什么 Agent 输出选 SSE；
2. LangGraph 流式节点（`astream_events`）适配 SSE；
3. FastAPI 的 StreamingResponse + Nginx buffering 必关；
4. 前端 Streamlit / 浏览器 EventSource 客户端；
5. 错误恢复（连接断了怎么办）；
6. 项目代码：`app/services/research/streaming.py` + `/api/v1/research/stream`。

---

## 博客 5（可选）：从 Streamlit 到 Production：把 Demo 变成可分发的产品

### 大纲速览
1. Streamlit 的快与坑（多页应用、缓存、session state）；
2. 多阶段 Dockerfile：runtime 350MB；
3. docker-compose 编排 backend / frontend / qdrant；
4. 数据持久化（卷设计）；
5. 升级与回滚（image tag）；
6. CI：GitHub Actions 跑 pytest；
7. Secrets 红线（vault / 不要进 git）；
8. 何时该换 React / Vue。

---

## 写作 SOP 建议

1. 先写大纲（用本文件作起点）；
2. 写代码 walkthrough 时直接贴项目代码片段，标注 GitHub 链接；
3. 每篇结尾必加 1 个 trade-off 表 + 1 段"我没做的事"，显得诚实；
4. 配图：架构图用 excalidraw 或 mermaid，导出 PNG；
5. 发布顺序：博客 3 → 1 → 2 → 4/5，最有"工程化高度"的先打头阵。

---

## 复用素材

| 内容 | 来源 |
|------|------|
| 架构图 | architecture_docs/phase{0..8}_architecture.md |
| 代码片段 | app/services/* |
| 评估数据 | eval/results/*.json |
| trace 截图 | /observability/traces 渲染 |
| docker 截图 | docker compose ps / logs |
