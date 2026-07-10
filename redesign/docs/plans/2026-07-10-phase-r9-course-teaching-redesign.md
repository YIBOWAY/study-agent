# Phase R9 Plan: Course Teaching Redesign - Reference & Support Materials

Date: 2026-07-10  
Branch: `codex/redesign-course-r7` (continue on teaching branch; R1–R8 already landed here)  
Status: Complete

## Goal

补齐课程参考支持材料，让学习者在 Parts 1–7 与 Capstone 之后有一份可检索的模式、排障、设计决策索引、讨论题（含详细参考答案与解析），并扩展术语表。不改 runtime / product 代码，不重写 Parts 1–7，不重做 Capstone。

## Scope

### In scope

| Deliverable | Path |
| --- | --- |
| Common patterns | `course/reference/common-patterns.md` |
| Troubleshooting | `course/reference/troubleshooting.md` |
| Design decisions index | `course/reference/design-decisions-index.md` |
| Discussion prompts + detailed answers | `course/reference/discussion-prompts.md` |
| Glossary expansion | `course/reference/agent-kernel-glossary.md` |
| Plan + progress | this file + `docs/progress/phases/phase-r9.md` |
| Index sync | course/README, docs/course/roadmap, docs/README, progress overall/README, execution roadmap, teaching redesign status |

### Out of scope

- Runtime or product code changes under `packages/`, `apps/`
- Rewrites of chapter/lab/solution content for Parts 1–7
- Capstone redo or new Capstone fixtures
- New third-party framework adapters

## Sources of truth

- Spec: `docs/specs/2026-06-30-course-teaching-redesign.md` Phase R9 section
- Roadmap: `docs/course/roadmap.md` R9 row
- Existing callouts: `[DD]` / `[TRAP]` across `course/chapters/`, labs, Capstone
- Capstone honesty: declarative role fields, non-auto MEMORY_*/SKILL_* events, inspectable-only `max_runtime_seconds`

## Tasks

1. Start plan + progress files; mark R9 active.
2. Inventory `[DD]` / `[TRAP]` / glossary gaps (Parts 0–7 + Capstone).
3. Author four reference files; expand glossary; discussion prompts must include **详细参考答案与解析** per Part and Capstone.
4. Sync indexes; verify suite/docs/ruff; mark R9 complete; commit and push.

## Discussion prompt requirements (user)

- 每章（Part 1–7）至少 2–4 道讨论题
- Capstone 单独一组
- 每题必须包含：题干、参考答案、解析（为什么对、常见错法、与 [DD]/[TRAP] 的关联）
- 答案必须与当前代码诚实边界一致（不写“会自动 kill / 会自动 emit MEMORY event”等神话）

## Verification target

```bash
PYTHONPATH=packages/research_core/src UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run pytest -q
PYTHONPATH=packages/research_core/src UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run ruff check .
PYTHONPATH=packages/research_core/src UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run pytest tests/course/test_docs_freshness.py -q
```

## Exit signal

- [x] Four new reference files exist and are linked from course/docs indexes
- [x] Glossary covers Parts 2–7 + Capstone terms, not only Part 1
- [x] Discussion prompts include detailed answers for every Part + Capstone
- [x] Docs freshness green; full suite green; ruff clean
- [x] Progress overall marks R9 complete
