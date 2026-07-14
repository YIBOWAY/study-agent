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

真正的控制点是 `build_approval_hook(approval)` 传入
`run_tool_calling_agent(before_tool=...)`。仅调用 `approval.decide()` 再打印结果，
没有阻止任何副作用。

Sandbox：`allow_network=False` 时 `network_decision().allowed is False`；path 必须落在 readable/writable 根下且不在 blocked 根下。

## L3 Trust pack keys（示例）

`callbacks`, `steps`, `diagnostics`, `jsonl_path`, `approvals`, `sandbox`。

## 为什么这样分层

- callback：框架生命周期证据；
- `AgentStep`：课程稳定语义；
- approval hook：工具执行前控制；
- sandbox：path/network/runtime 决策；
- JSONL：重放材料。

## 失败输出解释

- `side_effects != []`：gate 放晚了，回到 runner 的 tool invoke 顺序。
- callback 没有 `chat_model_start`：你可能绕过了 `BaseChatModel.invoke`。
- JSONL schema error：不要吞掉；定位行号并决定迁移或拒绝。
- unknown tool 默认执行：错误；没有匹配 rule 时应保持 review/deny 边界。

## 与 handwritten 的关系

两轨共享“control before effect”的安全原则；LC 轨额外展示 callback manager
和 `BaseTool.invoke` 的真实接点。框架 callback 不替代产品 policy。
