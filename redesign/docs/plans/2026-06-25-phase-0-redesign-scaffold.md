# Redesign Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a self-contained `redesign/` project shell with documentation, Python package boundaries, minimal runtime contracts, a fake model provider baseline, and an offline test baseline.

**Architecture:** The first phase creates a clean-room v2 workspace under `redesign/` without modifying the legacy app. `packages/research_core` is the only Python runtime package in this phase; apps, course material, and evals are represented by directories and docs until their own phase plans define implementation details.

**Tech Stack:** Python 3.11, uv, pytest, ruff, dataclasses, Pydantic-free core contracts for the first runtime layer.

**Implementation refinements applied during execution:**

- Shared recursive immutability helpers live in `runtime/immutability.py`.
- `AgentMessage.metadata` and `FakeModelResponse.metadata` are recursively frozen.
- `RunEvent.payload` is constrained to strict JSON-compatible values for JSONL event logs.
- `FakeModel.complete()` accepts `Sequence[AgentMessage]` and records a copied list.
- Fake search/retrieval fixtures are deferred to Phase 2, when retrieval contracts are introduced.
- The final Phase 0 suite contains 33 tests.

---

## File Structure

Create or update these files:

- Create: `redesign/README.md`
- Create: `redesign/AGENTS.md`
- Create: `redesign/pyproject.toml`
- Create: `redesign/apps/api/.gitkeep`
- Create: `redesign/apps/web/.gitkeep`
- Create: `redesign/course/chapters/.gitkeep`
- Create: `redesign/course/labs/.gitkeep`
- Create: `redesign/course/solutions/.gitkeep`
- Create: `redesign/course/framework_comparisons/.gitkeep`
- Create: `redesign/evals/datasets/.gitkeep`
- Create: `redesign/evals/reports/.gitkeep`
- Create: `redesign/infra/.gitkeep`
- Create: `redesign/docs/architecture/overview.md`
- Create: `redesign/docs/architecture/runtime.md`
- Create: `redesign/docs/glossary.md`
- Create: `redesign/packages/research_core/src/research_core/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/immutability.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/messages.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/events.py`
- Create: `redesign/packages/research_core/src/research_core/testing/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/testing/fakes.py`
- Create: `redesign/tests/research_core/test_messages.py`
- Create: `redesign/tests/research_core/test_events.py`
- Create: `redesign/tests/research_core/test_fakes.py`

Do not modify legacy `app/`, `frontend/`, `tests/`, `eval/`, or root project configuration in this phase.

### Task 1: Create Project Metadata and Directory Shell

**Files:**

- Create: `redesign/README.md`
- Create: `redesign/AGENTS.md`
- Create: `redesign/pyproject.toml`
- Create: `.gitkeep` files listed in the File Structure section

- [ ] **Step 1: Create the directory shell**

Create the directories:

```bash
mkdir -p \
  redesign/apps/api \
  redesign/apps/web \
  redesign/course/chapters \
  redesign/course/labs \
  redesign/course/solutions \
  redesign/course/framework_comparisons \
  redesign/evals/datasets \
  redesign/evals/reports \
  redesign/infra \
  redesign/docs/architecture \
  redesign/packages/research_core/src/research_core/runtime \
  redesign/packages/research_core/src/research_core/testing \
  redesign/tests/research_core
```

Create the empty keep files:

```bash
touch \
  redesign/apps/api/.gitkeep \
  redesign/apps/web/.gitkeep \
  redesign/course/chapters/.gitkeep \
  redesign/course/labs/.gitkeep \
  redesign/course/solutions/.gitkeep \
  redesign/course/framework_comparisons/.gitkeep \
  redesign/evals/datasets/.gitkeep \
  redesign/evals/reports/.gitkeep \
  redesign/infra/.gitkeep
```

- [ ] **Step 2: Add `redesign/README.md`**

Write:

````markdown
# Study Agent Redesign

This is the clean-room redesign version of the Study Agent project.

## Purpose

The redesign is both a course and a product reference:

- Course layer: learn modern Agent engineering from first principles.
- Product layer: build a professional Research Agent Workbench.
- Shared core: keep runtime contracts testable, offline-first, and framework-independent.

## Phase 0 Scope

Phase 0 creates the scaffold:

- Python package boundary under `packages/research_core`.
- Minimal runtime message and event contracts.
- Fake model fixture baseline.
- Offline pytest and ruff baseline.
- Architecture docs and glossary.

Fake search and retrieval fixtures arrive with the Research Core phase.

## Commands

Run from this directory:

```bash
uv run pytest -q
uv run ruff check .
```

## Boundaries

Legacy code remains outside this folder. New redesign work should live under `redesign/` unless an approved phase plan explicitly says otherwise.
````

- [ ] **Step 3: Add `redesign/AGENTS.md`**

Write:

````markdown
# Agent Instructions for Study Agent Redesign

## Scope

These instructions apply to files under `redesign/`.

## Rules

- Keep `packages/research_core` independent from FastAPI, React, databases, and provider SDKs.
- Keep tests offline by default.
- Use fake model fixtures for Phase 0 baseline tests.
- Add fake search/retrieval fixtures only when the Research Core phase introduces retrieval contracts.
- Add or update docs when a runtime concept is introduced.
- Do not import from the legacy root `app/` or `frontend/` directories.
- Store redesign specs and plans under `redesign/docs/`.

## Verification

Before claiming completion for a redesign change, run:

```bash
uv run pytest -q
uv run ruff check .
```

## Architecture Direction

The runtime should follow these boundaries:

- Internal messages are `AgentMessage`, not provider messages.
- Runtime activity is recorded as `RunEvent`.
- Provider adapters convert at the boundary.
- Fake model providers are first-class testing infrastructure.
````

- [ ] **Step 4: Add `redesign/pyproject.toml`**

Write:

```toml
[project]
name = "study-agent-redesign"
version = "0.1.0"
description = "Clean-room redesign of the Study Agent learning and research workbench project."
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = [
  "pytest>=8.2",
  "ruff>=0.5",
]

[tool.pytest.ini_options]
pythonpath = [
  "packages/research_core/src",
]
testpaths = [
  "tests",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 5: Run metadata smoke check**

Run:

```bash
cd redesign && uv run ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 6: Commit**

```bash
git add redesign/README.md redesign/AGENTS.md redesign/pyproject.toml redesign/apps redesign/course redesign/evals redesign/infra
git commit -m "chore: scaffold redesign workspace"
```

### Task 2: Add Architecture Docs and Glossary

**Files:**

- Create: `redesign/docs/architecture/overview.md`
- Create: `redesign/docs/architecture/runtime.md`
- Create: `redesign/docs/glossary.md`

- [ ] **Step 1: Add `redesign/docs/architecture/overview.md`**

Write:

```markdown
# Architecture Overview

## Shape

The redesign uses a double-layer repository under `redesign/`:

- `course/`: learning chapters, labs, solutions, and framework comparisons.
- `apps/`: product applications.
- `packages/`: shared runtime packages.
- `evals/`: datasets, trajectory fixtures, and evaluation reports.
- `docs/`: architecture, specs, plans, and glossary.

## Dependency Direction

`packages/research_core` is the center:

- `apps/api` may depend on `research_core`.
- `apps/web` may depend on API contracts generated from or aligned with `apps/api`.
- `course` may use `research_core` contracts for product integration labs.
- `research_core` must not depend on apps, course chapters, provider SDKs, or databases.

## Phase 0 Boundary

Phase 0 only creates:

- runtime message contracts,
- runtime event contracts,
- fake model provider baseline,
- tests,
- docs.

Product APIs, web UI, memory, skills, delegation, and retrieval are introduced by their approved phase plans.
```

- [ ] **Step 2: Add `redesign/docs/architecture/runtime.md`**

Write:

```markdown
# Runtime Architecture

## AgentMessage

`AgentMessage` is the internal message format. It is not an OpenAI, Anthropic, or framework-specific message.

## RunEvent

`RunEvent` records what happened during a research or agent run. Event logs are append-only and provide the basis for timeline UI, replay, trajectory tests, and evals.

## Provider Boundary

Provider adapters convert internal messages into provider-specific request payloads. The Phase 0 fake model provider uses the same internal contracts as live model providers.

## Phase 0 Runtime Scope

Phase 0 defines the contracts only:

- message roles,
- immutable agent messages,
- event types,
- immutable run events,
- deterministic fake model responses.
```

- [ ] **Step 3: Add `redesign/docs/glossary.md`**

Write:

```markdown
# Glossary

## AgentMessage

The internal message representation used by the redesign runtime.

## RunEvent

An append-only record of runtime activity.

## FakeModel

A deterministic offline model used for tests and labs.

## Research Agent Workbench

The final product interface for projects, research runs, delegation, evidence, reports, memory, skills, and evals.

## Skill

A folder-based capability package with a `SKILL.md` entrypoint and optional scripts, references, and assets.

## Harness

The engineering layer around an Agent: repository instructions, resource loading, run logs, replay, compaction, evals, and feedback loops.

## Multi-Agent Delegation

An orchestrator assigning scoped tasks to child agents with isolated context, budget, tool scope, skill scope, and merge contracts.
```

- [ ] **Step 4: Commit**

```bash
git add redesign/docs/architecture/overview.md redesign/docs/architecture/runtime.md redesign/docs/glossary.md
git commit -m "docs: add redesign architecture overview"
```

### Task 3: Add Runtime Message Contract

**Files:**

- Create: `redesign/packages/research_core/src/research_core/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/messages.py`
- Create: `redesign/tests/research_core/test_messages.py`

- [ ] **Step 1: Write failing tests**

Create `redesign/tests/research_core/test_messages.py`:

```python
from research_core.runtime.messages import AgentMessage, MessageRole


def test_agent_message_requires_non_empty_content() -> None:
    try:
        AgentMessage(id="msg_1", role=MessageRole.USER, content="")
    except ValueError as exc:
        assert "content must not be empty" in str(exc)
    else:
        raise AssertionError("Expected empty content to be rejected")


def test_agent_message_metadata_is_copied() -> None:
    metadata = {"source": "unit-test"}
    message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello", metadata=metadata)

    metadata["source"] = "mutated"

    assert message.metadata["source"] == "unit-test"


def test_agent_message_to_provider_dict() -> None:
    message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")

    assert message.to_provider_dict() == {"role": "user", "content": "hello"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_messages.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'research_core'
```

- [ ] **Step 3: Add package exports**

Create `redesign/packages/research_core/src/research_core/__init__.py`:

```python
"""Core runtime contracts for the Study Agent redesign."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `redesign/packages/research_core/src/research_core/runtime/__init__.py`:

```python
"""Runtime message and event contracts."""

from research_core.runtime.messages import AgentMessage, MessageRole

__all__ = ["AgentMessage", "MessageRole"]
```

- [ ] **Step 4: Add message contract**

Create `redesign/packages/research_core/src/research_core/runtime/messages.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.immutability import freeze_nested


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class AgentMessage:
    id: str
    role: MessageRole
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must not be empty")
        if not self.content.strip():
            raise ValueError("content must not be empty")
        object.__setattr__(self, "metadata", freeze_nested(dict(self.metadata)))

    def to_provider_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_messages.py -q
```

Expected:

```text
7 passed
```

- [ ] **Step 6: Run lint**

Run:

```bash
cd redesign && uv run ruff check packages/research_core/src/research_core/runtime/messages.py tests/research_core/test_messages.py
```

Expected:

```text
All checks passed!
```

- [ ] **Step 7: Commit**

```bash
git add redesign/packages/research_core/src/research_core redesign/tests/research_core/test_messages.py
git commit -m "feat: add redesign runtime message contract"
```

### Task 4: Add Runtime Event Contract

**Files:**

- Modify: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/events.py`
- Create: `redesign/tests/research_core/test_events.py`

- [ ] **Step 1: Write failing tests**

Create `redesign/tests/research_core/test_events.py`:

```python
from research_core.runtime.events import RunEvent, RunEventType


def test_run_event_requires_non_empty_run_id() -> None:
    try:
        RunEvent(id="evt_1", run_id="", type=RunEventType.MODEL_REQUEST, payload={})
    except ValueError as exc:
        assert "run_id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected empty run_id to be rejected")


def test_run_event_payload_is_copied() -> None:
    payload = {"model": "fake"}
    event = RunEvent(id="evt_1", run_id="run_1", type=RunEventType.MODEL_REQUEST, payload=payload)

    payload["model"] = "mutated"

    assert event.payload["model"] == "fake"


def test_run_event_to_record() -> None:
    event = RunEvent(
        id="evt_1",
        run_id="run_1",
        type=RunEventType.TOOL_CALL,
        payload={"tool": "search"},
    )

    assert event.to_record() == {
        "id": "evt_1",
        "run_id": "run_1",
        "type": "tool_call",
        "payload": {"tool": "search"},
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_events.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'research_core.runtime.events'
```

- [ ] **Step 3: Add event contract**

Create `redesign/packages/research_core/src/research_core/runtime/events.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.immutability import freeze_json_value, thaw_json_value


class RunEventType(StrEnum):
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SKILL_LOAD = "skill_load"
    MEMORY_RECALL = "memory_recall"
    MEMORY_WRITE = "memory_write"
    DELEGATE_START = "delegate_start"
    DELEGATE_FINISH = "delegate_finish"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class RunEvent:
    id: str
    run_id: str
    type: RunEventType
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must not be empty")
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        object.__setattr__(self, "payload", freeze_json_value(dict(self.payload)))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "type": self.type.value,
            "payload": thaw_json_value(self.payload),
        }
```

- [ ] **Step 4: Update runtime exports**

Replace `redesign/packages/research_core/src/research_core/runtime/__init__.py` with:

```python
"""Runtime message and event contracts."""

from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.messages import AgentMessage, MessageRole

__all__ = ["AgentMessage", "MessageRole", "RunEvent", "RunEventType"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_events.py -q
```

Expected:

```text
15 passed
```

- [ ] **Step 6: Run focused runtime tests**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_messages.py tests/research_core/test_events.py -q
```

Expected:

```text
22 passed
```

- [ ] **Step 7: Commit**

```bash
git add redesign/packages/research_core/src/research_core/runtime redesign/tests/research_core/test_events.py
git commit -m "feat: add redesign runtime event contract"
```

### Task 5: Add Fake Provider Baseline

**Files:**

- Create: `redesign/packages/research_core/src/research_core/testing/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/testing/fakes.py`
- Create: `redesign/tests/research_core/test_fakes.py`

- [ ] **Step 1: Write failing tests**

Create `redesign/tests/research_core/test_fakes.py`:

```python
from research_core.runtime.messages import AgentMessage, MessageRole
from research_core.testing.fakes import FakeModel, FakeModelResponse


def test_fake_model_returns_scripted_response() -> None:
    model = FakeModel([FakeModelResponse(content="hello from fake")])
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    response = model.complete(messages)

    assert response.content == "hello from fake"
    assert model.calls == [messages]


def test_fake_model_rejects_unexpected_call() -> None:
    model = FakeModel([])
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    try:
        model.complete(messages)
    except RuntimeError as exc:
        assert "FakeModel has no scripted responses left" in str(exc)
    else:
        raise AssertionError("Expected missing scripted response to fail")


def test_fake_model_response_can_include_metadata() -> None:
    response = FakeModelResponse(content="answer", metadata={"finish_reason": "stop"})

    assert response.metadata["finish_reason"] == "stop"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_fakes.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'research_core.testing'
```

- [ ] **Step 3: Add fake provider module**

Create `redesign/packages/research_core/src/research_core/testing/fakes.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from research_core.runtime.immutability import freeze_nested
from research_core.runtime.messages import AgentMessage


@dataclass(frozen=True, slots=True)
class FakeModelResponse:
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("content must not be empty")
        object.__setattr__(self, "metadata", freeze_nested(dict(self.metadata)))


class FakeModel:
    def __init__(self, responses: Iterable[FakeModelResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[AgentMessage]] = []

    def complete(self, messages: Sequence[AgentMessage]) -> FakeModelResponse:
        self.calls.append(list(messages))
        if not self._responses:
            raise RuntimeError("FakeModel has no scripted responses left")
        return self._responses.pop(0)
```

Create `redesign/packages/research_core/src/research_core/testing/__init__.py`:

```python
"""Testing utilities for offline-first redesign tests."""

from research_core.testing.fakes import FakeModel, FakeModelResponse

__all__ = ["FakeModel", "FakeModelResponse"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_fakes.py -q
```

Expected:

```text
11 passed
```

- [ ] **Step 5: Run all Phase 0 tests**

Run:

```bash
cd redesign && uv run pytest -q
```

Expected:

```text
33 passed
```

- [ ] **Step 6: Commit**

```bash
git add redesign/packages/research_core/src/research_core/testing redesign/tests/research_core/test_fakes.py
git commit -m "test: add fake model baseline"
```

### Task 6: Final Phase 0 Verification

**Files:**

- Modify: `redesign/README.md`
- Modify: `redesign/docs/architecture/runtime.md`

- [ ] **Step 1: Update README command output**

Append this section to `redesign/README.md`:

````markdown

## Phase 0 Verification

Expected local checks:

```bash
uv run pytest -q
uv run ruff check .
```

The pytest suite should include runtime message, event, and fake provider tests.
````

- [ ] **Step 2: Update runtime docs with fake provider boundary**

Append this section to `redesign/docs/architecture/runtime.md`:

```markdown

## Fake Provider Boundary

`FakeModel` is part of the testing surface. It records calls and returns scripted responses so labs, trajectory tests, and product smoke checks can run without API keys.
```

- [ ] **Step 3: Run full verification**

Run:

```bash
cd redesign && uv run pytest -q
cd redesign && uv run ruff check .
```

Expected:

```text
33 passed
All checks passed!
```

- [ ] **Step 4: Commit**

```bash
git add redesign/README.md redesign/docs/architecture/runtime.md
git commit -m "docs: record phase 0 verification"
```

## Phase 0 Completion Checklist

- [ ] `redesign/README.md` explains the redesign purpose and commands.
- [ ] `redesign/AGENTS.md` defines redesign-specific agent rules.
- [ ] `redesign/pyproject.toml` provides pytest and ruff configuration.
- [ ] `AgentMessage` tests pass.
- [ ] `RunEvent` tests pass.
- [ ] `FakeModel` tests pass.
- [ ] `cd redesign && uv run pytest -q` passes.
- [ ] `cd redesign && uv run ruff check .` passes.
- [ ] No legacy `app/`, `frontend/`, `tests/`, or `eval/` files are modified.
