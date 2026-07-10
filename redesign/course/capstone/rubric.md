# Capstone Rubric: 本地论文研究助手

Use this rubric to grade your own Capstone or a peer's. Every criterion is offline-checkable.

## Scoring

| Level | Meaning |
| --- | --- |
| Pass | Criterion fully met with evidence (tests, files, or inspectable records) |
| Partial | Intent is visible, but a required invariant is missing |
| Fail | Criterion not attempted or contradicts Capstone constraints |

**Overall Capstone Pass** requires **Pass on all six success criteria**. Partial on any criterion means revise before claiming done.

## Success Criteria

### 1. Evidence from at least 3 sources

| Check | Pass evidence |
| --- | --- |
| Fixture load | Capstone loads offline papers from `paper_fixtures/` (or equivalent local fixtures) |
| Source count | At least 3 distinct `Source` objects with stable IDs |
| Evidence count | At least 3 `Evidence` items, each referencing a real `source_id` |
| Offline | No network, embeddings, or provider API calls |

### 2. Every claim traces to evidence

| Check | Pass evidence |
| --- | --- |
| Claims | Report contains one or more `Claim` objects |
| Evidence IDs | Every claim has non-empty `evidence_ids` |
| Link integrity | `build_claim_source_links(...)` succeeds |
| Traceability | Each link record exposes claim → evidence quote → source URI |

### 3. At least 1 skill and 1 memory policy

| Check | Pass evidence |
| --- | --- |
| Skill | `SkillRuntime` loads a Capstone skill package (e.g. citation-check) |
| Memory write policy | A non-default or explicit `MemoryWritePolicy` is used |
| Memory write | At least one `MemoryRecord` is written under that policy |
| Honesty | Do not claim MEMORY_*/SKILL_* `RunEvent`s fire unless your adapter emits them |

### 4. Workbench timeline is inspectable

| Check | Pass evidence |
| --- | --- |
| Snapshot | A `WorkbenchSnapshot` is built from Capstone objects |
| Timeline | Snapshot timeline is non-empty and uses the Capstone run id |
| Record shape | `to_record()` exposes project/run/timeline/sources/report panels |
| Integrity | Snapshot construction does not raise referential-integrity errors |

### 5. Offline tests pass

| Check | Pass evidence |
| --- | --- |
| Capstone tests | `PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py -q` passes for the reference solution |
| Learner tests | Your filled starter or custom tests pass offline |
| Project gate (recommended) | `uv run pytest -q` and `uv run ruff check .` still pass |

### 6. Reflection explains 3 design decisions

| Check | Pass evidence |
| --- | --- |
| File | You write a reflection (see `solution/reflection.md` as a model) |
| Depth | At least 3 decisions, each with chosen option / rejected option / reason |
| Capstone scope | Decisions relate to this integrated assistant, not only one Part in isolation |

## Recommended Bonus Checks (not required for Pass)

- Delegation: one child review task with budget and parent `delegate_*` events.
- Production: `RunDiagnostics` + `JsonlRunEventStore` replay for the Capstone run.
- Policy: approval allow for retrieval, deny/require_approval for dangerous subjects; sandbox network disabled.
- Framework comparison note: one paragraph on why the Capstone stays on handwritten `research_core` contracts.

## Common Fail Modes

1. **Pretty report, broken chain** — summary reads well, but claims lack evidence IDs.
2. **Search results treated as evidence** — `SearchResult` is ranking, not a quote-backed `Evidence`.
3. **Claiming auto memory/skill events** — writing memory or loading a skill does not automatically append MEMORY_*/SKILL_* events unless you wire them.
4. **Network or live model** — Capstone must stay offline with fixtures + FakeModel/FakeRetriever.
5. **Workbench-only demo** — using `build_demo_workbench_snapshot()` without building your Capstone research objects does not satisfy criteria 1-3.

## Self-Check Commands

From `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py -q
PYTHONPATH=packages/research_core/src uv run python course/capstone/solution/agent.py
```

If you filled the starter:

```bash
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/starter/test_starter.py -q
```
