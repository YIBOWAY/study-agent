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
