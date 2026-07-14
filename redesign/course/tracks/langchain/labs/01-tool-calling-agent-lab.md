# Lab 01 — Tool-calling Agent（LangChain 轨）

接 Chapter 01。练习可观察的 tool-calling loop。

预计时间：45–60 分钟。

## Setup

```bash
cd redesign   # 仓库内 redesign 根
uv sync --group langchain-course
PYTHONPATH=packages/langchain_course/src uv run python
```

```python
from langchain_core.messages import AIMessage
from langchain_course.agent_kernel import (
    AgentKernelError,
    run_tool_calling_agent,
    step_kinds,
)
from langchain_course.tools_echo import add, echo
```

## Exercise 1 (L1 Follow): Plain final

用 scripted model 跑无工具 final：

```python
class Scripted:
    def __init__(self, responses):
        self._responses = list(responses)
    def bind_tools(self, tools, **kw):
        return self
    def invoke(self, messages, **kw):
        return self._responses.pop(0)

model = Scripted([AIMessage(content="final answer")])
result = run_tool_calling_agent(user_message="hello", tools=[], model=model)
print(result.final_text)
print(step_kinds(result))
assert step_kinds(result) == ["user_message", "model_request", "model_response"]
```

## Exercise 2 (L1 Follow): Echo tool loop

```python
model = Scripted([
    AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "echo", "args": {"text": "lab"}
    }]),
    AIMessage(content="echoed lab"),
])
result = run_tool_calling_agent(user_message="echo lab", tools=[echo], model=model)
assert "tool_result" in step_kinds(result)
assert result.final_text == "echoed lab"
tool_result = next(s for s in result.steps if s.kind == "tool_result")
assert tool_result.payload["content"] == "lab"
```

## Exercise 3 (L2 Modify): Inspect message_records

在 Exercise 2 的 `result` 上：

```python
types = [m["type"] for m in result.message_records]
print(types)
assert "tool" in types or any(m.get("tool_call_id") for m in result.message_records)
# 改拷贝不应影响 steps
copy = list(result.message_records)
copy.append({"type": "human", "content": "mutated"})
assert len(result.message_records) == len(copy) - 1
```

把 `add` 工具加入 tools，script 一轮 `add(a=2,b=3)`，断言 tool_result 为 `5` 或 `5.0`。

## Exercise 4 (L3 Design): max_steps 与未知工具

1. 构造永远返回 tool_call 的 scripted model，`max_steps=2`，断言 `AgentKernelError`。
2. 请求不存在的 tool 名，断言 `tool_result` 含 `unknown tool`，且仍有 final_text。

## Offline gate

```bash
uv run pytest packages/langchain_course/tests/test_agent_kernel.py -q
```

## Optional live smoke

需要 `.env` 中的 `DEEPSEEK_API_KEY`（见 `.env.example`）。只检查 `final_text` 非空与 steps 非空，**不要**全文相等。

## 对照

Solution：[../solutions/01-tool-calling-agent-solution.md](../solutions/01-tool-calling-agent-solution.md)
