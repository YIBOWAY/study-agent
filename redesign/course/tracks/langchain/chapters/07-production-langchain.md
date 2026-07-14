# Part 7: Production Readiness（LangChain 轨）

> 接 Part 6。上线前先回答：框架真的执行了什么？危险工具能否在副作用前
> 被拦住？记录能否重放？本章把 LangChain callback、课程 `AgentStep`、
> approval hook、JSONL 和 sandbox 决策放进同一张安全台。

预计时间：90–120 分钟。

## Learner Contract

- **你会构建**：`LangChainTraceRecorder`、`RunDiagnostics`、
  `JsonlStepStore`、执行前 approval hook 和 `SandboxPolicy`。
- **你会解释**：callback 与 `AgentStep` 的分工；观察为何不等于控制；
  approval 与 sandbox 为何不能合成一个万能 `if`。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_production.py -q`。
- **诚实边界**：sandbox 是可检查决策合同，不是 OS/container 隔离；本地
  callback 也不是 LangSmith 或不可篡改审计服务。

## 与 handwritten 对照

| Handwritten | LangChain 轨 |
| --- | --- |
| `RunEvent` | 课程 `AgentStep` + LangChain callback lifecycle |
| `RunDiagnostics.from_events` | `RunDiagnostics.from_steps` |
| `JsonlRunEventStore` | `JsonlStepStore` |
| runner 内 approval | `before_tool` hook → `BaseTool.invoke` |
| sandbox policy | 同语义教学类型，不声称系统隔离 |

> [DD] 保留两条观测线：callback 证明框架发生了什么；`AgentStep` 保存课程
> 关心的稳定语义。把二者强行做成一个对象，升级框架时会拖着产品合同一起变。

## Section 1：问题钩子

```text
ChatModel / BaseTool lifecycle ---> callback records
               |
               +---------------> AgentStep trail ---> diagnostics / JSONL

model requests tool
      ---> approval hook (ALLOW / REVIEW / DENY)
      ---> only ALLOW reaches BaseTool.invoke
```

如果 callback 只记录“工具开始”，却没有执行前 gate，危险动作仍然会发生。

## Section 2 [BUILD]：diagnostics + JSONL

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from langchain_course.agent_kernel import AgentStep
from langchain_course.production import JsonlStepStore, RunDiagnostics

steps = [
    AgentStep(kind="model_request", payload={"step": "plan"}),
    AgentStep(kind="tool_call", payload={"tool": "keyword_search"}),
    AgentStep(kind="error", payload={"error_kind": "tool_error", "message": "missing"}),
    AgentStep(kind="model_response", payload={"content": "partial"}),
]
diag = RunDiagnostics.from_steps("run_7", steps)
assert diag.event_count == 4
assert diag.error_summaries[0]["message"] == "missing"

with TemporaryDirectory() as tmp:
    store = JsonlStepStore(Path(tmp) / "steps.jsonl")
    store.append_steps("run_7", steps)
    assert store.list_run_ids() == ("run_7",)
    assert len(store.read_run("run_7")) == 4
```

## Section 3 [BUILD / INSPECT]：真实 callback 生命周期

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_course.agent_kernel import run_tool_calling_agent
from langchain_course.production import LangChainTraceRecorder

trace = LangChainTraceRecorder()
callback_model = FakeListChatModel(responses=["callback answer"])
callback_result = run_tool_calling_agent(
    user_message="hello callbacks",
    model=callback_model,
    config={"callbacks": [trace], "tags": ["part-7"]},
)
callback_kinds = [item["kind"] for item in trace.records]
print(callback_kinds)
assert "chat_model_start" in callback_kinds
assert "llm_end" in callback_kinds
assert callback_result.final_text == "callback answer"
```

> [CHECK] 这里用的不是手工 callback 记录；`FakeListChatModel` 经过真实
> `BaseChatModel.invoke`，LangChain callback manager 触发 recorder。

## Section 4 [BUILD]：approval 与 sandbox 决策

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from langchain_course.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    SandboxPolicy,
)

policy = ApprovalPolicy(
    rules=(
        ApprovalRule("keyword_*", ApprovalMode.ALLOW, "local retrieval ok"),
        ApprovalRule("shell_*", ApprovalMode.DENY, "no shell"),
    )
)
assert policy.decide("keyword_search").mode is ApprovalMode.ALLOW
assert policy.decide("shell_rm").mode is ApprovalMode.DENY
assert policy.decide("other").requires_review

with TemporaryDirectory() as tmp:
    workspace = Path(tmp) / "workspace"
    workspace.mkdir()
    sandbox = SandboxPolicy(
        readable_paths=(workspace,),
        writable_paths=(workspace,),
        allow_network=False,
    )
    assert sandbox.decide_path(workspace / "paper.json", access="read").allowed
    assert sandbox.network_decision().allowed is False
```

> [TRAP] Approval 管 tool subject；Sandbox 管 path/network/runtime。两者都
> 返回决定，但它们保护的对象不同。

## Section 5 [BREAK / FIX]：审批必须先于副作用

```python
from langchain_core.tools import StructuredTool
from langchain_course.fake_models import tool_then_final_model
from langchain_course.production import build_approval_hook

side_effects = []

def dangerous(value: str) -> str:
    """Record a side effect for the approval lesson."""
    side_effects.append(value)
    return value

dangerous_tool = StructuredTool.from_function(dangerous, name="shell_write")
gate_model = tool_then_final_model(
    tool_name="shell_write",
    tool_args={"value": "should-not-run"},
    final_text="blocked safely",
)
blocked = run_tool_calling_agent(
    user_message="write now",
    tools=[dangerous_tool],
    model=gate_model,
    before_tool=build_approval_hook(policy),
)
assert side_effects == []
assert any(step.kind == "tool_decision" for step in blocked.steps)
```

故意把 gate 移到 `tool.invoke()` 后面，测试中的 `side_effects` 就会出现内容。
修复不是“多记一条 DENY”，而是恢复执行顺序。

> [CHECK] control before effect；audit after decision。顺序本身就是安全合同。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_production.py -q
```

## Section 6 [REFLECT]

1. callback 能否代替 approval hook？为什么？
2. 默认 `REQUIRE_APPROVAL` 比默认 `ALLOW` 多付出了什么成本？
3. 什么时候本地 JSONL 足够，什么时候需要远程 tracing 或不可篡改日志？
4. 如果 sandbox 只返回 `allowed=False`、runner 却不调用它，安全性如何？

下一步：LC Capstone 用真实 tool loop 合成 Parts 1–7，并保留 offline/live 两条路。
