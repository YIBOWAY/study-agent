# Framework Recommendation Matrix

Date: 2026-06-27

## Boundary

Phase 6 compares framework fit without importing third-party frameworks.
The code under `course/framework_comparisons/` is a deterministic scoring and
teaching harness. It keeps `research_core` handwritten and framework-independent.

## Criteria

Scores are normalized from 0 to 1:

| Criterion | Meaning |
| --- | --- |
| `inspectability` | How easily a learner or maintainer can see the loop, events, and failure path. |
| `offline_testing` | How naturally the approach works with fake models and no API key. |
| `typed_contracts` | How strongly the approach encourages explicit schemas and typed boundaries. |
| `state_resume` | How well it fits checkpoint, resume, and human-in-the-loop workflows. |
| `multi_agent` | How well it supports scoped delegation without role-prompt theater. |
| `product_boundary` | How safely it stays out of `research_core` and product runtime internals. |
| `team_cost` | How low the learning and maintenance cost is for this course/product. |

## Task Results

### `echo_tool_trace`

This task rewards simple tool calling, event inspection, and offline tests.

| Profile | Score | Strengths | Tradeoffs |
| --- | ---: | --- | --- |
| Handwritten AgentRunner | 0.854 | inspectability, offline_testing, product_boundary | state_resume, multi_agent |
| PydanticAI | 0.745 | typed_contracts | state_resume, multi_agent |
| LangGraph | 0.6345 | state_resume, multi_agent | team_cost |
| LlamaIndex Workflows | 0.613 |  | multi_agent |
| OpenAI Agents SDK | 0.6095 | typed_contracts | offline_testing |
| CrewAI | 0.4795 | multi_agent | inspectability, offline_testing, typed_contracts, state_resume, product_boundary, team_cost |

Recommendation: `handwritten`.

Reason: the task is intentionally small. The primary learning value is seeing
`model_request`, `model_response`, `tool_call`, and `tool_result` directly.

### `state_resume_workflow`

This task weights checkpoint, resume, and human-review ergonomics above raw
local inspectability.

| Profile | Score | Strengths | Tradeoffs |
| --- | ---: | --- | --- |
| LangGraph | 0.78 | state_resume, multi_agent | team_cost |
| OpenAI Agents SDK | 0.665 | typed_contracts | offline_testing |
| LlamaIndex Workflows | 0.585 |  | multi_agent |
| PydanticAI | 0.58 | typed_contracts | state_resume, multi_agent |
| CrewAI | 0.5425 | multi_agent | inspectability, offline_testing, typed_contracts, state_resume, product_boundary, team_cost |
| Handwritten AgentRunner | 0.51 | inspectability, offline_testing, product_boundary | state_resume, multi_agent |

Recommendation: `langgraph`.

Reason: when the task truly needs checkpoint/resume and human-in-the-loop graph
state, LangGraph's state model becomes worth studying despite higher team cost.

## How To Regenerate

Run from `redesign/`:

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

Then:

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

The matrix is a teaching aid, not a procurement verdict. Update
`docs/living-landscape.md` when external framework behavior changes materially.
