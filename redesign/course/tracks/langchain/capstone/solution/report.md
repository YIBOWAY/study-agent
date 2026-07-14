# Capstone Report (LangChain track, sample)

## Question

Does citation grounding matter for trustworthy RAG evaluation, and what should a local research assistant remember or delegate when producing a cited report?

## Summary

Citation grounding keeps RAG evaluation reports auditable. Local assistants should remember write policies and may delegate focused citation review under budgets.

## Claims (structure)

Each claim is backed by an `EvidenceItem` quote from offline `paper_fixtures/papers.json`, linked via `build_claim_links`. See `trajectory.jsonl` and Workbench snapshot panels for the inspectable trail.

## Production trust

- Diagnostics summarize step kinds and errors.
- JSONL stores the AgentStep trail for replay.
- Approval allows `keyword_*`, denies `shell_*`.
- Sandbox disables network for the Capstone unit path.
