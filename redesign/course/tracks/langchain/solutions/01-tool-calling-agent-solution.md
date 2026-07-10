# Solution 01 — Tool-calling Agent（LangChain 轨）

## 参考要点

### L1 Plain final

- `tools=[]` 时不会 `bind_tools`。
- steps 固定为 `user_message → model_request → model_response`。
- 这对应 handwritten 的 `model_request → model_response`（本轨多记一条 user_message，便于对照输入）。

### L1 Echo loop

- 第一轮 AIMessage 带 `tool_calls`；runtime 执行 `echo`，写入 `ToolMessage`。
- 第二轮无 tool_calls → `final_text`。
- `tool_result.payload["content"] == "lab"` 证明工具真的跑了，不是 model 自说自话。

### L2 message_records

- records 是 dict 拷贝列表，适合打印与序列化；不要把它当成唯一真相源——`steps` 才是教学主 trail。
- `add(2,3)` 的 observation 可能是 `"5"` 或 `"5.0"`（float 工具返回），断言时兼容两者。

### L3 Design

```python
from langchain_course.agent_kernel import AgentKernelError, run_tool_calling_agent, step_kinds
from langchain_core.messages import AIMessage
from langchain_course.tools_echo import echo

class Scripted:
    def __init__(self, responses):
        self._responses = list(responses)
    def bind_tools(self, tools, **kw):
        return self
    def invoke(self, messages, **kw):
        return self._responses.pop(0)

loop_msg = AIMessage(content="", tool_calls=[{"id": "c1", "name": "echo", "args": {"text": "x"}}])
try:
    run_tool_calling_agent(user_message="x", tools=[echo], model=Scripted([loop_msg, loop_msg]), max_steps=2)
    raise AssertionError("should have failed")
except AgentKernelError as exc:
    assert "max_steps" in str(exc)

model = Scripted([
    AIMessage(content="", tool_calls=[{"id": "c1", "name": "nope", "args": {}}]),
    AIMessage(content="recovered"),
])
result = run_tool_calling_agent(user_message="x", tools=[echo], model=model)
assert "unknown tool" in next(s for s in result.steps if s.kind == "tool_result").payload["content"]
assert result.final_text == "recovered"
```

## 为何这样对照 handwritten

| 主课纪律 | 本轨如何兑现 |
| --- | --- |
| 看 event trail | 看 `step_kinds` / `AgentStep` |
| 工具必须真执行 | `tool_result` content 来自 `BaseTool.invoke` |
| 预算 | `max_steps` 用尽 raise |
| 离线可测 | Scripted model，不碰网络 |

## 常见错误

1. 把 live 输出当 golden string → 改用结构断言。
2. 忘记 `tools=[echo]` 却期望 tool_call → model 无法合法调用。
3. 复用耗尽的 Scripted responses → 重新创建 model。
