# Lab 03 — Memory + Skills（LangChain 轨）

接 Chapter 03。练习可检查的 notebook 与渐进式 skill 加载。

预计时间：45–60 分钟。

## Setup

```bash
cd redesign   # 仓库内 redesign 根
uv sync --group langchain-course
uv run python
```

```python
from pathlib import Path
import tempfile

from langchain_course.memory import (
    MemoryError,
    MemoryKind,
    MemoryNote,
    MemoryRecallPolicy,
    MemoryWritePolicy,
    Notebook,
    format_memory_block,
)
from langchain_course.skills import SkillError, SkillLoader
```

## Exercise 1 (L1 Follow): Write + pinned recall

```python
book = Notebook()
book.write(
    MemoryNote(
        id="n_draft",
        kind=MemoryKind.NOTE,
        content="temporary draft about cats",
        importance=1,
    )
)
book.write(
    MemoryNote(
        id="p_rule",
        kind=MemoryKind.PINNED,
        content="Always cite source evidence for RAG claims.",
        importance=9,
    )
)
book.write(
    MemoryNote(
        id="f_rag",
        kind=MemoryKind.FACT,
        content="Citation grounding matters for RAG evaluation.",
        tags=("rag", "citation"),
        importance=7,
    )
)
recalled = book.recall(
    MemoryRecallPolicy(query="citation RAG", limit=2, pinned_first=True)
)
assert recalled[0].id == "p_rule"
assert recalled[0].pinned is True
assert any(n.id == "f_rag" for n in recalled)
assert "PINNED" in format_memory_block(recalled)
```

## Exercise 2 (L1 Follow): Write policy rejects

```python
policy = MemoryWritePolicy(
    allowed_kinds=(MemoryKind.NOTE, MemoryKind.FACT),
    min_importance=3,
    banned_substrings=("password",),
    max_content_len=50,
)
strict = Notebook(write_policy=policy)
try:
    strict.write(
        MemoryNote(id="x", kind=MemoryKind.SCRATCH, content="tmp", importance=5)
    )
    raise AssertionError("should reject scratch")
except MemoryError as exc:
    assert "not allowed" in str(exc)

try:
    strict.write(
        MemoryNote(
            id="x",
            kind=MemoryKind.NOTE,
            content="user password is secret",
            importance=5,
        )
    )
    raise AssertionError("should reject banned")
except MemoryError as exc:
    assert "banned" in str(exc)
```

## Exercise 3 (L2 Modify): Skill load + explicit reference

1. 在临时目录创建 skill 包：`SKILL.md` frontmatter 含 `name` 与 `description`；`references/checklist.md` 含 “Collect sources”；`scripts/noop.py` 任意。
2. `SkillLoader().load(path)`：断言 `references` 含 `checklist.md`，且 `body` **不含** “Collect sources”。
3. `read_reference(manifest, "checklist.md")` 含 “Collect sources”。
4. `read_reference(manifest, "../secrets.txt")` 抛 `SkillError`（unsafe）。

## Exercise 4 (L3 Design): 边界选择

1. 用 `allowed_kinds=(MemoryKind.FACT,)` 的 recall，确认 `PINNED` 偏好是否仍被召回；解释你观察到的行为是否符合“kind 过滤优先于 pinned”。
2. 设计 3–5 句：若产品要“skill 加载也进 parent trail”，你会记录哪些字段（name / references 列表 / 是否已 read_reference），**而不是**假设 loader 自动写 event。

## Offline gate

```bash
uv run pytest packages/langchain_course/tests/test_memory.py packages/langchain_course/tests/test_skills.py -q
```

## Optional：memory block 进 chat（非门禁）

```python
block = format_memory_block(recalled)
# 有 .env 时再拼进 system prompt；本 lab 不要求 live
print(block)
```

## 对照

Solution：[../solutions/03-memory-skills-solution.md](../solutions/03-memory-skills-solution.md)
