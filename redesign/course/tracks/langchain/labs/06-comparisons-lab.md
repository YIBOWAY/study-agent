# Lab 06 — Framework Comparisons（LangChain 轨）

目标：把“我喜欢某框架”改写成可复算、可反驳的选择记录。

## Exercise 1 (L1): 默认矩阵

跑 `build_inspectability_task` 与 `build_state_resume_task`，断言赢家分别是 `handwritten` 与 `langgraph`。

**即时反馈**：如果两个 task 得到同一赢家，先打印 weights 和逐项 score；不要
直接改 expected winner。

## Exercise 2 (L1): LC baseline 结构

`run_lc_baseline` 返回的 `step_sequence` 必须同时含 `user_message`、
`model_response`、`tool_call`、`tool_result`，`error_count == 0`。

**故障练习**：临时把 baseline 改成手工 `AgentStep` 列表。测试为什么仍可能
绿？再增加一条证据，证明实际经过了 Part 1 loop。

## Exercise 3 (L2): 手算 total_score

自建 `ComparisonTask(weights={"inspectability": 1, "team_cost": 1})` 与一个 profile（1.0 / 0.0），断言 `total_score == 0.5`，并检查 strengths/tradeoffs。

**常见错误**：忘记除以总权重；把 `<0.55` 写成 `<=0.55`；用显示后的四舍
五入值参与下一轮计算。

## Exercise 4 (L3): 为 Capstone 写一段选型笔记

用矩阵结果写 5–8 句：Capstone 为何仍可离线；何时你会把产品默认 runtime 从 handwritten 迁到 LC/LG（需要单独 phase 计划）。

必须包含 `chosen / rejected / because / evidence / revisit when` 五项。没有
“什么时候重新评估”的结论，不是一条可维护的选型记录。

## Retrieval practice

不看代码写出 total score 公式，并解释 deterministic baseline 与 synthetic
trail 的区别。

## 对照答案

[Solution 06](../solutions/06-comparisons-solution.md)

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_comparisons.py -q
```
