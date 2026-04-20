# RAG Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the documented RAG evaluation workflow, fix octet-stream PDF ingestion, and align the top-level docs with the actual Python/runtime requirements.

**Architecture:** Keep the current RAG response contract intact and repair downstream consumers instead. Centralize PDF-vs-text routing in the ingest endpoint using the upload metadata and bytes so validation and dispatch agree. Update only the docs touched by these behaviors to avoid unrelated churn.

**Tech Stack:** Python, FastAPI, Pydantic, pytest

---

### Task 1: Repair RAG Evaluation Script

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\scripts\run_rag_eval.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_run_rag_eval.py`

- [ ] **Step 1: Write the failing test**

Add a regression test that runs `main()` with `--judge` and a fake `RAGService.ask()` result that omits `context`.

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_run_rag_eval.py`
Expected: FAIL with `KeyError: 'context'`

- [ ] **Step 3: Write minimal implementation**

Rebuild groundedness context from `sources` rather than indexing a removed response field.

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n ai-agent pytest -q tests/test_run_rag_eval.py`
Expected: PASS

### Task 2: Fix Octet-Stream PDF Dispatch

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\api\routes\rag.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\tests\test_rag_endpoints.py`

- [ ] **Step 1: Write the failing tests**

Add one endpoint test for octet-stream PDFs and one for non-PDF octet-stream uploads.

- [ ] **Step 2: Run tests to verify they fail**

Run: `conda run -n ai-agent pytest -q tests/test_rag_endpoints.py`
Expected: FAIL because octet-stream PDFs take the text path and arbitrary octet-stream is accepted.

- [ ] **Step 3: Write minimal implementation**

Detect plausible PDFs before dispatch and reject unsupported octet-stream uploads with `400`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `conda run -n ai-agent pytest -q tests/test_rag_endpoints.py`
Expected: PASS

### Task 3: Align Documentation

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\README.md`
- Modify: `E:\programs\AI_Agent_program\8w-plan\excut_docs\phase2_execution.md`
- Modify: `E:\programs\AI_Agent_program\8w-plan\architecture_docs\phase2_architecture.md`
- Modify: `E:\programs\AI_Agent_program\8w-plan\study_docs\phase2_rag.md`

- [ ] **Step 1: Update runtime requirement docs**

Add Python `3.10+` to the README quick start and sync any RAG docs that describe accepted upload types or evaluation behavior.

- [ ] **Step 2: Review affected docs for consistency**

Run: `rg -n "Python|PDF|Markdown|octet-stream|run_rag_eval|context" README.md excut_docs architecture_docs study_docs`
Expected: changed docs describe the current behavior consistently.

### Task 4: Verify End-to-End

**Files:**
- Verify only

- [ ] **Step 1: Run targeted regression tests**

Run: `conda run -n ai-agent pytest -q tests/test_run_rag_eval.py tests/test_rag_endpoints.py`
Expected: PASS

- [ ] **Step 2: Run the full suite**

Run: `conda run -n ai-agent pytest -q`
Expected: PASS
