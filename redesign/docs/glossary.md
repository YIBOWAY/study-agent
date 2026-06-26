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

## ToolRuntime

The local tool registry and invocation boundary.
It stores `ToolDefinition` objects, accepts `ToolCall` requests, returns
`ToolResult` objects, and raises `UnknownToolError` for missing registrations.

## ContextBuilder

The runtime component that owns the model context boundary.
It inserts the single reserved system prompt and rejects caller-provided system
messages so instruction ownership remains explicit.

## AgentRunner

The minimal Phase 1 agent loop.
It builds context, calls the model, emits runtime events, executes JSON tool
calls through `ToolRuntime`, appends tool observations, and returns the final
assistant message.

## Trajectory Regression

A test strategy that compares stable event records and event type sequences
instead of relying only on final answers.
It catches behavioral drift in the agent loop, including tool calls and error
paths.

## Project

A research workspace boundary containing related runs, sources, evidence,
reports, and later memory.

## ResearchRun

One research task inside a `Project`, with a question and lifecycle status.

## Source

An ingested local or external material item that can support evidence.

## Evidence

A quoted support item extracted from a `Source`.

## Claim

A verifiable report statement that references supporting evidence IDs.

## Report

A research output made of a title, summary, and ordered claims.

## SourceIngestor

A deterministic local ingestor that converts `SourceInput` records into
`Source` objects with stable IDs.

## FakeRetriever

An offline token/phrase search fixture over ingested sources.
It supports repeatable research tests without API keys or network access.

## ClaimSourceLink

A stable record that connects one report claim to one evidence item and the
source behind that evidence.

## MemoryRecord

An immutable memory entry with kind, content, tags, importance, and
JSON-compatible metadata.

## MemoryWritePolicy

The policy that decides whether a proposed memory record is safe and useful
enough to store.

## MemoryRecallPolicy

The policy that controls deterministic memory recall by query, kind filter,
limit, and pinned-first ordering.

## MemoryEngine

The Phase 3 in-process memory store.
It accepts records through `MemoryWritePolicy` and recalls them with
`MemoryRecallPolicy`.

## SkillPackage

The loaded representation of a folder-based skill, including its `SKILL.md`
entrypoint and discovered resource paths.

## SkillRuntime

The Phase 3 loader for folder-based skills.
It loads `SKILL.md` first and reads references only when explicitly requested.

## AgentRolePolicy

The Phase 4 child-agent role boundary.
It owns the child system prompt, scoped tool names, scoped skill names, scoped
memory kinds, and max-step limit.

## DelegationTask

A parent-to-child assignment with parent and child run IDs, an objective, a role
policy, and explicit non-system context messages.

## DelegationBudget

The local Phase 4 accounting policy for maximum child runs, maximum steps per
child, and maximum total child steps.

## DelegationRuntime

The deterministic Phase 4 orchestration layer.
It runs child tasks through a child runner, emits parent `delegate_*` events,
preserves child events, and returns `DelegationResult` records.

## DelegationResult

The result of one delegated child task.
It records status, final child message, child events, parent delegation events,
error message, and derived step count.

## DelegationMergeResult

The merge record for child results.
It preserves child task order and keeps failed, cancelled, planned, or running
children in unresolved conflicts until parent review.

## A2AEnvelope

The Phase 4 versioned task-delegation export record for future remote-agent
protocols. It is local and deterministic, not a full A2A wire implementation.

## A2AAdapterStub

The Phase 4 local adapter stub that exports `DelegationTask` values to
`A2AEnvelope` records and rejects send attempts because remote transport is not
implemented yet.

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
