# Capstone Report (LangChain track, sample)

## Question

Does citation grounding matter for trustworthy RAG evaluation, and what should a local research assistant remember or delegate when producing a cited report?

## Summary

Citation grounding keeps RAG evaluation reports auditable. Local assistants should remember write policies and may delegate focused citation review under budgets.

## Claims (structure)

Each claim is backed by an `EvidenceItem` quote from offline
`paper_fixtures/papers.json`. A real `BaseRetriever` selects `Document` objects,
then `build_claim_links` links the evidence. See `trajectory.jsonl` and the
Workbench snapshot panels for the inspectable trail.

## Production trust

- A deterministic `BaseChatModel` drives the real model → tool → model loop.
- LangChain callbacks capture model/tool lifecycle events; diagnostics summarize
  the stable `AgentStep` contract.
- JSONL stores the `AgentStep` trail for replay.
- A pre-tool approval hook allows `keyword_*` and blocks `shell_*` before side
  effects can execute.
- Sandbox disables network for the Capstone unit path.
