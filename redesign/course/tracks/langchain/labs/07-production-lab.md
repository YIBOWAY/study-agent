# Lab 07 — Production Readiness（LangChain 轨）

目标：证明“看得见、拦得住、留得下”是三件不同的事。

## Exercise 1 (L1): Diagnostics

用含 `error` 的 steps 生成 `RunDiagnostics`，断言 `error_summaries` 非空。

**即时反馈**：如果 error count 为零，检查的是 `step.kind == "error"`，不是
payload 中有没有字符串 `error`。

## Exercise 2 (L1): JSONL roundtrip

`append_steps` 两个 run_id，`list_run_ids` 与 `read_run` 正确。

再破坏一行 schema version，确认读取失败并报告行号；不要静默跳过坏日志。

## Exercise 3 (L2): Policy matrix

先用 `LangChainTraceRecorder` 跑一次真实 `BaseChatModel.invoke`，证明 callback
含 `chat_model_start/llm_end`。再配置 allow/deny/require_approval 三条规则；
sandbox 拒绝网络与越界写路径。

**检查点**：callback 只负责观察；它本身没有证明 DENY 发生在工具执行前。

## Exercise 4 (L3 Design): Trust pack

创建一个会向列表 append 的危险工具，让模型请求它，再用 `build_approval_hook`
阻止执行。最终 trust pack 包含：callback records、AgentStep、diagnostics、
JSONL、tool decision、network decision。断言副作用列表为空。

## Retrieval practice

遮住代码后画出：model request → approval decision → tool invoke → callback →
AgentStep/JSONL。若顺序画错，解释会产生什么真实后果。

## 对照答案

[Solution 07](../solutions/07-production-solution.md)

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_production.py -q
```
