# Solution 07 — Production（LangChain 轨）

## Diagnostics

`from_steps` 要求非空 steps、统一由调用方提供 `run_id`；`error` kind 进入 `error_summaries`。

## JSONL

schema：`lc.agent_step_log.v1`，每行 `{schema_version, step:{run_id,index,kind,payload}}`。

## Policy

```python
from langchain_course.production import ApprovalMode, ApprovalPolicy, ApprovalRule, SandboxPolicy

approval = ApprovalPolicy(
    rules=(
        ApprovalRule("keyword_*", ApprovalMode.ALLOW, "ok"),
        ApprovalRule("shell_*", ApprovalMode.DENY, "no"),
    )
)
assert approval.decide("keyword_search").mode is ApprovalMode.ALLOW
```

Sandbox：`allow_network=False` 时 `network_decision().allowed is False`；path 必须落在 readable/writable 根下且不在 blocked 根下。

## L3 Trust pack keys（示例）

`diagnostics`, `jsonl_path`, `approvals`, `sandbox`。
