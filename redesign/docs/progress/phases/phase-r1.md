# Phase R1 Progress: Course Teaching Redesign - Part 1

Status: In Progress

Started: 2026-06-30
Completed: Not complete
Branch: `codex/redesign-course-r1`

## Goal

Turn the learner entrypoint and Part 1 from technically correct module documentation into a project-driven self-study path for building a 本地论文研究助手.

## Start Conditions

- Runtime/product v1 baseline is complete through Phase 7.
- The course teaching redesign spec and R1 plan are approved and stored under `docs/specs/` and `docs/plans/`.
- `codegraph status .` in `redesign/` reports the index is up to date with 65 files, 1,001 nodes, and 2,751 edges.

## Planned Deliverables

- Capstone placeholder explaining the eventual offline 本地论文研究助手 project.
- Project-driven chapter authoring template.
- Course roadmap rewritten around Parts R1-R9.
- Part 1 Section 1 rewrite in Chapter 00.
- Part 1 Sections 2-5 rewrite in Chapter 01.
- Lab 01 rewritten as L1/L2/L3 exercises with feedback loops.
- Solution 01 rewritten with design rationale and "why correct" explanations.
- Course README rewritten as the project-driven learner guide.
- Docs index and progress sync.
- Final verification and cleanup.

## Task Checklist

- [x] Task 1: Create Capstone placeholder.
- [x] Task 2: Replace chapter template with the Part authoring template.
- [x] Task 3: Update course roadmap for project-driven Parts and R1-R9.
- [x] Task 4: Rewrite Chapter 00 as Part 1 Section 1.
- [x] Task 5: Rewrite Chapter 01 as Part 1 Sections 2-5.
- [x] Task 6: Rewrite Lab 01 with three-tier exercises and feedback.
- [x] Task 7: Rewrite Solution 01 with design rationale.
- [ ] Task 8: Rewrite Course README as the project-driven learning guide.
- [ ] Task 9: Update docs index and progress tracking.
- [ ] Task 10: Final verification and cleanup.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-30 | Phase R1 started with a first-principles review of the course-teaching plan. The plan direction was accepted, with corrections: R1 is explicitly limited to the learner entrypoint and Part 1, verification gates cannot be pre-marked as passing, milestone commits must push, and commit templates must not include inaccurate co-author trailers. |
| 2026-06-30 | Tasks 1-3 landed as the foundation: `course/capstone/README.md` previews the offline capstone without overclaiming, `docs/course/chapter-template.md` defines the reusable Part format, and `docs/course/roadmap.md` now separates R1 current work from R2-R9 planned course rewrites. Subagent spec/quality review found and fixed the ch00/ch01 Part 1 boundary in both capstone and roadmap. |
| 2026-06-30 | Task 4 rewrote `course/chapters/00-before-agent-kernel.md` as Part 1 Section 1. Review fixed the explicit `User` / `user_message` term boundary, reduced the first-contact architecture map, and clarified that event trail and final answer are sibling outputs from `AgentRunner`. |
| 2026-06-30 | Task 5 rewrote `course/chapters/01-agent-kernel-foundations.md` as Part 1 Sections 2-5. Review fixed the Break/Fix repair path so it remains runnable after changing `missing` back to `echo`, added L3 `tool_values == [7, 14]` causal assertions, completed the L3 feedback loop, and tightened the Part 1 closer to avoid implying real paper retrieval already exists. Focused snippet verification confirmed the unknown-tool failure path, fixed six-event tool path, and two-tool calculator event trail. |
| 2026-07-01 | Tasks 6-7 rewrote `course/labs/01-agent-runner-lab.md` and `course/solutions/01-agent-runner-solution.md` as the new Part 1 practice loop. Review confirmed the old missing-tool lab/solution mismatch is gone, all four lab exercises include feedback, L3 checks all four registered tools plus `tool_values == [7, 14]`, and the solution now explains both what each assertion proves and why the design matters for later evidence chains, Workbench timeline UI, and production diagnostics. |

## Verification Target

Run from `redesign/` unless noted:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
```

The web build is not expected to change in Phase R1, but it should be rerun before final completion if docs freshness or package metadata changes create uncertainty.
