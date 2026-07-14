# Lab 05 — Workbench（LangChain 轨）

接 Chapter 05。练习 snapshot 组装与 referential integrity。

## Setup

```bash
cd redesign
uv sync --group langchain-course
uv run python
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

## Exercise 2 (L1 Follow): from_step

构造两个 `AgentStep`，转成 timeline，断言 `type` 与 `run_id`。

## Exercise 3 (L2 Modify): Integrity failures

1. 故意把 `WorkbenchRun.project_id` 写成错误 id，确认 raise。  
2. report link 指向不存在的 `source_id`，确认 raise。

## Exercise 4 (L3 Design): Mini panel

用 Part 2 的 `default_paper_docs` + 一条 evidence + 一条 memory note，组一个带 sources/report/memory 的 snapshot（可无 delegation）。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_workbench.py -q
```
