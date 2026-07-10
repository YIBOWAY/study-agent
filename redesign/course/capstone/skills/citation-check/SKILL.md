---
name: citation-check
description: Use this skill when a Capstone report needs citation grounding checks against local paper fixtures.
---

# Citation Check Skill

This Capstone skill package teaches progressive disclosure:

1. Load `SKILL.md` first for the summary and workflow.
2. Read `references/citation-rules.md` only when you need the detailed checklist.

## When To Use

- Building Capstone claims from offline paper fixtures.
- Verifying every claim has evidence IDs.
- Preparing claim-source links for Workbench report panels.

## Workflow

1. Retrieve candidate sources with `FakeRetriever`.
2. Extract exact quotes into `Evidence`.
3. Attach evidence IDs to each `Claim`.
4. Call `build_claim_source_links(...)` before accepting a report.
5. Fail closed on unsupported claims.
