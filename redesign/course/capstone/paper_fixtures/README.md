# Capstone Paper Fixtures

Offline paper dataset for the Capstone local paper research assistant.

## Files

- `papers.json`: three deterministic paper records with stable `uri` values.

## Rules

- No network access.
- Content is short and citation-friendly so learners can quote exact sentences.
- URIs use the `paper://` scheme taught in Part 2.
- Adding papers is allowed; keep IDs/URIs stable once referenced by tests.

## Schema

Each paper object has:

| Field | Meaning |
| --- | --- |
| `uri` | Stable offline URI, e.g. `paper://rag-evaluation-survey` |
| `title` | Paper title shown in source panel / claim links |
| `content` | Full local text used by `FakeRetriever` and evidence quotes |
| `year` | Optional metadata for report narrative |
| `topics` | Optional tags for memory/search demos |
