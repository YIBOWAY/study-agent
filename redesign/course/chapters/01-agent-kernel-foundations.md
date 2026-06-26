# Chapter 01: Agent Kernel Foundations

## Goal

这一章会带你做出第一个最小 Agent kernel。

学完以后，你应该能看懂一次 Agent run 的主线：

```text
user message
  -> context
  -> model response
  -> optional tool call
  -> tool result
  -> final model response
  -> event sequence
```

预计时间：60 到 90 分钟。

## Before You Start

如果你是第一次看这套课程，请先完成：

- `00-before-agent-kernel.md`
- `../labs/00-environment-check.md`
- `../reference/agent-kernel-glossary.md`

这一章会用到 Python list、dict、`lambda`、`assert`、`try / except`。不熟也没关系，遇到卡点就回看 `../reference/python-terminal-primer.md`。

## The Idea In Plain Language

一个 Agent 不是“一个模型加一点 prompt”。

在这个项目里，一个 Agent 至少要有这几件事：

- 一套内部 message 格式，避免核心代码被某个 provider 绑死。
- 一个 context builder，决定这次 model 能看到什么。
- 一个 tool runtime，管理哪些工具能被调用。
- 一个 runner，把 model 和 tool 串成循环。
- 一条 event stream，把运行过程记下来。

Chapter 01 的重点不是让 Agent 变聪明，而是让 Agent 变得可观察。只有你能看清中间发生过什么，后面才谈得上 memory、delegation、product UI 和 eval。

## The Smallest Useful Loop

这章的 `AgentRunner` 做的事很少，但每一步都重要：

1. 把用户输入包装成 `AgentMessage`。
2. 用 `ContextBuilder` 插入唯一的 system prompt。
3. 记录 `model_request` event。
4. 调用 model。
5. 记录 `model_response` event。
6. 如果 model 返回普通文本，就结束。
7. 如果 model 返回 tool-call JSON，就解析成 `ToolCall`。
8. 记录 `tool_call` event。
9. 用 `ToolRuntime` 执行工具。
10. 记录 `tool_result` event。
11. 把 tool result 追加成一条 tool message。
12. 再问 model 一次，直到拿到最终文本或步数耗尽。

这就是一个最小的 think-act-observe loop。

## Core Objects

| Object | Plain Meaning | Why It Exists |
| --- | --- | --- |
| `AgentMessage` | 内部对话片段 | 让核心 runtime 不依赖 OpenAI、Anthropic 或任何框架的 message 格式 |
| `RunEvent` | 运行过程记录 | 让 timeline、debug、replay、eval 都有同一份事实来源 |
| `ContextBuilder` | context 组装器 | 保证 system prompt 从一个入口进入，并控制 message window |
| `ToolDefinition` | 工具注册信息 | 告诉 runtime 工具叫什么、做什么、怎么执行 |
| `ToolCall` | 工具调用请求 | 表示 model 想调用哪个工具，带哪些参数 |
| `ToolResult` | 工具执行结果 | 把工具输出变成可记录、可追加回对话的结构 |
| `ToolRuntime` | 工具管理器 | 注册工具、查找工具、执行工具 |
| `AgentRunner` | Agent loop | 把 context、model、tool、event 串起来 |
| `AgentRunResult` | 一次运行的结果包 | 同时保存 final message、messages 和 events |

## Response Shape

Chapter 01 里，model 有两种合法输出。

普通文本表示最终答案：

```text
The tool said hello.
```

JSON 表示它要调用工具：

```json
{
  "tool_call": {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"}
  }
}
```

这不是为了规定所有 Agent 都必须这样写。它只是课程里的最小协议：足够小，新手能看懂；足够清楚，测试能稳定检查。

## Minimal Example

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴这段代码：

```python
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime
from research_core.testing import FakeModel, FakeModelResponse

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
    run_id="run_1",
    system_prompt="You are careful.",
    user_message="Say hello through the tool.",
)

print(result.final_message.content)
```

你应该看到：

```text
The tool said hello.
```

这只是表面结果。真正重要的是它走过了哪些步骤。

继续粘贴：

```python
from research_core.runtime import event_type_sequence

print(event_type_sequence(result.events))
```

你应该看到：

```python
[
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]
```

这条 sequence 说明：Agent 先问了 model；model 要求调用 tool；Agent 调了 tool；Agent 带着工具结果又问了一次 model；最后 model 给出文本答案。

## Why Events Matter

只看 final answer，你只知道“最后说了什么”。

看 event sequence，你能知道“它怎么走到最后的”。

这在真实系统里非常关键。比如：

- final answer 看起来正常，但 tool 根本没被调用。
- tool 调用了，但参数错了。
- tool 成功了，但结果没被追加回 model context。
- run 失败了，但失败前的轨迹仍然能帮你定位问题。

所以本项目把 `RunEvent` 当成 runtime contract，而不是随手打印的 log。

## Failure Lab Preview

把 tool call 里的 `"name": "echo"` 改成 `"name": "missing"`，这次 run 会失败。

但失败不是一片空白。你仍然可以从异常里拿到 events，看到：

```python
["model_request", "model_response", "tool_call", "error"]
```

这就是本章最重要的工程习惯：失败也要留下可检查的 runtime artifact。

## Product Integration

Phase 1 还没有 UI，但它已经在给未来的 Research Agent Workbench 铺路。

后面的产品界面会把这些事件显示出来：

- `model_request` 和 `model_response` 进入 run timeline。
- `tool_call` 和 `tool_result` 进入 tool inspector。
- `error` 进入 failure diagnostics。
- trajectory helpers 进入 smoke tests 和 eval fixtures。

也就是说，Chapter 01 写的不是临时教学代码。它是在定义未来产品也会依赖的协议。

## Framework Comparison

本章先不引入 LangGraph、AutoGen、CrewAI 或其他框架。

原因不是框架不好，而是初学者需要先看见底层机制：message 怎么进来，tool 怎么执行，event 怎么留下。等 Phase 6 做 framework comparison 时，会用同一个 echo-tool task 对比手写 runner 和框架版本，看谁更容易观察、测试和 debug。

## Eval Gate

本章最小 eval gate 是 tool run 的 event sequence：

```python
[
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]
```

项目级检查命令是：

```bash
uv run pytest -q
uv run ruff check .
```

如果这两个命令通过，而且 lab 里的 event sequence 对得上，你就完成了 Chapter 01 的核心学习目标。

## Checkpoint

继续 lab 之前，用自己的话回答：

1. `AgentMessage` 为什么不能直接等同于 provider message？
2. 为什么 `ContextBuilder` 要拒绝 caller-provided system message？
3. `FakeModel` 在学习里解决了什么问题？
4. 为什么一次失败 run 也应该有 events？
5. 正常 tool run 的 event sequence 是什么？

答不完整没关系。带着问题去做 `../labs/01-agent-runner-lab.md`，做完再回来答一次。
