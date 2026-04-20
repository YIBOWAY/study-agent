# Phase 3 Tool Use 执行文档（Runbook）

## 1. 前置条件

Phase 0+1+2 环境已正常运行（参考 `excut_docs/phase0_1_execution.md` 和 `excut_docs/phase2_execution.md`）。

Phase 3 **无新增外部依赖**。所有能力基于已有的 httpx + FastAPI 栈实现。

## 2. 环境变量配置

在 `.env` 中追加以下配置：

```env
# ─── Tool Calling ───
TOOL_CALL_MAX_ITERATIONS=10
TOOL_CALL_TIMEOUT=30
```

**说明**：

| 变量 | 类型 | 默认值 | 含义 |
|------|------|--------|------|
| `TOOL_CALL_MAX_ITERATIONS` | int ≥ 1 | 10 | 单次对话中工具调用的最大轮次 |
| `TOOL_CALL_TIMEOUT` | int > 0 | 30 | 单个工具执行的超时时间（秒）|

两个配置项都有合理默认值，**不配置也能运行**。

## 3. 启动服务

```bash
cd E:\programs\AI_Agent_program\8w-plan
conda activate ai-agent
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

确认 Swagger 文档中出现 Tools 相关端点：访问 `http://127.0.0.1:8001/docs`，应看到 `tools` 标签下的两个端点。

> **注意**：如果同时需要 `search_knowledge_base` 工具正常工作，需要确保 Qdrant 已启动且有已 ingest 的数据。参考 Phase 2 Runbook。

## 4. 接口验证

### 4.1 查看已注册工具

```bash
curl http://127.0.0.1:8001/api/v1/tools/list
```

PowerShell：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/tools/list" | ConvertTo-Json -Depth 5
```

预期返回：

```json
{
    "tools": [
        {
            "name": "get_current_time",
            "description": "Get the current date and time for a given timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone name such as Asia/Shanghai or UTC."
                    }
                }
            }
        },
        {
            "name": "calculate",
            "description": "Safely evaluate a mathematical expression.",
            "parameters": { "..." }
        },
        {
            "name": "search_knowledge_base",
            "description": "Search the project's knowledge base using the existing RAG retrieval pipeline.",
            "parameters": { "..." }
        }
    ]
}
```

### 4.2 工具对话 — 单工具调用

```bash
curl -X POST http://127.0.0.1:8001/api/v1/tools/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京现在几点了？", "enabled_tools": ["get_current_time"]}'
```

PowerShell：

```powershell
$body = @{
    message = "北京现在几点了？"
    enabled_tools = @("get_current_time")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/tools/chat" -Method Post -Body $body -ContentType "application/json"
```

预期：
- `reply` 包含当前时间
- `tool_calls_made` 有 1 条记录：`get_current_time`

### 4.3 工具对话 — 多工具并行

```bash
curl -X POST http://127.0.0.1:8001/api/v1/tools/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京现在几点？23乘以47等于多少？", "enabled_tools": ["get_current_time", "calculate"]}'
```

预期：
- `reply` 同时包含时间和计算结果
- `tool_calls_made` 有 2 条记录

### 4.4 工具对话 — 知识库搜索（需要 Qdrant + 已 ingest 数据）

```bash
curl -X POST http://127.0.0.1:8001/api/v1/tools/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我查一下学习计划中关于RAG的内容"}'
```

预期：
- LLM 自动决定调用 `search_knowledge_base`
- `tool_calls_made` 中可看到搜索查询和结果摘要
- `reply` 基于检索结果回答

### 4.5 工具对话 — 不指定工具（使用全部）

```bash
curl -X POST http://127.0.0.1:8001/api/v1/tools/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "现在几点了？顺便帮我算 sqrt(144) + 25"}'
```

不传 `enabled_tools` 时，所有已注册工具都可用。LLM 自主选择。

### 4.6 覆盖 max_iterations

```bash
curl -X POST http://127.0.0.1:8001/api/v1/tools/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我做个复杂计算", "max_iterations": 3}'
```

`max_iterations` 范围 1-20，超出范围返回 422。

## 5. 运行测试

```bash
cd E:\programs\AI_Agent_program\8w-plan
python -m pytest -v --tb=short
```

只运行 Phase 3 测试：

```bash
python -m pytest tests/test_tool_registry.py tests/test_tools_builtin.py tests/test_tool_calling_loop.py tests/test_tools_endpoint.py -v
```

预期结果：103/103 通过（Phase 0+1: 2 个，Phase 2: 77 个，Phase 3: 24 个）。

## 6. 添加自定义工具

如果你想新增一个工具，步骤如下：

### 步骤 1：创建工具文件

在 `app/services/tools/` 下新建文件，例如 `weather.py`：

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class BuiltinTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Any

async def _get_weather(arguments: dict[str, Any]) -> str:
    city = str(arguments.get("city") or "").strip()
    if not city:
        raise ValueError("city is required")
    # 实际实现：调用天气 API
    return f"Weather in {city}: 25°C, sunny"

def build_weather_tool() -> BuiltinTool:
    return BuiltinTool(
        name="get_weather",
        description="Get the current weather for a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. Beijing, Tokyo"
                }
            },
            "required": ["city"]
        },
        handler=_get_weather,
    )
```

### 步骤 2：在 `__init__.py` 中导出

编辑 `app/services/tools/__init__.py`：

```python
from app.services.tools.weather import build_weather_tool
# 加入 __all__
```

### 步骤 3：在 Registry 中注册

编辑 `app/services/tool_registry.py` 的 `_register_defaults()`：

```python
def _register_defaults(self) -> None:
    # ... 已有工具 ...
    weather_tool = build_weather_tool()
    self.register_tool(
        name=weather_tool.name,
        description=weather_tool.description,
        parameters_schema=weather_tool.parameters,
        handler=weather_tool.handler,
    )
```

### 步骤 4：编写测试

在 `tests/test_tools_builtin.py` 中添加测试用例。

### 步骤 5：验证

```bash
python -m pytest -v
curl http://127.0.0.1:8001/api/v1/tools/list  # 确认新工具出现
```

## 7. 完整工作流示例

```
1. （如需知识库搜索）启动 Qdrant
   docker start qdrant

2. 启动服务
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

3. 查看可用工具
   GET /api/v1/tools/list

4. 工具对话测试
   POST /api/v1/tools/chat → 观察 tool_calls_made

5. 运行测试
   python -m pytest -v

6. 需要新工具 → 按第 6 节步骤添加
```

## 8. 常见报错与排查

### 报错 1：`400 Bad Request` — "Unknown tool(s): xxx"

原因：`enabled_tools` 中包含了未注册的工具名。

排查：
```bash
curl http://127.0.0.1:8001/api/v1/tools/list  # 查看实际注册的工具名
```

### 报错 2：工具对话响应 `"Tool call limit reached before a final answer was produced."`

原因：LLM 在 `max_iterations` 轮内没有生成最终回答，一直在调工具。

排查：
- 检查 `tool_calls_made` 看 LLM 在循环做什么
- 尝试增大 `max_iterations`（请求中覆盖，上限 20）
- 检查工具是否持续返回错误导致 LLM 重试

### 报错 3：`search_knowledge_base` 工具返回 "No knowledge base results found."

原因：Qdrant 中无数据或未启动。

排查：
```bash
curl http://localhost:6333/collections/phase2_chunks  # 检查集合和数据量
```

### 报错 4：`422 Unprocessable Entity` — max_iterations

原因：`max_iterations` 超出范围（需 1-20）。

### 报错 5：工具执行超时

原因：某个工具执行超过 `TOOL_CALL_TIMEOUT` 秒。

`tool_calls_made` 中该条目的 `error` 会包含超时信息。可在 `.env` 中调大 `TOOL_CALL_TIMEOUT`。

### 报错 6：LLM 不调用工具，直接回答

原因：LLM 认为不需要工具就能回答（这是正常行为）。

如果期望 LLM 使用工具，可在 system_prompt 中明确指示，或改进问题措辞。
