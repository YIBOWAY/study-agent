# Solution 01: Agent Runner Lab

这份 solution 不是用来跳过 lab 的。它的用法是：

1. 先读每题的 **What This Proves**，知道这些 `assert` 到底在证明什么。
2. 再读代码，或者把代码粘进从 `redesign/` 打开的 Python shell 里运行。
3. 最后读 **Why This Design**，把这一题和后面的离线“本地论文研究助手”连起来。

Part 1 还没有真实论文检索，也没有真实证据抽取。这里练的是更底层的能力：一次 agent run 必须留下可检查的 event trail。后面做“检索论文 -> 抽取证据 -> 写报告”时，我们才有办法判断答案是不是沿着正确路径产生的。

所有 snippets 都从 `redesign/` 的 Python shell 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Imports

```python
from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    event_type_sequence,
    events_to_records,
)
from research_core.testing import FakeModel, FakeModelResponse
```

## Exercise 1 Solution: Plain Final Response

### What This Proves

这一题的断言证明三件事：

- 最短 agent run 真的发生过：先 `model_request`，再 `model_response`。
- `ContextBuilder` 自动把系统提示词插到最前面，所以第一次 model request 的 message ids 是 `["system_1", "user_1"]`。
- 普通文本 response 会直接成为 final answer，不会误触发 tool flow。

### Runnable Solution

```python
model = FakeModel([FakeModelResponse(content="final answer")])

result = AgentRunner(model=model).run(
    run_id="lab_plain",
    system_prompt="You are careful.",
    user_message="hello",
)

records = events_to_records(result.events)

assert result.final_message.content == "final answer"
assert event_type_sequence(result.events) == ["model_request", "model_response"]
assert len(result.events) == 2
assert records[0]["payload"]["message_ids"] == [
    "system_1",
    "user_1",
]
```

### Why This Design

`ContextBuilder` 统一插入 system prompt，看起来只是一个小细节，但它是在保护未来的研究助手。

以后我们会在 system prompt 顶部放规则，比如“回答必须引用证据”“不能编造论文来源”。如果每次 run 都由 `ContextBuilder` 自动把这条规则放到第一位，调用方就不需要靠记忆手动拼上下文。对本地论文研究助手来说，这意味着“引用证据”这种安全规则可以稳定地排在用户问题前面。

## Exercise 2 Solution: Add An Echo Tool

### What This Proves

这一题的断言证明一次完整 tool run 发生了：

- 第一条 model response 被解析成 `echo` tool call。
- `ToolRuntime` 找到并执行了注册好的 `echo` tool。
- tool result 的内容是 `{"text": "hello"}`。
- tool result 发生在第二次 `model_request` 之前，所以 model 生成最终答案时已经拿到了工具观察结果。

### Runnable Solution

```python
tool_call_json = '{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}'

model = FakeModel(
    [
        FakeModelResponse(content=tool_call_json),
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

expected_sequence = [
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]
records = events_to_records(result.events)

assert result.final_message.content == "The tool said hello."
assert event_type_sequence(result.events) == expected_sequence
assert records[2]["payload"]["tool_call"]["name"] == "echo"
assert records[3]["payload"]["tool_result"]["content"] == {"text": "hello"}
assert records[3]["type"] == "tool_result"
assert records[4]["type"] == "model_request"
assert len(model.calls) == 2
assert [message.id for message in model.calls[1]] == [
    "system_1",
    "user_1",
    "assistant_1",
    "tool_call_1",
]
```

### Why This Design

Tool result 必须先进入对话，再发生第二次 model request。否则 model 的最终答案只是在“猜工具会返回什么”，不是在基于工具观察结果回答。

本地论文研究助手以后会有类似链路：先查本地论文，再读片段，再写报告。每一步都必须把上一步的结果放进下一次上下文。Exercise 2 用 `echo` 做最小版本，就是为了证明 runtime 已经具备这个“观察结果回填”的基本结构。

## Exercise 3 Solution: Inspect And Modify The Trajectory

### What This Proves

这一题的断言证明 `events_to_records(...)` 返回的是 independent plain copies：

- records 里能看到 `tool_call` 和 `tool_result` 的详细内容。
- 修改 returned record 只会改这份普通 dict copy。
- 原始 `result.events` 不会被 record mutation 改坏。
- 再次调用 `events_to_records(result.events)`，仍然能拿到干净的 `"hello"`。

### Runnable Solution

这段代码继续使用 Exercise 2 里的 `result`。如果你开了新 shell，先重跑 Exercise 2。

```python
records = events_to_records(result.events)

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

records[3]["payload"]["tool_result"]["content"]["text"] = "mutated"

assert records[3]["payload"]["tool_result"]["content"]["text"] == "mutated"
assert result.events[3].payload["tool_result"]["content"]["text"] == "hello"

fresh_records = events_to_records(result.events)
assert fresh_records[3]["payload"]["tool_result"]["content"]["text"] == "hello"
```

### Why This Design

Workbench UI 以后会过滤、排序、展开、折叠、标注 event records。如果 UI 拿到的是原始 runtime 对象，展示层一次不小心的修改就可能污染真实运行轨迹。

所以这里要证明：`events_to_records(...)` 给 UI 的是可安全消费的普通 records。Workbench 可以放心显示 timeline，而 runtime 仍然保留自己的原始事实。这对 Part 5 的 timeline UI 特别重要。

## Exercise 4 Solution: Design A Multi-Tool Calculator

### What This Proves

这一题的断言不只是证明 final answer 正确。它证明的是：

- runner 连续完成了两轮 tool call，所以总共有 10 个 events。
- 第一轮工具结果是 7，第二轮工具结果是 14。
- calculator tool surface 真的包含 `add`、`subtract`、`multiply`、`divide` 四个工具。
- final answer 是第三次 model response，而不是前两次 tool-call JSON。

### Runnable Solution

```python
add_json = '{"tool_call": {"id": "call_1", "name": "add", "arguments": {"a": 3, "b": 4}}}'
multiply_json = '{"tool_call": {"id": "call_2", "name": "multiply", "arguments": {"a": 7, "b": 2}}}'

model = FakeModel(
    [
        FakeModelResponse(content=add_json),
        FakeModelResponse(content=multiply_json),
        FakeModelResponse(content="3+4 is 7, and 7*2 is 14."),
    ]
)

tools = ToolRuntime()
tools.register(
    ToolDefinition(
        name="add",
        description="Add two numbers.",
        handler=lambda arguments: {"value": arguments["a"] + arguments["b"]},
    )
)
tools.register(
    ToolDefinition(
        name="subtract",
        description="Subtract b from a.",
        handler=lambda arguments: {"value": arguments["a"] - arguments["b"]},
    )
)
tools.register(
    ToolDefinition(
        name="multiply",
        description="Multiply two numbers.",
        handler=lambda arguments: {"value": arguments["a"] * arguments["b"]},
    )
)
tools.register(
    ToolDefinition(
        name="divide",
        description="Divide a by b.",
        handler=lambda arguments: {"value": arguments["a"] / arguments["b"]},
    )
)

expected_sequence = [
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]

result = AgentRunner(model=model, tools=tools).run(
    run_id="lab_calculator",
    system_prompt="You are careful.",
    user_message="3+4 then multiply by 2",
)

records = events_to_records(result.events)
tool_values = [
    record["payload"]["tool_result"]["content"]["value"]
    for record in records
    if record["type"] == "tool_result"
]

assert result.final_message.content == "3+4 is 7, and 7*2 is 14."
assert event_type_sequence(result.events) == expected_sequence
assert len(result.events) == 10
assert tool_values == [7, 14]
assert {tool.name for tool in tools.list_tools()} == {
    "add",
    "subtract",
    "multiply",
    "divide",
}
```

### Why This Design

Final answer 在这个 lab 里是 scripted response。只检查 final answer，很容易得到一种假的安全感：文本看起来对，但你不知道工具有没有真的跑，顺序有没有对，中间值有没有产生。

所以这一题必须检查 `tool_values == [7, 14]`。它证明两步链路里有真实中间产物：先 `add` 产出 7，再把 7 用进 `multiply` 产出 14。

这就是未来本地论文研究助手的缩小版。以后链路会变成“search papers -> extract evidence -> write report”。我们不能只看最终报告写得像不像；必须检查中间 evidence artifact 是否真的出现、顺序是否正确、是否被下一步使用。

## Final Takeaway

这份 lab 的核心不是 echo tool，也不是 calculator。核心习惯是：

```text
看 event sequence，不要只看 final answer。
```

Part 2 做 evidence chain 时，它能告诉你“论文检索、证据抽取、报告生成”有没有真的按顺序发生。Part 5 做 timeline UI 时，它能让用户看到每一步 agent 到底做了什么。Part 7 做 production diagnostics 时，它能让失败 run 也留下可排查的路径。

但也要记住边界：Part 1 还只是离线 runtime 训练。这里证明的是 agent loop、tool result、record copy 和 event trail 的形状，不是在宣称真实论文检索或真实证据系统已经完成。
