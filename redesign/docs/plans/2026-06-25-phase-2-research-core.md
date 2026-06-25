# Research Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first research-domain layer to `packages/research_core`: durable research entities, deterministic source ingestion, fake retrieval, claim-source mapping helpers, docs, and offline tests.

**Architecture:** Phase 2 introduces a `research_core.research` package that remains independent from FastAPI, React, databases, provider SDKs, embeddings, and legacy root code. The research layer may depend on runtime immutability helpers but runtime modules must not depend on research modules. All fixtures stay offline and deterministic so later product APIs, evals, memory, and delegation can reuse the same contracts.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, dataclasses, enums, JSON-compatible metadata, deterministic fake retrieval.

---

## File Structure

Create or update these files:

- Create: `redesign/packages/research_core/src/research_core/research/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/research/entities.py`
- Create: `redesign/packages/research_core/src/research_core/research/ingestion.py`
- Create: `redesign/packages/research_core/src/research_core/research/retrieval.py`
- Create: `redesign/packages/research_core/src/research_core/research/mapping.py`
- Create: `redesign/tests/research_core/test_research_entities.py`
- Create: `redesign/tests/research_core/test_research_retrieval.py`
- Create: `redesign/tests/research_core/test_claim_source_mapping.py`
- Create: `redesign/docs/architecture/data-model.md`
- Modify: `redesign/docs/architecture/overview.md`
- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-2.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

Do not modify legacy `app/`, `frontend/`, root `tests/`, root `eval/`, root project configuration, or provider-specific code.

## Contracts

### Research Entities

- `Project`: research workspace boundary with `id`, `name`, optional `description`, and JSON-compatible `metadata`.
- `ResearchRun`: one research task with `id`, `project_id`, `question`, `status`, and JSON-compatible `metadata`.
- `ResearchRunStatus`: `planned`, `running`, `completed`, and `failed`.
- `Source`: ingested material with `id`, `uri`, `title`, `content`, and JSON-compatible `metadata`.
- `Evidence`: quoted or summarized support extracted from a `Source`, with `id`, `source_id`, `quote`, optional `summary`, optional `location`, and JSON-compatible `metadata`.
- `Claim`: a verifiable report claim with `id`, `text`, `evidence_ids`, and JSON-compatible `metadata`.
- `Report`: final research output with `id`, `run_id`, `title`, `summary`, `claims`, and JSON-compatible `metadata`.

Entity metadata must be copied, recursively read-only, and strict JSON-compatible. Sequences stored on entities should be immutable tuples.

### Source Ingestion

- `SourceInput`: caller-facing source ingestion request with `uri`, `title`, `content`, and optional metadata.
- `SourceIngestor`: deterministic local ingestor that assigns stable IDs with a configurable prefix and produces `Source` objects.
- Blank source title, URI, or content is rejected.

### Fake Retrieval

- `FakeRetriever`: deterministic offline search over ingested `Source` objects.
- `SearchResult`: immutable retrieval hit containing `source_id`, `title`, `snippet`, `score`, and metadata.
- Retrieval is substring/token based, stable, and sorted by score then source order.
- Empty queries are rejected. Limits must be positive integers.

### Claim-Source Mapping

- `ClaimSourceLink`: stable plain link between a claim, an evidence item, and a source.
- `build_claim_source_links(report, evidence, sources)` validates that every claim evidence ID exists and every evidence source ID exists.
- The helper returns deterministic links in report claim order and evidence ID order.
- Missing evidence and missing sources raise `ValueError` with actionable messages.

## Task 1: Add Phase 2 Plan and Start Progress

**Files:**

- Create: `redesign/docs/plans/2026-06-25-phase-2-research-core.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-2.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this Phase 2 plan**

Save this plan at `redesign/docs/plans/2026-06-25-phase-2-research-core.md`.

- [x] **Step 2: Mark Phase 2 as active**

Update the progress dashboard so Phase 2 is in progress, Phase 1 remains complete, and the verification baseline records the Phase 1 baseline before Phase 2 changes.

- [x] **Step 3: Verify docs are indexed**

Run:

```bash
rg -n "phase-2-research-core|Phase 2|Research Core" redesign/docs/README.md redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md redesign/docs/progress
```

Expected: the Phase 2 plan and active progress state are discoverable from the docs index, roadmap, and progress dashboard.

## Task 2: Add Research Domain Entities

**Files:**

- Create: `redesign/packages/research_core/src/research_core/research/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/research/entities.py`
- Create: `redesign/tests/research_core/test_research_entities.py`
- Modify: `redesign/docs/progress/phases/phase-2.md`

- [x] **Step 1: Write failing tests**

Create tests for:

- each entity rejects blank required identifiers or text fields;
- metadata is copied, strict JSON-compatible, and recursively read-only;
- `ResearchRunStatus` accepts string values and rejects unsupported status values;
- `Claim.evidence_ids` and `Report.claims` are immutable tuples;
- `Report` preserves claim order.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_research_entities.py -q
```

Expected: failure because `research_core.research` does not exist.

- [x] **Step 3: Implement entities**

Create the research package and entity dataclasses. Reuse `freeze_json_value` for metadata and `thaw_json_value` for record helpers where needed.

- [x] **Step 4: Export entities**

Update `research_core.research.__init__` to export all public Phase 2 entity contracts.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_research_entities.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/research tests/research_core/test_research_entities.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 3: Add Source Ingestion and Fake Retrieval

**Files:**

- Create: `redesign/packages/research_core/src/research_core/research/ingestion.py`
- Create: `redesign/packages/research_core/src/research_core/research/retrieval.py`
- Create: `redesign/tests/research_core/test_research_retrieval.py`
- Modify: `redesign/packages/research_core/src/research_core/research/__init__.py`
- Modify: `redesign/docs/progress/phases/phase-2.md`

- [ ] **Step 1: Write failing tests**

Create tests for:

- `SourceInput` rejects blank URI, title, or content;
- `SourceIngestor.ingest_many()` assigns deterministic IDs and preserves metadata;
- `FakeRetriever.search()` returns matching sources with stable snippets and scores;
- search results are sorted by score then source order;
- empty queries and invalid limits are rejected.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_research_retrieval.py -q
```

Expected: failure because ingestion and retrieval modules do not exist.

- [ ] **Step 3: Implement ingestion and fake retrieval**

Create deterministic source ingestion and token/substring fake retrieval without external dependencies.

- [ ] **Step 4: Export ingestion and retrieval contracts**

Update `research_core.research.__init__`.

- [ ] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_research_retrieval.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/research tests/research_core/test_research_retrieval.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 4: Add Claim-Source Mapping

**Files:**

- Create: `redesign/packages/research_core/src/research_core/research/mapping.py`
- Create: `redesign/tests/research_core/test_claim_source_mapping.py`
- Modify: `redesign/packages/research_core/src/research_core/research/__init__.py`
- Modify: `redesign/docs/progress/phases/phase-2.md`

- [ ] **Step 1: Write failing tests**

Create tests for:

- `build_claim_source_links()` returns deterministic claim/evidence/source links;
- returned links expose plain serializable records;
- missing evidence IDs raise `ValueError`;
- missing source IDs raise `ValueError`;
- claims with no evidence are rejected.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_claim_source_mapping.py -q
```

Expected: failure because `research_core.research.mapping` does not exist.

- [ ] **Step 3: Implement mapping helpers**

Create `ClaimSourceLink` and `build_claim_source_links()` using only Phase 2 entity contracts.

- [ ] **Step 4: Export mapping contracts**

Update `research_core.research.__init__`.

- [ ] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_claim_source_mapping.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/research tests/research_core/test_claim_source_mapping.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 5: Update Architecture, Glossary, README, and Progress

**Files:**

- Create: `redesign/docs/architecture/data-model.md`
- Modify: `redesign/docs/architecture/overview.md`
- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-2.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [ ] **Step 1: Add data model docs**

Document Project, ResearchRun, Source, Evidence, Claim, Report, fake retrieval, ingestion, and claim-source mapping.

- [ ] **Step 2: Update overview and runtime architecture**

Record that Phase 2 adds the research data layer while runtime remains independent from product apps and providers.

- [ ] **Step 3: Update glossary and root docs**

Add concise definitions for Phase 2 concepts and update current scope.

- [ ] **Step 4: Update progress**

Mark Phase 2 complete only after final verification passes.

- [ ] **Step 5: Verify docs**

Run:

```bash
rg -n "Project|ResearchRun|Source|Evidence|Claim|Report|FakeRetriever|claim-source" redesign/docs redesign/README.md redesign/AGENTS.md
```

Expected: Phase 2 concepts are discoverable from docs, architecture, glossary, and progress.

## Task 6: Final Phase 2 Verification

**Files:**

- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-2.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
cd redesign && uv run pytest -q
cd redesign && uv run ruff check .
git diff --check
```

Expected:

```text
All tests pass.
All checks passed!
No whitespace errors.
```

- [ ] **Step 2: Clean generated side effects**

Remove generated `redesign/.venv`, `redesign/.ruff_cache`, `redesign/.pytest_cache`, `redesign/uv.lock`, and any `__pycache__` directories unless an approved plan adds them as tracked artifacts.

- [ ] **Step 3: Commit and push**

Commit with a message that records the Phase 2 deliverables and verification commands. Push branch `codex/redesign-phase-1`.

## Phase 2 Completion Checklist

- [ ] Research entities are implemented and exported.
- [ ] Research entity tests pass.
- [ ] Source ingestion and fake retrieval are implemented and exported.
- [ ] Retrieval tests pass.
- [ ] Claim-source mapping helpers are implemented and exported.
- [ ] Claim-source mapping tests pass.
- [ ] `redesign/docs/architecture/data-model.md` documents Phase 2 contracts.
- [ ] `redesign/docs/progress/overall.md` and `phase-2.md` are updated.
- [ ] `cd redesign && uv run pytest -q` passes.
- [ ] `cd redesign && uv run ruff check .` passes.
- [ ] `git diff --check` is clean.
- [ ] No legacy `app/`, `frontend/`, root `tests/`, or root `eval/` files are modified.
