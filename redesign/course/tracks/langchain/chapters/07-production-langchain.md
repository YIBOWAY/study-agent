# Part 7: Production Readiness（LangChain 轨）

> 接 Part 6。上线前先回答：出事能否复盘？记录能否保存？危险动作能否在执行前被挡住？本轨用 `AgentStep` 轨迹做 diagnostics / JSONL / approval / sandbox——**离线、可测**，不接云日志。

预计时间：60–90 分钟。

## Learner Contract

- **你会构建**：`RunDiagnostics.from_steps`、`JsonlStepStore`、`ApprovalPolicy`、`SandboxPolicy`。
- **你会解释**：diagnostics 与 raw steps 的分工；JSONL 为何够本地审计；approval vs sandbox。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_production.py -q`。
- **诚实边界**：policy **不会**自动挂进 `run_tool_calling_agent`；你必须在产品适配层显式调用。教学 contract，不是 Kubernetes。

## 与 handwritten 对照

| Handwritten | 本轨 |
| --- | --- |
| `RunDiagnostics.from_events(RunEvent)` | `RunDiagnostics.from_steps(run_id, AgentStep)` |
| `JsonlRunEventStore` | `JsonlStepStore` |
| `ApprovalPolicy` / `SandboxPolicy` | 同名教学类型 |
| docs freshness gate | 主课 gate 仍在；本轨额外靠 unit |

## Section 1：本地安全台

```text
AgentStep trail
   -> RunDiagnostics (what happened)
   -> JsonlStepStore (what survives)
tool subject -> ApprovalPolicy.decide
path/network -> SandboxPolicy.decide_*
```

## Section 2 [BUILD]：diagnostics + JSONL

```bash
uv run python
```

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from langchain_course.agent_kernel import AgentStep
from langchain_course.production import JsonlStepStore, RunDiagnostics

steps = [
    AgentStep(kind="model_request", payload={"step": "plan"}),
    AgentStep(kind="tool_call", payload={"tool": "keyword_search"}),
    AgentStep(kind="error", payload={"error_kind": "tool_error", "message": "missing"}),
    AgentStep(kind="final", payload={"text": "partial"}),
]
diag = RunDiagnostics.from_steps("run_7", steps)
print(diag.to_record())
assert diag.event_count == 4
assert diag.error_summaries[0]["message"] == "missing"

with TemporaryDirectory() as tmp:
    store = JsonlStepStore(Path(tmp) / "steps.jsonl")
    store.append_steps("run_7", steps)
    assert store.list_run_ids() == ("run_7",)
    assert len(store.read_run("run_7")) == 4
```

## Section 3 [BUILD]：approval + sandbox

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
    root = Path(tmp)
    ws = root / "ws"
    ws.mkdir()
    sandbox = SandboxPolicy(
        readable_paths=(ws,),
        writable_paths=(ws,),
        allow_network=False,
    )
    assert sandbox.decide_path(ws / "a.json", access="read").allowed
    assert sandbox.network_decision().allowed is False
```

> [TRAP] **Approval 管 tool subject；Sandbox 管 path/network/runtime**。不要合成一个万能 if。

## Section 4：Reflection

1. 为什么默认 `REQUIRE_APPROVAL` 比默认 `ALLOW` 更安全？  
2. 若 runner 从不调用 policy，合同再漂亮有什么用？  

下一步：**LC Capstone** 把 Parts 1–7 合成一个离线助手。
