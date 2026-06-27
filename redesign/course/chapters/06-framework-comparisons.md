# Chapter 06: Framework Comparisons

## Goal

这一章补上 Phase 6 的判断力训练：你已经手写过 AgentRunner、research
contracts、memory、skills、delegation 和 Workbench，现在开始问一个更接近真实工程的问题：

```text
什么时候继续用手写 runtime，什么时候学习或引入框架？
```

学完以后，你应该能用同一个任务、同一套 fake fixtures、同一套指标来比较框架，而不是被框架 README 或营销词牵着走。

预计时间：60 到 75 分钟。

## Before You Start

请先完成：

- `01-agent-kernel-foundations.md`
- `04-multi-agent-delegation.md`
- `05-workbench-product.md`

这一章不会安装 PydanticAI、LangGraph、OpenAI Agents SDK 或 CrewAI。Phase 6 先建立比较方法：框架候选用 deterministic profile 表示，手写 baseline 用真实 `AgentRunner` 执行。

## The Idea In Plain Language

框架比较最容易犯的错误是“每个框架跑一个它最擅长的 demo”。

那不叫比较，只叫看宣传册。

真正有用的比较必须固定三件事：

1. 同一个 task。
2. 同一套 fake model/tool fixtures。
3. 同一套评价指标。

在 Phase 6 里，第一个 task 是 `echo_tool_trace`。它很小，只做一件事：

```text
model asks for echo tool -> tool returns result -> model gives final answer
```

这足够暴露一个框架最基础的工程问题：你能不能看见 event trail，能不能离线测试，能不能稳定 debug。

## Why Frameworks Come After Handwritten Mechanisms

如果你还没亲手写过 loop，就会把框架封装当成魔法。

前几章先手写这些机制：

| Mechanism | Earlier Chapter |
| --- | --- |
| message/event/tool loop | Chapter 01 |
| source/evidence/claim/report | Chapter 02 |
| memory and skill loading | Chapter 03 |
| delegation and child context isolation | Chapter 04 |
| product snapshot/API/UI boundary | Chapter 05 |

现在再看框架，你会问的不是“它火不火”，而是：

- 它能不能保留 event stream？
- 它能不能离线跑 fake model？
- 它是不是把 product runtime 绑死在某个 SDK 上？
- 它的 checkpoint/resume 是否真的比手写划算？
- 它的 multi-agent 是真实隔离和 merge，还是 role prompt 表演？

## The Phase 6 Comparison Harness

代码在：

```text
course/framework_comparisons/
```

核心对象：

| Object | Job |
| --- | --- |
| `ComparisonTask` | 固定同一个任务、prompt、fake responses、expected event sequence 和权重 |
| `TaskRunSummary` | 手写 runner 跑完任务后的结果摘要 |
| `FrameworkProfile` | 一个候选框架在各评价维度上的 deterministic profile |
| `FrameworkRecommendation` | 某个 task 下某个 profile 的得分、优势和 tradeoffs |

注意：`FrameworkProfile` 不是第三方框架 wrapper。它是课程里的比较记录。这样可以先训练判断力，不把产品 runtime 拉进依赖泥潭。

## Minimal Example

从 `redesign/` 运行：

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

粘贴：

```python
from course.framework_comparisons import build_echo_tool_task, run_handwritten_task

task = build_echo_tool_task()
summary = run_handwritten_task(task)

print(summary.to_record())
```

你应该看到：

```text
event_sequence: model_request, model_response, tool_call, tool_result, model_request, model_response
tool_call_count: 1
error_count: 0
```

这证明 handwritten baseline 不是文档想象出来的，它真的跑了 `AgentRunner`、`FakeModel` 和 `ToolRuntime`。

## Recommendation Matrix

再运行：

```python
from course.framework_comparisons import (
    build_echo_tool_task,
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
)

tasks = [build_echo_tool_task(), build_state_resume_task()]
matrix = build_recommendation_matrix(
    tasks=tasks,
    profiles=default_framework_profiles(),
)

for task in tasks:
    print(task.id, recommend_profile(matrix, task_id=task.id).to_record())
```

当前结果：

```text
echo_tool_trace -> handwritten, score 0.854
state_resume_workflow -> langgraph, score 0.78
```

这不是矛盾，而是重点：不同任务权重会改变推荐。

小任务重视 inspectability 和 offline testing，所以 handwritten 赢。
state/resume-heavy 任务重视 checkpoint 和 human-in-the-loop，所以 LangGraph 值得学习。

## Failure Lab Preview

改坏一个 task 的权重：

```python
from course.framework_comparisons import ComparisonTask, build_echo_tool_task

task = build_echo_tool_task()
ComparisonTask(
    id="bad",
    title="Bad task",
    system_prompt=task.system_prompt,
    user_message=task.user_message,
    model_responses=task.model_responses,
    tool_name=task.tool_name,
    tool_description=task.tool_description,
    tool_argument_name=task.tool_argument_name,
    required_capabilities=task.required_capabilities,
    expected_event_sequence=task.expected_event_sequence,
    weights={"marketing_claims": 1.0},
)
```

你应该看到：

```text
ValueError: unknown weight criteria: marketing_claims
```

这很重要：比较框架时，如果指标不受控，结论就会漂。

## Product Boundary

Phase 6 的所有比较代码都在 `course/framework_comparisons/`。

不允许：

```text
research_core -> LangGraph
research_core -> PydanticAI
apps/api -> CrewAI shortcut
apps/web -> framework-specific runtime object
```

允许：

```text
course/framework_comparisons -> research_core runtime contracts
course reports -> framework recommendation matrix
future optional adapters -> separate approved phase plan
```

## Eval Gate

运行：

```bash
uv run pytest tests/course/test_framework_comparisons.py -q
uv run ruff check course/framework_comparisons tests/course/test_framework_comparisons.py
```

核心自查：

```python
task = build_echo_tool_task()
summary = run_handwritten_task(task)
assert summary.event_sequence == task.expected_event_sequence

matrix = build_recommendation_matrix(
    tasks=[build_echo_tool_task(), build_state_resume_task()],
    profiles=default_framework_profiles(),
)
assert recommend_profile(matrix, task_id="echo_tool_trace").profile_id == "handwritten"
assert recommend_profile(matrix, task_id="state_resume_workflow").profile_id == "langgraph"
```

## Checkpoint

继续 Phase 7 前，用自己的话回答：

1. 为什么不能让每个框架各跑一个不同 demo？
2. 为什么 `echo_tool_trace` 这么小也有比较价值？
3. 为什么 `handwritten` 和 `langgraph` 会分别赢不同任务？
4. `FrameworkProfile` 为什么不是第三方框架 adapter？
5. 如果你要真的引入某个框架，应该先写什么测试和文档？
