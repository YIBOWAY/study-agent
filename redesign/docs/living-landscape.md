# Living Landscape

This document records dated changes in agent frameworks, protocols, and external
tooling. Keep stable design principles in architecture docs; keep fast-changing
market or framework notes here.

## 2026-06-26

- Current stable redesign direction remains handwritten `research_core` first,
  with frameworks used for controlled comparisons.
- Candidate comparison targets remain PydanticAI, LlamaIndex Workflows,
  LangGraph, OpenAI Agents SDK, CrewAI, MCP, and A2A protocol integrations.

## 2026-06-27

- Phase 6 baseline compares frameworks through deterministic profiles and shared
  tasks under `course/framework_comparisons/`; no third-party framework is
  imported into `research_core` or product apps.
- Current profile recommendations: handwritten `AgentRunner` wins the
  `echo_tool_trace` task, while LangGraph wins the state/resume-heavy workflow.
  These are task-weighted course recommendations, not permanent adoption
  decisions.
