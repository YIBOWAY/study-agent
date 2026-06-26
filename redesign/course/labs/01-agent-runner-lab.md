# Lab 01: Build And Inspect An Agent Run

## Goal

这个 lab 会带你亲手跑四种情况：

1. model 直接返回最终答案。
2. model 先调用 `echo` tool，再返回最终答案。
3. 把 events 转成普通 records，检查运行轨迹。
4. 故意调用不存在的 tool，观察失败轨迹。

预计时间：45 到 60 分钟。

## Setup

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

保持这个 shell 打开，后面的练习会复用前面创建的 `tools` 和 `result`。

先粘贴 imports：

```python
from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    UnknownToolError,
    event_type_sequence,
    events_to_records,
)
from research_core.testing import FakeModel, FakeModelResponse
```

如果这里报 `ModuleNotFoundError`，先回到 `../labs/00-environment-check.md`。

## Exercise 1: Plain Final Response

这一题没有 tool。model 只返回一句最终答案。

粘贴：

```python
model = FakeModel([FakeModelResponse(content="final answer")])

result = AgentRunner(model=model).run(
    run_id="lab_plain",
    system_prompt="You are careful.",
    user_message="hello",
)

print(result.final_message.content)
print(event_type_sequence(result.events))
```

你应该看到：

```text
final answer
['model_request', 'model_response']
```

这说明一件事：如果 model 返回普通文本，`AgentRunner` 不会继续找 tool call，它会把这条 assistant message 当成 final answer。

自查：

```python
assert result.final_message.content == "final answer"
assert event_type_sequence(result.events) == ["model_request", "model_response"]
```

## Exercise 2: Add An Echo Tool

这一题让 model 先返回 tool-call JSON。Agent 会调用 `echo` tool，然后把工具结果带回下一次 model request。

粘贴：

```python
model = FakeModel(
    [
        FakeModelResponse(
            content='{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}'
        ),
        FakeModelResponse(content="The tool said hello."),
    ]
)

tools = ToolRuntime()
tools.register(
    ToolDefinition(
        name="echo",
        description="Return the input text.",
        handler=lambda arguments: {"text": arguments["text"]},
    )
)

result = AgentRunner(model=model, tools=tools).run(
    run_id="lab_tool",
    system_prompt="You are careful.",
    user_message="Say hello through the tool.",
)

print(result.final_message.content)
print(event_type_sequence(result.events))
```

你应该看到：

```text
The tool said hello.
['model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response']
```

自查：

```python
assert result.final_message.content == "The tool said hello."
assert event_type_sequence(result.events) == [
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]
```

## Exercise 3: Inspect The Trajectory

最终答案只是最后一句话。现在看过程。

粘贴：

```python
records = events_to_records(result.events)

print(records[2])
print(records[3])
```

第三条 record 应该是 `tool_call`，第四条 record 应该是 `tool_result`。

自查：

```python
assert records[2]["type"] == "tool_call"
assert records[2]["payload"]["tool_call"] == {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"},
}

assert records[3]["type"] == "tool_result"
assert records[3]["payload"]["tool_result"] == {
    "call_id": "call_1",
    "name": "echo",
    "content": {"text": "hello"},
    "metadata": {},
}
```

现在故意改一下 returned records：

```python
records[3]["payload"]["tool_result"]["content"]["text"] = "mutated"
print(result.events[3].payload["tool_result"]["content"]["text"])
```

你应该看到：

```text
hello
```

这说明 `events_to_records(...)` 返回的是可检查的普通 copy，不会把原始 `RunEvent` 改坏。对 event trail 来说，这很重要。

## Exercise 4: Break The Tool Name

现在故意让 model 调用不存在的 tool。

粘贴：

```python
model = FakeModel(
    [
        FakeModelResponse(
            content='{"tool_call": {"id": "call_1", "name": "missing", "arguments": {"text": "hello"}}}'
        )
    ]
)

try:
    AgentRunner(model=model, tools=tools).run(
        run_id="lab_missing_tool",
        system_prompt="You are careful.",
        user_message="Say hello through a missing tool.",
    )
except UnknownToolError as exc:
    error_events = exc.events
    print(type(exc).__name__)
    print(event_type_sequence(error_events))
    print(error_events[-1].payload["error"]["kind"])
else:
    raise AssertionError("Expected missing tool to fail")
```

你应该看到：

```text
UnknownToolError
['model_request', 'model_response', 'tool_call', 'error']
unknown_tool
```

这就是本章的核心工程习惯：失败的 run 也必须留下可检查的 trajectory。

## Reflection

做完以后，回答这几个问题：

1. Plain final response 为什么只有两个 events？
2. Tool run 为什么会有第二次 `model_request`？
3. `tool_result` 里为什么同时有 `content` 和 `metadata`？
4. `missing` tool 为什么不是静默失败？
5. 你会怎么向别人解释 trajectory regression？

如果能答出大概意思，再看 `../solutions/01-agent-runner-solution.md`。
