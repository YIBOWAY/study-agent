# Phase 4 Workflow & Agent 执行文档（Runbook）

## 1. 前置条件

Phase 0+1+2+3 环境已正常运行。Phase 4 新增一个外部依赖 `langgraph`。

确认环境：

```bash
conda activate ai-agent
python --version   # 3.11.x
```

## 2. 依赖安装

```bash
cd E:\programs\AI_Agent_program\8w-plan
pip install -r requirements.txt
```

验证关键依赖：

```bash
python -c "from langgraph.graph import StateGraph, END; print('langgraph OK')"
python -c "import httpx; print('httpx OK')"
```

Phase 4 新增依赖仅 `langgraph>=0.2.0`。Tavily Web Search 和代码执行不需要额外依赖（分别用 httpx 和标准库 asyncio.create_subprocess_exec）。

## 3. 环境变量配置

在 `.env` 中追加以下配置：

```env
# ─── Tavily Web Search ───
TAVILY_API_KEY=tvly-dev-xxxxxxxxxxxxxxxxxxxxxxxx
TAVILY_BASE_URL=https://api.tavily.com

# ─── Code Execution Tool ───
ENABLE_CODE_EXECUTION_TOOL=false

# ─── Research Settings ───
RESEARCH_MAX_ITERATIONS=3
RESEARCH_TOP_K=5
```

**说明**：

| 变量 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| `TAVILY_API_KEY` | str | `""` | Tavily Search API key（Researcher plan，免费 1000 credits/月） |
| `TAVILY_BASE_URL` | str | `https://api.tavily.com` | Tavily API 基础 URL |
| `ENABLE_CODE_EXECUTION_TOOL` | bool | `false` | 是否注册 execute_python 工具（安全考量默认关闭） |
| `RESEARCH_MAX_ITERATIONS` | int 1-10 | 3 | Agent 模式最大搜索轮次 |
| `RESEARCH_TOP_K` | int 1-20 | 5 | 每次搜索的结果数 |

**重要**：
- `TAVILY_API_KEY` 不配置时，搜索节点会跳过 Web 搜索，只用本地知识库。不会报错。
- `ENABLE_CODE_EXECUTION_TOOL=false` 时，`/tools/list` 会列出 4 个工具（无 execute_python）。设为 `true` 后列出 5 个。
- `RESEARCH_MAX_ITERATIONS` 和 `RESEARCH_TOP_K` 都有合理默认值，**不配置也能运行**。

## 4. 启动服务

```bash
cd E:\programs\AI_Agent_program\8w-plan
conda activate ai-agent
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

确认 Swagger 文档中出现 Research 相关端点：访问 `http://127.0.0.1:8001/docs`，应看到 `research` 标签下的 `POST /api/v1/research` 端点。

> **注意**：如果需要多源搜索完整工作，需要：
> 1. Qdrant 已启动且有已 ingest 的数据（参考 Phase 2 Runbook）
> 2. TAVILY_API_KEY 已配置（否则只用本地知识库）

## 5. 接口验证

### 5.1 查看已注册工具

```bash
curl http://127.0.0.1:8001/api/v1/tools/list
```

PowerShell：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/tools/list" | ConvertTo-Json -Depth 5
```

预期返回工具列表中包含 `web_search`：

```json
{
    "tools": [
        {"name": "get_current_time", "description": "..."},
        {"name": "calculate", "description": "..."},
        {"name": "search_knowledge_base", "description": "..."},
        {"name": "web_search", "description": "Search the web for real-time information using Tavily Search API."}
    ]
}
```

如果 `ENABLE_CODE_EXECUTION_TOOL=true`，还会有 `execute_python`。

### 5.2 Web Search 工具对话测试

```powershell
$body = @{
    message = "搜索最新的 RAG 技术进展"
    enabled_tools = @("web_search")
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8001/api/v1/tools/chat" `
    -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 5
```

预期：LLM 调用 web_search 工具，返回带网络搜索结果的回答。如果 TAVILY_API_KEY 未配置，会返回错误信息 "Tavily API key is not configured"。

### 5.3 代码执行工具对话测试（需要 ENABLE_CODE_EXECUTION_TOOL=true）

```powershell
$body = @{
    message = "帮我计算斐波那契数列前20项"
    enabled_tools = @("execute_python")
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8001/api/v1/tools/chat" `
    -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 5
```

预期：LLM 生成 Python 代码，execute_python 工具执行后返回结果。

### 5.4 Workflow 模式研究

```powershell
$body = @{
    topic = "RAG 分块策略对检索质量的影响"
    mode = "workflow"
    max_iterations = 3
    top_k = 5
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8001/api/v1/research" `
    -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 10
```

预期返回：

```json
{
    "topic": "RAG 分块策略对检索质量的影响",
    "mode": "workflow",
    "report": "# 研究报告\n\n...",
    "queries": ["chunking strategy retrieval quality impact"],
    "steps": [
        {"node": "rewrite_query", "action": "Rewrote topic to search query", ...},
        {"node": "search_knowledge_base", "action": "Searched local knowledge base", ...},
        {"node": "web_search", "action": "Searched the web", ...},
        {"node": "generate_report", "action": "Generated research report", ...}
    ],
    "iterations_used": 1,
    "search_result_count": 8
}
```

**验证要点**：
- `iterations_used` 应为 1（Workflow 只搜索一轮）
- `steps` 应恰好 4 步：rewrite_query → search_knowledge_base → web_search → generate_report
- 如果无 Tavily key，web_search 步骤的 action 为 "Skipped web search"

### 5.5 Agent 模式研究

```powershell
$body = @{
    topic = "RAG 分块策略对检索质量的影响"
    mode = "agent"
    max_iterations = 3
    top_k = 5
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8001/api/v1/research" `
    -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 10
```

**验证要点**：
- `iterations_used` 可能为 1-3（取决于 LLM 对结果的评估）
- `steps` 中应包含 `evaluate_results` 节点
- 如果 LLM 认为第一轮结果不够，会看到 `refine_query` 节点和额外的搜索步骤
- `queries` 列表可能有多个查询（每轮一个）

### 5.6 对比 Workflow 和 Agent 结果

对同一个 topic 分别用 workflow 和 agent 模式，比较：
- `iterations_used`：Workflow 永远是 1，Agent 可能是 1-3
- `steps` 数量：Workflow 固定 4 步，Agent 可能 6-12 步
- `search_result_count`：Agent 通常更多（多轮搜索累积）
- `report` 质量：Agent 通常更详细（多角度覆盖）

## 6. 运行测试

```bash
cd E:\programs\AI_Agent_program\8w-plan
conda activate ai-agent
python -m pytest -v
```

预期：135 个测试全部通过。

Phase 4 新增测试分布：

| 测试文件 | 测试数 | 覆盖范围 |
|----------|--------|----------|
| `test_tools_builtin.py` | 9 新增 | web_search (4) + code_executor (5) |
| `test_research_nodes.py` | 9 | 5 个节点函数 + 多源搜索降级 |
| `test_research_workflow.py` | 1 | Workflow 完整路径 |
| `test_research_agent.py` | 3 | Agent 三种场景 |
| `test_research_endpoint.py` | 5 | API 端点 + 错误处理 |
| `test_tool_registry.py` | 1 新增 | enable_code_execution_tool 配置 |
| **合计** | **32 新增** | Phase 4 全覆盖 |

## 7. 完整工作流示例

### 场景：研究"向量数据库选型"

**步骤 1**：确保 Qdrant 运行、有已 ingest 的文档、TAVILY_API_KEY 已配置

**步骤 2**：用 Agent 模式发起研究

```powershell
$body = @{
    topic = "向量数据库选型对比：Qdrant vs Pinecone vs Weaviate"
    mode = "agent"
    max_iterations = 3
    top_k = 5
} | ConvertTo-Json

$result = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8001/api/v1/research" `
    -ContentType "application/json" -Body $body
```

**步骤 3**：检查执行路径

```powershell
$result.steps | Format-Table node, action -AutoSize
```

可能输出：

```
node                   action
----                   ------
rewrite_query          Rewrote topic to search query
search_knowledge_base  Searched local knowledge base
web_search             Searched the web
evaluate_results       Evaluated search results
refine_query           Generated refined query
search_knowledge_base  Searched local knowledge base
web_search             Searched the web
evaluate_results       Evaluated search results
generate_report        Generated research report
```

**步骤 4**：查看报告

```powershell
$result.report
```

## 8. 常见报错与排查

### 报错 1：`ValueError: Tavily API key is not configured.`

**场景**：直接通过 `/tools/chat` 调用 web_search 工具，但未配置 TAVILY_API_KEY

**解决**：在 `.env` 中设置 `TAVILY_API_KEY=tvly-dev-...`。如果不需要 Web 搜索，可以忽略——研究模式会自动跳过。

### 报错 2：`Tavily API error (401): ...`

**场景**：TAVILY_API_KEY 无效或已过期

**解决**：登录 https://app.tavily.com 检查 API key 状态和剩余 credits。

### 报错 3：`422 Unprocessable Entity` — 研究请求参数错误

**场景**：mode 不是 "workflow"/"agent"，或 topic 太短

**解决**：`mode` 只接受 `"workflow"` 或 `"agent"`。`topic` 最少 2 个字符。`max_iterations` 范围 1-10。

### 报错 4：`Blocked unsafe keyword: import os`

**场景**：execute_python 工具拦截了不安全的代码

**解决**：代码中不能包含文件/网络/系统操作相关的 import。这是教学级安全措施。

### 报错 5：Agent 模式延迟很高

**场景**：Agent 循环了多轮，每轮都有 LLM 调用 + 搜索

**诊断**：查看响应中的 `iterations_used`。如果接近 `max_iterations`，说明 LLM 很难被满足。

**解决**：降低 `max_iterations`（例如 2），或给更具体的 topic。

### 报错 6：`ImportError: No module named 'langgraph'`

**场景**：未安装 langgraph

**解决**：

```bash
pip install langgraph>=0.2.0
```

### 报错 7：研究报告为空

**场景**：`report` 字段为空字符串

**诊断**：检查 `steps` 中 `generate_report` 节点的 output_summary。如果包含错误信息，通常是 LLM API 调用失败。

**解决**：确认 LLM_API_KEY 和 LLM_BASE_URL 配置正确，LLM 服务可用。
