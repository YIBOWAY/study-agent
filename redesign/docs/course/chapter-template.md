# Chapter Template

Use this template for course chapters after the initial scaffold.

## Theory

Explain the concept, its vocabulary, and the failure modes that make it matter.

## Handwritten Implementation

Build the smallest useful version from first principles using public redesign
contracts. Keep the implementation offline-first and deterministic.

## Product Integration

Explain how the mechanism will surface in the Research Agent Workbench. Name the
screen, API, timeline event, or domain object it will eventually connect to.

## Failure Lab

Break the mechanism deliberately. The failure should produce an inspectable
runtime artifact such as an event sequence, rejected write, failed eval, or
structured error.

## Framework Comparison

Rebuild or map the same task with a framework only when the comparison teaches a
real tradeoff. Framework code belongs under `course/framework_comparisons/`, not
the product runtime path.

## Eval Gate

Define the command or fixture that proves the chapter still works. Prefer
offline tests, trajectory checks, and deterministic eval records.

## Solution

Provide a complete solution that a learner can run from `redesign/`.
