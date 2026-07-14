# LC Capstone Rubric

Use this rubric for the **LangChain track** Capstone. Every criterion is offline-checkable.

## Scoring

| Level | Meaning |
| --- | --- |
| Pass | Criterion fully met with evidence (tests, files, or inspectable records) |
| Partial | Intent is visible, but a required invariant is missing |
| Fail | Criterion not attempted or contradicts Capstone constraints |

**Overall Pass** requires **Pass on all six success criteria**.

## Success Criteria

### 1. Evidence from at least 3 sources

| Check | Pass evidence |
| --- | --- |
| Fixture load | Capstone loads offline papers from `paper_fixtures/` |
| Source count | At least 3 distinct `PaperDoc` objects with stable IDs |
| Evidence count | At least 3 `EvidenceItem`s, each referencing a real `source_id` |
| Offline unit path | No network required for solution tests |

### 2. Every claim traces to evidence

| Check | Pass evidence |
| --- | --- |
| Claims | Report contains one or more `ClaimItem`s |
| Evidence IDs | Every claim has non-empty `evidence_ids` |
| Link integrity | `build_claim_links(...)` succeeds |
| Traceability | Each link exposes claim → quote → source URI |

### 3. At least 1 skill and 1 memory policy

| Check | Pass evidence |
| --- | --- |
| Skill | `SkillLoader` loads Capstone `citation-check` package |
| Memory write policy | Explicit `MemoryWritePolicy` is used |
| Memory write | At least one `MemoryNote` written under that policy |

### 4. Workbench timeline is inspectable

| Check | Pass evidence |
| --- | --- |
| Snapshot | A `WorkbenchSnapshot` is built |
| Timeline | Non-empty timeline using Capstone run id |
| Record shape | `to_record()` exposes project/run/timeline/sources/report |
| Integrity | Construction does not raise referential errors |

### 5. Offline tests pass

| Check | Pass evidence |
| --- | --- |
| Solution tests | `uv run pytest course/tracks/langchain/capstone/solution -q` |
| Learner starter | starter tests skip until TODOs filled, then pass |
| Project gate (recommended) | `uv run pytest -q` and `uv run ruff check .` |

### 5A. LangChain execution is real

| Check | Pass evidence |
| --- | --- |
| Model boundary | Offline model subclasses `BaseChatModel` |
| Tool path | run contains model response → tool call → decision → tool result |
| Retriever path | local tool invokes `LangChainPaperRetriever(BaseRetriever)` |
| No synthetic pass | main trail is not hand-built merely to satisfy the rubric |
| Live boundary | optional DeepSeek smoke asserts tool structure, not exact prose |

### 6. Reflection explains 3 design decisions

| Check | Pass evidence |
| --- | --- |
| File | `solution/reflection.md` (or your own) |
| Depth | At least 3 decisions with chosen / rejected / because |
| Scope | Decisions about the integrated LC assistant |

## Recommended Bonus Checks

- Delegation: one child review with parent `delegate_*` steps.
- Production: `RunDiagnostics` + `JsonlStepStore` + approval/sandbox decisions.
- Comparison note: one paragraph on when handwritten vs LC vs LG wins after this Capstone.
