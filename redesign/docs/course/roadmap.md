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

### Engineer Track

For readers already comfortable with Python projects, pytest, and basic Agent terminology:

1. Skim `../../course/reference/agent-kernel-glossary.md`.
2. Start at `../../course/chapters/01-agent-kernel-foundations.md`.
3. Use labs and solutions as runnable verification material.

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

## Near-Term Course Work

- Add a Memory and Skills chapter after Phase 3 runtime contracts.
- Add a Knowledge and Deep Research slice for research planning and report synthesis now that initial memory and skill policies are available.
- Add framework comparisons only when they teach a real tradeoff, keeping framework code out of the product runtime path.
