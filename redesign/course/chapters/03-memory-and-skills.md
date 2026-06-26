# Chapter 03: Memory And Skills

## Goal

这一章补上 Phase 3 的学习路径：Agent 从一次性运行，走向带状态、会加载能力包的系统。

学完以后，你应该能看懂两条主线：

```text
MemoryWritePolicy -> MemoryEngine -> MemoryRecallPolicy
SkillRuntime -> SKILL.md -> explicit reference reads
```

预计时间：60 到 75 分钟。

## Before You Start

请先完成：

- `01-agent-kernel-foundations.md`
- `02-research-core-foundations.md`

这一章仍然不使用真实数据库、向量库或远程 skill marketplace。我们先用最小离线实现理解边界。

## The Idea In Plain Language

Memory 和 Skills 都是在回答同一个问题：Agent 这次运行以外，还能依赖什么？

Memory 处理“系统记住什么”。如果什么都能写进 memory，Agent 很快会被低价值、错误或隐私敏感内容污染。所以 Phase 3 先引入 `MemoryWritePolicy` 和 `MemoryRecallPolicy`。

Skills 处理“系统能学会什么能力包”。一个 skill folder 里可能有 `SKILL.md`、references、scripts 和 assets。Phase 3 的重点是 progressive disclosure：先读入口说明，只在需要时显式读取 references。

## Core Objects

| Object | Plain Meaning | Why It Exists |
| --- | --- | --- |
| `MemoryRecord` | 一条记忆 | 保存 kind、content、tags、importance 和 metadata |
| `MemoryKind` | 记忆类别 | 区分 working、session、semantic、procedural、pinned 等用途 |
| `MemoryWritePolicy` | 写入规则 | 拦截不该写入的 memory |
| `MemoryRecallPolicy` | 召回规则 | 控制查询、允许的 kind、limit 和 pinned ordering |
| `MemoryEngine` | 离线记忆引擎 | 提供确定性的 write/list/recall 行为 |
| `SkillPackage` | 已加载 skill | 保存 entrypoint 和资源清单 |
| `SkillRuntime` | skill 加载器 | 读取 `SKILL.md`，发现资源，但不偷读 references |

## Minimal Memory Example

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴：

```python
from research_core.memory import (
    MemoryEngine,
    MemoryKind,
    MemoryRecallPolicy,
    MemoryRecord,
    MemoryWritePolicy,
)

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

`mem_2` 先出现，是因为默认 `pinned_first=True`。这不是语义搜索，它只是一个确定性的入门版本：足够小，可以看清 policy 怎么影响结果。

## Minimal Skill Example

继续在同一个 shell 粘贴：

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from research_core.skills import SkillRuntime

with TemporaryDirectory() as tmp:
    root = Path(tmp) / "deep-research"
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
    print(runtime.read_reference(package, "references/guide.md"))
```

你应该看到：

```text
deep-research
('references/guide.md',)
False
REFERENCE: cite every claim.
```

关键点是第三行：`SKILL.md` 入口没有把 reference 内容自动塞进 context。reference 只有在显式读取时才进入。

## Why Policies Matter

没有 policy 的 memory 很容易变成“什么都记”：

- 临时草稿被当成长期偏好。
- 模型猜测被当成事实。
- 敏感内容被永久保存。
- 低价值噪音压过真正重要的规则。

没有 progressive disclosure 的 skill 也会出问题：

- 一次任务加载过多资料，context 被挤爆。
- reference 里的长文档还没判断是否相关，就污染当前任务。
- skill 越多，Agent 越难解释自己到底用了什么依据。

Phase 3 的实现还很小，但它把这两个边界先立住了。

## Failure Lab Preview

故意写入低价值 memory：

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
```

你应该看到：

```text
content contains forbidden phrase
```

再故意越界读取 skill reference：

```python
# 在上面的 TemporaryDirectory 示例里，把这一行放到 with block 内运行：
# runtime.read_reference(package, "../SKILL.md")
```

会得到 `reference path must stay under references`。这说明 skill runtime 不允许借 reference API 偷读目录外文件。

## Product Integration

Phase 5 的 Workbench 至少会需要这些视图：

- memory panel：列出 recalled memory，并显示 kind、tags、importance。
- write policy inspector：解释为什么某条候选 memory 被拒绝。
- skills panel：显示 skill entrypoint、references、scripts、assets。
- context inspector：显示这次 run 实际加载了哪些 skill reference。

这些 UI 都依赖 Phase 3 的边界：memory 要可解释，skill 加载要可追踪。

## Eval Gate

项目级检查：

```bash
uv run pytest tests/research_core/test_memory_engine.py tests/research_core/test_skill_runtime.py tests/research_core/test_memory_skill_evals.py -q
uv run ruff check packages/research_core/src/research_core/memory packages/research_core/src/research_core/skills tests/research_core/test_memory_engine.py tests/research_core/test_skill_runtime.py tests/research_core/test_memory_skill_evals.py
```

核心自查：

```python
assert [record.id for record in recalled] == ["mem_2", "mem_1"]
```

## Checkpoint

继续后面的章节前，用自己的话回答：

1. 为什么 memory write 需要 policy？
2. `pinned` memory 为什么默认排在前面？
3. `MemoryRecallPolicy` 控制了哪些事情？
4. Skill runtime 为什么先读 `SKILL.md`，不直接读所有 references？
5. `read_reference()` 为什么要拒绝 `../SKILL.md`？
