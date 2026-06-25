# Course Roadmap

This roadmap turns the comprehensive redesign spec into a learner-facing course
map. It is intentionally high level; executable phase plans live under
`docs/plans/`.

## Shape

The course is organized into eight domains across roughly 24 weeks:

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

- theory,
- handwritten implementation,
- product integration,
- failure lab,
- framework comparison,
- eval gate,
- solution.

Early scaffold chapters may start as a spine, but they must be backfilled before
the related domain is considered complete.

## Current Chapters

- `../../course/chapters/01-agent-kernel-foundations.md`: introduces internal
  messages, event streams, tool runtime, context builder, and the minimal
  `AgentRunner`.

## Near-Term Course Work

- Backfill Chapter 01 into the complete chapter contract.
- Add the Memory and Skills chapter after Phase 3 runtime contracts land.
- Add a Knowledge and Deep Research slice for research planning and report
  synthesis now that initial memory and skill policies are available.
- Keep framework comparisons out of the product runtime path.
