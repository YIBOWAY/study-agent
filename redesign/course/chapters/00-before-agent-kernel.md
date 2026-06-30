# Part 1: 你的第一个 Agent — 让它跑起来，并且能看懂它做了什么

## 你的本地论文研究助手现在需要：会跑

你要做的是一个完全离线的本地论文研究助手。它服务的是一个研究团队：有人会问“最近哪些论文在讨论检索增强生成的评测？”或者“帮我比较这几篇论文的实验结论”。现在它还什么都不会做，只是一堆即将被连接起来的代码和课程材料。

Part 1 只解决第一件事：让它会跑，并且让你看得懂它跑的时候做了什么。

先不要急着让它“聪明”。一个研究助手如果连自己的步骤都说不清，就算最后写出一段漂亮总结，研究员也很难信任它。Part 1 会先搭出最小 Agent loop：收到研究问题，交给 model，必要时调用工具，再把过程记成事件轨迹。

> [BIG] **大局观**：Part 1 只做两件事：让助手能跑一次，并且留下你看得懂的 event trail。后面的论文检索、记忆、委派和界面，都会接在这条 trail 后面。

```text
Local Paper Research Assistant
  [*] Part 1: run once -> inspect the event trail
      [*] Section 1: mental model
      [ ] Section 2: build the smallest loop
      [ ] Section 3: break it and read the failure trail
  [ ] Later Parts: evidence, memory, delegation, UI, production checks
```

## Section 1: Agent 的心智模型 — 它到底在管什么

### Problem Hook

先想一个没有 Agent runtime 的下午。

研究员问你：“帮我看一下这批本地论文里，哪些在讨论 RAG 的评测方法？顺便总结一下它们怎么做实验。”

如果没有 runtime，你会手动做很多事：

- 打开论文目录，自己找可能相关的文件。
- 复制标题、摘要、实验段落。
- 临时调用一个检索函数或者脚本。
- 把检索结果贴给模型。
- 再把模型总结出来的内容整理成回答。
- 如果哪里不对，你只能靠记忆回想刚才到底复制过什么、漏看了什么。

这很累，而且不可靠。更麻烦的是，研究员看到的只有最后那段总结。他看不到你搜过哪些论文、模型看到了什么、工具有没有真的跑、工具结果有没有被重新交回模型。

本地论文研究助手要解决的不是“替你写一句更像样的话”，而是把这些步骤变成一条可重复、可检查的流程。

### Explore

把刚才的场景拆开看：

```text
Researcher asks a question
  -> someone prepares context from local papers
  -> someone asks the model what to do next
  -> maybe someone runs a search/summarize tool
  -> someone gives the tool result back to the model
  -> someone returns the final answer
  -> someone keeps a trace of every important step
```

停一下：如果这件事要交给程序，至少要自动化哪些动作？

你不需要马上知道代码怎么写。先抓住几个动作：

- 把研究员的问题保存下来。
- 决定这次 model 能看到什么上下文。
- 调用 model，让它产出下一步。
- 如果 model 要用工具，就由 runtime 去执行工具。
- 把工具结果放回对话，再问 model。
- 把每一步记录下来，方便之后检查。

这就是 Part 1 的范围。它还不是完整产品，也不是高级智能体。它只是让研究助手第一次有了“跑起来的骨架”。

### 概念：人话版

先记住一句话：Agent 不是脑子，它更像一个认真记账的协调员。

模型负责生成下一句话；工具负责做某个确定动作；Agent runtime 负责把这些东西按顺序管起来，并且记账。这里的“账”不是财务账，而是运行轨迹：什么时候问了 model，model 回了什么，什么时候调用了工具，工具返回了什么。

```text
User Input: "帮我找出这批论文里讨论 RAG 评测的证据"
      |
      v
+--------------------------------------------------+
| AgentRunner                                      |
|  1. ContextBuilder prepares model-visible context |
|  2. Model returns the next response               |
|  3. ToolRuntime runs a tool only when requested   |
+----------------------+---------------------------+
        |                              |
        v                              v
RunEvent stream                  Final Answer
model_request -> ...             "Here is what I found..."
```

这张图里，`AgentRunner` 是总协调员。当前代码里的真实关系也很朴素：`AgentRunner` 会调用 `ContextBuilder`，再调用 model，必要时调用 `ToolRuntime`，同时产出一串 `RunEvent`。

这些名字先不用背成 API。把它们放回研究助手的故事里看：

| Story Role | Human Meaning | Code Name |
| --- | --- | --- |
| 研究员 | 提出原始问题的人 | `User` / `user_message` |
| 对话便签 | runtime 内部统一保存的一条消息 | `AgentMessage` |
| 材料整理员 | 决定这次 model 能看到哪些消息 | `ContextBuilder` |
| 练习用模型 | 按剧本返回下一句话，不连真实网络 | `FakeModel` |
| 工具管理员 | 管理可用工具，并在被要求时执行工具 | `ToolRuntime` |
| 运行账本 | 记录每个关键步骤发生过什么 | `RunEvent` |
| 总协调员 | 把 context、model、tool、event 串成循环 | `AgentRunner` |
| 交给研究员的话 | 这次 run 最后返回的回答 | final answer |

`AgentMessage` 值得单独停一下。研究员说出的字符串是 `user_message`，但一旦进入 runtime，它会被包装成一条 `AgentMessage`。这样做不是为了复杂，而是为了让系统有统一的内部语言：user、assistant、tool、system 都能用同一种结构被保存、检查、追加。

> [DD] **设计决策**：为什么 `AgentMessage` 不是 provider message？
>
> **选了**：runtime 内部使用自己的 `AgentMessage`，必要时再转换成 provider 能懂的格式。
> **没选**：直接在核心代码里到处传 OpenAI、Anthropic 或其他 provider 的 message 字典。
> **因为**：这门课要先教清楚 Agent runtime 的机制，而不是把你绑在某个 API 形状上。以后研究助手可以继续用 `FakeModel`，也可以换成真实模型；核心 loop 不应该因为 provider 改了就被迫重写。

`FakeModel` 也不是“假装有智能”。它更像练车场里的固定路线：你已经知道它会怎么回，所以你能专心观察车是不是按路线开、仪表盘是不是记录正确。

> [DD] **设计决策**：为什么学习阶段先用 `FakeModel`？
>
> **选了**：`FakeModel` 返回预先写好的 `FakeModelResponse`，每次运行都稳定。
> **没选**：一开始就接真实大模型。
> **因为**：真实模型需要 API key 和网络，而且输出可能每次不同。初学时最怕把 provider 抖动误判成 runtime 错误。`FakeModel` 不聪明，正好让你看清 `AgentRunner` 的流程是不是对的。

> [CHECK] **Model vs AgentRunner vs ToolRuntime：谁负责什么？**
>
> `FakeModel` 只负责返回下一段内容。`AgentRunner` 负责决定什么时候问 model、什么时候解析 tool call、什么时候继续下一轮。`ToolRuntime` 负责找到已经注册的工具并执行它。模型可以“提出要用工具”，但真正执行工具的是 runtime 管起来的 `ToolRuntime`。

## The First Rule Of This Course

不要只看 final answer。

对本地论文研究助手来说，这条规则尤其重要。研究员要的不是一段看起来很会说话的文本，而是可信的研究过程：它到底看了哪些材料？有没有真的调用检索工具？工具结果有没有进入下一轮总结？最后的回答能不能追溯到过程？

所以本课程会一直训练你看 event sequence。

如果 model 直接给出普通回答，一次 run 的轨迹应该很短：

```text
model_request -> model_response
```

意思是：runtime 把上下文交给 model，model 返回最终文本，没有工具步骤。

如果 model 需要工具，一次 run 会多出中间过程：

```text
model_request
  -> model_response
  -> tool_call
  -> tool_result
  -> model_request
  -> model_response
```

意思是：model 先请求工具，`AgentRunner` 记录这个请求，`ToolRuntime` 执行工具，工具结果再被追加回对话，然后 runtime 再问 model 一次，直到拿到最终回答。

现在先不展开各种失败情况。Section 2 会开始让你亲手跑最小 loop，后面会故意打坏它，再学习怎么看轨迹。这里你只要先养成一个习惯：每次看到 final answer，都顺手问一句“event sequence 长什么样？”

## 继续 Section 2 之前

继续之前，你需要准备好这些东西：

- 能在 `redesign/` 目录运行 terminal 命令。
- 已经知道 `../reference/python-terminal-primer.md` 是 Python 和 terminal 卡住时的回看材料。
- 已经知道 `../reference/agent-kernel-glossary.md` 是术语卡住时的回看材料。
- 接受 Part 1 先用完全离线、确定性的 `FakeModel`，不接真实 API key。

Concept-check questions：

1. 如果研究助手最后给出了一段漂亮总结，但 event sequence 里没有任何 `tool_call`，你应该怎样解释这个结果？
2. 为什么 `AgentRunner` 不能只把研究员的问题丢给 model 就结束，而要同时管理 context、tool 和 event？
3. 如果将来把 `FakeModel` 换成真实模型，为什么 `AgentMessage` 这种内部格式仍然有价值？

下一节是 [01-agent-kernel-foundations.md](01-agent-kernel-foundations.md)。它就是 Part 1 的 Section 2：把这张心智地图变成一个真的最小 loop，让你的本地论文研究助手第一次跑起来。
