# LangChain 轨排障

## `DEEPSEEK_API_KEY is required`

- 离线 unit 不需要 key；先确认你没有误跑 `python-live` 示例。
- live 时从 `redesign/` 运行，检查 `.env`，不要提交真实 key。

## Retriever 有结果，但 claim link 失败

Retriever 返回 `Document` 只证明“找到了文本”。检查
`metadata.source_id → EvidenceItem.source_id → ClaimItem.evidence_ids` 是否完整。

## `RunnableWithMessageHistory` 要求 `session_id`

调用必须包含：

```python
config={"configurable": {"session_id": "research-1"}}
```

若看到迁往 LangGraph 的 warning，记录它，不要用全局 filter 隐藏。F4 会处理
新的 persistence 路径。

## Callback 没有事件

确认你调用的是 `BaseChatModel.invoke` / `BaseTool.invoke`，并把 recorder 放在
`config={"callbacks": [recorder]}`。直接调用普通 Python 函数不会触发 LC callback。

## DENY 了但工具仍有副作用

gate 放在工具执行之后。检查 runner 顺序必须是：

```text
tool call -> before_tool -> decision -> BaseTool.invoke
```

## Markdown gate 访问真实 API

离线可执行块使用 `python`；明确需要 key/费用的展示块使用 `python-live`。
不要靠本机恰好存在 `.env` 让文档测试通过。
