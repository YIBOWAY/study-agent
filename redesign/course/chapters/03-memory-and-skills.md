# Part 3: Memory and Skills - 让助手下次还能接着研究

> 接 Part 2。你已经能把 report claim 接回 source/evidence。Part 3 继续训练同一个习惯：不要问 "助手最后答得像不像"，要问 "它这次到底记住了什么、加载了什么能力包、为什么这些东西可以进入上下文"。

预计时间：75 到 100 分钟。

## Learner Contract

- **Who this is for**: Beginner Track 和 Engineer Track 都适合。你需要会运行 Python shell，知道 `assert` 是检查条件。
- **Before you start**: 先完成 Part 1 的 Agent event trail 和 Part 2 的 source -> evidence -> claim -> report 证据链。
- **You will build**: 一个完全离线的 memory notebook 和 skill package loader：写入、检查、召回 memory；加载 skill folder；只在需要时显式读取 reference。
- **You will be able to explain**: 为什么不是所有内容都应该进 memory；为什么 `PINNED` 会排在普通 memory 前面；为什么 skill runtime 先读 `SKILL.md`，不偷读全部 references。
- **You will prove it works by running**: `uv run pytest tests/research_core/test_memory_engine.py tests/research_core/test_skill_runtime.py tests/research_core/test_memory_skill_evals.py -q`。
- **Offline guarantee**: 所有 memory 都在内存里；skill folder 用临时目录；没有数据库、向量库、网络 skill marketplace 或 API key。

## 你的本地论文研究助手现在需要：笔记本

研究员昨天问过：

> "之后回答 RAG 评测问题时，所有结论都要带 source evidence。"

今天他继续问：

> "基于昨天那批论文，继续写 citation grounding 的研究摘要。"

如果助手没有 memory，它会重新推导一遍昨天已经确认过的偏好和规则。如果它没有 skill package，它也不知道 "deep research" 这类能力应该从哪里读取操作说明。更糟糕的是，如果它什么都记、什么都加载，临时草稿、错误猜测、超长 reference 会一起污染上下文。

Part 3 解决的是这个问题：让助手有一本可检查的笔记本，也有一组按需打开的技能包。

> [BIG] **大局观**：Part 2 证明研究回答有出处；Part 3 让助手在多次研究会话之间保留该保留的规则，并在需要时打开正确的能力包。后面的 Delegation 会把任务分给 child agent，Workbench 会把 memory/skill 状态展示给人看。

```text
Local Paper Research Assistant
  [x] Part 1: Agent Kernel, event trail
  [x] Part 2: Research Core, evidence chain
  [*] Part 3: Memory and Skills
      [*] Memory notebook with write/recall policy
      [*] Skill package with progressive disclosure
      [*] Break/Fix for state and capability boundaries
  [ ] Part 4: Delegation
  [ ] Part 5: Workbench UI
  [ ] Part 6: Framework comparison
  [ ] Part 7: Production readiness
```

## Section 1 [LIGHT Concept]: 笔记本和技能包

### Problem Hook

没有 Memory 时，助手像一个每次都失忆的研究助理：

```text
Session 1:
  user says "Always cite source evidence."
  assistant follows the rule.

Session 2:
  user asks a follow-up.
  assistant has no notebook, so the rule is gone.
```

没有 Skills 时，助手像一个把所有教材都摊在桌上的新人：不知道当前任务需要哪份资料，也不知道什么时候才该读取 reference。

```text
Bad shape:
  every skill doc + every reference + every script note
      -> dumped into context before the task is understood
```

### 两个心智模型

| System piece | Plain-language model | What to inspect |
| --- | --- | --- |
| `MemoryRecord` | 笔记本里的一条笔记 | `id`, `kind`, `content`, `tags`, `importance` |
| `MemoryWritePolicy` | 记笔记前的规则 | 允许哪些 kind、最低重要性、禁词、最长内容 |
| `MemoryRecallPolicy` | 翻笔记时的筛选器 | query、允许哪些 kind、limit、是否 pinned first |
| `MemoryEngine` | 这本离线笔记本 | `write()`, `recall()`, `list_records()` |
| `SkillPackage` | 一个技能包的清单 | entrypoint、references、scripts、assets |
| `SkillRuntime` | 打开技能包的人 | `load()` 只读入口和清单，`read_reference()` 才读正文 |

Memory = 研究助手的笔记本。不是所有话都值得写进去，笔记也要能被筛选、排序、检查。

Skills = 研究助手的技能包。平时收在抽屉里；要做 deep research 时，先看 `SKILL.md` 的入口说明，再决定是否读取某份 reference。

> [DD] **设计决策**：Part 3 先做确定性的本地 memory 和 folder skill runtime，不做真实长期数据库或远程 skill marketplace。因为这节课要先看清边界：什么能写、什么能召回、什么资源被加载。

### `MemoryKind` 什么时候用

这些 kind 现在主要是策略标签，让人和 policy 都能分清用途。源码里只有 `PINNED` 有特殊 recall 排序；其它 kind 不代表六套不同算法。

| Kind | When to use |
| --- | --- |
| `WORKING` | 当前任务里的临时草稿、假设、待验证线索；会话后通常不该被召回。 |
| `SESSION` | 本次会话内有用、下次不一定有用的上下文，例如 "刚才用户选择了第 2 篇论文"。 |
| `EPISODIC` | 发生过的一次具体事件，例如 "2026-07-01 这次研究 run 发现 citation link 缺失"。 |
| `SEMANTIC` | 稳定事实或长期偏好，例如 "用户喜欢 citation-backed research answers"。 |
| `PROCEDURAL` | 做事步骤或操作规则，例如 "生成 report 前先检查 claim-source links"。 |
| `PINNED` | 必须优先看到的规则或安全边界，例如 "Always cite source evidence"。 |

> [CHECK] **检查一下**：如果一条内容只是 "这次先试试看" 的草稿，它更像 `WORKING`，不是 `SEMANTIC`。如果你把草稿写成长期事实，下次召回就会污染研究。

## Section 2 [FULL Build]: Build The Notebook

### Architecture

Memory 写入和召回是两条不同的边界：

```text
WRITE PATH

MemoryRecord
    |
    v
MemoryWritePolicy.validate()
    |
    |  check order:
    |  kind -> importance -> forbidden_phrases -> max_content_chars
    v
MemoryEngine.write()
    |
    v
stored records in write order

RECALL PATH

MemoryRecallPolicy(query, allowed_kinds, limit, pinned_first)
    |
    v
MemoryEngine.recall()
    |
    |  score matching records
    |  sort key = (pinned_rank, -score, index)
    v
tuple[MemoryRecord, ...]
```

`pinned_rank` 是 `0` 时排在前面；`-score` 让分数高的排在前面；`index` 保留写入顺序作为最后的稳定 tie-breaker。

### Build

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

先准备 imports：

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

创建一本只允许研究相关记忆进入的笔记本：

```python
memory_engine = MemoryEngine(
    write_policy=MemoryWritePolicy(
        allowed_kinds=[
            MemoryKind.PINNED,
            MemoryKind.SEMANTIC,
            MemoryKind.WORKING,
            MemoryKind.PROCEDURAL,
        ],
        min_importance=0.2,
        max_content_chars=180,
        forbidden_phrases=["remember everything"],
    )
)
```

写入三条记忆：长期偏好、临时草稿、必须优先看的规则。

```python
memory_engine.write(
    MemoryRecord(
        id="pref_grounding",
        kind=MemoryKind.SEMANTIC,
        content="The user prefers citation-backed research answers with evidence.",
        tags=["preference", "citation"],
        importance=0.8,
    )
)

memory_engine.write(
    MemoryRecord(
        id="draft_hypothesis",
        kind=MemoryKind.WORKING,
        content="Draft note: citation evidence section may need a rewrite.",
        tags=["draft", "citation"],
        importance=0.3,
    )
)

memory_engine.write(
    MemoryRecord(
        id="rule_citation",
        kind=MemoryKind.PINNED,
        content="Always cite source evidence in research answers.",
        tags=["rule", "citation"],
        importance=0.9,
    )
)
```

### Inspect

先检查整本笔记本，再检查下一次研究会话会召回什么。

```python
all_records = memory_engine.list_records()
recalled = memory_engine.recall(
    MemoryRecallPolicy(
        query="citation evidence research",
        allowed_kinds=[MemoryKind.PINNED, MemoryKind.SEMANTIC],
        limit=5,
    )
)

print([record.id for record in all_records])
print([record.id for record in recalled])
```

Expected output:

```text
['pref_grounding', 'draft_hypothesis', 'rule_citation']
['rule_citation', 'pref_grounding']
```

`draft_hypothesis` 还在 notebook 里，所以可以检查；但它没有进入下一次 recall，因为 `allowed_kinds` 只允许 `PINNED` 和 `SEMANTIC`。`rule_citation` 排在 `pref_grounding` 前面，是因为 sort key 的第一项 `pinned_rank` 更高优先级。

> [TRAP] **常见陷阱：list 和 recall 不是一回事**
>
> `list_records()` 是审计整本笔记本。`recall()` 是给当前任务挑选上下文。一个 record 能被列出，不代表它应该被下一次任务召回。

### Break/Fix: Memory write policy

先打坏 kind allowlist：

```python
semantic_only_policy = MemoryWritePolicy(allowed_kinds=[MemoryKind.SEMANTIC])

try:
    semantic_only_policy.validate(
        MemoryRecord(
            id="bad_kind",
            kind=MemoryKind.WORKING,
            content="Draft citation note.",
        )
    )
except ValueError as exc:
    print(str(exc))
```

Expected output:

```text
kind 'working' is not allowed
```

再打坏 forbidden phrase 和 max length：

```python
phrase_policy = MemoryWritePolicy(
    allowed_kinds=[MemoryKind.SEMANTIC],
    forbidden_phrases=["remember everything"],
)
length_policy = MemoryWritePolicy(
    allowed_kinds=[MemoryKind.SEMANTIC],
    max_content_chars=30,
)

for policy, record in [
    (
        phrase_policy,
        MemoryRecord(
            id="bad_phrase",
            kind=MemoryKind.SEMANTIC,
            content="Remember everything the user says.",
        ),
    ),
    (
        length_policy,
        MemoryRecord(
            id="bad_length",
            kind=MemoryKind.SEMANTIC,
            content="Citation evidence needs a longer note than policy allows.",
        ),
    ),
]:
    try:
        policy.validate(record)
    except ValueError as exc:
        print(str(exc))
```

Expected output:

```text
content contains forbidden phrase
content exceeds policy maximum
```

最后看一个很适合做 failure interpretation 的细节：一条记录同时违反多条规则时，只报第一条。

```python
strict_policy = MemoryWritePolicy(
    allowed_kinds=[MemoryKind.SEMANTIC],
    min_importance=0.8,
    forbidden_phrases=["draft"],
    max_content_chars=20,
)

try:
    strict_policy.validate(
        MemoryRecord(
            id="many_failures",
            kind=MemoryKind.WORKING,
            content="draft citation evidence is much too long",
            importance=0.1,
        )
    )
except ValueError as exc:
    print(str(exc))
```

Expected output:

```text
kind 'working' is not allowed
```

这不是说 importance、forbidden phrase、length 都没问题，而是 `validate()` 按 `kind -> importance -> forbidden_phrases -> max_content_chars` 短路。读失败输出时，先修最早失败的边界，再继续跑。

## Section 3 [FULL Build]: Build The Skill Package

### Architecture

Skill runtime 的核心不是 "把所有资料塞进上下文"，而是 progressive disclosure：

```text
Skill folder
  SKILL.md
  references/*.md
  scripts/*
  assets/*
      |
      v
SkillRuntime.load(path)
      |
      v
SkillPackage(
  entrypoint = SKILL.md text,
  references = path manifest,
  scripts = path manifest,
  assets = path manifest,
)
      |
      v
explicit runtime.read_reference(package, "references/guide.md")
```

### Build

创建一个临时 `deep-research` skill folder。注意它不只有 references，也有 scripts 和 assets。

```python
skill_tmp = TemporaryDirectory()
skill_root = Path(skill_tmp.name) / "deep-research"
(skill_root / "references").mkdir(parents=True)
(skill_root / "scripts").mkdir()
(skill_root / "assets").mkdir()

(skill_root / "SKILL.md").write_text(
    """---
name: deep-research
description: Find and ground research sources.
---
# Deep Research

Use this skill when the task needs paper evidence and citation checks.
Read references only when the task needs their details.
""",
    encoding="utf-8",
)
(skill_root / "references" / "citation-style.md").write_text(
    "STYLE: every claim must name a source URI.",
    encoding="utf-8",
)
(skill_root / "scripts" / "check_claims.py").write_text(
    "print('check claims')\n",
    encoding="utf-8",
)
(skill_root / "assets" / "rubric.txt").write_text(
    "citation rubric",
    encoding="utf-8",
)

skill_runtime = SkillRuntime()
skill_package = skill_runtime.load(skill_root)

print(skill_package.name)
print(skill_package.references)
print(skill_package.scripts)
print(skill_package.assets)
print("STYLE:" in skill_package.entrypoint)
```

Expected output:

```text
deep-research
('references/citation-style.md',)
('scripts/check_claims.py',)
('assets/rubric.txt',)
False
```

`False` 是重点：`SkillRuntime.load()` 发现了 reference 路径，但没有把 reference 正文偷塞进 entrypoint。

### Inspect

现在显式读取 reference：

```python
style_guide = skill_runtime.read_reference(skill_package, "references/citation-style.md")
print(style_guide)
```

Expected output:

```text
STYLE: every claim must name a source URI.
```

### Break/Fix: Skill reference boundary

越界读取必须失败：

```python
try:
    skill_runtime.read_reference(skill_package, "../SKILL.md")
except ValueError as exc:
    print(str(exc))
```

Expected output:

```text
reference path must stay under references
```

读取不存在的 reference 也必须失败：

```python
try:
    skill_runtime.read_reference(skill_package, "references/missing.md")
except ValueError as exc:
    print(str(exc))
```

Expected output:

```text
reference file does not exist
```

修复方式不是绕过 `read_reference()`，而是只读取 `references/` 下确实存在的文件：

```python
assert skill_runtime.read_reference(skill_package, "references/citation-style.md") == (
    "STYLE: every claim must name a source URI."
)

skill_tmp.cleanup()
```

> [DEEP] **更深一层**：Progressive disclosure 不是为了省事，而是为了审计。之后 Workbench 的 context inspector 要能回答：这次 run 到底加载了哪个 skill entrypoint？又显式读取了哪份 reference？

## Product Connection

Part 5 的 Workbench 至少会需要这些视图：

- memory panel：列出 recalled memory，并显示 kind、tags、importance。
- write policy inspector：解释为什么某条候选 memory 被拒绝。
- skills panel：显示 skill entrypoint、references、scripts、assets。
- context inspector：显示这次 run 实际加载了哪些 skill reference。

这些 UI 都依赖 Part 3 的边界：memory 要可解释，skill 加载要可追踪。否则界面只能展示 final answer，不能解释这次研究到底使用了哪些状态和能力。

## Eval Gate

项目级检查：

```bash
PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_memory_engine.py tests/research_core/test_skill_runtime.py tests/research_core/test_memory_skill_evals.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
PYTHONPATH=packages/research_core/src uv run ruff check packages/research_core/src/research_core/memory packages/research_core/src/research_core/skills tests/research_core/test_memory_engine.py tests/research_core/test_skill_runtime.py tests/research_core/test_memory_skill_evals.py
```

核心自查：

```python
assert [record.id for record in recalled] == ["rule_citation", "pref_grounding"]
assert skill_package.references == ("references/citation-style.md",)
```

## Checkpoint

继续后面的章节前，用自己的话回答：

1. 为什么 memory write policy 和 recall policy 保护的风险不一样？
2. `WORKING` 和 `SEMANTIC` 的差别是什么？如果把草稿写成 `SEMANTIC` 会发生什么？
3. `MemoryEngine.recall()` 为什么需要 `(pinned_rank, -score, index)` 这种稳定排序？
4. `SkillRuntime.load()` 为什么只返回 references/scripts/assets 清单，不直接读取所有文件正文？
5. 如果一个 memory 同时 kind 不允许、importance 太低、content 太长，你应该先修哪一个？为什么？
