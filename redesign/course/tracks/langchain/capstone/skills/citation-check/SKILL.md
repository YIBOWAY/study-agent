---
name: citation-check
description: Use this skill when a LangChain Capstone report needs citation grounding checks against local paper fixtures.
---

# Citation Check Skill (LangChain track)

Progressive disclosure:

1. Load `SKILL.md` first for the summary and workflow.
2. Read `references/citation-rules.md` only when you need the detailed checklist.

## When To Use

- Building Capstone claims from offline paper fixtures.
- Verifying every claim has evidence IDs.
- Preparing claim links for Workbench report panels.

## Workflow

1. Retrieve candidate sources through `LangChainPaperRetriever(BaseRetriever)`.
2. Extract exact quotes into `EvidenceItem`.
3. Attach evidence IDs to each `ClaimItem`.
4. Call `build_claim_links(...)` before accepting a report.
5. Fail closed on unsupported claims.
