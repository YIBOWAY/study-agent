# Lab 01: Build And Inspect An Agent Run

## Goal

这个 lab 只做一件事：让你能自己跑一次 agent，并且看懂它留下的 event trail。

| Tier | Exercise | 你要练什么 |
| --- | --- | --- |
| L1 Follow | Exercise 1: Plain Final Response | 跟着跑最短 run：只有 model request 和 model response。 |
| L1 Follow | Exercise 2: Add An Echo Tool | 跟着跑一次 tool run：model 请求工具，runtime 执行工具，再回到 model。 |
| L2 Modify | Exercise 3: Inspect And Modify The Trajectory | 观察 `events_to_records(...)` 的普通 copy，并确认改 record 不会改坏原始 events。 |
| L3 Design | Exercise 4: Design A Multi-Tool Calculator | 从要求出发，自己设计连续两轮 tool call 的 agent run。 |

预计时间：45 到 60 分钟。

这份 lab 可以单独使用；如果概念卡住，回到 `../chapters/01-agent-kernel-foundations.md`。如果 Python shell、`assert`、list/dict 访问卡住，回到 `../reference/python-terminal-primer.md`。

## Setup

从 `redesign/` 目录打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

后面的练习全都离线运行，不需要真实 API key，不会访问论文库，也不会访问网络。

先粘贴 imports：

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

如果这里报 `ModuleNotFoundError`，先确认你是不是在 `redesign/` 目录，并且命令里有没有带上 `PYTHONPATH=packages/research_core/src`。仍然卡住就回到 `../labs/00-environment-check.md`。

每个练习都会重新创建自己的 `model`。这是故意的：`FakeModel` 会按顺序消耗 scripted responses，用过的 response 不会自动回来。

## Exercise 1 (L1 Follow): Plain Final Response

这一题没有 tool。model 只返回一句最终答案，所以 event sequence 应该只有两步：

```text
model_request -> model_response
```

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

Expected output：

```text
final answer
['model_request', 'model_response']
```

Self-check：

```python
assert result.final_message.content == "final answer"
assert event_type_sequence(result.events) == ["model_request", "model_response"]
assert len(result.events) == 2
```

这说明：如果 model 返回普通文本，`AgentRunner` 不会继续找 tool call，它会把这条 assistant message 当成 final answer。

### Feedback

**Common Errors**:

1. `ModuleNotFoundError: No module named 'research_core'` - 通常是没有用 setup 里的 `PYTHONPATH=packages/research_core/src uv run python`。
2. `NameError: name 'FakeModelResponse' is not defined` - imports 没粘完整，或者只导入了 `FakeModel`。
3. `TypeError` 或 `ValueError` 出现在 `FakeModelResponse(...)` 附近 - 检查你是不是写成了错误参数名，比如 `FakeModelResponse(text="final answer")`；这里的字段叫 `content`。
4. `RuntimeError: FakeModel has no scripted responses left` - 同一个 `model` 被跑了第二次；重新创建 `FakeModel([...])` 再跑。

**Failure Output Interpretation**:

如果 `event_type_sequence(result.events)` 是空 list，通常说明 `run(...)` 根本没有成功返回，先看异常本身。如果 sequence 不是 `['model_request', 'model_response']`，检查 `FakeModelResponse(content=...)` 里面是不是以 `{` 开头的 JSON；JSON tool-call 会把 run 带进工具流程。 如果 final answer 不是 `"final answer"`，说明你改了 scripted response，不是 runner 自动改写了答案。

**Where To Go Back**:

回到 Chapter 01 的 Section 2，重新看 plain response 的两步 sequence。环境或 import 卡住，回到 `../labs/00-environment-check.md` 和 `../reference/python-terminal-primer.md`。

**Why Correct Answer Is Correct**:

正确答案证明了最短 agent loop 真的发生过：runtime 先记录 `model_request`，再记录 `model_response`。因为 model response 是普通文本，不是 tool-call JSON，所以没有 `tool_call`、没有 `tool_result`、也没有第二次 `model_request`。

## Exercise 2 (L1 Follow): Add An Echo Tool

这一题让 model 先返回 tool-call JSON。`AgentRunner` 看到这个 JSON 后，会调用 `echo` tool，把工具结果追加回对话，然后再次请求 model 生成最终答案。

一次成功 tool run 应该是六步：

```text
model_request
  -> model_response
  -> tool_call
  -> tool_result
  -> model_request
  -> model_response
```

粘贴：

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

print(result.final_message.content)
print(event_type_sequence(result.events))
```

Expected output：

```text
The tool said hello.
['model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response']
```

Self-check：

```python
expected_sequence = [
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]

assert result.final_message.content == "The tool said hello."
assert event_type_sequence(result.events) == expected_sequence

records = events_to_records(result.events)
assert records[2]["payload"]["tool_call"]["name"] == "echo"
assert records[3]["payload"]["tool_result"]["content"] == {"text": "hello"}
```

注意：第一条 `FakeModelResponse` 不是最终答案，它只是 tool-call JSON。第二条 `FakeModelResponse` 才是最终答案。

### Feedback

**Common Errors**:

1. JSON 格式写错 - 外层必须是字符串，顶层必须有 `"tool_call"`，里面必须有 `"id"`、`"name"`、`"arguments"`。
2. 忘记把 `tools` 传给 runner - `AgentRunner(model=model)` 会使用空工具表；这里必须写 `AgentRunner(model=model, tools=tools)`。
3. 注册工具名和 JSON 工具名不一致 - `ToolDefinition(name="echo", ...)` 必须和 JSON 里的 `"name": "echo"` 对上。
4. `FakeModel` response 顺序写反 - 如果第一条就是 `"The tool said hello."`，runner 会直接结束，根本不会调用工具。

**Failure Output Interpretation**:

如果只有 2 个 events，通常说明第一条 model response 被当成普通文本：它可能不是以 `{` 开头，或者你把第一条 response 写成了 `"The tool said hello."`。 如果 `FakeModelResponse(...)` 附近直接报错，检查 `content` 是否真的是字符串；Python dict 不能直接当成 model response content。 如果出现 `unknown_tool`，说明 JSON 已经解析成功，但工具没有注册到这次 runner 使用的 `ToolRuntime`。 如果出现 `JSON model responses must contain tool_call`，说明 content 看起来像 JSON，但顶层 key 不是 `"tool_call"`。

**Where To Go Back**:

回到本题的 `tool_call_json`，逐字检查 JSON 形状。再看 `tools.register(...)` 和 `AgentRunner(model=model, tools=tools)` 是否都在同一个代码块里。

**Why Correct Answer Is Correct**:

六步 sequence 证明了完整 think-act-observe loop：model 先请求工具，runner 记录 `tool_call`，`ToolRuntime` 执行 `echo`，runner 记录 `tool_result`，然后带着工具结果再次请求 model，最后拿到普通文本作为 final answer。

## Exercise 3 (L2 Modify): Inspect And Modify The Trajectory

这一题继续使用 Exercise 2 里成功跑出来的 `result`。如果你开了新 shell，先重跑 Exercise 2。

先不要粘贴代码，先预测：

1. `records[2]["type"]` 应该是什么？
2. `records[3]["payload"]["tool_result"]["content"]["text"]` 应该是什么？
3. 如果你修改 `records[3]`，原始的 `result.events[3]` 会不会跟着变？

现在粘贴：

```python
records = events_to_records(result.events)

print(records[2])
print(records[3])
print(records[3]["payload"]["tool_result"]["content"]["text"])
```

Expected output 形状类似：

```text
{'id': 'evt_3', 'run_id': 'lab_tool', 'type': 'tool_call', 'payload': {'step': 1, 'tool_call': {'id': 'call_1', 'name': 'echo', 'arguments': {'text': 'hello'}}}}
{'id': 'evt_4', 'run_id': 'lab_tool', 'type': 'tool_result', 'payload': {'step': 1, 'tool_result': {'call_id': 'call_1', 'name': 'echo', 'content': {'text': 'hello'}, 'metadata': {}}}}
hello
```

现在故意改 returned records：

```python
records[3]["payload"]["tool_result"]["content"]["text"] = "mutated"

print(records[3]["payload"]["tool_result"]["content"]["text"])
print(result.events[3].payload["tool_result"]["content"]["text"])
```

Expected output：

```text
mutated
hello
```

> [TRAP] **`records[3]["payload"]` 和 `result.events[3].payload` 不是同一种东西**
>
> `events_to_records(...)` 返回的是普通 dict copies，所以访问 record 时要写 `records[3]["payload"]`。`result.events[3]` 是 `RunEvent` 对象，所以访问原始 event 时要写 `result.events[3].payload`。如果你把这两种语法混用，Python 会报错，但那不是 agent loop 的问题。

Self-check：

```python
assert records[2]["type"] == "tool_call"
assert records[2]["payload"]["tool_call"] == {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"},
}

assert records[3]["type"] == "tool_result"
assert records[3]["payload"]["tool_result"]["content"]["text"] == "mutated"
assert result.events[3].payload["tool_result"]["content"]["text"] == "hello"

fresh_records = events_to_records(result.events)
assert fresh_records[3]["payload"]["tool_result"]["content"]["text"] == "hello"
```

这说明 `events_to_records(result.events)` 返回的是可检查、可展示的普通 copy。你可以修改这个 copy 做实验，但不会把原始 event trail 改坏。

### Feedback

**Common Errors**:

1. 写成 `records[3].payload` - `records[3]` 是 dict，不是 `RunEvent`。
2. 写成 `result.events[3]["payload"]` - `result.events[3]` 是 `RunEvent`，不是 dict。
3. 先重跑了 Exercise 1，再做本题 - 那时 `result.events` 只有两条，没有 `records[3]`。
4. 以为 record mutation 会改变原始 event - 这里正好要证明它不会。

**Failure Output Interpretation**:

如果报 `IndexError: list index out of range`，说明当前 `result` 不是 Exercise 2 的六步 tool run，先打印 `event_type_sequence(result.events)`。如果报 `'dict' object has no attribute 'payload'`，说明你把 record 当成了 event。 如果报 `'RunEvent' object is not subscriptable`，说明你把 event 当成了 dict。 如果原始 event 也显示 `"mutated"`，那就不是当前 API 的预期行为，需要停下来检查你是不是直接改了 `result.events`，而不是改 `records`。

**Where To Go Back**:

回到 Chapter 01 的 Section 4，看为什么 Workbench 更适合消费普通 dict records。再回到本 lab Exercise 2，确认你手里的 `result` 是六步 tool run。

**Why Correct Answer Is Correct**:

正确结果同时证明两件事：`records` 里能看见 tool call 和 tool result 的具体内容；`events_to_records(...)` 返回的是 independent plain copies。修改 record copy 只影响 copy，不影响 `result.events` 里的原始 `RunEvent`。

## Exercise 4 (L3 Design): Design A Multi-Tool Calculator

这一题先不给 skeleton。你要从要求反推 model 剧本、工具注册和自查方式。

Requirements：

- 注册 4 个工具：`add`、`subtract`、`multiply`、`divide`。
- 用户任务是：`"3+4 then multiply by 2"`。
- 你要自己写出 `FakeModel` sequence 和 4 个 `ToolDefinition`。
- 你要先预测 `event_type_sequence(result.events)`，再运行代码比较。
- final answer 之前必须连续完成两轮工具调用：先 `add` 得到 7，再 `multiply` 得到 14。
- 自查时必须检查 tool result values 是 `[7, 14]`，不能只看 final text。

先在自己的 shell 里写一版。写之前，先把你预测的 sequence 写下来。你应该需要 10 个 events：

```python
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
```

不要马上看下面。先自己尝试 10 到 15 分钟；卡住时回到 Exercise 2，看“一轮 tool call”是怎么写出来的。

### Reference Shape After You Try

下面不是唯一写法，但它给出一个可运行的参考形状：

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

print(result.final_message.content)
print(event_type_sequence(result.events))
print(tool_values)
```

Expected output：

```text
3+4 is 7, and 7*2 is 14.
['model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response']
[7, 14]
```

Self-check：

```python
assert result.final_message.content == "3+4 is 7, and 7*2 is 14."
assert event_type_sequence(result.events) == expected_sequence
assert tool_values == [7, 14]
assert {tool.name for tool in tools.list_tools()} == {
    "add",
    "subtract",
    "multiply",
    "divide",
}
```

### Feedback

**Common Errors**:

1. 只写一次 tool call 就 final - 这样只能得到六个 events，没有证明连续两轮工具调用。
2. 第二次 `multiply` 的参数还写成 `{"a": 3, "b": 4}` - 这样没有表达“先 add 得到 7，再乘以 2”。
3. 注册了 4 个工具，但 JSON 里的 `"name"` 和 `ToolDefinition(name=...)` 对不上 - 这会变成 `unknown_tool`。
4. 以为 runtime 会自动把第一次工具结果塞进第二次 tool-call JSON - 当前 `FakeModel` 是固定剧本，第二次参数要你自己写清楚。
5. 只注册 `add` 和 `multiply` - 这样虽然能跑通这次 happy path，但没有满足“设计 4 个工具”的题目要求。
6. 只断言 final text - final text 是 scripted response，不能证明工具真的算出了 `[7, 14]`。

**Failure Output Interpretation**:

如果只有 6 个 events，说明你只完成了一轮工具调用。 如果最后出现 `unknown_tool`，先看 JSON 里的 `"name"` 是否和注册表完全一致。 如果 event sequence 正确但 `tool_values` 不是 `[7, 14]`，优先检查 handler 的加法/乘法逻辑和第二次 tool-call 参数。 如果工具集合断言失败，说明你没有注册完整的 4 个工具。 如果 `tool_values` 对了但 final answer 不对，检查第三条 `FakeModelResponse`，因为 final answer 来自最后一次 model response。

**Where To Go Back**:

回到 Exercise 2，把“一轮 tool call = tool-call JSON + registered tool + 第二条 model response”重新跑通。再回到 Chapter 01 的 Checkpoint，看 multi-tool calculator 为什么是未来“先检索论文，再总结证据”的简化训练。

**Why Correct Answer Is Correct**:

十个 events 证明 runner 连续完成了两轮“model 请求工具 -> runtime 执行工具 -> 工具结果进入对话 -> 再问 model”。`tool_values == [7, 14]` 证明两个 handler 真的产出了中间值和最终值。工具集合断言证明你按题目设计了完整 calculator tool surface，而不是只为 happy path 临时凑两个工具。final answer 则证明第三次 model response 才是最终回复，前两次 model response 都只是工具请求。

## Reflection

做完以后，用自己的话回答：

1. Plain final response 为什么只有两个 events？
2. Tool run 为什么会有第二次 `model_request`？
3. 为什么 Exercise 3 要区分 `records[3]["payload"]` 和 `result.events[3].payload`？
4. 为什么 calculator 不能只检查 final answer？
5. 如果未来本地论文研究助手回答错了，你会先看 final answer，还是先看 event trail？为什么？

如果能答出大概意思，再看 `../solutions/01-agent-runner-solution.md`。答案文件可以帮你确认思路，但不要用它替代这份 lab 的动手过程。
