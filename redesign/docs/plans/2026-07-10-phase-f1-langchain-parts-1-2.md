# Phase F1: LangChain Parts 1–2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver LangChain track Parts 1–2 (Agent Kernel + Research Core) as framework-native teaching code and course materials, plus `.env` loading for DeepSeek keys, without touching `research_core` or breaking offline main CI.

**Architecture:** Teaching-only package `packages/langchain_course` implements (1) a `bind_tools` tool-calling agent loop with inspectable intermediate steps, and (2) local paper fixtures + keyword retriever + claim/evidence link records. Course materials under `course/tracks/langchain/` mirror main-course Part contract (chapter/lab/solution, L1–L3, mapping table). No `langchain` meta-package (it pulls LangGraph); stay on `langchain-core` + `langchain-openai`.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, langchain-core, langchain-openai, python-dotenv, DeepSeek OpenAI-compatible API.

**Spec:** `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md`

## Global Constraints

- Zero import between `langchain_course` and `research_core` (either direction).
- Secrets: `DEEPSEEK_API_KEY` via env or local gitignored `.env`; never commit real keys.
- Default `uv run pytest -q` stays offline green without LC group or key.
- Integration tests: `@pytest.mark.integration` + skip unless `RUN_DEEPSEEK_TESTS=1`.
- LC track must not require `langgraph` packages for Parts 1–2.
- User-facing track docs in Chinese; plan/progress English OK.
- Agent commits and pushes; user does not run multi-line git.
- Do not start F2 until F1 is complete and user continues (this phase includes Parts 1–2 only).

---

### Task 1: `.env` support + ignore + example

**Files:**
- Modify: `packages/langchain_course/src/langchain_course/config.py`
- Modify: `packages/langchain_course/tests/test_config.py`
- Modify: `.gitignore` — add `.env`, `.env.local`
- Create: `.env.example`
- Modify: `pyproject.toml` — add `python-dotenv` to `langchain-course` group
- Modify: track README + lab 00 for `.env` workflow
- Modify: `AGENTS.md` if needed (secrets)

**Interfaces:**
- Produces: `load_deepseek_settings` loads `.env` when `environ is None` and file exists; does not override already-set process env; `load_dotenv_files(*, project_root=None, environ=None)` helper optional
- Produces: `.env.example` with `DEEPSEEK_API_KEY=`, optional base_url/model

- [x] **Step 1:** Implement dotenv load; unit tests for file load and “env wins over .env”
- [x] **Step 2:** gitignore + example; docs for lab 00 / track README
- [x] **Step 3:** `uv sync --group langchain-course` and unit tests pass

### Task 2: Part 1 code — tool-calling agent loop

**Files:**
- Create: `packages/langchain_course/src/langchain_course/agent_kernel.py`
- Create: `packages/langchain_course/tests/test_agent_kernel.py`
- Create: `packages/langchain_course/src/langchain_course/tools_echo.py` (demo tools)

**Interfaces:**
- `AgentStep` frozen dataclass: `kind: str`, `payload: dict`
- `AgentRunResult`: `final_text: str`, `steps: list[AgentStep]`, `messages: list` (serializable records)
- `run_tool_calling_agent(*, user_message, system_prompt, tools, model=None, settings=None, max_steps=6) -> AgentRunResult`
- `step_kinds(result) -> list[str]` for assertions
- Tools via `@tool` / `BaseTool`; default demo `echo(text: str) -> str`

Unit tests use a fake model object with `bind_tools` + `invoke` scripted responses (no network).

- [x] **Step 1:** Failing tests for plain final + tool loop + max_steps
- [x] **Step 2:** Implement loop
- [x] **Step 3:** Tests green offline

### Task 3: Part 2 code — research evidence chain (LC-native)

**Files:**
- Create: `packages/langchain_course/src/langchain_course/research.py`
- Create: `packages/langchain_course/src/langchain_course/paper_fixtures.py`
- Create: `packages/langchain_course/tests/test_research.py`

**Interfaces:**
- `PaperDoc(id, uri, title, content)`
- `EvidenceItem(id, source_id, quote, location)`
- `ClaimItem(id, text, evidence_ids: list[str])`
- `ResearchReport(id, title, summary, claims: list[ClaimItem])`
- `ClaimLink(claim_id, evidence_id, source_id, source_uri, source_title, quote)`
- `KeywordRetriever(docs).search(query, limit=3) -> list[SearchHit]`
- `ingest_paper_fixtures() -> list[PaperDoc]`
- `build_claim_links(report, evidence, docs) -> list[ClaimLink]` (raises if broken links)
- Optional: `answer_with_context(question, docs, *, settings=None) -> str` integration-only helper

No `research_core` types.

- [x] **Step 1:** Failing unit tests for retrieve + link integrity + missing evidence
- [x] **Step 2:** Implement
- [x] **Step 3:** Tests green offline

### Task 4: Course materials Parts 1–2

**Files:**
- Create: `course/tracks/langchain/chapters/01-agent-kernel-langchain.md`
- Create: `course/tracks/langchain/labs/01-tool-calling-agent-lab.md`
- Create: `course/tracks/langchain/solutions/01-tool-calling-agent-solution.md`
- Create: `course/tracks/langchain/chapters/02-research-core-langchain.md`
- Create: `course/tracks/langchain/labs/02-evidence-chain-lab.md`
- Create: `course/tracks/langchain/solutions/02-evidence-chain-solution.md`
- Modify: `course/tracks/langchain/README.md` progress + path table
- Create: `course/tracks/langchain/reference/handwritten-mapping.md` (Parts 1–2 rows)

Each chapter: problem-first, handwritten↔LC mapping, BUILD/INSPECT/BREAK notes, `[DD]`/`[TRAP]`/`[CHECK]`, eval gate commands. Labs: L1/L2/L3. Solutions: expected structures + why.

- [x] **Step 1:** Write Part 1 materials
- [x] **Step 2:** Write Part 2 materials + mapping
- [x] **Step 3:** Docs freshness paths resolve

### Task 5: Indexes, progress, verify, commit

**Files:**
- Create: `docs/progress/phases/phase-f1.md`
- Modify: `docs/progress/overall.md`, `docs/progress/README.md`
- Modify: `docs/course/roadmap.md`, `docs/README.md`, `course/README.md`, root `README.md` as needed
- Modify: `docs/plans/2026-06-25-redesign-execution-roadmap.md` F1 complete note
- Modify: design status line if needed

Verification:

```bash
uv sync --group langchain-course
uv run pytest packages/langchain_course/tests -q   # unit pass; integration skip
uv run pytest -q                                  # main still green
uv run ruff check .
uv run pytest tests/course/test_docs_freshness.py -q
```

- [x] **Step 1:** Mark F1 complete in progress
- [x] **Step 2:** Commit + push
- [x] **Step 3:** Stop before F2 unless user already asked to continue entire LC track

## Spec coverage (F1)

| Spec § | Coverage |
| --- | --- |
| 5 DeepSeek + .env | Task 1 |
| 6.2 Part 1–2 LC focus | Tasks 2–4 |
| 6.3 Part artifact contract | Task 4 |
| 7 Testing | Tasks 2–3, 5 |
| 8 No langgraph for LC | Task 2 uses bind_tools only |
| 9 Phase F1 | Entire plan |

## Honesty

- Live API non-deterministic; unit path is default gate.
- Part 1 intermediate steps are framework-native (message/tool records), not `RunEvent` clones.
- Part 2 is LC-native evidence records, not a port of `research_core` classes.
