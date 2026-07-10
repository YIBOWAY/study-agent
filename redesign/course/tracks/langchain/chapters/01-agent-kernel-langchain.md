# Part 1: Agent Kernel（LangChain 轨）

> 前置：完成 [Lab 00 DeepSeek Hello](../labs/00-deepseek-hello.md)。主课 Part 1 可对照阅读，但**本轨不 import** `research_core`。

预计时间：60–90 分钟。

## Learner Contract

- **你会构建**：一次可观察的 tool-calling loop：`bind_tools` → model → tool → 再 model。
- **你会解释**：为什么只看 final text 不够；中间 `AgentStep` 证明什么。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_agent_kernel.py -q`（离线）。
- **诚实边界**：真实 DeepSeek 回复非确定性；unit 用 scripted model，live 只做 smoke。

## 与 handwritten 对照

| Handwritten (`research_core`) | 本轨 (LangChain) |
| --- | --- |
| `AgentRunner` + `FakeModel` | `run_tool_calling_agent` + `ChatOpenAI` / scripted fake |
| `ToolRuntime` + `ToolDefinition` | `langchain_core.tools.tool` / `BaseTool` |
| `RunEvent` sequence | `AgentStep.kind`：`model_request` / `model_response` / `tool_call` / `tool_result` |
| 离线默认 | 默认真实 API；unit 仍离线 |

> [DD] **为何不用 `langchain` meta 包的高阶 AgentExecutor？** 当前 `langchain` 元包会拉进 LangGraph。LC 轨 Parts 1–7 约定**不依赖 LangGraph**；因此用 `bind_tools` 手写可观察 loop，概念更透明，也方便和 handwritten event trail 对照。

## Section 1：问题钩子

研究员问本地论文助手一个问题。如果系统只返回一句最终答案，你无法回答：

- model 有没有请求工具？
- 工具有没有真的执行？
- 工具结果有没有回到 model？

handwritten 用 `RunEvent` 回答这些问题。本轨用 **`AgentStep` 列表** 回答同一类问题。

```text
user_message
  -> model_request
  -> model_response          # 可能带 tool_calls
  -> tool_call / tool_result # 可重复
  -> model_request
  -> model_response          # 无 tool_calls → final_text
```

## Section 2 [BUILD]：最短 plain final

```bash
# 在 redesign/ 下；unit 不需要 key
uv run python
```

```python
from langchain_core.messages import AIMessage
from langchain_course.agent_kernel import run_tool_calling_agent, step_kinds

class Scripted:
    def __init__(self, responses):
        self._responses = list(responses)
    def bind_tools(self, tools, **kw):
        return self
    def invoke(self, messages, **kw):
        return self._responses.pop(0)

model = Scripted([AIMessage(content="final answer")])
result = run_tool_calling_agent(
    user_message="hello",
    tools=[],
    model=model,
)
print(result.final_text)
print(step_kinds(result))
assert result.final_text == "final answer"
assert step_kinds(result) == ["user_message", "model_request", "model_response"]
```

> [CHECK] 没有 `tool_call` 时，loop 在第一轮 `model_response` 结束。

## Section 3 [BUILD]：echo 工具一轮

```python
from langchain_core.messages import AIMessage
from langchain_course.agent_kernel import run_tool_calling_agent, step_kinds
from langchain_course.tools_echo import echo

class Scripted:
    def __init__(self, responses):
        self._responses = list(responses)
        self.bind_names = []
    def bind_tools(self, tools, **kw):
        self.bind_names = [t.name for t in tools]
        return self
    def invoke(self, messages, **kw):
        return self._responses.pop(0)

model = Scripted([
    AIMessage(content="", tool_calls=[{
        "id": "call_1", "name": "echo", "args": {"text": "hello"}
    }]),
    AIMessage(content="The tool said hello."),
])
result = run_tool_calling_agent(
    user_message="echo hello",
    tools=[echo],
    model=model,
)
print(step_kinds(result))
assert "tool_call" in step_kinds(result)
assert "tool_result" in step_kinds(result)
assert result.final_text == "The tool said hello."
```

> [TRAP] **只看 final_text 不够**：模型可以说“我已经调用了工具”，但 steps 里没有 `tool_result` 就说明 runtime 没执行。和主课 event trail 同一纪律。

## Section 4 [BREAK / FIX]

故意把 tool 名改成 `missing`（见 unit `test_unknown_tool_records_error_observation`）：loop **不崩溃**，`tool_result` 内容含 `unknown tool`，然后 model 再答一轮。

> [DD] 未知工具记 observation 而不是静默吞掉，是为了可检查；产品里你可能改成硬失败——教学上先看见失败。

## Section 5：Live smoke（可选，需 `.env`）

```bash
# redesign/.env 中设置 DEEPSEEK_API_KEY=...
uv run python -c "
from langchain_course.agent_kernel import run_tool_calling_agent, step_kinds
from langchain_course.tools_echo import echo
r = run_tool_calling_agent(
    user_message='Use the echo tool once with text pong, then reply briefly.',
    tools=[echo],
    max_steps=4,
)
print(step_kinds(r))
print(r.final_text)
"
```

期望：steps 中**可能**出现 `tool_call`（非确定性）；`final_text` 非空即可。不要用全文相等断言。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_agent_kernel.py -q
```

## Reflection

1. handwritten 的 `RunEvent` 与本轨 `AgentStep` 各自优化了什么？
2. 为什么本轨坚持不在 Part 1 引入 LangGraph？
3. 如果 max_steps 用尽，你更希望 raise 还是返回“未完成”结构？为什么？

## 下一步

- Lab：[labs/01-tool-calling-agent-lab.md](../labs/01-tool-calling-agent-lab.md)
- Solution：[solutions/01-tool-calling-agent-solution.md](../solutions/01-tool-calling-agent-solution.md)
