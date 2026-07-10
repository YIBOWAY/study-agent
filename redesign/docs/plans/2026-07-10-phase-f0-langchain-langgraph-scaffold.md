# Phase F0: LangChain / LangGraph Parallel Track Scaffold — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Scaffold the parallel LangChain and LangGraph teaching tracks so a learner can install optional deps, configure DeepSeek, run one hello chat (integration), and find clear entrypoints—without touching `research_core` or breaking the main offline CI.

**Architecture:** Teaching-only packages `packages/langchain_course` and `packages/langgraph_course` sit beside `research_core`. Course materials live under `course/tracks/langchain/` and `course/tracks/langgraph/`. Optional uv extras install framework deps; default `pytest` stays on handwritten tests only. DeepSeek is accessed via OpenAI-compatible client settings from env vars.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, langchain-core / langchain-openai (LC extra), langgraph (LG extra), DeepSeek OpenAI-compatible API.

**Spec:** `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md`

## Global Constraints

- Do **not** import `research_core` from `langchain_course` or `langgraph_course`, or the reverse.
- Do **not** add LC/LG deps to the default `[project].dependencies` list—only optional extras / dependency-groups.
- Do **not** put API keys in the repo; only env: `DEEPSEEK_API_KEY`, optional `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`.
- Default `uv run pytest -q` must still be offline and green without LC/LG installed and without a key.
- Integration tests use `@pytest.mark.integration` and skip unless `RUN_DEEPSEEK_TESTS=1`.
- F0 does **not** implement Parts 1–7 content or Capstone—scaffold + hello only.
- User-facing docs for the new tracks may be Chinese where the main course is Chinese; plan/progress English is fine to match existing docs style.
- Commit and push without asking the user to run shell git; segment if sandbox blocks `.git`.

---

### Task 1: Progress + package skeletons + DeepSeek config (unit-tested)

**Files:**
- Create: `docs/progress/phases/phase-f0.md`
- Create: `packages/langchain_course/src/langchain_course/__init__.py`
- Create: `packages/langchain_course/src/langchain_course/config.py`
- Create: `packages/langchain_course/tests/test_config.py`
- Create: `packages/langgraph_course/src/langgraph_course/__init__.py`
- Create: `packages/langgraph_course/src/langgraph_course/__init__.py` content only (package marker; LG hello deferred to later in F0 as import-only)
- Modify: `pyproject.toml` — optional dependency groups, pythonpath, markers
- Modify: `AGENTS.md` — framework track boundaries
- Test: `packages/langchain_course/tests/test_config.py`

**Interfaces:**
- Consumes: env vars `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
- Produces:
  - `DeepSeekSettings` dataclass with fields `api_key: str`, `base_url: str`, `model: str`
  - `DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"`
  - `DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"`
  - `load_deepseek_settings(*, environ: Mapping[str, str] | None = None) -> DeepSeekSettings`
  - raises `DeepSeekConfigError` if `DEEPSEEK_API_KEY` missing or blank

- [x] **Step 1: Write failing unit tests for config**

```python
# packages/langchain_course/tests/test_config.py
import pytest

from langchain_course.config import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DeepSeekConfigError,
    load_deepseek_settings,
)


def test_load_deepseek_settings_requires_api_key() -> None:
    with pytest.raises(DeepSeekConfigError, match="DEEPSEEK_API_KEY"):
        load_deepseek_settings(environ={})


def test_load_deepseek_settings_uses_defaults() -> None:
    settings = load_deepseek_settings(environ={"DEEPSEEK_API_KEY": "sk-test"})
    assert settings.api_key == "sk-test"
    assert settings.base_url == DEFAULT_DEEPSEEK_BASE_URL
    assert settings.model == DEFAULT_DEEPSEEK_MODEL


def test_load_deepseek_settings_respects_overrides() -> None:
    settings = load_deepseek_settings(
        environ={
            "DEEPSEEK_API_KEY": "sk-test",
            "DEEPSEEK_BASE_URL": "https://example.com/v1",
            "DEEPSEEK_MODEL": "deepseek-reasoner",
        }
    )
    assert settings.base_url == "https://example.com/v1"
    assert settings.model == "deepseek-reasoner"
```

- [x] **Step 2: Run test to verify it fails**

```bash
cd redesign
PYTHONPATH=packages/langchain_course/src uv run pytest packages/langchain_course/tests/test_config.py -q
```

Expected: FAIL (module not found or import error)

- [x] **Step 3: Implement package + config + pyproject + progress + AGENTS**

`packages/langchain_course/src/langchain_course/__init__.py`:

```python
"""Teaching-only LangChain course package (not product runtime)."""

__all__ = ["__version__"]
__version__ = "0.1.0"
```

`packages/langchain_course/src/langchain_course/config.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


class DeepSeekConfigError(ValueError):
    """Raised when DeepSeek environment configuration is invalid."""


@dataclass(frozen=True, slots=True)
class DeepSeekSettings:
    api_key: str
    base_url: str
    model: str


def load_deepseek_settings(*, environ: Mapping[str, str] | None = None) -> DeepSeekSettings:
    env = os.environ if environ is None else environ
    api_key = (env.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise DeepSeekConfigError(
            "DEEPSEEK_API_KEY is required for the LangChain/LangGraph tracks"
        )
    base_url = (env.get("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL).strip()
    model = (env.get("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL).strip()
    if not base_url:
        raise DeepSeekConfigError("DEEPSEEK_BASE_URL must not be blank when set")
    if not model:
        raise DeepSeekConfigError("DEEPSEEK_MODEL must not be blank when set")
    return DeepSeekSettings(api_key=api_key, base_url=base_url, model=model)
```

`packages/langgraph_course/src/langgraph_course/__init__.py`:

```python
"""Teaching-only LangGraph course package (not product runtime)."""

__all__ = ["__version__"]
__version__ = "0.1.0"
```

`pyproject.toml` changes (merge carefully):

```toml
[dependency-groups]
dev = [
  "httpx>=0.27",
  "pytest>=8.2",
  "ruff>=0.5",
]
langchain-course = [
  "langchain-core>=0.3",
  "langchain-openai>=0.2",
]
langgraph-course = [
  "langchain-core>=0.3",
  "langchain-openai>=0.2",
  "langgraph>=0.2",
]

[tool.pytest.ini_options]
pythonpath = [
  ".",
  "apps/api/src",
  "packages/research_core/src",
  "packages/langchain_course/src",
  "packages/langgraph_course/src",
]
testpaths = [
  "tests",
]
markers = [
  "integration: hits live network/API; skipped unless RUN_DEEPSEEK_TESTS=1",
]
```

Note: keep default `testpaths = ["tests"]` so `packages/*/tests` are **not** in the main suite. Framework unit tests are run with explicit paths.

`docs/progress/phases/phase-f0.md` — Status In progress, goal, checklist Tasks 1–4, branch, started 2026-07-10.

`AGENTS.md` add bullets:

```markdown
- Keep `packages/langchain_course` and `packages/langgraph_course` teaching-only; do not import them from `research_core`, `apps/api`, or `apps/web`.
- Keep framework track materials under `course/tracks/langchain/` and `course/tracks/langgraph/`; do not mix their code with handwritten Capstone under `course/capstone/`.
- Framework track live API tests require `DEEPSEEK_API_KEY` and `RUN_DEEPSEEK_TESTS=1`; default CI stays offline.
```

- [x] **Step 4: Run unit tests + main suite**

```bash
cd redesign
PYTHONPATH=packages/langchain_course/src:packages/research_core/src uv run pytest packages/langchain_course/tests/test_config.py -q
# Expected: 3 passed
PYTHONPATH=packages/research_core/src uv run pytest -q
# Expected: 215 passed (or current baseline)
uv run ruff check packages/langchain_course packages/langgraph_course
```

- [x] **Step 5: Commit**

```bash
git add packages/langchain_course packages/langgraph_course pyproject.toml AGENTS.md docs/progress/phases/phase-f0.md docs/plans/2026-07-10-phase-f0-langchain-langgraph-scaffold.md
git commit -m "feat: scaffold langchain_course config and F0 progress"
```

---

### Task 2: DeepSeek chat factory + hello lab materials + integration test

**Files:**
- Create: `packages/langchain_course/src/langchain_course/deepseek.py`
- Create: `packages/langchain_course/tests/test_deepseek_hello.py`
- Create: `course/tracks/langchain/README.md`
- Create: `course/tracks/langchain/labs/00-deepseek-hello.md`
- Create: `course/tracks/langchain/solutions/00-deepseek-hello-solution.md`
- Create: `course/tracks/langgraph/README.md` (placeholder: LC first)
- Create: `course/tracks/langchain/reference/version-matrix.md`
- Test: `packages/langchain_course/tests/test_deepseek_hello.py`

**Interfaces:**
- Consumes: `load_deepseek_settings`, `DeepSeekSettings`
- Produces:
  - `build_deepseek_chat_model(settings: DeepSeekSettings | None = None)`
  - returns a LangChain chat model instance (`ChatOpenAI` with `api_key`, `base_url`, `model`)
  - `run_hello_chat(prompt: str = "Reply with exactly: pong", *, settings: DeepSeekSettings | None = None) -> str`

- [x] **Step 1: Write unit test that mocks model construction (no network)**

```python
# In test_deepseek_hello.py — unit portion
from langchain_course.config import DeepSeekSettings
from langchain_course import deepseek as deepseek_mod


def test_build_deepseek_chat_model_passes_settings(monkeypatch) -> None:
    captured: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(deepseek_mod, "ChatOpenAI", FakeChatOpenAI)
    settings = DeepSeekSettings(
        api_key="sk-test",
        base_url="https://example.com/v1",
        model="deepseek-chat",
    )
    model = deepseek_mod.build_deepseek_chat_model(settings)
    assert isinstance(model, FakeChatOpenAI)
    assert captured["api_key"] == "sk-test"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["model"] == "deepseek-chat"
```

- [x] **Step 2: Write integration test (skip without flag)**

```python
import os
import pytest

from langchain_course.deepseek import run_hello_chat


@pytest.mark.integration
def test_run_hello_chat_live() -> None:
    if os.environ.get("RUN_DEEPSEEK_TESTS") != "1":
        pytest.skip("set RUN_DEEPSEEK_TESTS=1 and DEEPSEEK_API_KEY to run")
    text = run_hello_chat("Reply with one short word only.")
    assert isinstance(text, str)
    assert text.strip()
```

- [x] **Step 3: Implement deepseek.py**

```python
from __future__ import annotations

from langchain_openai import ChatOpenAI

from langchain_course.config import DeepSeekSettings, load_deepseek_settings


def build_deepseek_chat_model(
    settings: DeepSeekSettings | None = None,
) -> ChatOpenAI:
    resolved = load_deepseek_settings() if settings is None else settings
    return ChatOpenAI(
        api_key=resolved.api_key,
        base_url=resolved.base_url,
        model=resolved.model,
        temperature=0,
    )


def run_hello_chat(
    prompt: str = "Reply with exactly: pong",
    *,
    settings: DeepSeekSettings | None = None,
) -> str:
    model = build_deepseek_chat_model(settings)
    message = model.invoke(prompt)
    content = message.content
    if isinstance(content, str):
        return content
    return str(content)
```

- [x] **Step 4: Write track READMEs and lab/solution (Chinese learner-facing)**

`course/tracks/langchain/README.md` must cover:

- 这是并行轨，不替代 handwritten 主课
- 安装：`uv sync --group langchain-course`（or documented equivalent）
- env 变量表
- 如何跑 unit vs integration
- 学习顺序：先 LC 再 LG
- 诚实边界：真实 API 非确定、费用、与 research_core 无关

`course/tracks/langchain/labs/00-deepseek-hello.md`:

- 目标：配置 DeepSeek，完成一次 chat
- 命令：

```bash
export DEEPSEEK_API_KEY=...
uv sync --group langchain-course
PYTHONPATH=packages/langchain_course/src uv run python -c "from langchain_course.deepseek import run_hello_chat; print(run_hello_chat())"
```

- 检查点：有非空回复；配置错误时看到 `DeepSeekConfigError`

`course/tracks/langgraph/README.md`:

- 说明 F0 仅占位；请先完成 LC 轨；LG 从 F4 起系统展开
- 包路径与「勿混 research_core」边界

`course/tracks/langchain/reference/version-matrix.md`:

- Document intended packages: langchain-core, langchain-openai, langgraph (for LG group)
- Pin guidance: use dependency-group lower bounds; re-verify on upgrade

- [x] **Step 5: Install group and run tests**

```bash
cd redesign
uv sync --group langchain-course
PYTHONPATH=packages/langchain_course/src uv run pytest packages/langchain_course/tests -q
# Expected: unit tests pass; integration skipped
# If key available (optional, do not fail F0 if missing):
# RUN_DEEPSEEK_TESTS=1 DEEPSEEK_API_KEY=... uv run pytest packages/langchain_course/tests -m integration -q
uv run pytest -q
# Expected: main suite still green
uv run ruff check packages/langchain_course packages/langgraph_course
```

- [x] **Step 6: Commit**

```bash
git add packages/langchain_course course/tracks pyproject.toml
git commit -m "feat: DeepSeek hello for LangChain track scaffold"
```

---

### Task 3: Index sync + docs freshness safety

**Files:**
- Modify: `course/README.md` — add「并行框架轨」section linking tracks
- Modify: `docs/course/roadmap.md` — F0–F5 near-term bullets; F0 in progress/complete
- Modify: `docs/README.md` — link design spec + track entrypoints
- Modify: `docs/progress/overall.md` — F0 row / current state note
- Modify: `docs/progress/README.md` — phase-f0 entry
- Modify: `README.md` — short pointer to parallel tracks
- Modify: `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md` status line if needed
- Test: `tests/course/test_docs_freshness.py` (must stay green)

**Rules for code spans in indexes:**

- Always use full repo-relative paths in backticks when the path is not relative to the index file, e.g. `` `course/tracks/langchain/README.md` `` not `` `README.md` `` for track files from root README.
- Prefer markdown links with relative paths for navigation; use backticks only for paths that should be freshness-checked.

- [x] **Step 1: Edit indexes** (content as above; R1–R9 status unchanged)

- [x] **Step 2: Verify docs freshness + main suite**

```bash
cd redesign
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
uv run pytest -q
uv run ruff check .
```

Expected: all green

- [x] **Step 3: Commit**

```bash
git commit -am "docs: index LangChain/LangGraph parallel track scaffold"
```

---

### Task 4: Mark F0 complete, baseline, push

**Files:**
- Modify: `docs/progress/phases/phase-f0.md` — Complete, exit signals, verification results
- Modify: `docs/plans/2026-07-10-phase-f0-langchain-langgraph-scaffold.md` — Status Complete, checkboxes done
- Modify: `docs/progress/overall.md` — F0 complete baseline

- [x] **Step 1: Record verification**

```text
- Main suite: N passed
- langchain_course unit: N passed, integration skipped (or passed if key present)
- ruff: clean
- docs freshness: green
```

- [x] **Step 2: Final commit + push**

```bash
git add docs/progress docs/plans
git commit -m "docs: mark phase F0 LangChain/LangGraph scaffold complete"
git push -u origin HEAD
```

- [x] **Step 3: Stop** — do not start F1 (LC Parts 1–2) until user asks or a new plan is approved.

---

## Spec coverage check (F0 only)

| Spec § | F0 coverage |
| --- | --- |
| 4.1 Directory layout | Task 2 track dirs; Task 1 packages |
| 4.2 Dependency isolation | Task 1 pyproject groups + testpaths |
| 5 DeepSeek config | Task 1–2 |
| 9 Phase F0 deliverable | All tasks |
| 10 Index surfaces | Task 3 |
| 14 F0 preview | Entire plan |
| Parts 1–7 / Capstone | Deferred F1–F5 |

## Placeholder scan

None intentional. Exact file paths and code included.

## Type consistency

- `DeepSeekSettings`, `load_deepseek_settings`, `build_deepseek_chat_model`, `run_hello_chat` names stable across tasks.
