# Phase 3：Tool Use 与 Function Calling

> 目标：理解 LLM 如何决策并调用外部工具，掌握 Function Calling 的工程实现
> 前置要求：完成 Phase 1（LLM + Prompt），Phase 2（RAG）有助于理解 search_knowledge_base 工具
> 预计时间：有工程经验 3-5 天，零基础 1-2 周

---

## 0. 为什么需要 Tool Use

没有工具的 LLM 只是一个"文本生成器"——它只能回答训练数据范围内的问题，不能查时间、不能算数学、不能查你的数据库。

Tool Use（又叫 Function Calling）的思路：

> 不让 LLM 自己算/查/做，而是让 LLM **决定**该调哪个工具、传什么参数。你的代码负责真正执行，然后把结果反馈给 LLM，LLM 再基于结果生成最终回答。

```
用户提问 → LLM 决定调哪个工具 → 你的代码执行工具 → 结果返回给 LLM → LLM 生成最终回答
```

类比：
- 不用 Tool Use = 学生闭卷考试（只能靠记忆，算数可能出错）
- 用 Tool Use = 学生可以用计算器、查字典、上网搜索

**关键认知**：LLM 本身不会"调用"任何函数。它只是输出一个 JSON，说"我想调 `calculate`，参数是 `{"expression": "23 * 47"}`"。真正执行是你的代码。LLM 只负责**决策**。

---

## 1. Function Calling 工作原理

### 1.1 完整流程

```
┌───────────────────────────────────────────────────┐
│  1. 注册工具：告诉 LLM 有哪些工具可用              │
│     → 每个工具有 name, description, parameters     │
│     → parameters 用 JSON Schema 描述               │
│                                                     │
│  2. 用户提问："北京现在几点？23 × 47 等于多少？"    │
│                                                     │
│  3. LLM 分析后输出 tool_calls：                     │
│     [{name: "get_current_time", args: {...}},       │
│      {name: "calculate", args: {...}}]              │
│                                                     │
│  4. 你的代码执行这些函数，得到结果                   │
│                                                     │
│  5. 把结果以 role="tool" 消息追加到对话              │
│                                                     │
│  6. 再次调用 LLM，LLM 看到结果后生成最终回答        │
│                                                     │
│  7. 如果 LLM 还想调工具 → 回到步骤 3（循环）       │
│     如果 LLM 直接回答 → 流程结束                    │
└───────────────────────────────────────────────────┘
```

### 1.2 OpenAI 兼容的 Tools 格式

API 请求中 `tools` 参数是一个数组，每个元素描述一个可用工具：

```json
{
    "type": "function",
    "function": {
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
    }
}
```

三要素：
- **name**：唯一标识符，LLM 用它来指定调哪个工具
- **description**：告诉 LLM 什么时候该用这个工具（这是最关键的，写不好 LLM 会选错工具）
- **parameters**：JSON Schema，描述参数的类型、约束和含义

### 1.3 API 响应中的 tool_calls

当 LLM 决定调用工具时，响应中 `message` 会包含 `tool_calls` 字段：

```json
{
    "role": "assistant",
    "content": null,
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "calculate",
                "arguments": "{\"expression\": \"23 * 47\"}"
            }
        }
    ]
}
```

注意：
- `content` 通常为 `null`（LLM 选择调工具而不是直接回答）
- `arguments` 是**字符串**（JSON 序列化的），需要你 `json.loads()` 解析
- `id` 用于后续匹配工具结果（`tool_call_id`）
- 一次响应可能包含**多个** tool_calls（并行调用）

### 1.4 工具结果的反馈格式

执行完工具后，将结果作为 `role="tool"` 消息追加：

```json
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "name": "calculate",
    "content": "1081"
}
```

`tool_call_id` 必须匹配 LLM 响应中对应的 `id`，否则 API 会报错。

---

## 2. 工具定义的设计原则

### 2.1 Description 写作技巧

工具的 `description` 决定了 LLM 什么时候选择它。好的 description 需要：

| 原则 | 好的写法 | 坏的写法 |
|------|----------|----------|
| 说清楚**何时使用** | "Search the knowledge base when the user asks about project documents or internal data" | "Search knowledge base" |
| 说清楚**不能做什么** | "Only evaluates mathematical expressions, not text queries" | "Calculator" |
| 避免歧义 | "Get the current wall-clock time in a specified timezone" | "Get time" |

### 2.2 Parameters Schema 设计

```python
{
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query for the knowledge base."  # 加描述
        },
        "top_k": {
            "type": "integer",
            "description": "Maximum number of results.",
            "default": 3  # 提供默认值
        }
    },
    "required": ["query"]  # 标明必填
}
```

要点：
- 每个参数都加 `description`，这是 LLM 理解参数含义的唯一线索
- 用 `required` 区分必填和可选
- 可选参数提供 `default`
- 参数类型精确（`integer` 而非 `number`，除非确实需要浮点）

### 2.3 常见坑

1. **Description 太模糊**：LLM 分不清两个工具的适用场景，乱调
2. **参数不加 description**：LLM 不知道 `q` 是搜索词还是问题，瞎填
3. **太多工具**：一次传 20+ 工具，LLM 选择准确率下降。实践中 5-10 个效果最好
4. **工具名不直观**：`func_1` 比 `search_knowledge_base` 差很多

---

## 3. 工具调用循环（Tool Calling Loop）

### 3.1 为什么需要循环

单轮工具调用不够用的场景：

- LLM 调了搜索工具，发现结果不够，想换个关键词再搜一次
- LLM 调了计算工具得到中间结果，还需要用这个结果再算一次
- LLM 先查时间，再根据时间决定调不同的工具

所以 Tool Calling 本质是一个**循环**：

```
while 还没得到最终答案 and 没超过最大轮次:
    response = call_llm(messages, tools)
    if response 包含 tool_calls:
        执行每个工具
        把结果追加到 messages
    else:
        返回 response.content  # 最终答案
```

### 3.2 你的项目实现

`llm_service.py` 中 `chat_with_tools` 方法实现了完整循环：

```python
async def chat_with_tools(
    self,
    user_message: str,
    tools: list[dict],
    tool_executor: ToolRegistry,
    max_iterations: int = 5,
    system_prompt: str | None = None,
) -> dict:
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_message},
    ]
    tool_calls_made = []

    for _ in range(max_iterations):
        message = await self._call_chat_completion(messages=messages, tools=tools)
        messages.append(assistant_message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return {"reply": content, "model": ..., "tool_calls_made": ...}

        # 并行执行所有工具
        results = await asyncio.gather(
            *[self._execute_tool_call(tc, tool_executor) for tc in tool_calls]
        )
        # 把每个结果以 role="tool" 追加
        for result in results:
            messages.append({"role": "tool", "tool_call_id": ..., "content": ...})

    return {"reply": "Tool call limit reached...", ...}
```

### 3.3 并行 vs 顺序调用

**并行调用**（你的项目实现）：
```
LLM 一次返回: [call_time, call_calculate]
→ asyncio.gather(execute_time, execute_calculate)
→ 两个工具同时执行
```

**顺序调用**（多轮循环）：
```
轮次 1: LLM 返回 call_search → 执行 → 反馈结果
轮次 2: LLM 看到搜索结果，返回 call_calculate → 执行 → 反馈结果
轮次 3: LLM 生成最终答案
```

实际中两者经常混合出现：一轮中并行调多个工具，跑多轮循环。

### 3.4 max_iterations 的重要性

没有 `max_iterations`，LLM 可能陷入无限循环：
- 工具报错 → LLM 重试 → 还是报错 → 无限循环
- LLM 搜索 → 觉得不够 → 再搜 → 觉得还不够 → 永远不满意

你的项目中 `tool_call_max_iterations` 默认 10，API 请求可覆盖（上限 20）。

---

## 4. 工具注册表（Tool Registry）

### 4.1 设计模式

集中管理所有可用工具的注册、查询、执行：

```python
class ToolRegistry:
    def register_tool(name, description, parameters_schema, handler)
    def list_tools(enabled_tools=None) -> list[RegisteredTool]
    def get_openai_tools_schema(enabled_tools=None) -> list[dict]  # 转为 API 格式
    def execute(name, arguments) -> ToolCallRecord  # 白名单 + 执行
```

### 4.2 白名单安全

`execute()` 方法首先检查工具名是否在注册表中：

```python
async def execute(self, name: str, arguments: dict) -> ToolCallRecord:
    tool = self._tools.get(name)
    if tool is None:
        raise ValueError(f"Tool '{name}' is not registered.")
    # ... 执行
```

这就是白名单机制：只有明确注册过的工具才能被执行。LLM 如果幻觉出一个不存在的工具名（如 `exec_shell_command`），会被拦截。

### 4.3 超时保护

工具执行有超时限制（默认 30 秒）：

```python
raw_result = await asyncio.wait_for(
    tool.handler(arguments),
    timeout=self.settings.tool_call_timeout,
)
```

如果工具（如外部 API 调用）卡住，不会阻塞整个请求。

### 4.4 错误处理策略

工具执行出错时，不直接抛异常给用户，而是把错误信息作为工具结果反馈给 LLM：

```python
try:
    raw_result = await asyncio.wait_for(tool.handler(arguments), ...)
    return ToolCallRecord(tool=name, args=arguments, result=result)
except Exception as exc:
    return ToolCallRecord(tool=name, args=arguments, result="", error=str(exc))
```

LLM 收到错误后通常会：
- 换一种参数重试
- 告诉用户这个工具暂时不可用
- 尝试用其他方式回答

---

## 5. 内置工具详解

### 5.1 get_current_time — 时间查询

**用途**：返回指定时区的当前时间

**参数**：`timezone`（可选，默认 `Asia/Shanghai`）

**实现要点**：
- 使用 Python 3.9+ 的 `zoneinfo.ZoneInfo`（标准库，无第三方依赖）
- 无效时区名 → 抛出 `ValueError`，由 Registry 捕获

```python
from zoneinfo import ZoneInfo
zone = ZoneInfo("Asia/Shanghai")
current_time = datetime.now(zone)
```

**为什么这是好的第一个工具**：
- 纯本地计算，无外部依赖，不会因网络问题失败
- 结果确定性高，容易验证
- 让你专注于 Tool Use 流程本身，而不是工具实现的复杂性

### 5.2 calculate — 安全计算器

**用途**：安全地计算数学表达式

**参数**：`expression`（必填，如 `"23 * 47"` 或 `"sqrt(144)"`)

**安全设计**（这是本工具最重要的部分）：

| 风险 | 对策 |
|------|------|
| `eval()` 代码注入 | **完全不使用 eval()**，用 `ast.parse()` + 白名单遍历 |
| `__import__('os').system('rm -rf /')` | AST 只允许 `Constant`, `BinOp`, `UnaryOp`, `Call`（白名单函数）|
| `2 ** 999999999`（计算爆炸） | 限制指数绝对值 ≤ 100 |
| 超长表达式 | 限制 200 字符 |

核心逻辑是递归遍历 AST 节点，只允许白名单操作：

```python
_ALLOWED_BINARY_OPERATORS = {ast.Add, ast.Sub, ast.Mult, ast.Div, ...}
_ALLOWED_FUNCTIONS = {"sqrt": math.sqrt, "abs": abs, "round": round}

def _evaluate_expression(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):     # 数字常量 → OK
    if isinstance(node, ast.BinOp):        # 二元运算 → 检查白名单
    if isinstance(node, ast.Call):          # 函数调用 → 检查白名单
    raise ValueError("Unsupported")        # 其他一切 → 拒绝
```

**为什么不用 `ast.literal_eval`**：`literal_eval` 只能解析常量（数字、字符串、列表等），不支持运算表达式。`1 + 2` 会报错。

### 5.3 search_knowledge_base — 知识库搜索

**用途**：调用 Phase 2 RAG 的检索 + 精排能力

**参数**：
- `query`（必填）：搜索关键词
- `top_k`（可选，默认 3）：返回结果数
- `document_id`（可选）：限定搜索范围

**实现要点**：
- 复用 `RAGService.search()`，不重新实现检索逻辑
- 将 `SearchResult` 对象格式化为 LLM 可读的文本摘要
- 每条结果截断到 200 字符，避免工具输出过长撑爆 context

```python
result = await self.rag_service.search(query=query, top_k=top_k)
for item in result["results"]:
    snippet = item.text[:200]
    summary_lines.append(f"[{index}] {source_name}{location}: {snippet}")
return "\n".join(summary_lines)
```

**这是 RAG + Tool Use 的结合点**：Phase 2 的检索能力变成了 Phase 3 的一个可调用工具。LLM 可以在对话中动态决定是否需要查知识库。

---

## 6. API 端点设计

### 6.1 两个 Tool 端点

**`GET /api/v1/tools/list`** — 列出所有已注册工具

响应：
```json
{
    "tools": [
        {
            "name": "get_current_time",
            "description": "Get the current date and time for a given timezone.",
            "parameters": {...}
        },
        ...
    ]
}
```

**`POST /api/v1/tools/chat`** — 带工具的对话

请求：
```json
{
    "message": "北京现在几点了？顺便帮我算一下 23 × 47",
    "enabled_tools": ["get_current_time", "calculate"],
    "max_iterations": 5
}
```

响应：
```json
{
    "reply": "北京现在是 2026-04-19 14:30:00 CST。23 × 47 = 1081。",
    "model": "gpt-5.4",
    "tool_calls_made": [
        {"tool": "get_current_time", "args": {"timezone": "Asia/Shanghai"}, "result": "2026-04-19 14:30:00 CST", "error": null},
        {"tool": "calculate", "args": {"expression": "23 * 47"}, "result": "1081", "error": null}
    ]
}
```

### 6.2 enabled_tools 的设计

请求中 `enabled_tools` 允许客户端控制本次对话可用的工具子集：
- `null` / 不传 → 使用全部已注册工具
- `["calculate"]` → 只允许计算器
- `["missing_tool"]` → 400 错误

这比全局开关灵活：不同场景可以暴露不同的工具集。

### 6.3 tool_calls_made 的透明性

响应中 `tool_calls_made` 完整记录了每次工具调用：
- 调了什么工具
- 传了什么参数
- 返回了什么结果
- 是否有错误

这对调试和审计至关重要。你可以看到 LLM 的每一步决策过程。

---

## 7. 安全性考量

Tool Use 引入了新的安全面：LLM 现在不只是生成文本，它的输出会触发实际代码执行。

### 7.1 工具白名单

**必须做**：只有明确注册的工具才能执行。

反例：如果你的系统允许 LLM 调用任意函数名，恶意 Prompt 可能诱导 LLM 尝试调用 `exec_command` 或 `delete_database`。

你的项目通过 `ToolRegistry._tools` 字典实现白名单，`execute()` 中检查。

### 7.2 参数验证

LLM 生成的参数不可信——它可能产出：
- 格式错误的 JSON（`json.loads` 失败）
- 类型不匹配的值（期望 int，给了 string）
- 恶意内容（SQL 注入、命令注入）

你的项目中：
- `_parse_tool_call` 捕获 JSON 解析错误
- `calculate` 工具用 AST 白名单完全杜绝代码注入
- `search_knowledge_base` 的 query 只传给已有的安全检索管道

### 7.3 执行限制

- **max_iterations**：防止无限调用循环（默认 10，上限 20）
- **tool_call_timeout**：防止单个工具执行卡死（默认 30 秒）
- **表达式长度限制**：calculate 工具限制 200 字符
- **指数限制**：防止 `2 ** 999999` 导致的计算爆炸

### 7.4 信息泄露

工具错误信息会返回给 LLM。确保错误消息不包含：
- 内部文件路径
- 数据库连接字符串
- API 密钥

你的项目通过 `str(exc)` 返回标准异常消息，API 端点对外只返回 `"Failed to complete tool chat."`。

---

## 8. 配置管理

Phase 3 在 `Settings` 中新增两个配置项：

```python
tool_call_max_iterations: int = Field(default=10, ge=1)   # 工具调用最大轮次
tool_call_timeout: int = Field(default=30, gt=0)           # 单个工具执行超时(秒)
```

对应 `.env`：
```env
TOOL_CALL_MAX_ITERATIONS=10
TOOL_CALL_TIMEOUT=30
```

**设计决策**：
- `max_iterations` 在 API 请求中可覆盖（`ToolChatRequest.max_iterations`），但上限 20
- `tool_call_timeout` 只能通过环境变量配置，不暴露给 API 调用者

---

## 9. 测试策略

### 9.1 分层测试

Phase 3 的测试分四层：

| 测试文件 | 测试什么 | Mock 了什么 |
|----------|----------|-------------|
| `test_tool_registry.py` | 注册表的注册、查询、执行 | RAGService（Fake 对象） |
| `test_tools_builtin.py` | 每个工具的正常/边界/安全用例 | RAGService（Fake 对象） |
| `test_tool_calling_loop.py` | LLM 工具调用循环逻辑 | httpx（Mock LLM API 响应） |
| `test_tools_endpoint.py` | API 端点集成 | LLMService.chat_with_tools |

### 9.2 关键测试用例

**安全测试**：
```python
async def test_calculate_rejects_injection():
    # __import__('os') 必须被拒绝
    with pytest.raises(ValueError, match="not allowed"):
        await tool.handler({"expression": "__import__('os')"})
```

**并行调用测试**：
```python
async def test_chat_with_tools_handles_parallel_tool_calls():
    # LLM 一次返回两个 tool_calls
    # 验证两个工具都被执行，结果正确
```

**迭代上限测试**：
```python
async def test_returns_limit_message_when_iterations_exhausted():
    # LLM 每次都返回 tool_calls（不给最终答案）
    # max_iterations=1 时应返回 "limit reached" 消息
```

**错误传播测试**：
```python
async def test_reports_tool_argument_error():
    # LLM 返回无法解析的 JSON arguments
    # 验证错误被捕获并反馈给 LLM（不崩溃）
```

---

## 10. 与 Phase 2 RAG 的关系

Phase 3 不是替代 Phase 2，而是将 Phase 2 的能力"工具化"：

| Phase 2 | Phase 3 |
|---------|---------|
| 用户显式调用 `POST /rag/search` | LLM **自动决定**是否需要搜索知识库 |
| 检索逻辑硬编码在 RAG 端点中 | 检索成为 LLM 可调度的工具之一 |
| 只能做 RAG | 可以同时做 RAG + 计算 + 时间查询 + ... |

这就是从"流水线"到"Agent"的过渡：
- Phase 2 RAG = 确定性流水线（用户问 → 一定检索 → 一定生成）
- Phase 3 Tool Use = LLM 动态决策（用户问 → LLM 判断需不需要检索 → 可能检索也可能直接回答）

---

## 11. 阶段自检清单

### 概念理解

- [ ] 能解释 Function Calling 的完整流程（注册 → 请求 → 响应 → 执行 → 反馈 → 循环）
- [ ] 能说清 LLM 在 Tool Use 中只负责"决策"，不负责"执行"
- [ ] 理解工具 description 对 LLM 选择工具的重要性
- [ ] 能区分并行调用和顺序调用
- [ ] 理解 max_iterations 和 timeout 的安全意义

### 工程能力

- [ ] 能从零定义一个新工具的 JSON Schema
- [ ] 能向 ToolRegistry 注册自定义工具
- [ ] 能处理工具执行失败的场景
- [ ] 理解为什么 calculate 不能用 eval()

### 代码能力

- [ ] 能读懂 `chat_with_tools` 的循环逻辑
- [ ] 能读懂 `_parse_tool_call` 和 `_execute_tool_call` 的错误处理
- [ ] 能读懂 `calculate.py` 的 AST 安全解析
- [ ] 能为新工具编写对应的 pytest 测试

---

## 12. 推荐资料

| 资料 | 说明 |
|------|------|
| [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) | 官方指南，格式标准参考 |
| [Anthropic Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) | Claude 的 Tool Use 实现，思路类似 |
| [JSON Schema 入门](https://json-schema.org/learn/getting-started-step-by-step) | 工具参数定义的基础 |
| Python ast 模块文档 | 理解 calculate 工具的安全解析原理 |

---

## 13. 下一步

Phase 3 让 LLM 有了"做事"的能力，但每次对话的工具集是固定的，决策是单轮的。

Phase 4（Workflow → Agent）将引入：
- **确定性工作流**：预定义的多步骤流程（classify → retrieve → generate → review）
- **动态 Agent**：LLM 自主规划、选择路径、检查结果、决定是否继续
- **状态管理**：跨步骤的上下文传递和状态图
- **何时用 Workflow vs Agent** 的工程判断
