# Part 1: Agent Kernel Foundations (Sections 2-5)

> 接 Section 1。如果你还没读 `00-before-agent-kernel.md`，先回去读完。

这一章继续搭你的完全离线本地论文研究助手。Chapter 00 已经讲清楚心智模型：不要只看 final answer，要看 event trail。现在我们把这个模型跑起来、故意打坏、读懂失败，然后把它接到未来 Workbench 的产品视角里。

预计时间：60 到 90 分钟。

从 `redesign/` 目录打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

如果 Python shell、list、dict、`lambda`、`assert` 或 `try / except` 卡住，先回看 `../reference/python-terminal-primer.md`。如果 `AgentRunner`、`ToolRuntime`、`RunEvent` 这些词卡住，回看 `../reference/agent-kernel-glossary.md`。

## Section 2: 第一个可观察的 Agent Loop [BUILD - FULL CYCLE]

### 概念：最小的 think-act-observe loop

先看结果，不先背对象表。

普通回答的一次 run 应该只有两步：

```text
model_request -> model_response
```

意思是：本地论文研究助手把研究问题交给 model，model 直接给出最终文本。没有工具，没有第二轮。

如果 model 要调用工具，一次 run 会长这样：

```text
model_request
  -> model_response
  -> tool_call
  -> tool_result
  -> model_request
  -> model_response
```

这才是最小的 think-act-observe loop：

```text
Research question
      |
      v
[think] AgentRunner asks the model
      |
      v
[act]   ToolRuntime runs a requested tool
      |
      v
[observe] tool_result is added back to the conversation
      |
      v
[think] AgentRunner asks the model again
      |
      v
Final answer + event trail
```

把它放回本地论文研究助手的故事里：研究员问了一个问题，model 可能先说“我要查一下本地论文索引”，runtime 真的去调用工具，工具结果再回到 model 面前，最后 model 才回答研究员。Part 1 暂时用 `echo` 代替“查论文”工具，因为我们现在练的是 loop，不是检索质量。

> [CHECK] **检查一下**：看到 `model_request -> model_response`，你只能说明 model 回答了；看到中间有 `tool_call -> tool_result`，你才能说明 runtime 真的执行过工具。

### Build: 你的第一个 Agent Run

#### L1 Follow 练习 1：Plain final response first

在刚才打开的 Python shell 里粘贴：

```python
from research_core.runtime import AgentRunner, event_type_sequence
from research_core.testing import FakeModel, FakeModelResponse

model = FakeModel([FakeModelResponse(content="final answer")])

result = AgentRunner(model=model).run(
    run_id="plain_1",
    system_prompt="You are careful.",
    user_message="Summarize the local paper question.",
)

print(result.final_message.content)
print(event_type_sequence(result.events))

assert result.final_message.content == "final answer"
assert event_type_sequence(result.events) == ["model_request", "model_response"]
```

你应该看到：

```text
final answer
['model_request', 'model_response']
```

这个例子没有注册任何工具。`FakeModel` 直接返回普通文本，所以 `AgentRunner` 不会进入工具步骤。

#### L1 Follow 练习 2：Tool call with echo

继续在同一个 Python shell 里粘贴：

```python
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime
from research_core.runtime import event_type_sequence
from research_core.testing import FakeModel, FakeModelResponse

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
    run_id="tool_1",
    system_prompt="You are careful.",
    user_message="Say hello through the tool.",
)

print(result.final_message.content)
print(event_type_sequence(result.events))

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

你应该看到：

```text
The tool said hello.
['model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response']
```

这段代码里最关键的一行是这个 JSON 字符串，形状必须正好是：

```json
{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}
```

> [TRAP] **常见陷阱：FakeModel 的 tool call 是 JSON 字符串，不是 Python dict**
>
> `FakeModelResponse(content=...)` 的 `content` 必须是字符串。你可以把 JSON 写成字符串，但不能把 Python dict 直接塞进去。否则 model response content 就不是 runtime 期待的文本。

#### 练习反馈

**Common Errors**:

1. 忘记从 `redesign/` 启动 shell - 原因：普通 `uv run python` 不一定能找到 `research_core`。
2. 把 `FakeModelResponse(content=tool_call_json)` 写成 dict - 原因：看起来像 JSON，但 runtime 收到的不是字符串。
3. 忘记注册 `echo` - 原因：model 可以请求工具，但 `ToolRuntime` 才知道哪些工具真的存在。

**Failure Output Interpretation**: 如果 plain response 的 sequence 不是 `['model_request', 'model_response']`，先检查 `FakeModel` 是不是只给了一条普通文本。如果 tool run 只剩两步，通常说明 model 返回的是普通文本，runtime 没有进入 tool-call 解析。如果出现 `malformed_tool_call` 或 “JSON model responses must contain tool_call”，说明内容以 `{` 开头但顶层 key 不是 `tool_call`。如果出现 `unknown tool 'echo'`，说明 JSON 被解析成功了，但工具没有注册成功。

**Where To Go Back**: plain response 卡住，回到“概念：最小的 think-act-observe loop”的第一条 sequence。tool run 卡住，回到 L1 练习 2 的 `tool_call_json` 和 `tools.register(...)`。

**Why Correct Answer Is Correct**: plain response 的两步 sequence 证明 runtime 问过 model 并拿到最终文本。tool run 的六步 sequence 证明 runtime 不只是看到了 JSON，还完成了“记录 tool_call -> 执行工具 -> 记录 tool_result -> 再问 model”这一整圈。

### Inspect The Trail

只看 sequence 还不够。sequence 告诉你“发生过哪些类型的事”，record 才告诉你“每件事的内容是什么”。

继续粘贴：

```python
from research_core.runtime import events_to_records

records = events_to_records(result.events)

for record in records:
    if record["type"] in {"tool_call", "tool_result"}:
        print(record)
```

你应该看到类似：

```text
{'id': 'evt_3', 'run_id': 'tool_1', 'type': 'tool_call', 'payload': {'step': 1, 'tool_call': {'id': 'call_1', 'name': 'echo', 'arguments': {'text': 'hello'}}}}
{'id': 'evt_4', 'run_id': 'tool_1', 'type': 'tool_result', 'payload': {'step': 1, 'tool_result': {'call_id': 'call_1', 'name': 'echo', 'content': {'text': 'hello'}, 'metadata': {}}}}
```

`events_to_records(result.events)` 返回的是普通 record copies。未来 Workbench 不需要直接拿 dataclass 对象，它可以用这些普通 dict 画 timeline、tool inspector 和 failure diagnostics。

> [DD] **设计决策**：为什么这里用课程自定义 JSON tool-call 格式，而不是 OpenAI function calling？
>
> **选了**：`{"tool_call": {"id": "...", "name": "...", "arguments": {...}}}` 这个最小 JSON 协议。
> **没选**：一开始就使用 OpenAI function calling、Anthropic tool use 或某个框架自己的格式。
> **因为**：Part 1 要教的是 Agent loop 的机制，不是 provider API。自定义 JSON 很小、完全离线、可复制、可断言。等以后接真实 provider，核心问题仍然一样：model 提出工具请求，runtime 执行工具，event trail 记录过程。

### Modify: 改 echo 的返回值

现在改一个地方：让 `echo` 工具返回大写文本。先预测两个问题：

1. `event_type_sequence(result.events)` 会变吗？
2. `result.final_message.content` 会变吗？

#### L2 Modify 练习：只改工具返回值

粘贴这段完整代码：

```python
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime
from research_core.runtime import event_type_sequence, events_to_records
from research_core.testing import FakeModel, FakeModelResponse

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
        description="Return the input text in uppercase.",
        handler=lambda arguments: {"text": arguments["text"].upper()},
    )
)

result = AgentRunner(model=model, tools=tools).run(
    run_id="tool_2",
    system_prompt="You are careful.",
    user_message="Say hello through the tool.",
)

print(event_type_sequence(result.events))
print(result.final_message.content)

for record in events_to_records(result.events):
    if record["type"] == "tool_result":
        print(record["payload"]["tool_result"])
```

你应该看到：

```text
['model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response']
The tool said hello.
{'call_id': 'call_1', 'name': 'echo', 'content': {'text': 'HELLO'}, 'metadata': {}}
```

答案是：event sequence 不变，final message 也不变，变的是 `tool_result` record 里的内容。

> [TRAP] **常见陷阱：tool result != model response**
>
> 工具只返回数据，model 才负责解释数据并写成回答。这里工具返回了 `HELLO`，但第二条 `FakeModelResponse` 仍然是固定剧本 `"The tool said hello."`，所以 final message 不会自动跟着工具结果改。

#### L2 Modify 练习反馈

**Common Errors**:

1. 以为工具返回值会自动改写 final answer - 原因：把 `tool_result` 和第二次 `model_response` 混成了一件事。
2. 只打印 final answer，不看 `tool_result` record - 原因：还没养成“先看 trail”的习惯。
3. 同时改了 handler 和第二条 `FakeModelResponse` - 原因：一次修改两个变量，会看不清到底是谁造成了变化。

**Failure Output Interpretation**: 如果 sequence 变短，说明 model 没有产生 tool call，先查 JSON。 如果 final message 变了，检查你是不是改了第二条 `FakeModelResponse`。如果 `tool_result` 还是 `hello`，检查 handler 里有没有真的调用 `.upper()`。

**Where To Go Back**: 回到“Inspect The Trail”，重新看 `tool_call` 和 `tool_result` record 分别保存什么。再回到 Chapter 00 的规则：不要只看 final answer。

**Why Correct Answer Is Correct**: 正确输出同时证明三件事：runtime 流程没有变，工具数据确实变了，final answer 来自第二次 model response 而不是来自工具 handler。

## Section 3: Break It, Fix It - 失败也是信息 [BREAK & FIX - FULL CYCLE]

### Break It: 故意调一个不存在的工具

现在把 tool-call JSON 里的 `"echo"` 改成 `"missing"`。注意：我们仍然只注册 `echo`，所以这是故意打坏。

粘贴：

```python
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime
from research_core.runtime import UnknownToolError, event_type_sequence, events_to_records
from research_core.testing import FakeModel, FakeModelResponse

missing_tool_json = '{"tool_call": {"id": "call_1", "name": "missing", "arguments": {"text": "hello"}}}'

model = FakeModel(
    [
        FakeModelResponse(content=missing_tool_json),
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

try:
    AgentRunner(model=model, tools=tools).run(
        run_id="broken_1",
        system_prompt="You are careful.",
        user_message="Say hello through the tool.",
    )
except UnknownToolError as exc:
    print(type(exc).__name__)
    print(event_type_sequence(exc.events))
    print(events_to_records(exc.events)[-1]["payload"]["error"]["kind"])
```

你应该看到：

```text
UnknownToolError
['model_request', 'model_response', 'tool_call', 'error']
unknown_tool
```

这次 run 失败了，但不是一片空白。event trail 告诉你：model request 成功，model response 成功，tool-call JSON 也解析成功；真正失败的位置是工具查找。

### Fix It: 分析事件轨迹

不要马上把 `"missing"` 改回 `"echo"`。先回答三个诊断问题：

1. 这条 trail 里有 `model_response` 吗？如果有，说明 model 有没有成功返回内容？
2. 这条 trail 里有 `tool_call` 吗？如果有，说明 JSON 格式有没有通过 runtime 解析？
3. 最后一条 `error` 的 kind 是 `unknown_tool`，这说明问题在 JSON、model、handler，还是工具注册表？

回答完再修。这里有两种合理修法：

- 把 JSON 里的 `"name": "missing"` 改回 `"name": "echo"`。
- 或者真的注册一个名叫 `missing` 的工具。

对这个练习，优先选第一种，因为我们是在练“读 trail 找错位”，不是新增工具。上面的 `FakeModel` 已经准备了第二条最终回答；所以你把工具名修回 `echo` 以后，这个 run 应该能恢复成六步成功轨迹。

> [DD] **设计决策**：为什么 `AgentRunner` 不在调用前把工具存在性预先吞掉？
>
> **选了**：`AgentRunner` 先记录 model 真实提出的 `tool_call`，再交给 `ToolRuntime` 查找和执行；如果工具不存在，就由 `ToolRuntime` 抛出 `UnknownToolError`，runner 记录 `error` event。
> **没选**：runner 在记录 `tool_call` 之前就静默拒绝、改写工具名，或把所有工具查找逻辑散落在 runner 里。
> **因为**：失败轨迹必须保留 model 原本想做什么。研究助手以后调错论文检索工具时，Workbench 需要显示“model 请求了哪个工具”和“工具注册表为什么拒绝”，而不是只显示一个模糊失败。

#### Break & Fix 练习反馈

**Common Errors**:

1. 看到异常就只改代码，不看 events - 原因：把异常当终点，而不是当诊断入口。
2. 以为 `unknown_tool` 是 JSON 格式错 - 原因：没有注意 trail 里已经出现 `tool_call`。
3. 把 handler 里的逻辑改来改去 - 原因：不知道错误发生在 handler 执行之前。

**Failure Output Interpretation**: `['model_request', 'model_response', 'tool_call', 'error']` 表示 runtime 已经走到“准备执行工具”。`unknown_tool` 表示工具名没有出现在 `ToolRuntime` 的注册表里。它不是 model 没回答，也不是 handler 返回错。

**Where To Go Back**: 回到 Section 2 的 tool run sequence，对照每个 event 的意义。再看 L1 练习 2 里 `ToolDefinition(name="echo", ...)` 和 JSON 里的 `"name": "echo"` 必须对上。

**Why Correct Answer Is Correct**: 正确诊断应该指出：失败发生在工具查找边界。因为 `FakeModel` 已经有第二条 final response，把 JSON 名称改回已注册工具以后，sequence 应该恢复成六步 tool run；如果只改 handler，错误不会消失。

## Section 4: 接入你的 Workbench [PRODUCT - LIGHT]

现在还没有打开 UI，但 Part 1 已经在定义未来 Workbench 会依赖的数据协议。

本地论文研究助手以后不是只在终端里跑。研究员会在 Workbench 里问问题、看时间线、检查工具参数、定位失败。那时，Section 2 和 Section 3 看到的 event trail 会变成产品界面的数据来源。

| Event Type | Future Workbench Location | Researcher Sees |
| --- | --- | --- |
| `model_request` | Timeline panel | 这次 run 第几步把哪些 message 交给 model |
| `model_response` | Timeline panel | model 返回的是最终文本，还是 tool-call JSON |
| `tool_call` | Tool Inspector | model 请求了哪个工具，参数是什么 |
| `tool_result` | Tool Inspector | 工具实际返回了什么数据 |
| `error` | Failure Diagnostics | 失败种类、失败消息、失败发生在哪一步 |

> [BIG] **大局观**：Part 1 的 event trail 会成为 Part 5 Workbench timeline 的数据源。你现在写的不是“为了测试方便的打印”，而是产品将来解释一次研究过程的共同事实。

这也是为什么 `events_to_records(result.events)` 很重要。dataclass 适合核心代码，普通 dict record 更适合 API、UI 和测试 fixture。未来 Workbench 可以拿到 records 后渲染 timeline；eval 也可以拿同一份 records 断言“这个 run 有没有真的调用工具”。

Product 视角下最重要的问题不是“这个回答好不好听”，而是：

```text
Can the researcher inspect how the answer was produced?
```

如果 Workbench 只展示 final answer，研究员很难知道本地论文助手有没有真的查资料。如果 Workbench 展示 event trail，研究员至少能看见：模型请求了什么、工具返回了什么、失败发生在哪里。

## Section 5: Eval Gate [GATE - LIGHT]

### Minimal eval

项目级检查命令：

```bash
uv run pytest -q
uv run ruff check .
```

这两个命令不是为了证明你“懂了”，而是为了证明 runtime 和课程相关代码没有被破坏。你真正的学习 self-check 是：不看上面的代码，自己从空 Python shell 写出一个完整 tool run。

### Core self-check

从新的 shell 开始：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

然后自己完成这几件事：

1. import `AgentRunner`、`ToolRuntime`、`ToolDefinition`、`event_type_sequence`。
2. import `FakeModel`、`FakeModelResponse`。
3. 写出这个精确 tool-call JSON：

```json
{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}
```

4. 注册 `echo`。
5. 运行 `AgentRunner`。
6. 断言 event sequence 是六步 tool run。

如果你能不看答案写出来，Part 1 的 kernel 基本过关。

## Checkpoint

### L3 Design 练习

设计一个 multi-tool calculator agent。它不是论文助手的最终工具，但它会训练你设计连续工具调用的 event trail。后面本地论文研究助手做“先检索论文，再总结证据”时，本质上也是连续工具步骤。

要求：

- 4 个工具：`add`、`subtract`、`multiply`、`divide`。
- 任务：`"3+4 then multiply by 2"`。
- 你要写出 `FakeModel` sequence、`ToolDefinition`、预测 event sequence、运行、比较。
- 必须连续调用两次工具后才给 final answer：先 `add`，再 `multiply`。

先预测 event sequence：

```python
[
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

完成后再对照这个参考实现：

```python
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime
from research_core.runtime import event_type_sequence, events_to_records
from research_core.testing import FakeModel, FakeModelResponse

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

result = AgentRunner(model=model, tools=tools).run(
    run_id="calculator_1",
    system_prompt="You are careful.",
    user_message="3+4 then multiply by 2",
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

print(result.final_message.content)
print(event_type_sequence(result.events))

records = events_to_records(result.events)
tool_values = [
    record["payload"]["tool_result"]["content"]["value"]
    for record in records
    if record["type"] == "tool_result"
]
print(tool_values)

assert result.final_message.content == "3+4 is 7, and 7*2 is 14."
assert event_type_sequence(result.events) == expected_sequence
assert tool_values == [7, 14]
```

你应该看到：

```text
3+4 is 7, and 7*2 is 14.
['model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response', 'tool_call', 'tool_result', 'model_request', 'model_response']
[7, 14]
```

#### L3 Design 练习反馈

**Common Errors**:

1. 只写一个 tool call 就 final - 这样没有证明 runner 能连续执行两轮工具。
2. 第二次 `multiply` 的参数还写成 `{"a": 3, "b": 4}` - 这样没有表达“先 add 得到 7，再 multiply by 2”。
3. 注册了 4 个工具，但 JSON name 和工具 name 对不上 - 这会变成 Section 3 的 `unknown_tool`。
4. 以为 runtime 会自动把第一次工具结果填进第二次 tool-call JSON - 当前 `FakeModel` 是固定剧本，第二次参数要你自己写清楚。

**Failure Output Interpretation**: 如果只有六个 event，说明你只完成了一次工具调用。 如果最后是 `unknown_tool`，先看 JSON 里的 `"name"` 是否和 `ToolDefinition(name=...)` 完全一致。 如果 event sequence 正确但 `tool_values` 不是 `[7, 14]`，优先检查 handler 的加法/乘法逻辑。 如果 tool values 对了但 final answer 不对，检查第三条 `FakeModelResponse`，因为 final answer 来自最后一次 model response。

**Where To Go Back**: 回到 Section 2 的 tool run sequence，先确认“一次工具调用 = 四个中间事件 + 下一次 model_request”。再回到 Section 3，看 `unknown_tool` 怎样说明工具名和注册表没有对上。

**Why Correct Answer Is Correct**: 十个 event 证明 runner 连续完成了两轮“model 请求工具 -> runtime 执行工具 -> 工具结果回到对话 -> 再问 model”。`tool_values == [7, 14]` 证明两个 handler 真的算出了中间值和最终值。`3+4 is 7, and 7*2 is 14.` 证明最后答案来自第三次 model response；前两次 model response 都只是工具请求。

### Reflection

用自己的话回答，不要背定义：

1. 为什么 Part 1 要先用固定的 `FakeModel`，而不是一上来接真实大模型？
2. 如果未来本地论文研究助手回答错了，event trail 能帮你区分哪三类问题？
3. 为什么 tool-call JSON 是 model response 的内容，但 tool result 必须是单独的 event？

### Discussion

可以自己写下来，也可以和同伴讨论：

1. 如果 Workbench timeline 只能显示 final answer 和 error，中间工具步骤被隐藏，研究员会误判什么？
2. 如果以后接真实 OpenAI function calling，你会保留当前 `ToolRuntime` 和 event trail 的哪些边界？

完成 Part 1 后，你的本地论文研究助手已经有了最小 agent loop 骨架：它可以接收研究问题形状的输入，调用一个已注册工具，返回 scripted final answer，并且整个运行过程被 event trail 完整记录。

Next - Part 2 teaser: 你的助手能回答了，但它的回答有证据吗？
