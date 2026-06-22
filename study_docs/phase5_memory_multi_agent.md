# Phase 5：Memory 与多 Agent 协作

> 目标：给 Agent 装上"记忆"，并让多个角色 Agent 协作完成研究任务
> 前置要求：完成 Phase 4（Workflow & Agent）
> 预计时间：有工程经验 4-7 天，零基础 2 周

---

## 0. 为什么需要 Phase 5

Phase 4 的 Agent 已经能"边搜边想"，但有两个明显短板：

1. **没有记忆**：每次对话都是"失忆症患者"——上次回答过什么、用户偏好什么、哪些主题已研究过，全都不记得。
2. **单兵作战**：研究、分析、写作、审核全靠一个 LLM 角色搞定，prompt 越写越胖，能力越摊越薄。

Phase 5 解决这两件事：
- 给 Agent **加 Memory**：跨会话保留"主题历史"和"高质量洞见"
- 把 Agent 拆成 **多角色协作**：研究员（Researcher）→ 分析师（Analyst）→ 写作员（Writer）→ 审核员（Reviewer）

---

## 1. Memory 系统：三层设计

很多教程把 Memory 讲得很玄。本质就是**三个时间尺度的存储**：

| 层级 | 生命周期 | 存什么 | 在本项目里 |
|------|---------|--------|----------|
| **工作记忆** | 单次请求 | LangGraph state 里的 messages、search_results | `MultiAgentState` |
| **会话记忆** | 同一 session_id 下持续 | 当前会话讨论过的 topics + insights | `MemoryService._sessions` |
| **长期记忆** | 永久持久化 | 跨会话有价值的洞见，落盘 JSON | `MemoryService._insights` + `data/memory/long_term.json` |

### 1.1 为什么不直接用向量数据库

很多人一上来就用 Qdrant 存 Memory。我们的选择是**先用最简方案**：
- 会话记忆：进程内 dict，会话过期（默认 30 分钟 TTL）自动失效
- 长期记忆：JSON 文件 + 关键词重叠匹配

理由：
- 长期记忆 < 1000 条时，关键词匹配的命中率不输向量检索
- 不引入额外依赖，开发/调试/单测都更轻
- 接口足够稳定，后续要换向量后端就在 `retrieve_relevant_insights` 里替换实现

> **学习要点**：Memory 设计的第一原则是"**先证明你需要它**"。能用 dict 解决的别上 Redis，能用 JSON 解决的别上 Postgres。

### 1.2 关键 API

```python
class MemoryService:
    async def add_session_context(session_id, topic, insights): ...
    async def get_session_context(session_id) -> SessionMemory | None: ...
    async def save_insight(topic, insight, source_count, session_id): ...
    async def retrieve_relevant_insights(query, top_k=3) -> list[InsightRecord]: ...
```

API 故意做得**短小**：四个核心方法覆盖 90% 需求，剩下 10% 由调用方拼装。

### 1.3 Memory 在 LangGraph 里的接入位置

```
START → recall_memory → plan → researcher → analyst → writer → reviewer → save_memory → END
        │                                                                 │
        └── 注入 prior_insights                          抽取本轮的 insight 落库
```

两个边界节点：
- `recall_memory`：从 `MemoryService` 拿 top-k 相关 insight，写入 state.prior_insights
- `save_memory`：从 reviewer 通过的报告里抽取本轮关键洞见，写回 MemoryService

> **常见坑**：把 Memory 读写分散到每个节点里 → 状态难追、单测难写。  
> **正确做法**：只在图的入口/出口节点跟 Memory 交互，中间节点只读 state。

---

## 2. 多 Agent 协作：Supervisor 与 Specialist

### 2.1 为什么要拆角色

Phase 4 的研究 Agent 把"搜→评→改写→产报告"塞进一个循环，问题：
- System prompt 越写越长，模型越来越"分心"
- 想增强"审核环节"就得动整个 prompt
- 调试时分不清"是搜得不好还是写得不好"

拆成多角色后：
- 每个角色只关心一件事，prompt 短而精
- 角色之间通过 **共享 state** 通信，而不是通过 prompt 拼接
- 可以单独评估某一个角色（例如只测 reviewer 的判定准确率）

### 2.2 本项目的角色分工

| Agent | 输入 | 输出 | 决定下一步的关键字段 |
|-------|------|------|--------------------|
| **Planner** | topic, prior_insights | plan: list[str]（拆解后的 3-5 个子问题） | — |
| **Researcher** | plan 当前步、queries | search_results 增量、queries 增量 | — |
| **Analyst** | search_results 全量 | analysis（一段中文分析）、`evaluation` ∈ {sufficient, more_research} | route_after_analysis |
| **Writer** | analysis, search_results | report（Markdown 格式） | — |
| **Reviewer** | report, topic | review_verdict ∈ {approved, needs_revision}, review_feedback | route_after_review |

### 2.3 状态图

```
START
  │
  ▼
recall_memory ──▶ plan_research ──▶ researcher ──▶ analyst
                                       ▲              │
                                       │      sufficient│  more_research
                                       └──────────────┤
                                                      ▼
                                                   writer ◀─── revise
                                                      │
                                                      ▼
                                                  reviewer
                                                      │ approved
                                                      ▼
                                                save_memory ──▶ END
```

两个 conditional edge：
- `analyst` 后：信息够 → writer，不够 → 回 researcher
- `reviewer` 后：通过 → save_memory，不通过 → 回 writer 修改

### 2.4 防止死循环

任何带 LLM 决策的循环都必须有**硬上限**：
- `iteration < max_iterations`：研究循环上限（默认 3）
- `revision_count < max_revisions`：写作返工上限（默认 2）

> **学习要点**：LLM 永远可能"我觉得还不够好"地无限循环下去。**硬编码上限**是 production-grade Agent 的红线。

---

## 3. 单 Agent 升级：agent_v2（Plan-and-Solve）

Phase 4 的 agent 是 ReAct 风格："看一步走一步"。Phase 5 同时新增了一个 **agent_v2**，采用 **Plan-and-Solve** 风格：

```
plan_research（先拆问题）→ research_step（按计划执行）→ reflect → 下一步 / 结束
```

差异：

| 维度 | agent (ReAct) | agent_v2 (Plan-and-Solve) |
|------|--------------|--------------------------|
| 决策粒度 | 每步独立判断 | 先有总体计划，再按步执行 |
| 适合场景 | 探索性强、不知道要找什么 | 主题清晰、需要系统性覆盖 |
| 调试 | 难（路径每次不同） | 容易（计划明确） |

`/research` 端点支持 `mode = workflow / agent / agent_v2 / multi_agent`，让你**亲手对比四种**。

---

## 4. SSE 流式返回（关键工程细节）

研究 Agent 跑完一次可能 30-90 秒。如果同步返回，前端用户会以为系统卡死。

我们在 `app/services/research/streaming.py` 里实现了 LangGraph 的增量事件流：
- 每个节点完成都会 yield 一个 `update` 事件，前端实时显示"正在搜索…"、"分析中…"
- 使用 SSE（Server-Sent Events）协议，浏览器原生支持
- FastAPI 端点：`GET /research/stream`

```python
async def stream_research_events(...) -> AsyncIterator[str]:
    async for chunk in compiled.astream(initial_state):
        yield f"data: {json.dumps({'type': 'update', 'payload': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'final', 'payload': final_state})}\n\n"
```

> **常见坑**：SSE 必须以 `data: ...\n\n` 结尾，少一个 `\n` 浏览器就不刷新。

---

## 5. 完成本阶段你应当能回答

- [ ] 短期/会话/长期 Memory 各自适合什么数据？为什么不全用向量？
- [ ] LangGraph 里 Memory 应该接在图的什么位置？为什么不能"哪需要哪写"？
- [ ] Supervisor 模式 vs Hierarchical 模式 vs P2P 模式分别画图
- [ ] 多 Agent 系统的"硬上限"为什么是必须的？设多少合适？
- [ ] ReAct vs Plan-and-Solve 各自适合什么任务？
- [ ] SSE 和 WebSocket 的区别？什么时候选 SSE？

---

## 6. 推荐资料

| 主题 | 资源 |
|------|------|
| Anthropic：Building Effective Agents | 必读，明确指出"多 Agent 不是首选" |
| LangGraph 官方：Multi-Agent Patterns | 官方提供 supervisor / hierarchy 的对比 demo |
| Memory 综述论文 | "MemoryBank: Enhancing LLMs with Long-Term Memory"（参考思路即可） |
| SSE vs WebSocket | MDN Web Docs 比较两者，重点看场景区别 |
