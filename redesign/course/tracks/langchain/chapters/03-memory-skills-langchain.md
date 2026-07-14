# Part 3: Memory + Skills（LangChain 轨）

> 接 Part 2。Part 2 证明 claim 有出处；Part 3 证明**下次还能接着研究**：该记的规则进 notebook，该开的能力包按需加载。主课 Part 3 可对照，但**本轨不 import** `research_core`。

预计时间：60–90 分钟。

## Learner Contract

- **你会构建**：离线 `Notebook` policy、LangChain
  `RunnableWithMessageHistory` 会话历史，以及 progressive `SkillLoader`。
- **你会解释**：为什么不是什么都能写进 memory；为什么 `load()` 不偷读全部 references；`PINNED` 如何影响召回顺序。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_memory.py packages/langchain_course/tests/test_skills.py -q`（离线）。
- **诚实边界**：`RunnableWithMessageHistory` 在当前 LangChain Core 1.4.x
  已提示迁往 LangGraph persistence；本章用它理解 LC 历史合同，F4 再学
  checkpoint/store。Notebook policy 与聊天历史不是同一件事。

## 与 handwritten 对照

| Handwritten (`research_core`) | 本轨 (`langchain_course`) |
| --- | --- |
| `MemoryEngine` / `MemoryRecord` | `Notebook` / `MemoryNote` |
| `MemoryWritePolicy` / `MemoryRecallPolicy` | 同名语义的 `MemoryWritePolicy` / `MemoryRecallPolicy` |
| `MemoryKind`（WORKING / SESSION 等） | `MemoryKind`：`note` / `preference` / `fact` / `warning` / `pinned` / `scratch` |
| `SkillRuntime` / `SkillPackage` | `SkillLoader` / `SkillManifest` |
| progressive disclosure | `load()` 只读 `SKILL.md`；`read_reference()` 显式读 |
| 会话消息历史 | `RunnableWithMessageHistory` + `InMemoryChatMessageHistory` |

> [DD] **为何不直接上 LangChain ConversationBuffer / VectorStore？** 教学目标是写/召回 **策略** 与 progressive skill 边界，而不是绑定某一家 memory 产品 API。`Notebook` 保持可检查、可单测。类型名刻意不同，避免与产品 core 共享类。

## Section 1：问题钩子

研究员昨天说：

> 之后回答 RAG 评测问题时，所有结论都要带 source evidence。

今天继续问 follow-up。如果助手没有笔记本，规则会丢；如果它把所有 skill 文档和草稿一股脑塞进 prompt，上下文会被污染。

```text
write policy  ->  Notebook.write  ->  recall policy  ->  format_memory_block
SkillLoader.load(SKILL.md)  ->  (optional) read_reference(...)
```

## Section 2 [BUILD]：写入与列表

```bash
# 在 redesign/ 下；unit 不需要 key
PYTHONPATH=packages/langchain_course/src uv run python
```

```python
from langchain_course.memory import MemoryKind, MemoryNote, Notebook

book = Notebook()
note = book.write(
    MemoryNote(
        id="m1",
        kind=MemoryKind.PREFERENCE,
        content="Always cite source evidence.",
        tags=("citation",),
        importance=5,
    )
)
assert note.id == "m1"
assert book.list_notes()[0].content.startswith("Always cite")
```

> [CHECK] `list_notes()` 按 id 排序返回 tuple；同一 id 再次 write 会覆盖。

## Section 3 [BUILD]：Write policy

```python
from langchain_course.memory import (
    MemoryError,
    MemoryKind,
    MemoryNote,
    MemoryWritePolicy,
    Notebook,
)

policy = MemoryWritePolicy(
    allowed_kinds=(MemoryKind.NOTE, MemoryKind.FACT),
    min_importance=3,
    banned_substrings=("password",),
    max_content_len=50,
)
book = Notebook(write_policy=policy)

try:
    book.write(MemoryNote(id="x", kind=MemoryKind.SCRATCH, content="tmp", importance=5))
except MemoryError as exc:
    assert "not allowed" in str(exc)

try:
    book.write(MemoryNote(id="x", kind=MemoryKind.NOTE, content="ok", importance=1))
except MemoryError as exc:
    assert "min_importance" in str(exc)

try:
    book.write(
        MemoryNote(
            id="x",
            kind=MemoryKind.NOTE,
            content="user password is secret",
            importance=5,
        )
    )
except MemoryError as exc:
    assert "banned" in str(exc)
```

> [TRAP] **不是“能写就写”**：临时草稿、敏感串、低重要性噪音会污染后续 recall。policy 是 gate，不是装饰。

## Section 4 [BUILD]：Recall + PINNED

```python
from langchain_course.memory import (
    MemoryKind,
    MemoryNote,
    MemoryRecallPolicy,
    Notebook,
    format_memory_block,
)

book = Notebook()
book.write(
    MemoryNote(
        id="n1",
        kind=MemoryKind.NOTE,
        content="temporary draft about cats",
        importance=1,
    )
)
book.write(
    MemoryNote(
        id="p1",
        kind=MemoryKind.PINNED,
        content="Always cite source evidence for RAG claims.",
        importance=9,
    )
)
book.write(
    MemoryNote(
        id="n2",
        kind=MemoryKind.FACT,
        content="Citation grounding matters for RAG evaluation.",
        tags=("rag", "citation"),
        importance=7,
    )
)
recalled = book.recall(
    MemoryRecallPolicy(query="citation RAG", limit=2, pinned_first=True)
)
assert recalled[0].id == "p1"
assert recalled[0].pinned is True
assert any(n.id == "n2" for n in recalled)
block = format_memory_block(recalled)
assert "PINNED" in block
print(block)
```

> [DD] `MemoryKind.PINNED` 在 write 时会自动把 `pinned=True`，方便 recall 排序（`pinned_first` 时 pinned_rank 优先）。

## Section 5 [BUILD]：Skill progressive load

```python
from pathlib import Path
import tempfile

from langchain_course.skills import SkillError, SkillLoader

skill = Path(tempfile.mkdtemp()) / "deep-research"
(skill / "references").mkdir(parents=True)
(skill / "scripts").mkdir(parents=True)
(skill / "SKILL.md").write_text(
    "---\n"
    "name: deep-research\n"
    "description: Structured deep research checklist\n"
    "---\n\n"
    "# Deep Research\n\n"
    "Start with the checklist. Read references only when needed.\n",
    encoding="utf-8",
)
(skill / "references" / "checklist.md").write_text(
    "# Checklist\n\n1. Collect sources\n2. Extract evidence\n",
    encoding="utf-8",
)
(skill / "scripts" / "noop.py").write_text("print('noop')\n", encoding="utf-8")

loader = SkillLoader()
manifest = loader.load(skill)
assert manifest.name == "deep-research"
assert "checklist.md" in manifest.references
assert "noop.py" in manifest.scripts
assert "Collect sources" not in manifest.body  # load 不读 reference 正文

text = loader.read_reference(manifest, "checklist.md")
assert "Collect sources" in text

try:
    loader.read_reference(manifest, "../secrets.txt")
except SkillError as exc:
    assert "unsafe" in str(exc)
```

要点：

1. `load()` 只读 `SKILL.md` frontmatter + body，列出 `references/` / `scripts/` 文件名。
2. `read_reference()` 才打开正文；拒绝 `..` 路径穿越。
3. 未列入 manifest 的 reference 名会 `SkillError`——**含** `references/hidden.md` 前缀形式；只允许 bare 列表名或 `references/<listed-name>`。

> [TRAP] **progressive disclosure 不是“懒加载缓存”**：是教学纪律——默认不把全部 reference 塞进 agent 上下文。

## Section 6 [BUILD / INSPECT]：真实 LC message history

Notebook 保存的是经过策略筛选、值得跨任务保留的事实；message history
保存的是某个会话的 Human/AI 消息。下面用真实 Runnable 包装器观察隔离：

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_course.memory import SessionHistoryStore, build_history_runnable

history_store = SessionHistoryStore()
history_model = FakeListChatModel(responses=["noted", "the rule was citations"])
history_chain = build_history_runnable(history_model, history_store)

history_chain.invoke(
    {"question": "Remember: claims need evidence."},
    config={"configurable": {"session_id": "research-1"}},
)
history_chain.invoke(
    {"question": "What rule did we discuss?"},
    config={"configurable": {"session_id": "research-1"}},
)
messages = history_store.get("research-1").messages
print([message.type for message in messages])
assert len(messages) == 4
```

> [CHECK] 如果忘记 `configurable.session_id`，框架会拒绝调用；它不会偷偷把
> 所有用户放进同一个全局历史。

> [DD] 当前版本会发出迁移 LangGraph persistence 的 warning。这不是课程坏了，
> 而是一个值得保留的版本事实：LC 先教 Runnable/history 合同，LG 再教持久化状态。

## Section 7 [BREAK / FIX]

1. `importance` 低于 `min_importance` → `MemoryError`
2. `read_reference(..., "missing.md")` → `SkillError`（not listed）
3. `kind=PINNED` 且传入 `pinned=False` → 返回 note 的 `pinned is True`
4. history 调用不带 `session_id` → 配置错误；修复 invocation config。
5. 把完整 history 当长期 memory → prompt 越来越长；修复为“history 管会话，
   Notebook 管筛选后的长期记录”。

## Section 8 [REFLECT]：与 Part 1 trail 的关系

Memory / skill **本身不自动**写入 `AgentStep`。你在产品里会选择：

- 把 `format_memory_block(recalled)` 拼进 system/user 消息；
- 或在 tool 层暴露 `notebook_write` / `skill_load`。

本 Part 先把状态边界教清楚；Part 4 会把类似边界扩展到 child agent 的 context isolation。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_memory.py packages/langchain_course/tests/test_skills.py -q
```

## Reflection

1. `PINNED` 与高 `importance` 的 FACT 同时命中 query 时，排序键是什么？
2. 若产品要“会话结束自动清理 scratch”，你会改 write 还是 recall policy？
3. skill 的 `scripts/` 被 list 但不执行——教学上为什么先停在“清单级”？

## 下一步

- Lab：[labs/03-memory-skills-lab.md](../labs/03-memory-skills-lab.md)
- Solution：[solutions/03-memory-skills-solution.md](../solutions/03-memory-skills-solution.md)
