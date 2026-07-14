# Lab 06 — Framework Comparisons（LangChain 轨）

## Exercise 1 (L1): 默认矩阵

跑 `build_inspectability_task` 与 `build_state_resume_task`，断言赢家分别是 `handwritten` 与 `langgraph`。

## Exercise 2 (L1): LC baseline 结构

`run_lc_baseline` 返回的 `step_sequence` 含 `model_request` 与 `tool_call`，`error_count == 0`。

## Exercise 3 (L2): 手算 total_score

自建 `ComparisonTask(weights={"inspectability": 1, "team_cost": 1})` 与一个 profile（1.0 / 0.0），断言 `total_score == 0.5`，并检查 strengths/tradeoffs。

## Exercise 4 (L3): 为 Capstone 写一段选型笔记

用矩阵结果写 5–8 句：Capstone 为何仍可离线；何时你会把产品默认 runtime 从 handwritten 迁到 LC/LG（需要单独 phase 计划）。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_comparisons.py -q
```
