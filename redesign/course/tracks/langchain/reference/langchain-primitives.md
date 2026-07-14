# LangChain Core 原语速查（LC 轨）

这张表回答一个问题：当前课程中的哪一部分是 LangChain 框架能力，哪一部分是
我们为了研究助手业务显式补上的合同。

## 组合原语

| 原语 | 本课用途 | 不自动提供 |
| --- | --- | --- |
| `BaseChatModel` | 统一 live DeepSeek 与离线确定性模型 | 引用正确性、审批策略 |
| `AIMessage.tool_calls` | 模型声明工具调用 | 工具是否被授权 |
| `BaseTool.invoke` | 实际执行工具并触发 callback | sandbox、业务幂等 |
| `Document` | 在 Retriever/Runnable 中传递文本和 metadata | Claim/Evidence 强引用 |
| `BaseRetriever` | `invoke(query)` 的标准检索边界 | embedding、引用校验 |
| `RunnableSequence` / `|` | 上一步输出进入下一步 | 产品数据模型 |
| `RunnableParallel` | 同一输入并发进入多个只读 worker | 总预算、失败回滚 |
| `RunnableWithMessageHistory` | 按 session 读写 Human/AI 消息 | 长期记忆 policy |
| `BaseCallbackHandler` | 观察 model/tool lifecycle | 执行前阻断、不可篡改日志 |

官方参考：

- [Runnable](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable)
- [RunnableParallel](https://reference.langchain.com/python/langchain-core/runnables/base/RunnableParallel)
- [RunnableWithMessageHistory](https://reference.langchain.com/python/langchain-core/runnables/history/RunnableWithMessageHistory)
- [LangChain Core reference](https://reference.langchain.com/python/langchain-core)

## 三条不要混淆的边界

```text
framework execution: message / runnable / retriever / callback
business invariants: claim links / memory policy / approval / snapshot integrity
product boundary: stable JSON panels / API / UI
```

框架升级时，第一层最容易变；研究助手仍必须守住后两层。

## Offline 不等于 fake architecture

离线测试应替换网络模型，不应绕过框架路径：

- 好：确定性 `BaseChatModel` → `bind_tools` → `BaseTool.invoke`；
- 坏：直接创建一串看起来像运行结果的 `AgentStep`；
- 好：本地 `BaseRetriever` 返回 `Document`；
- 坏：只测自定义列表排序，却宣称测过 LangChain Retriever。

## Version boundary

当前课程验证于 LangChain Core 1.4.x。`RunnableWithMessageHistory` 会提示把新的
持久化应用迁往 LangGraph。LC 轨保留它来学习 history invocation contract；
F4/F5 用 graph state/store/checkpoint 接棒，而不是假装 warning 不存在。
