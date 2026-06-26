# Lab 03: Memory And Skill Runtime

## Goal

这个 lab 会带你亲手跑四种情况：

1. 写入并召回 memory。
2. 验证 write policy 会拒绝污染性 memory。
3. 加载一个本地 skill folder。
4. 显式读取 reference，并故意尝试越界读取。

预计时间：45 到 60 分钟。

## Setup

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

保持这个 shell 打开，后面的练习会复用变量。

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

## Exercise 1: Write And Recall Memory

粘贴：

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
print([record.id for record in recalled])
```

你应该看到：

```python
['mem_2', 'mem_1']
```

自查：

```python
assert [record.id for record in recalled] == ["mem_2", "mem_1"]
```

## Exercise 2: Reject Polluted Memory

粘贴：

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
    print(str(exc))
else:
    raise AssertionError("Expected polluted memory to fail")
```

你应该看到：

```text
content contains forbidden phrase
```

## Exercise 3: Load A Skill Without Reading References

粘贴这一整段：

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

print(package.name)
print(package.references)
print("REFERENCE:" in package.entrypoint)
```

你应该看到：

```text
deep-research
('references/guide.md',)
False
```

`False` 是重点：加载 skill 时没有自动把 reference 内容塞进 entrypoint。

自查：

```python
assert package.name == "deep-research"
assert package.references == ("references/guide.md",)
assert "REFERENCE:" not in package.entrypoint
```

## Exercise 4: Read Reference Explicitly And Block Traversal

粘贴：

```python
reference = runtime.read_reference(package, "references/guide.md")
print(reference)
```

你应该看到：

```text
REFERENCE: cite every claim.
```

现在故意越界读取：

```python
try:
    runtime.read_reference(package, "../SKILL.md")
except ValueError as exc:
    print(str(exc))
else:
    raise AssertionError("Expected path traversal to fail")

tmp.cleanup()
```

你应该看到：

```text
reference path must stay under references
```

## Reflection

做完以后，回答：

1. 为什么 `MemoryWritePolicy` 不应该允许所有内容无条件写入？
2. `pinned_first=True` 改变了召回排序的哪一部分？
3. 为什么 `SkillRuntime.load()` 不读取 reference 正文？
4. `package.references` 是正文内容还是资源清单？
5. 为什么 `read_reference(package, "../SKILL.md")` 必须失败？
