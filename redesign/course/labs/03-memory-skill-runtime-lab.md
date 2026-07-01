# Lab 03: Memory And Skill Runtime

这个 lab 让你把 Chapter 03 的两个边界亲手跑出来：

1. Memory notebook：写入、检查、召回，并故意触发 write policy 失败。
2. Skill package：加载清单、显式读取 reference，并故意触发 reference boundary 失败。

预计时间：60 到 75 分钟。

## Setup

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

保持这个 shell 打开。后面的 L1 和 L2 会复用变量。

先粘贴 imports：

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

## L1 Follow: Build A Notebook And A Skill Package

目标：照着跑一遍，先不要改。你要看到两件事：

- `list_records()` 能检查整本 notebook。
- `recall()` 可以把 `WORKING` 草稿过滤掉，只给下一次研究会话稳定 memory。

### Step 1: Write and recall memory

```python
lab_engine = MemoryEngine(
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
    lab_engine.write(record)

lab_next_recall = lab_engine.recall(
    MemoryRecallPolicy(
        query="citation evidence research",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
        limit=5,
    )
)

print([record.id for record in lab_engine.list_records()])
print([record.id for record in lab_next_recall])
```

Expected output:

```text
['lab_pref', 'lab_draft', 'lab_rule']
['lab_rule', 'lab_pref']
```

Self-check:

```python
assert [record.id for record in lab_next_recall] == ["lab_rule", "lab_pref"]
assert [record.id for record in lab_engine.list_records()] == [
    "lab_pref",
    "lab_draft",
    "lab_rule",
]
```

### Step 2: Load a skill package

```python
lab_tmp = TemporaryDirectory()
lab_root = Path(lab_tmp.name) / "deep-research"
(lab_root / "references").mkdir(parents=True)
(lab_root / "scripts").mkdir()
(lab_root / "assets").mkdir()

(lab_root / "SKILL.md").write_text(
    """---
name: deep-research
description: Find and ground research sources.
---
# Deep Research

Use this skill when the task needs paper evidence and citation checks.
""",
    encoding="utf-8",
)
(lab_root / "references" / "citation.md").write_text(
    "STYLE: cite every claim with a source URI.",
    encoding="utf-8",
)
(lab_root / "scripts" / "check_claims.py").write_text(
    "print('check claims')\n",
    encoding="utf-8",
)
(lab_root / "assets" / "rubric.txt").write_text(
    "citation rubric",
    encoding="utf-8",
)

lab_runtime = SkillRuntime()
lab_package = lab_runtime.load(lab_root)

print((lab_package.name, lab_package.references, lab_package.scripts, lab_package.assets))
print("STYLE:" in lab_package.entrypoint)
print(lab_runtime.read_reference(lab_package, "references/citation.md"))
```

Expected output:

```text
('deep-research', ('references/citation.md',), ('scripts/check_claims.py',), ('assets/rubric.txt',))
False
STYLE: cite every claim with a source URI.
```

Self-check:

```python
assert lab_package.references == ("references/citation.md",)
assert lab_package.scripts == ("scripts/check_claims.py",)
assert lab_package.assets == ("assets/rubric.txt",)
assert "STYLE:" not in lab_package.entrypoint
```

### Exercise Feedback - L1 Follow

Common Errors:

- You used `print(package.references)` but expected reference content. `package.references` is only a path manifest.
- You expected `lab_draft` to disappear from `list_records()`. It should still be stored; it is filtered only during recall.
- You forgot `PYTHONPATH=packages/research_core/src`, so Python cannot import `research_core`.

Failure Output Interpretation:

- `ModuleNotFoundError: No module named 'research_core'` means your shell is not using the course import path.
- `AssertionError` after recall usually means your `allowed_kinds` or query changed.
- `False` in the skill output is correct. It proves `SKILL.md` did not automatically include reference content.

Where To Go Back:

- Re-read Chapter 03 Section 2 if memory list vs recall feels fuzzy.
- Re-read Chapter 03 Section 3 if skill entrypoint vs reference content feels fuzzy.

Why Correct Answer Is Correct:

- `lab_rule` appears before `lab_pref` because recall sorts by `(pinned_rank, -score, index)`.
- `lab_draft` stays in `list_records()` because inspection and recall are different operations.
- `STYLE:` is absent from `lab_package.entrypoint` because references are loaded only by explicit `read_reference()`.

## L2 Modify: Predict, Break, Fix

目标：改一个边界，然后先预测，再运行。你要练会读失败输出，而不是只看最后一行。

### Step 1: Let drafts appear, then filter them out

先预测：如果 recall 允许 `WORKING`，`lab_draft` 会不会出现？如果下一次会话只允许 `PINNED` 和 `SEMANTIC`，它还会出现吗？

```python
with_drafts = lab_engine.recall(
    MemoryRecallPolicy(
        query="citation draft",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC, MemoryKind.WORKING],
        limit=5,
    )
)
without_drafts = lab_engine.recall(
    MemoryRecallPolicy(
        query="citation draft",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
        limit=5,
    )
)

print([record.id for record in with_drafts])
print([record.id for record in without_drafts])
```

Expected output:

```text
['lab_rule', 'lab_draft', 'lab_pref']
['lab_rule', 'lab_pref']
```

Self-check:

```python
assert "lab_draft" in [record.id for record in with_drafts]
assert "lab_draft" not in [record.id for record in without_drafts]
```

### Step 2: Break memory policy on purpose

```python
memory_errors = []

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
        memory_errors.append(str(exc))

print(memory_errors)
```

Expected output:

```text
["kind 'working' is not allowed", 'content contains forbidden phrase', 'content exceeds policy maximum', "kind 'working' is not allowed"]
```

The last error is the important one: the record also has low importance, a forbidden phrase, and too many characters, but `validate()` stops at the first failing boundary: kind.

### Step 3: Break skill reference reads on purpose

```python
skill_errors = []

for relative_path in ["../SKILL.md", "references/missing.md"]:
    try:
        lab_runtime.read_reference(lab_package, relative_path)
    except ValueError as exc:
        skill_errors.append(str(exc))

print(skill_errors)
```

Expected output:

```text
['reference path must stay under references', 'reference file does not exist']
```

Fix by reading the existing reference:

```python
assert lab_runtime.read_reference(lab_package, "references/citation.md") == (
    "STYLE: cite every claim with a source URI."
)
```

### Exercise Feedback - L2 Modify

Common Errors:

- You expected `lab_draft` to outrank `lab_rule` because it has a higher token score. `PINNED` wins the first sort key when `pinned_first=True`.
- You expected the multi-violation memory to report max length first. It reports kind first.
- You tried to read `scripts/check_claims.py` through `read_reference()`. That API is only for files under `references/`.

Failure Output Interpretation:

- `kind 'working' is not allowed` means the write policy rejected the record before it checked content length.
- `content contains forbidden phrase` means the content matched a forbidden phrase after casefolding.
- `reference path must stay under references` means the path escapes or does not live under `references/`.
- `reference file does not exist` means the path is scoped correctly but missing.

Where To Go Back:

- Re-read the memory diagram in Chapter 03 if the validate order is surprising.
- Re-read the skill diagram in Chapter 03 if reference path scoping is surprising.

Why Correct Answer Is Correct:

- The L2 recall checks prove write and recall policy are separate: a draft can exist in the notebook but not enter a later context.
- The memory failures prove policy short-circuit order.
- The skill failures prove progressive disclosure has a filesystem boundary, not only a "please be careful" convention.

## L3 Design: Policy For The Next Research Session

目标：自己设计，不要照抄 L1/L2。这个题没有唯一答案，但有必须满足的不变量。

Scenario:

> 研究员要开始下一次 citation-grounding session。他希望 pinned rules 永远优先；session notes 可以在当前 session 内出现；working drafts 绝不能在 session 结束后的 recall 中出现；skill folder 需要包含一个 citation-style reference 和一个 check script。

Your task:

1. Design a `MemoryWritePolicy` that accepts the kinds you need but still rejects low-value or polluted records.
2. Write at least one `PINNED`, one `SESSION`, one `WORKING`, and one `SEMANTIC` record.
3. Design one recall policy for "during the session" and one recall policy for "after the session".
4. Build a `citation-style` skill folder with `SKILL.md`, one `references/style.md`, and one `scripts/check_style.py`.
5. Explicitly read `references/style.md`.

Required invariants:

| Invariant | What must be true |
| --- | --- |
| Pinned priority | A matching `PINNED` rule must appear before matching non-pinned notes. |
| Draft isolation | A `WORKING` draft may appear during-session only if you allowed it, but must not appear in after-session recall. |
| Session boundary | A `SESSION` note may appear during-session but should be filtered from after-session recall unless your scenario explicitly says otherwise. |
| Skill disclosure | `package.references` lists `references/style.md`, but the style text only appears after `read_reference()`. |
| Failure proof | At least one intentionally bad memory record is rejected with the error you predicted. |

### Exercise Feedback - L3 Design

Common Errors:

- Treating L3 like a fill-in-the-blank exercise. It is a design task; choose policies and then prove the invariants.
- Forgetting to test after-session recall separately from during-session recall.
- Creating `scripts/check_style.py` but expecting `read_reference()` to read it. Scripts are discovered as a manifest, not read through the reference API.

Failure Output Interpretation:

- If your after-session recall contains a draft, your `allowed_kinds` is too wide.
- If pinned memory does not appear first, either it did not match the query or you disabled `pinned_first`.
- If your bad record reports a different error than expected, check the `validate()` order: kind, importance, forbidden phrase, max length.

Where To Go Back:

- Use Chapter 03's `MemoryKind` table to decide which kind matches each note.
- Use L2's `with_drafts` and `without_drafts` example as the smallest recall-policy comparison.
- Use L1's skill package example to remember which folders are manifest-only.

Why Correct Answer Is Correct:

- A correct L3 answer is not the one with the same variable names as the solution. It is correct if the invariants hold under assertions.
- The design should make policy intent visible: durable rules, session notes, and drafts should not collapse into one memory bucket.

## Cleanup

```python
lab_tmp.cleanup()
```

## Reflection

Write short answers before reading the solution:

1. Which of your records are safe to recall next session, and why?
2. Which failure message was easiest to misread?
3. What is the difference between a skill manifest and reference content?
4. What assertion proves your L3 design instead of merely showing a plausible final answer?
