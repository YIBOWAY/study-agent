# Phase 4：Workflow & Agent（工作流与智能体）

> 目标：理解确定性工作流（Workflow）与 LLM 驱动智能体（Agent）的本质区别，掌握 LangGraph 状态图编排
> 前置要求：完成 Phase 1（LLM + Prompt）、Phase 2（RAG）、Phase 3（Tool Use）
> 预计时间：有工程经验 3-5 天，零基础 1-2 周

---

## 0. 为什么需要 Workflow 和 Agent

Phase 1-3 我们建了一个"能查文档、能用工具的 LLM 助手"。但每次请求都是单轮的——用户问一个问题，LLM 回答一个答案。

真实的任务往往是**多步骤**的：

> "帮我研究一下 RAG 分块策略对检索质量的影响"
>
> 这需要：① 把研究主题变成搜索查询 → ② 搜索知识库和网络 → ③ 判断结果够不够 → ④ 不够就换角度再搜 → ⑤ 最终整理成报告

这种多步骤任务有两种编排方式：

| 方式 | 特点 | 类比 |
|------|------|------|
| **Workflow**（工作流） | 路径固定，步骤确定 | 流水线工人——每个人做固定工序 |
| **Agent**（智能体） | LLM 动态决策，路径不确定 | 自由职业者——自己判断下一步做什么 |

```
Workflow:  A → B → C → D（永远走同一条路）
Agent:    A → B → [LLM判断] → C 或回到 B（路径由 LLM 实时决定）
```

Phase 4 同时实现两种模式，让你**亲眼看到**区别。

---

## 1. Workflow 与 Agent 的核心区别

### 1.1 Workflow（确定性工作流）

```
START → 重写查询 → 搜索 → 生成报告 → END
```

- **路径固定**：不管搜索结果好不好，都直接生成报告
- **无决策**：没有 LLM 判断"结果够不够"这一步
- **可预测**：同样的输入，永远走同样的路径
- **适用场景**：简单任务、对延迟敏感、不需要迭代优化

### 1.2 Agent（LLM 驱动智能体）

```
START → 重写查询 → 搜索 → [LLM评估] ──够了──→ 生成报告 → END
                             │
                          不够 ↓
                        换角度重写 → 搜索 → [LLM评估] → ...
```

- **路径动态**：LLM 实时判断下一步做什么
- **有决策节点**：evaluate_results 是关键——LLM 评估搜索结果是否充分
- **条件循环**：如果不满意，换角度搜索，最多 N 轮
- **适用场景**：复杂研究、需要多角度覆盖、对质量要求高

### 1.3 为什么不全用 Agent？

| 维度 | Workflow | Agent |
|------|----------|-------|
| 延迟 | 低（固定 3 步） | 高（可能循环多轮） |
| 成本 | 低（LLM 调用次数固定） | 高（每轮额外 evaluate + refine） |
| 可控性 | 高（路径可预测） | 低（LLM 可能做出意外决策） |
| 质量 | 一般（一次搜索可能不够） | 较高（多轮覆盖多角度） |
| 调试 | 容易（路径固定） | 困难（每次可能不同路径） |

**结论**：简单任务用 Workflow，复杂任务用 Agent。这就是为什么我们同时实现两种模式。

---

## 2. LangGraph 状态图编排

### 2.1 什么是 LangGraph

LangGraph 是一个用**图**（Graph）来编排 LLM 应用的库。核心概念：

```
State（状态）+ Nodes（节点）+ Edges（边）= 一个可执行的工作流
```

- **State**：一个 TypedDict，存放整个流程的所有数据（查询、搜索结果、报告等）
- **Node**：一个函数，接收 State，返回要更新的字段
- **Edge**：节点之间的连接（固定边 or 条件边）

类比：
- State = 一张传递的工作单
- Node = 工位（每个工位负责填写工作单的某些字段）
- Edge = 传送带（决定工作单传给哪个工位）

### 2.2 State 的 Annotated 累积语义

```python
from typing import Annotated
import operator

class ResearchState(TypedDict):
    topic: str                                              # 覆盖语义
    queries: Annotated[list[str], operator.add]             # 累积语义
    search_results: Annotated[list[dict], operator.add]     # 累积语义
    report: str                                             # 覆盖语义
    iteration: int                                          # 覆盖语义
```

- **累积语义**（`Annotated[list, operator.add]`）：每次节点返回的列表会**追加**到已有列表后
- **覆盖语义**（普通字段）：每次节点返回的值直接**替换**旧值

为什么需要累积？因为 Agent 可能搜索多轮，每轮的 queries 和 search_results 需要全部保留，不能被覆盖。

### 2.3 条件边（Conditional Edge）

```python
# Agent 图中的关键——条件路由
graph.add_conditional_edges(
    "evaluate_results",          # 从哪个节点出发
    route_function,              # 路由函数
    {
        "sufficient": "generate_report",   # 够了 → 生成报告
        "needs_more": "refine_query",      # 不够 → 换角度搜
    },
)
```

路由函数的逻辑：

```python
def _route_after_evaluation(state: ResearchState) -> str:
    if state["iteration"] >= state["max_iterations"]:
        return "sufficient"     # 安全阀：达到上限强制结束
    if state["evaluation"] == "sufficient":
        return "sufficient"     # LLM 认为够了
    return "needs_more"         # 继续搜索
```

**关键设计**：`max_iterations` 是安全阀。即使 LLM 永远觉得"不够"，也会在达到上限后强制结束。

### 2.4 节点函数的工厂模式

本项目用工厂函数创建节点：

```python
def make_search_node(rag_service, tool_registry) -> NodeHandler:
    async def search(state: ResearchState) -> dict[str, Any]:
        # 使用闭包捕获的 rag_service 和 tool_registry
        ...
    return search
```

为什么用工厂？
- 节点函数需要依赖（LLMService、RAGService、ToolRegistry）
- LangGraph 要求节点函数签名是 `(state) -> dict`
- 工厂函数通过**闭包**把依赖注入进去，保持节点函数签名干净

---

## 3. 多源搜索（RAG + Web 并行）

### 3.1 为什么需要多源

Phase 2 只有本地知识库（RAG），Phase 4 的搜索节点同时查询两个来源：

```
                    ┌── RAGService.search() ──→ 知识库结果
搜索查询 ─→ 并行 ──┤
                    └── web_search 工具 ──→ 网络结果
                                              ↓
                                         合并 + 标记来源
```

### 3.2 asyncio.gather 并行执行

```python
await asyncio.gather(search_knowledge_base(), search_web())
```

两个搜索**同时发出**，不需要等一个完成再做另一个。总延迟 ≈ max(RAG延迟, Web延迟)，而不是两者之和。

### 3.3 优雅降级

| 场景 | 行为 |
|------|------|
| Tavily API key 未配置 | 跳过 Web 搜索，只用知识库结果 |
| RAG 搜索失败 | Web 结果仍然返回，steps 记录 RAG 错误 |
| Web 搜索失败 | RAG 结果仍然返回，steps 记录 Web 错误 |
| 两个都失败 | 返回空结果，后续节点可以处理 |

**关键原则**：一个数据源的失败不应阻塞另一个。这是分布式系统的基本设计——部分失败 ≠ 全部失败。

### 3.4 结果标记

每条搜索结果都标记了来源：

```python
{
    "source": "knowledge_base",  # 或 "web"
    "query": "chunking strategy",
    "text_snippet": "...",
    "score": 0.9,
    "title": "guide.pdf",
    "url": None                  # 知识库结果无 URL
}
```

标记来源的好处：
- 生成报告时可以标注"来自本地文档"或"来自网络"
- 调试时知道哪个源的结果被使用
- 未来可以对不同来源设置不同的可信度权重

---

## 4. Web Search 工具（Tavily）

### 4.1 为什么选 Tavily

| 方案 | 优点 | 缺点 |
|------|------|------|
| Google Search API | 全面 | 配置复杂，免费额度少 |
| Bing Search API | 微软生态 | 需要 Azure 订阅 |
| **Tavily** | AI 搜索优化，API 简洁 | 免费额度 1000/月 |
| SerpAPI | 多引擎 | 贵 |

Tavily 的优势：结果已经是**AI 友好的文本摘要**（不是原始网页 HTML），特别适合喂给 LLM。

### 4.2 实现要点

```python
# 直接用 httpx，不引入 tavily-python SDK
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"query": query, "max_results": 5},
    )
```

为什么不用官方 SDK？
- 项目约束：httpx 是唯一 HTTP 客户端
- Tavily REST API 很简单，直接调就行
- 减少依赖 = 减少维护负担

### 4.3 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | 必填 | 搜索查询 |
| `max_results` | int | 5 | 返回结果数（1-10） |
| `search_depth` | str | "basic" | "basic" 或 "advanced"（更深入但更慢） |
| `topic` | str | "general" | "general"、"news"、"finance" |

---

## 5. 沙箱代码执行工具

### 5.1 为什么需要代码执行

LLM 擅长生成代码，但**不能运行代码**。给它一个沙箱执行工具，它就能：
- 做复杂计算（比 calculate 工具更灵活）
- 验证自己写的代码
- 数据处理（排序、统计、格式转换）

### 5.2 沙箱设计

```
用户代码 → 关键词检查 → 写入临时文件 → 子进程执行 → 捕获输出 → 清理文件
```

**三层防护**：

1. **长度限制**：代码不能超过 5000 字符
2. **关键词黑名单**：
   ```python
   ["import os", "import sys", "import subprocess", "import shutil",
    "__import__", "eval(", "exec(", "open(",
    "import socket", "import http", "import requests"]
   ```
3. **超时限制**：最多 30 秒，超时 kill 进程

### 5.3 为什么用子进程而不是 exec/eval

| 方式 | 安全性 | 说明 |
|------|--------|------|
| `exec(code)` | 极低 | 在当前进程执行，可以访问所有变量、修改状态 |
| `eval(code)` | 低 | 只能执行表达式，但仍在当前进程 |
| **`subprocess`** | 中 | 独立进程，崩溃不影响主服务 |
| Docker 容器 | 高 | 完全隔离，但需要额外基础设施 |

本项目使用 subprocess（教学级别）。生产环境应升级到 Docker 或 gVisor。

### 5.4 输出控制

- stdout/stderr 各自截断到 2000 字符
- 防止 `print("a" * 10**8)` 这种输出爆炸
- 清晰的返回格式：`Exit code: N\n\nSTDOUT:\n...\n\nSTDERR:\n...`

---

## 6. Action Trace（步骤追踪）

### 6.1 为什么需要追踪

Agent 的行为是动态的。如果不记录每一步，出问题时完全无法调试：

> "为什么报告质量差？" → 看 trace →
> 原来第 2 轮搜索失败了，只用了第 1 轮的结果

### 6.2 Trace 结构

```python
{
    "node": "search",                    # 哪个节点
    "action": "Searched the web",        # 做了什么
    "output_summary": "Found 5 results", # 结果摘要（截断到 200 字符）
    "timestamp": "2026-04-20T10:30:00+00:00"
}
```

每个节点在执行前后都往 state.steps 追加记录。由于使用 `Annotated[list, operator.add]`，所有步骤自动累积，不会互相覆盖。

### 6.3 Trace 对比

```
Workflow trace:  rewrite_query → search_kb → web_search → generate_report（固定 4 步）
Agent trace:     rewrite_query → search_kb → web_search → evaluate → refine → search_kb → web_search → evaluate → generate_report（7 步，搜了 2 轮）
```

API 响应中 `steps` 字段让调用方看到完整执行路径。这是**可观测性**的基础。

---

## 7. 关键概念总结

### 7.1 Graph Thinking（图思维）

传统编程是写一个函数调另一个函数。LangGraph 是：
1. 定义**状态**（所有数据放一起）
2. 定义**节点**（每个函数只负责更新状态的一部分）
3. 定义**边**（节点之间怎么连接）
4. 编译成图，然后 `ainvoke()` 执行

好处：
- 流程可视化（图就是最好的文档）
- 节点可复用（Workflow 和 Agent 共享 5 个节点）
- 条件路由自然表达

### 7.2 Workflow vs Agent 的选择框架

```
你的任务是否需要根据中间结果做不同的决策？
├─ 是 → Agent（用条件边）
└─ 否 → Workflow（用固定边）

你能否承受多轮 LLM 调用的延迟和成本？
├─ 是 → Agent
└─ 否 → Workflow

你需要可预测的执行路径吗？
├─ 是 → Workflow
└─ 否 → Agent 也可以
```

### 7.3 安全阀设计模式

Agent 有循环能力 → 必须有终止条件：
- `max_iterations`：物理上限，防止无限循环
- 节点级别检查（evaluate_results 到达上限时强制返回 "sufficient"）
- 路由级别检查（_route_after_evaluation 双重验证）

**永远不要信任 LLM 会自行终止循环**。一定要有硬限制。

---

## 8. 本项目的设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 图编排库 | LangGraph | 轻量、与 LLM 生态兼容、不引入 langchain-openai |
| 搜索策略 | RAG + Web 并行 | 多源提高覆盖率，asyncio.gather 降低延迟 |
| Web 搜索 | Tavily + httpx | API 简洁、AI 优化结果、不引入额外 SDK |
| 代码执行 | subprocess 沙箱 | 教学级隔离，平衡安全性和实现复杂度 |
| 节点共享 | 5 个节点两个图复用 | DRY 原则，修改一处两种模式都受益 |
| 代码执行注册 | 默认关闭，配置启用 | 安全考量，需要显式 opt-in |
| 结果标记 | source 字段 | 可追溯、可调试、可扩展 |
