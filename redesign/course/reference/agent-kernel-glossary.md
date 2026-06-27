# Agent Kernel Glossary

这页用人话解释 Chapter 01 会遇到的词。先有感觉，再看代码。

## Agent

Agent 不是一个神秘的大脑。这里的 Agent 是一段 runtime：它把用户问题交给 model，必要时调用 tool，把结果再交回 model，最后产出答案。

本项目里，Agent 的核心不是“聪明”，而是“可观察、可测试、可复盘”。

## Model

Model 是生成文本的东西。真实项目里它可能是 OpenAI、Anthropic、本地模型或别的 provider。课程里先不用真实模型，而是用 `FakeModel`。

## FakeModel

`FakeModel` 是一个离线模型替身。你提前告诉它第一步返回什么、第二步返回什么，它就照着返回。

这让课程和测试不依赖网络、不依赖 API key，也不会因为真实模型输出漂移而得到不同答案。

## Message

Message 是对话里的一个片段。比如用户说了什么、assistant 回了什么、tool 返回了什么。

代码里用 `AgentMessage` 表示内部 message。它不是 OpenAI message，也不是 Anthropic message。这样以后换 provider 时，核心 runtime 不需要跟着大改。

## Role

Role 表示一条 message 的身份：

- `system`: 系统规则。
- `user`: 用户输入。
- `assistant`: 模型或 Agent 的回复。
- `tool`: tool 执行后的观察结果。

## System Prompt

System prompt 是系统给 Agent 的最高层指令，比如“你要谨慎”。Chapter 01 里，`ContextBuilder` 会保证 system prompt 只能从一个入口进入，避免调用方偷偷塞第二条 system message。

## Context

Context 是一次 model request 看到的全部 message。它不是整个世界，也不是所有历史，只是这一次传给 model 的输入窗口。

## Tool

Tool 是 Agent 可以调用的函数。比如搜索、读文件、查数据库、计算、发请求。Chapter 01 里只有一个最小的 `echo` tool，用来证明 tool call 机制能跑通。

## Tool Call

Tool call 是 model 发出的“我要调用这个工具”的请求。Chapter 01 里约定 model 如果要调用工具，就返回这样的 JSON：

```json
{
  "tool_call": {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"}
  }
}
```

这不是所有框架都通用的格式。它只是本课程为了讲清机制而定的最小协议。

## Tool Result

Tool result 是 tool 执行后的结果。比如 `echo` 收到 `{"text": "hello"}`，返回 `{"text": "hello"}`。

AgentRunner 会把 tool result 追加成一条 `tool` message，让下一次 model request 能看到工具返回了什么。

## RunEvent

`RunEvent` 是运行过程里的事件记录。它回答的问题不是“最后答案是什么”，而是“中间发生过什么”。

比如：

- 发起了一次 model request。
- 收到了一次 model response。
- model 请求调用 tool。
- tool 返回了结果。
- 某一步失败了。

## Event Sequence

Event sequence 是事件类型的顺序。比如一次正常 tool run 应该是：

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

这比只看最终答案更可靠。最终答案可能一样，但中间路径可能已经坏了。

## Trajectory

Trajectory 是一次 Agent run 的运行轨迹。你可以把它理解成 Agent 的“行车记录”。它包含事件顺序和关键 payload。

课程会反复强调 trajectory，因为真正的 Agent 工程需要能复盘过程，而不是只看最终一句话。

## JSON-Compatible

JSON-compatible 表示数据能安全变成 JSON。简单说，字符串、数字、布尔值、list、dict 通常可以；Python 的 `set` 不行。

Tool arguments、tool result、event payload 都要尽量保持 JSON-compatible，这样后面才能保存、展示、回放、对比。

## Immutable

Immutable 表示创建后不应该被随便改。课程里的 message、event、tool call、tool result 都倾向 immutable，因为运行轨迹一旦记录下来，就应该像证据一样可靠。

## Eval Gate

Eval gate 是每章结束时用来证明“这个机制还正常”的检查。Chapter 01 的 gate 是 event sequence 和完整测试命令。

## Workbench

Workbench 是这个项目的产品界面。Phase 5 已经有第一个本地版本：FastAPI 提供 `/api/workbench/snapshot`，React/Vite 在 `apps/web` 渲染 timeline、delegation、evidence、report、memory、skills 和 eval panels。

Chapter 01 的 `RunEvent` 仍然是 Workbench timeline 的底层来源；Chapter 05 会解释它如何被 `WorkbenchSnapshot` 转成 API/UI 能消费的 record。
