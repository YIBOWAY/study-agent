# Solution 03: Memory And Skill Runtime

这份 solution 用来校准理解。请先自己完成 Lab 03，再看这里。尤其是 L3：这里给的是一个参考设计，不是唯一正确答案。

所有 snippets 都从 `redesign/` 的 Python shell 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Imports

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from research_core.memory import (
    MemoryEngine,
    MemoryKind,
    MemoryRecallPolicy,
    MemoryRecord,
    MemoryWritePolicy,
)
from research_core.skills import SkillRuntime
```

## L1 Follow Solution

### Memory notebook answer

```python
solution_engine = MemoryEngine(
    write_policy=MemoryWritePolicy(
        allowed_kinds=[
            MemoryKind.PINNED,
            MemoryKind.SEMANTIC,
            MemoryKind.WORKING,
            MemoryKind.PROCEDURAL,
        ],
        min_importance=0.2,
        max_content_chars=160,
        forbidden_phrases=["remember everything"],
    )
)

for record in [
    MemoryRecord(
        id="lab_pref",
        kind=MemoryKind.SEMANTIC,
        content="The user prefers citation-backed research answers with evidence.",
        tags=["preference", "citation"],
        importance=0.8,
    ),
    MemoryRecord(
        id="lab_draft",
        kind=MemoryKind.WORKING,
        content="Draft note: citation evidence section may need a rewrite.",
        tags=["draft", "citation"],
        importance=0.3,
    ),
    MemoryRecord(
        id="lab_rule",
        kind=MemoryKind.PINNED,
        content="Always cite source evidence in research answers.",
        tags=["rule", "citation"],
        importance=0.9,
    ),
]:
    solution_engine.write(record)

solution_next_recall = solution_engine.recall(
    MemoryRecallPolicy(
        query="citation evidence research",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
        limit=5,
    )
)

assert [record.id for record in solution_engine.list_records()] == [
    "lab_pref",
    "lab_draft",
    "lab_rule",
]
assert [record.id for record in solution_next_recall] == ["lab_rule", "lab_pref"]
```

What This Proves:

- `list_records()` is the notebook audit view, and it preserves write order.
- `recall()` is the context-selection view, and it can filter out `WORKING` memory.
- A matching `PINNED` rule outranks matching non-pinned memory.

Why This Design:

- The lab starts with `SEMANTIC`, `WORKING`, and `PINNED` because those three labels make the notebook boundary visible immediately: durable preference, temporary draft, and priority rule.
- The recall policy only allows `PINNED` and `SEMANTIC` because the query represents a next-session context, not the current draft workspace.

### Skill package answer

```python
solution_tmp = TemporaryDirectory()
solution_root = Path(solution_tmp.name) / "deep-research"
(solution_root / "references").mkdir(parents=True)
(solution_root / "scripts").mkdir()
(solution_root / "assets").mkdir()

(solution_root / "SKILL.md").write_text(
    """---
name: deep-research
description: Find and ground research sources.
---
# Deep Research

Use this skill when the task needs paper evidence and citation checks.
""",
    encoding="utf-8",
)
(solution_root / "references" / "citation.md").write_text(
    "STYLE: cite every claim with a source URI.",
    encoding="utf-8",
)
(solution_root / "scripts" / "check_claims.py").write_text(
    "print('check claims')\n",
    encoding="utf-8",
)
(solution_root / "assets" / "rubric.txt").write_text(
    "citation rubric",
    encoding="utf-8",
)

solution_runtime = SkillRuntime()
solution_package = solution_runtime.load(solution_root)

assert solution_package.name == "deep-research"
assert solution_package.references == ("references/citation.md",)
assert solution_package.scripts == ("scripts/check_claims.py",)
assert solution_package.assets == ("assets/rubric.txt",)
assert "STYLE:" not in solution_package.entrypoint
assert solution_runtime.read_reference(solution_package, "references/citation.md") == (
    "STYLE: cite every claim with a source URI."
)
```

What This Proves:

- `SkillRuntime.load()` reads `SKILL.md` and discovers resource paths.
- `references`, `scripts`, and `assets` are manifests, not automatically loaded context.
- Reference content enters context only through explicit `read_reference()`.

Why This Design:

- A skill package may have many supporting files. Loading all of them by default would make context hard to audit.
- The manifest-first shape lets the future Workbench show what exists before showing what was actually read.

## L2 Modify Solution

### Recall with and without drafts

```python
solution_with_drafts = solution_engine.recall(
    MemoryRecallPolicy(
        query="citation draft",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC, MemoryKind.WORKING],
        limit=5,
    )
)
solution_without_drafts = solution_engine.recall(
    MemoryRecallPolicy(
        query="citation draft",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
        limit=5,
    )
)

assert [record.id for record in solution_with_drafts] == [
    "lab_rule",
    "lab_draft",
    "lab_pref",
]
assert [record.id for record in solution_without_drafts] == ["lab_rule", "lab_pref"]
```

What This Proves:

- `allowed_kinds` is a recall-time boundary. It can hide drafts without deleting them.
- `PINNED` still comes first even when a draft has more query-token matches.

Why This Design:

- During-session recall and after-session recall should not be the same policy. A draft can help while you are working, then disappear from durable context.

### Memory failure answers

```python
solution_memory_errors = []

for policy, record in [
    (
        MemoryWritePolicy(allowed_kinds=[MemoryKind.SEMANTIC]),
        MemoryRecord(
            id="l2_bad_kind",
            kind=MemoryKind.WORKING,
            content="Draft citation note.",
        ),
    ),
    (
        MemoryWritePolicy(
            allowed_kinds=[MemoryKind.SEMANTIC],
            forbidden_phrases=["remember everything"],
        ),
        MemoryRecord(
            id="l2_bad_phrase",
            kind=MemoryKind.SEMANTIC,
            content="Remember everything the user says.",
        ),
    ),
    (
        MemoryWritePolicy(
            allowed_kinds=[MemoryKind.SEMANTIC],
            max_content_chars=25,
        ),
        MemoryRecord(
            id="l2_bad_length",
            kind=MemoryKind.SEMANTIC,
            content="Citation evidence note is too long.",
        ),
    ),
    (
        MemoryWritePolicy(
            allowed_kinds=[MemoryKind.SEMANTIC],
            min_importance=0.8,
            forbidden_phrases=["draft"],
            max_content_chars=20,
        ),
        MemoryRecord(
            id="l2_many_failures",
            kind=MemoryKind.WORKING,
            content="draft citation evidence is much too long",
            importance=0.1,
        ),
    ),
]:
    try:
        policy.validate(record)
    except ValueError as exc:
        solution_memory_errors.append(str(exc))

assert solution_memory_errors == [
    "kind 'working' is not allowed",
    "content contains forbidden phrase",
    "content exceeds policy maximum",
    "kind 'working' is not allowed",
]
```

What This Proves:

- Write policy rejects kind, content, and length problems before records enter the engine.
- Multi-violation records report the first failing boundary.

Why This Design:

- The last assertion is deliberately not "all failures at once." The real `validate()` order is `kind -> importance -> forbidden_phrases -> max_content_chars`, so the correct diagnosis starts with kind.

### Skill failure answers

```python
solution_skill_errors = []

for relative_path in ["../SKILL.md", "references/missing.md"]:
    try:
        solution_runtime.read_reference(solution_package, relative_path)
    except ValueError as exc:
        solution_skill_errors.append(str(exc))

assert solution_skill_errors == [
    "reference path must stay under references",
    "reference file does not exist",
]
assert solution_runtime.read_reference(solution_package, "references/citation.md") == (
    "STYLE: cite every claim with a source URI."
)
```

What This Proves:

- The reference API is scoped to `references/`.
- A scoped path can still fail if the file does not exist.
- The fix is to read a real reference, not to bypass the skill runtime.

Why This Design:

- A skill loader that allows `../SKILL.md` through the reference API would make context provenance unclear. The runtime must keep "which resource did we read" auditable.

## L3 Design Reference Solution

This is one valid design. Other answers are fine if they satisfy the same invariants.

### Reference memory design

```python
l3_engine = MemoryEngine(
    write_policy=MemoryWritePolicy(
        allowed_kinds=[
            MemoryKind.PINNED,
            MemoryKind.SESSION,
            MemoryKind.WORKING,
            MemoryKind.SEMANTIC,
            MemoryKind.PROCEDURAL,
        ],
        min_importance=0.25,
        max_content_chars=180,
        forbidden_phrases=["remember everything"],
    )
)

for record in [
    MemoryRecord(
        id="l3_rule",
        kind=MemoryKind.PINNED,
        content="Always cite source evidence before writing citation summaries.",
        tags=["rule", "citation"],
        importance=0.95,
    ),
    MemoryRecord(
        id="l3_session",
        kind=MemoryKind.SESSION,
        content="This session is focusing on paper two and citation grounding.",
        tags=["session", "paper"],
        importance=0.5,
    ),
    MemoryRecord(
        id="l3_draft",
        kind=MemoryKind.WORKING,
        content="Draft note: paper two may need a stronger citation example.",
        tags=["draft", "paper"],
        importance=0.4,
    ),
    MemoryRecord(
        id="l3_pref",
        kind=MemoryKind.SEMANTIC,
        content="The user prefers concise citation-backed research answers.",
        tags=["preference", "citation"],
        importance=0.7,
    ),
]:
    l3_engine.write(record)

l3_during_session = l3_engine.recall(
    MemoryRecallPolicy(
        query="citation source draft paper",
        allowed_kinds=[
            MemoryKind.PINNED,
            MemoryKind.SESSION,
            MemoryKind.WORKING,
            MemoryKind.SEMANTIC,
        ],
        limit=10,
    )
)
l3_after_session = l3_engine.recall(
    MemoryRecallPolicy(
        query="citation source draft paper",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC, MemoryKind.PROCEDURAL],
        limit=10,
    )
)

assert [record.id for record in l3_during_session] == [
    "l3_rule",
    "l3_draft",
    "l3_session",
    "l3_pref",
]
assert [record.id for record in l3_after_session] == ["l3_rule", "l3_pref"]
assert "l3_draft" not in [record.id for record in l3_after_session]
assert "l3_session" not in [record.id for record in l3_after_session]
```

What This Proves:

- Pinned priority holds even when the draft has a higher token score.
- Draft and session notes can help during the session.
- After-session recall filters out `WORKING` and `SESSION` records.

Why This Design:

- The write policy allows `WORKING` and `SESSION` because the notebook must be able to store inspectable state.
- The after-session recall policy excludes them because durable context should not inherit transient drafts.

### Reference failure invariant

```python
try:
    l3_engine.write(
        MemoryRecord(
            id="l3_bad",
            kind=MemoryKind.WORKING,
            content="remember everything about this draft",
            importance=0.1,
        )
    )
except ValueError as exc:
    l3_bad_error = str(exc)
else:
    raise AssertionError("Expected low-importance polluted draft to fail")

assert l3_bad_error == "importance is below policy minimum"
```

What This Proves:

- The bad record is rejected before it enters the engine.
- The first error is importance, not forbidden phrase, because kind is allowed and `validate()` checks importance before forbidden phrases.

Why This Design:

- This is a useful failure-output interpretation exercise: a later failure can be real but hidden until earlier boundaries pass.

### Reference skill design

```python
l3_tmp = TemporaryDirectory()
l3_root = Path(l3_tmp.name) / "citation-style"
(l3_root / "references").mkdir(parents=True)
(l3_root / "scripts").mkdir()

(l3_root / "SKILL.md").write_text(
    """---
name: citation-style
description: Keep research claims tied to source URIs.
---
# Citation Style

Use this skill when revising report claims and source links.
""",
    encoding="utf-8",
)
(l3_root / "references" / "style.md").write_text(
    "STYLE: preserve source URI next to each claim.",
    encoding="utf-8",
)
(l3_root / "scripts" / "check_style.py").write_text(
    "print('check citation style')\n",
    encoding="utf-8",
)

l3_runtime = SkillRuntime()
l3_package = l3_runtime.load(l3_root)
l3_style_text = l3_runtime.read_reference(l3_package, "references/style.md")

assert l3_package.name == "citation-style"
assert l3_package.references == ("references/style.md",)
assert l3_package.scripts == ("scripts/check_style.py",)
assert "STYLE:" not in l3_package.entrypoint
assert l3_style_text == "STYLE: preserve source URI next to each claim."
```

What This Proves:

- The skill folder includes the required reference and script.
- Loading the skill discovers the manifest.
- The style content enters only through explicit reference read.

Why This Design:

- The runtime can show the skill package shape without flooding context. That is the same progressive-disclosure boundary the Workbench will later expose.

## Forward Connections

Part 4 connection:

- Delegated child agents should not inherit unfiltered parent memory. The L3 after-session policy is the same habit you will use for child-context isolation.

Part 5 connection:

- Workbench memory and skills panels need inspectable manifests and recalled records. Without `list_records()`, `allowed_kinds`, and explicit `read_reference()`, the UI cannot explain what context entered a run.

Part 7 connection:

- Production diagnostics need to audit what a run had access to. A final answer is not enough; you need memory IDs, skill package manifests, and explicit reference reads.

## Cleanup

```python
solution_tmp.cleanup()
l3_tmp.cleanup()
```

## Final Takeaway

The important lesson is:

```text
Persistent state and reusable skills become useful only after they become inspectable and policy-bound.
```

Memory without write/recall policy becomes pollution. Skills without progressive disclosure become context flooding. The correct design is the one whose invariants you can prove with assertions.
