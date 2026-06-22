# Phase 5 架构文档：Memory + Multi-Agent

> 本阶段在 Phase 4 LangGraph 编排之上，新增 Memory 层和多 Agent 协作图。

---

## 1. 全局架构

```
┌─────────────────────────────────────────────────────────────┐
│  /api/v1/research?mode=workflow|agent|agent_v2|multi_agent  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Research Layer (LangGraph)                 │
│  ┌─────────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐ │
│  │ workflow.py │ │ agent.py │ │ agent_v2   │ │ multi_agent│ │
│  │ (固定 3 步) │ │ (ReAct)  │ │ (Plan&Solv)│ │ (4 角色)   │ │
│  └─────────────┘ └──────────┘ └────────────┘ └────────────┘ │
│            │           │             │             │         │
│            └───────────┴──────┬──────┴─────────────┘         │
│                               ▼                               │
│   recall_memory  ←──┐   nodes.py（共享节点工厂）              │
│   save_memory    ←──┘   plan / research / reflect / report   │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Memory Layer                            │
│  MemoryService                                               │
│   ├── _sessions: dict[str, SessionMemory]   # 会话记忆       │
│   └── _insights: list[InsightRecord]        # 长期记忆       │
│                                                              │
│   持久化：data/memory/long_term.json                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 模块职责清单

### 2.1 `app/services/memory_service.py`（160 行）

| 职责 | 说明 |
|------|------|
| 会话记忆管理 | 进程内 dict，按 TTL 过期 |
| 长期记忆管理 | JSON 落盘，关键词重叠检索 |
| 并发安全 | 写操作加 `asyncio.Lock` |
| 容量上限 | `max_insights` 控制总条数（FIFO 淘汰） |

**关键设计决策**：
1. **检索算法**：用 token 集合的 overlap，不上向量。理由：千条以内速度足够，单测可复现。
2. **session_id 为空时的兼容**：所有方法在 `not session_id` 时静默返回 None / no-op，不抛异常——这样 RAG/Chat 老接口不需要改动。
3. **持久化策略**：每次 `save_insight` 都全量重写 JSON。简单但 O(N) 写。当总量超过 1k 应换成增量写（已在 P2 待办）。

### 2.2 `app/services/multi_agent/`

```
multi_agent/
├── state.py    # MultiAgentState TypedDict（共 17 个字段）
├── roles.py    # 4 个角色节点工厂 + 2 个 router
└── graph.py    # build_multi_agent_graph + run_multi_agent
```

**角色节点工厂模式**：

```python
def make_researcher_node(llm, rag, registry):
    async def node(state: MultiAgentState) -> dict:
        # ... 调 LLM 决定 query → 调 RAG/工具 → 返回 state 增量
    return node
```

为什么用工厂闭包而不是类？
- LangGraph 节点要求 `Callable[[State], dict | Awaitable[dict]]`
- 类的 `__call__` 也行，但闭包更轻、方便单测（直接 `make_xxx_node(fake_llm, fake_rag, ...)`）

### 2.3 `app/services/research/agent_v2.py`

Plan-and-Solve 实现：
- 节点：`plan_research → execute_step → reflect`
- `reflect` 节点判断 `current_step_index < len(plan)`，未完成则回 `execute_step`
- 与 `agent.py`（ReAct）共享 `recall_memory` / `save_memory` / nodes 中的工具调用逻辑

### 2.4 `app/services/research/streaming.py`

| 函数 | 作用 |
|------|------|
| `stream_research_events(mode, ...)` | 以 SSE 格式 yield update/final 事件 |
| `_merge_state(state, update)` | 合并 LangGraph astream 的增量到完整 state |
| `_summarize_update(update)` | 给前端的人类可读 1 行摘要 |

### 2.5 `app/api/routes/memory.py`

```
GET    /api/v1/memory/sessions/{id}       # 看会话历史
DELETE /api/v1/memory/sessions/{id}       # 清掉某次会话
GET    /api/v1/memory/insights            # 列出所有长期洞见（分页）
GET    /api/v1/memory/insights/search?q=  # 关键词检索
DELETE /api/v1/memory/insights            # 全部清空（危险）
```

### 2.6 `app/api/routes/research.py`（修改）

新增：
- `POST /research` 增加 `mode=multi_agent / agent_v2`、`session_id` 字段
- `GET /research/stream` SSE 流式接口

---

## 3. 数据流：multi_agent 模式一次完整调用

```
1. POST /research {topic, mode=multi_agent, session_id=abc}
   │
   ▼
2. build_multi_agent_initial_state(topic, max_iter=3, top_k=5, session_id)
   │
   ▼
3. recall_memory(state)
   ├── memory_service.retrieve_relevant_insights(topic, k=3)
   └── state.prior_insights = [...]
   │
   ▼
4. plan_research(state)  ← LLMService.chat (JSON output: list[str])
   └── state.plan = ["子问题1", "子问题2", "子问题3"]
   │
   ▼
5. researcher(state)
   ├── 取 state.plan[i] 生成 query
   ├── RAGService.search + ToolRegistry.execute(web_search)
   └── state.search_results += [...], state.queries += [query]
   │
   ▼
6. analyst(state)
   ├── LLM 综合 state.search_results
   ├── state.analysis = "...."
   └── state.evaluation = "sufficient" | "more_research"
   │
   ├── more_research → 回 researcher (但 iteration++)
   │   若 iteration >= max → 强制 sufficient
   ▼
7. writer(state)
   └── state.report = "# Markdown 报告..."
   │
   ▼
8. reviewer(state)
   ├── LLM 检查报告质量
   ├── state.review_verdict = "approved" | "needs_revision"
   └── state.review_feedback = "..."
   │
   ├── needs_revision → 回 writer (revision_count++)
   │   若 revision_count >= max → 强制 approved
   ▼
9. save_memory(state)
   ├── 抽取 report 中的 1-3 条 insight
   └── memory_service.save_insight(...)
   │
   ▼
10. 返回 dict {report, queries, plan, analysis, review_verdict, agents_involved, ...}
```

---

## 4. 关键技术选型与取舍

| 决策点 | 选项 | 选择 | 理由 |
|--------|------|------|------|
| Memory 存储 | dict / SQLite / Qdrant | dict + JSON | 数据量小、便于单测；预留接口未来切换 |
| 长期检索 | 向量 / BM25 / token overlap | token overlap | 千条内足够；零依赖 |
| Memory 写入位置 | 每个节点 / 边界节点 | 边界节点 | 状态可追、单测可复现 |
| 多 Agent 通信 | prompt 拼接 / 共享 state | 共享 state | LangGraph 原生支持，避免 prompt 漂移 |
| 角色实现 | 类 / 工厂闭包 | 工厂闭包 | 更易注入 mock |
| 流式协议 | SSE / WebSocket | SSE | 单向推送够用，浏览器/curl 兼容 |
| 防死循环 | LLM 自判 / 硬编码 | 硬编码 | LLM 不可信，必须强制 |

---

## 5. 配置项（`app/core/config.py`）

```python
# Memory
memory_data_dir: str = "data/memory"
memory_max_insights: int = 1000
memory_session_ttl: int = 1800  # 30 min

# Multi-agent
multi_agent_max_iterations: int = 3
multi_agent_max_revisions: int = 2
```

环境变量同名（大写）。

---

## 6. 测试矩阵

| 文件 | 覆盖点 |
|------|--------|
| test_memory_service.py | session 增删、TTL 过期、insight 检索排序、容量淘汰、JSON 持久化、并发写 |
| test_memory_endpoint.py | 5 个 REST 端点的 happy/error path |
| test_multi_agent_roles.py | 4 个角色节点 + 2 个 router 的边界条件 |
| test_multi_agent_graph.py | 完整一次跑通；强制循环达上限 |
| test_research_agent_v2.py | Plan-and-Solve 节点路径 |
| test_research_endpoint_phase5.py | 4 种 mode + session_id 接入 |
| test_research_stream_endpoint.py | SSE 输出格式（data:\n\n）|
| test_research_streaming.py | _merge_state 的列表追加语义 |

---

## 7. 已知限制 & 未来工作

- **Memory 检索准确率**：token overlap 在中英文混合 query 下偏弱，>1k 条后建议切向量
- **角色 prompt 工程**：当前 4 个角色 prompt 还是 inline 写在 roles.py，未来抽到 prompt_service.py 统一管理
- **写作返工逻辑**：reviewer 反馈是字符串，writer 简单拼到 system prompt 末尾。可改为结构化 diff
- **持久化原子性**：JSON 全量重写，崩溃中途可能损坏。改用 `tempfile + os.replace` 即可（单行修复）
