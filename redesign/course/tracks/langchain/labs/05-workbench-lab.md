# Lab 05 — Workbench（LangChain 轨）

接 Chapter 05。练习 snapshot 组装与 referential integrity。

完成后你应提交一份能解释“错误必须在哪一层失败”的 snapshot 记录，而不是
只有一段能打印 JSON 的代码。

## Setup

```bash
cd redesign
uv sync --group langchain-course
PYTHONPATH=packages/langchain_course/src uv run python
```

## Exercise 1 (L1 Follow): Demo keys

```python
from langchain_course.workbench import build_demo_snapshot

rec = build_demo_snapshot().to_record()
assert set(rec.keys()) == {
    "project", "run", "timeline", "delegation", "sources",
    "report", "memory", "skills", "evals",
}
```

**即时反馈**：若 key 少了，先检查 `WorkbenchSnapshot.to_record()`；若 key
齐全但内容为空，不代表失败——不同 run 可以没有 delegation 或 memory。

## Exercise 2 (L1 Follow): from_step

构造两个 `AgentStep`，转成 timeline，断言 `type` 与 `run_id`。

**检查点**：交换两个 step 的顺序后，timeline id/index 应随顺序变化，run_id
不应变化。

## Exercise 3 (L2 Modify): Integrity failures

1. 故意把 `WorkbenchRun.project_id` 写成错误 id，确认 raise。  
2. report link 指向不存在的 `source_id`，确认 raise。

**失败解释**：如果没有 raise，不要在测试里忽略坏 link；回到 snapshot 的
referential-integrity 校验。正确修复是传入缺失 source 或删除无效 link。

## Exercise 4 (L3 Design): Mini panel

用 Part 2 的 `default_paper_docs` + 一条 evidence + 一条 memory note，组一个带 sources/report/memory 的 snapshot（可无 delegation）。

要求同时写三句设计说明：

1. 哪些对象属于 LC 执行面；
2. 哪个 adapter 把它变成 panel；
3. UI 最多可以怎样变形、绝不能补造什么。

## Retrieval practice

合上 Chapter 05 后回答：为什么 `to_record()` 成功不等于引用关系正确？再用
一条测试证明你的回答。

## 对照答案

完成后再看 [Solution 05](../solutions/05-workbench-solution.md)，先比 invariant，
再比代码长相。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_workbench.py -q
```
