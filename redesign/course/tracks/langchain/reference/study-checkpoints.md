# LangChain 轨学习检查点

不要用“看完了”判断掌握。每完成一 Part，合上材料，用下面的问题做检索练习。

## Part 0–1

1. `ChatOpenAI` 在哪里读取 base URL、model 和 key？
2. 模型返回 tool call 后，哪四类 message 会出现在下一次 model request？
3. 为什么确定性 `BaseChatModel` 仍比手工轨迹更适合离线验收？

## Part 2–3

1. `PaperDoc` 与 LangChain `Document` 为什么同时存在？
2. `BaseRetriever` 保证了什么，又没有保证什么？
3. message history 与长期 Notebook policy 的生命周期差异是什么？
4. 当前 history API 的弃用提示为什么是进入 LangGraph 的学习线索？

## Part 4–5

1. `RunnableParallel` 与 budgeted coordinator 各负责什么？
2. child context isolation 为什么不能靠 system prompt 声明完成？
3. snapshot 构造失败为什么优于 UI 自动修复？

## Part 6–7

1. 一条公平 framework comparison 至少要固定哪三项？
2. callback、approval hook、sandbox、JSONL 各保护哪条边界？
3. 为什么 DENY 必须发生在 `BaseTool.invoke` 之前？

## Capstone exit ticket

不看 solution，画出并解释：

```text
question -> LC model -> tool call -> approval -> local retrieval
         -> evidence/claim link -> snapshot -> diagnostics/JSONL
```

然后指出哪些箭头属于 LangChain，哪些 invariant 属于课程自己。
