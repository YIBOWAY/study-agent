# Solution 03 — Memory + Skills（LangChain 轨）

## 参考要点

### L1 Write + pinned recall

- `MemoryKind.PINNED` 写入时若 `pinned=False`，`Notebook.write` 会强制 `pinned=True`。
- `MemoryRecallPolicy(query=..., pinned_first=True)` 排序键：`(pinned_rank, -score, -importance, id)`。
- `format_memory_block` 对 pinned 行加 `PINNED` 前缀，便于注入 prompt 时肉眼检查。

### L1 Write policy

- 校验顺序教学上按：kind → importance → 非空 id/content → max length → banned substring。
- `SCRATCH` 不在 `allowed_kinds` 时 raise `MemoryError: not allowed`。
- banned 匹配对 content **大小写不敏感**。

### L2 Skill progressive disclosure

```python
from pathlib import Path
import tempfile

from langchain_course.skills import SkillError, SkillLoader

root = Path(tempfile.mkdtemp()) / "deep-research"
(root / "references").mkdir(parents=True)
(root / "scripts").mkdir(parents=True)
(root / "SKILL.md").write_text(
    "---\nname: deep-research\ndescription: Structured deep research checklist\n---\n\n"
    "# Deep Research\n\nStart with the checklist.\n",
    encoding="utf-8",
)
(root / "references" / "checklist.md").write_text(
    "# Checklist\n\n1. Collect sources\n2. Extract evidence\n",
    encoding="utf-8",
)
(root / "scripts" / "noop.py").write_text("print('noop')\n", encoding="utf-8")

loader = SkillLoader()
manifest = loader.load(root)
assert manifest.name == "deep-research"
assert "checklist.md" in manifest.references
assert "noop.py" in manifest.scripts
assert "Collect sources" not in manifest.body

text = loader.read_reference(manifest, "checklist.md")
assert "Collect sources" in text

try:
    loader.read_reference(manifest, "../secrets.txt")
    raise AssertionError("should reject traversal")
except SkillError as exc:
    assert "unsafe" in str(exc)
```

### L3 Design 参考

1. **kind 过滤优先**：`allowed_kinds=(MemoryKind.FACT,)` 时，即使 note 是 PINNED，只要 kind 不在集合内就不会进入候选。pinned 只影响**已通过 kind 过滤**的排序。
2. **trail 设计**：若要审计 skill 加载，adapter 应显式记录例如 `skill_load`：`name`、`root`、`references` 列表、`read_reference` 的相对路径；**不要**假设 `SkillLoader` 自动写 parent steps——与 memory 同为独立 contract。

## 与 handwritten 的差异（有意）

| 主课 | 本轨 |
| --- | --- |
| `MemoryRecord` / `MemoryEngine` | `MemoryNote` / `Notebook` |
| kind 命名偏认知科学（WORKING…） | kind 偏产品标签（note/fact/preference…） |
| `SkillRuntime` | `SkillLoader` |
| 可挂 event 枚举值 | 教学包不自动发 event |

## 常见错误

1. 把 notebook 当成向量 RAG → 本轨是 token overlap + policy。
2. 以为 `load()` 已读完 references → 断言 body 不含 reference 正文。
3. 用 `research_core` import → 本轨禁止；只用 `langchain_course.*`。

## Offline gate

```bash
uv run pytest packages/langchain_course/tests/test_memory.py packages/langchain_course/tests/test_skills.py -q
```
