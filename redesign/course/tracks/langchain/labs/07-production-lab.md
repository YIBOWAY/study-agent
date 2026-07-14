# Lab 07 — Production Readiness（LangChain 轨）

## Exercise 1 (L1): Diagnostics

用含 `error` 的 steps 生成 `RunDiagnostics`，断言 `error_summaries` 非空。

## Exercise 2 (L1): JSONL roundtrip

`append_steps` 两个 run_id，`list_run_ids` 与 `read_run` 正确。

## Exercise 3 (L2): Policy matrix

配置 allow/deny/require_approval 三条规则；sandbox 拒绝网络与越界写路径。

## Exercise 4 (L3 Design): Trust pack

把 Part 1 某次 scripted run 的 steps 打包成：diagnostics record + jsonl 文件 + 2 条 approval + 1 条 network decision。写成 dict 打印 keys。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_production.py -q
```
