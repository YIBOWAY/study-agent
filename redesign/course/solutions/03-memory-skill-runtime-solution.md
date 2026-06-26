# Solution 03: Memory And Skill Runtime

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

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

## Exercise 1 Solution

```python
engine = MemoryEngine(
    write_policy=MemoryWritePolicy(
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
        min_importance=0.2,
    )
)

engine.write(
    MemoryRecord(
        id="mem_1",
        kind=MemoryKind.SEMANTIC,
        content="The user prefers citation-backed research answers.",
        tags=["preference"],
        importance=0.8,
    )
)

engine.write(
    MemoryRecord(
        id="mem_2",
        kind=MemoryKind.PINNED,
        content="Always preserve source evidence in research answers.",
        tags=["rule"],
        importance=0.7,
    )
)

recalled = engine.recall(MemoryRecallPolicy(query="research evidence answers", limit=2))

assert [record.id for record in recalled] == ["mem_2", "mem_1"]
```

What this proves:

- Memory recall is deterministic for this local engine.
- Pinned memory can take priority over a normal semantic memory.
- Recall uses policy, not hidden global state.

## Exercise 2 Solution

```python
policy = MemoryWritePolicy(
    allowed_kinds=[MemoryKind.SEMANTIC],
    min_importance=0.5,
    forbidden_phrases=["remember everything"],
)

bad_record = MemoryRecord(
    id="bad_1",
    kind=MemoryKind.SEMANTIC,
    content="Remember everything the user says.",
    importance=0.9,
)

try:
    policy.validate(bad_record)
except ValueError as exc:
    error_message = str(exc)
else:
    raise AssertionError("Expected polluted memory to fail")

assert error_message == "content contains forbidden phrase"
```

What this proves:

- Write policy is an active gate.
- A high-importance score is not enough to bypass forbidden content.
- Memory quality is controlled before records enter the engine.

## Exercise 3 Solution

```python
tmp = TemporaryDirectory()
root = Path(tmp.name) / "deep-research"
(root / "references").mkdir(parents=True)
(root / "SKILL.md").write_text(
    """---
name: deep-research
description: Find and ground research sources.
---
# Deep Research

Load references only when the task needs them.
""",
    encoding="utf-8",
)
(root / "references" / "guide.md").write_text(
    "REFERENCE: cite every claim.",
    encoding="utf-8",
)

runtime = SkillRuntime()
package = runtime.load(root)

assert package.name == "deep-research"
assert package.description == "Find and ground research sources."
assert package.references == ("references/guide.md",)
assert "REFERENCE:" not in package.entrypoint
```

What this proves:

- `SkillRuntime` reads `SKILL.md` first.
- It discovers reference paths as a manifest.
- It does not automatically read reference content.

## Exercise 4 Solution

```python
reference = runtime.read_reference(package, "references/guide.md")
assert reference == "REFERENCE: cite every claim."

try:
    runtime.read_reference(package, "../SKILL.md")
except ValueError as exc:
    error_message = str(exc)
else:
    raise AssertionError("Expected path traversal to fail")

assert error_message == "reference path must stay under references"

tmp.cleanup()
```

What this proves:

- References are loaded explicitly.
- The reference API is scoped to the `references/` directory.
- Skill loading follows progressive disclosure instead of dumping all resources into context.

## Final Takeaway

The important lesson is:

```text
State and capabilities need policy boundaries before they are useful.
```

Memory without write policy becomes noise. Skills without progressive disclosure become context pollution.
