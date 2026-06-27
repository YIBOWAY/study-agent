# Echo Tool Comparison Task

Date: 2026-06-27

## Purpose

`echo_tool_trace` is the first shared framework-comparison task. It is small on
purpose: the learner should see whether a runtime exposes the tool loop clearly
before comparing bigger frameworks.

## Fixture

The task uses:

- system prompt: `You are careful and expose the event trail.`
- user message: `Echo hello through the tool, then explain the observation.`
- tool: `echo`
- fake model response 1: JSON `tool_call`
- fake model response 2: final answer

Expected event sequence:

```text
model_request
model_response
tool_call
tool_result
model_request
model_response
```

## Handwritten Baseline

Run from `redesign/`:

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

Then:

```python
from course.framework_comparisons import build_echo_tool_task, run_handwritten_task

task = build_echo_tool_task()
summary = run_handwritten_task(task)

print(summary.to_record())
```

Expected record:

```python
{
    "task_id": "echo_tool_trace",
    "final_answer": "The echo tool returned hello.",
    "event_sequence": [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ],
    "tool_call_count": 1,
    "error_count": 0,
}
```

## What This Task Teaches

- A framework comparison must use the same task, not a different demo per framework.
- A tiny task can still reveal observability and testing differences.
- If a framework hides the event sequence, debugging a bigger research workflow gets harder.
- If a framework requires live credentials for this task, it is a poor fit for the offline course baseline.

## Not A Product Runtime

The task stays under `course/framework_comparisons/`. It does not replace
`research_core.runtime.AgentRunner`, and it does not add third-party framework
dependencies to the product.
