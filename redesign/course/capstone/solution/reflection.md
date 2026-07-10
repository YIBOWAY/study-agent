# Capstone Reflection

This reflection models criterion 6 of the Capstone rubric. When you write your own, keep the same shape: **chose / rejected / because**.

## Decision 1 — Compose public contracts instead of a new mega-module

- **Chose:** Capstone solution code under `course/capstone/solution/` that imports public `research_core` APIs from Parts 1-7.
- **Rejected:** Adding a new `research_core.capstone` product package or copying private helpers.
- **Because:** Capstone is a teaching integration exam, not a product feature. Keeping it as a course artifact preserves the dual-layer boundary (course vs product) and forces learners to use the same contracts they already tested.

## Decision 2 — Evidence chain before narrative polish

- **Chose:** Build `Source -> Evidence -> Claim -> Report -> ClaimSourceLink` first, then write the human-readable `report.md`.
- **Rejected:** Free-writing a beautiful markdown report and reverse-fitting citations later.
- **Because:** Unsupported claims are research defects. The mapping function fails closed when evidence IDs are missing; narrative text cannot repair a broken chain.

## Decision 3 — Honesty about declarative role fields and non-auto events

- **Chose:** Use `filter_tools_for_role(...)` in the child factory, load skills/memory explicitly, and document that `skill_names` / `memory_kinds` are declarative until wired. Do not emit fake MEMORY_*/SKILL_* events.
- **Rejected:** Pretending role labels auto-load skills/memory, or inventing event types the runner does not produce.
- **Because:** Capstone must reinforce course honesty. A greener demo that lies about wiring teaches the wrong production habit.

## Decision 4 — Production trust evidence is part of the deliverable

- **Chose:** Ship diagnostics, JSONL trajectory, approval allow/deny, network-disabled sandbox decisions, and explicit `SandboxPolicy.runtime_decision(...)` checks for under/over budget elapsed time.
- **Rejected:** Treating Part 7 as optional garnish after a pretty answer, or configuring `max_runtime_seconds` without calling `runtime_decision` (the inspectable-only trap).
- **Because:** Part 7's forward contract for Capstone is explicit: a report without replay/audit/policy evidence is not ready to hand to a research team. Setting a runtime limit without exercising the decision API would re-teach the auto-kill myth.

## Decision 5 — Stay offline with fixtures and fakes

- **Chose:** `paper_fixtures/papers.json` + `FakeRetriever` + `FakeModel`.
- **Rejected:** Live Semantic Scholar / provider calls for "more realism".
- **Because:** Offline determinism is what makes Capstone testable, reviewable, and fair across machines. Realism without replay is a demo, not an engineering artifact.

## What I Would Change Next (optional stretch)

1. Add an eval that checks quotes are literal substrings of `Source.content`.
2. Wire a product adapter that turns Capstone `WorkbenchSnapshot` into the live FastAPI demo without inventing a second data model.
3. Emit optional custom timeline notes for memory/skill steps without overloading reserved MEMORY_*/SKILL_* event semantics until the runtime owns them.
