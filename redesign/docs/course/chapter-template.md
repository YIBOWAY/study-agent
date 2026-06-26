# Chapter Template

Use this template for course chapters after the initial scaffold. A chapter is not beginner-ready just because it is technically correct; it must also make the path of understanding visible.

## Learner Contract

State:

- who the chapter is for,
- what the learner should already know,
- expected time,
- what they will be able to do afterward,
- which earlier chapter, lab, or reference page to read first.

## Plain-Language Mental Model

Explain the mechanism without framework names first. Use the fewest necessary nouns. A learner should be able to paraphrase this section before seeing code.

## Theory

Explain the concept, its vocabulary, and the failure modes that make it matter. Keep vocabulary aligned with `docs/glossary.md` and any course reference glossary.

## Handwritten Implementation

Build the smallest useful version from first principles using public redesign contracts. Keep the implementation offline-first and deterministic.

## Runnable Minimal Example

Provide a copy-pasteable snippet that runs from `redesign/`. Python shell snippets must use:

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Product Integration

Explain how the mechanism will surface in the Research Agent Workbench. Name the screen, API, timeline event, or domain object it will eventually connect to.

## Failure Lab

Break the mechanism deliberately. The failure should produce an inspectable runtime artifact such as an event sequence, rejected write, failed eval, or structured error.

## Framework Comparison

Rebuild or map the same task with a framework only when the comparison teaches a real tradeoff. Framework code belongs under `course/framework_comparisons/`, not the product runtime path. If deferred, say why.

## Eval Gate

Define the command or fixture that proves the chapter still works. Prefer offline tests, trajectory checks, and deterministic eval records.

## Reflection Questions

End with a short checkpoint that forces recall. Questions should test the mechanism, not trivia.

## Solution

Provide a complete solution that a learner can run from `redesign/`. Explain what each assertion proves.
