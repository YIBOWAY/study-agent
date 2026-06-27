# Course Roadmap

This roadmap turns the comprehensive redesign spec into a learner-facing course map. Executable phase plans live under `docs/plans/`; this file explains how those phases become teachable material.

## Course Promise

The course should teach Agent engineering as an inspectable system, not as prompt folklore. Every learner-facing chapter should explain the mechanism in plain language, run offline, expose the event trail, include a deliberate failure case, and end with a concrete eval gate.

## Tracks

### Beginner Track

For learners who know some Python but are new to Agent engineering:

1. `../../course/README.md`
2. `../../course/reference/python-terminal-primer.md`
3. `../../course/reference/agent-kernel-glossary.md`
4. `../../course/chapters/00-before-agent-kernel.md`
5. `../../course/labs/00-environment-check.md`
6. `../../course/solutions/00-environment-check-solution.md`
7. `../../course/chapters/01-agent-kernel-foundations.md`
8. `../../course/labs/01-agent-runner-lab.md`
9. `../../course/solutions/01-agent-runner-solution.md`
10. `../../course/chapters/02-research-core-foundations.md`
11. `../../course/labs/02-source-evidence-claim-lab.md`
12. `../../course/solutions/02-source-evidence-claim-solution.md`
13. `../../course/chapters/03-memory-and-skills.md`
14. `../../course/labs/03-memory-skill-runtime-lab.md`
15. `../../course/solutions/03-memory-skill-runtime-solution.md`
16. `../../course/chapters/04-multi-agent-delegation.md`
17. `../../course/labs/04-delegation-runtime-lab.md`
18. `../../course/solutions/04-delegation-runtime-solution.md`
19. `../../course/chapters/05-workbench-product.md`
20. `../../course/labs/05-workbench-product-lab.md`
21. `../../course/solutions/05-workbench-product-solution.md`
22. `../../course/chapters/06-framework-comparisons.md`
23. `../../course/labs/06-framework-comparisons-lab.md`
24. `../../course/solutions/06-framework-comparisons-solution.md`

### Engineer Track

For readers already comfortable with Python projects, pytest, and basic Agent terminology:

1. Skim `../../course/reference/agent-kernel-glossary.md`.
2. Start at `../../course/chapters/01-agent-kernel-foundations.md`.
3. Continue through Chapters 02-06 when reading Phase 2-6 source modules.
4. Use labs and solutions as runnable verification material.

## Shape

The full course is organized into eight domains across roughly 24 weeks:

1. Agent Engineering Foundations
2. Agent Kernel and Context Engine
3. Memory and Stateful Agents
4. Tools, Skills, MCP, and Extensions
5. Knowledge and Deep Research
6. Delegation and Multi-Agent Systems
7. Harness and Loop Engineering
8. Frameworks, Product, and Production

## Chapter Contract

Every full chapter should include:

- learner level, prerequisites, and expected time,
- a plain-language mental model,
- theory,
- handwritten implementation,
- product integration,
- failure lab,
- framework comparison or an explicit deferral,
- eval gate,
- reflection questions,
- solution.

Early scaffold chapters may start as a spine, but they must be backfilled before the related domain is considered complete.

## Current Materials

- `../../course/README.md`: learner entrypoint, track selection, commands, and common stuck points.
- `../../course/reference/python-terminal-primer.md`: minimal terminal and Python concepts needed for the course.
- `../../course/reference/agent-kernel-glossary.md`: plain-language Agent kernel vocabulary.
- `../../course/chapters/00-before-agent-kernel.md`: pre-kernel mental model.
- `../../course/labs/00-environment-check.md`: local environment readiness check.
- `../../course/solutions/00-environment-check-solution.md`: expected environment-check outputs.
- `../../course/chapters/01-agent-kernel-foundations.md`: first-principles Agent kernel chapter.
- `../../course/labs/01-agent-runner-lab.md`: hands-on AgentRunner trajectory lab.
- `../../course/solutions/01-agent-runner-solution.md`: annotated lab solution.
- `../../course/chapters/02-research-core-foundations.md`: source/evidence/claim/report evidence-chain chapter.
- `../../course/labs/02-source-evidence-claim-lab.md`: hands-on Research Core lab.
- `../../course/solutions/02-source-evidence-claim-solution.md`: annotated Research Core solution.
- `../../course/chapters/03-memory-and-skills.md`: memory policy and skill progressive-disclosure chapter.
- `../../course/labs/03-memory-skill-runtime-lab.md`: hands-on MemoryEngine and SkillRuntime lab.
- `../../course/solutions/03-memory-skill-runtime-solution.md`: annotated memory/skill solution.
- `../../course/chapters/04-multi-agent-delegation.md`: child context isolation, budget, and delegation-event chapter.
- `../../course/labs/04-delegation-runtime-lab.md`: hands-on DelegationRuntime lab.
- `../../course/solutions/04-delegation-runtime-solution.md`: annotated delegation solution.
- `../../course/chapters/05-workbench-product.md`: product adapter, WorkbenchSnapshot, FastAPI, and React Workbench chapter.
- `../../course/labs/05-workbench-product-lab.md`: hands-on WorkbenchSnapshot/API/web build lab.
- `../../course/solutions/05-workbench-product-solution.md`: annotated product integration solution.
- `../../course/chapters/06-framework-comparisons.md`: framework comparison method chapter.
- `../../course/labs/06-framework-comparisons-lab.md`: hands-on recommendation matrix lab.
- `../../course/solutions/06-framework-comparisons-solution.md`: annotated framework comparison solution.
- `../../course/framework_comparisons/reports/echo-tool-task.md`: shared echo-tool task report.
- `../../course/framework_comparisons/reports/recommendation-matrix.md`: current recommendation matrix report.

## Near-Term Course Work

- Keep future phase plans honest: if a phase introduces a new learner-facing runtime concept, the phase plan must either add course material or explicitly defer it in this roadmap.
- Add a Knowledge and Deep Research slice for research planning and report synthesis now that initial memory and skill policies are available.
- Keep Phase 5 product/workbench lessons aligned with `WorkbenchSnapshot`, `research_api`, and `apps/web` as the product surface evolves.
- Keep Phase 6 framework comparisons tied to real task tradeoffs, keeping framework code out of the product runtime path.
