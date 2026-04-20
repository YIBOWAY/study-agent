# RAG Review Fixes Design

**Date:** 2026-04-19

## Scope

Fix the three verified review issues without expanding the public API contract:

1. `scripts/run_rag_eval.py` must work when `RAGService.ask()` returns only `answer`, `sources`, `model`, and `rerank_model`.
2. `/api/v1/rag/ingest` must route octet-stream PDF uploads to the PDF ingestion path instead of decoding them as UTF-8 text.
3. The top-level quick start must state the Python `3.10+` requirement clearly, and related docs should stay aligned with actual runtime behavior.

## Approach

### 1. RAG evaluation script

Keep `AskResponse` unchanged. The script will rebuild the groundedness context from returned `sources`, using the same formatting logic as the RAG service. This preserves the existing endpoint contract while restoring the documented evaluation workflow.

### 2. PDF ingest dispatch

Unify validation and dispatch in the ingest route after reading the upload bytes. For `application/octet-stream`, only treat the upload as a PDF when it is plausibly a PDF based on filename (`.pdf`) or PDF magic header (`%PDF-`). Plain text and markdown uploads continue through the text path. Non-PDF octet-stream uploads are rejected with `400`.

### 3. Documentation alignment

Update the top-level README quick start to call out Python `3.10+`. Update the RAG execution docs to reflect the actual accepted upload types and evaluation behavior where relevant so the user-facing docs match the runtime requirements.

## Testing

1. Add a regression test for `run_rag_eval.py` proving `--judge` works when `ask()` does not return `context`.
2. Add endpoint regression tests showing:
   - octet-stream PDFs go through `ingest_pdf()`
   - non-PDF octet-stream uploads are rejected
3. Run the targeted tests first, then run the full `pytest -q` suite.
