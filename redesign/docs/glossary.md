# Glossary

## AgentMessage

The internal message representation used by the redesign runtime.
It is intentionally separate from provider-specific chat message payloads so
tests, fakes, adapters, and trajectory replay can share one stable contract.

## RunEvent

An append-only record of runtime activity.
It is the unit that event streams, timelines, replay, and evals build on.

## FakeModel

A deterministic offline model used for tests and labs.

## Research Agent Workbench

The final product interface for projects, research runs, delegation, evidence, reports, memory, skills, and evals.

## Skill

A folder-based capability package with a `SKILL.md` entrypoint and optional scripts, references, and assets.

## Harness

The engineering layer around an Agent: repository instructions, resource loading, run logs, replay, compaction, evals, and feedback loops.
The harness is not the model or the business domain; it is the runtime wrapper
that makes agent behavior inspectable and repeatable.

## Multi-Agent Delegation

An orchestrator assigning scoped tasks to child agents with isolated context, budget, tool scope, skill scope, and merge contracts.
Delegation is only considered real when child work has boundaries, accounting,
and a merge path; role-prompt theater is not enough.
