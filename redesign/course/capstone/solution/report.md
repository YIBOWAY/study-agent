# Capstone Sample Report

**Run ID:** `run_capstone`  
**Question:** Does citation grounding matter for trustworthy RAG evaluation, and what should a local research assistant remember or delegate?

## Summary

Trustworthy local research assistants need citation grounding, memory write policy, and budgeted delegation. This Capstone report is generated offline from static paper fixtures; every claim below keeps evidence IDs that resolve to quotes and source URIs.

## Claims

### Claim 1 — Citation grounding

**Text:** RAG evaluation should preserve citation grounding so readers can audit generated claims.

**Evidence:**

- `evidence_rag_grounding` from `paper://rag-evaluation-survey`  
  Quote: "RAG evaluation should report retrieval quality and citation grounding."
- `evidence_citation_map` from `paper://citation-mapping`  
  Quote: "Citation mapping connects every report claim to a quote, source URI, and paper title."

### Claim 2 — Memory write policy

**Text:** Local research assistants should use write policies so memory does not pollute later sessions.

**Evidence:**

- `evidence_memory_policy` from `paper://agent-memory-notes`  
  Quote: "Memory records can pollute an agent when write policy is missing."

### Claim 3 — Delegation budgets

**Text:** Delegated review needs isolated child context and explicit budgets.

**Evidence:**

- `evidence_delegation_budget` from `paper://delegation-budgets`  
  Quote: "Child agents need isolated context and explicit budgets."

## Assistant Final Answer (scripted FakeModel)

Citation grounding matters: evaluation reports should keep evidence links so claims stay auditable.

## Trust Evidence Bundled With This Report

| Artifact | Why it matters |
| --- | --- |
| Event trail / `trajectory.jsonl` | Replay what the run did |
| Workbench snapshot timeline | Product-facing inspectable history |
| Memory records | Session continuity under write policy |
| Skill package `citation-check` | Progressive disclosure checklist |
| Delegation parent events | Child review isolation and budgets |
| Approval + sandbox decisions | Dangerous tools and network blocked |

## How To Reproduce Offline

```bash
PYTHONPATH=packages/research_core/src uv run python course/capstone/solution/agent.py
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py -q
```
