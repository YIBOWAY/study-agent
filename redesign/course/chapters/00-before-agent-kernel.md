# Chapter 00: Before You Build An Agent Kernel

## Goal

这一章帮你建立第一张心智地图：一个 Agent runtime 到底在管什么。

读完以后，你不需要会写完整 Agent，但应该能说清楚：

- model 和 Agent runtime 不是一回事。
- tool 只是被 runtime 管起来的函数。
- event stream 是为了让运行过程可观察。
- fake model 是为了让学习和测试稳定。

预计时间：30 到 45 分钟。

## The Plain Version

很多人第一次学 Agent，会直接从“让大模型调用工具”开始。这样很容易晕，因为你会同时遇到 provider API、prompt、JSON、tool schema、memory、UI、数据库、异步任务、权限控制。

本课程先把这些东西拆开。

Chapter 01 只关心一个最小问题：

```text
用户说一句话
Agent 把这句话交给 model
model 如果要用工具，就返回一个 tool_call
Agent 调用工具
Agent 把工具结果再交给 model
model 给出最终回答
整个过程留下事件记录
```

这就是最小 Agent kernel。

## First Mental Model

先把 Agent 想成一个很认真记账的协调员：

```text
User
  -> AgentRunner
      -> ContextBuilder
      -> Model
      -> ToolRuntime
      -> RunEvent stream
  -> Final answer
```

每个部件只做一件事：

| Part | Human Meaning | Code Name |
| --- | --- | --- |
| User | 提出任务的人 | `user_message` |
| Internal message | 对话片段 | `AgentMessage` |
| Context builder | 组装这次要给 model 看的消息 | `ContextBuilder` |
| Model | 生成下一步文本 | `FakeModel` in labs |
| Tool runtime | 注册和执行工具 | `ToolRuntime` |
| Event | 运行过程记录 | `RunEvent` |
| Runner | 把以上步骤串起来 | `AgentRunner` |

## Why Not Use A Real Model First

真实模型很有用，但不适合做第一节课的基础设施练习。

原因很简单：

- 它需要 API key。
- 它可能输出不同内容。
- 网络失败会干扰学习。
- 新手会把 provider 问题误以为 runtime 问题。

所以课程先用 `FakeModel`。它不会思考，只会按你给的剧本返回内容。正因为它“不聪明”，你才能清楚看到 runtime 是怎么工作的。

## What You Need To Know Before Chapter 01

你需要会一点 Python，但要求不高：

- 能运行 terminal 命令。
- 能进入 Python shell。
- 能看懂 list 和 dict。
- 能看懂 `from ... import ...`。
- 能用 `print(...)` 看变量。
- 能接受暂时不理解每个实现细节，先把路径跑通。

如果这些还不熟，先读：

- `../reference/python-terminal-primer.md`
- `../reference/agent-kernel-glossary.md`

## The First Rule Of This Course

不要只看 final answer。

Agent 系统最危险的地方是：它最后可能说了一句看起来对的话，但中间过程已经错了。比如它调用了错误工具、漏掉了证据、吞掉了异常、用了不该用的上下文。

所以本课程会一直要求你看 event sequence：

```python
["model_request", "model_response"]
```

或者：

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

这就是 Agent 的运行轨迹。学会看轨迹，比背框架 API 更重要。

## Checkpoint

继续 Chapter 01 之前，先用自己的话回答：

1. 为什么课程先用 `FakeModel`，而不是直接接真实模型？
2. `RunEvent` 记录的是最终答案，还是运行过程？
3. Tool 是模型自己执行的，还是 Agent runtime 执行的？
4. 如果一次 run 失败了，为什么还要保留 event sequence？

如果这四个问题能答出大概意思，就可以去做 `../labs/00-environment-check.md`。
