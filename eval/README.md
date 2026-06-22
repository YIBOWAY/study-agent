# Evaluation Data

## Files

- `rag_questions.jsonl`
  - one JSON object per line
  - fields: `question`, `expected_substring`, optional `document_id`, optional `reference_answer`

- `agent_topics.jsonl`
  - one JSON object per line
  - fields: `topic`, `expected_keywords`, `mode`, `max_iterations`

## Results

Evaluation scripts write result files under `eval/results/`.

## Scripts

- `python -m scripts.run_rag_eval --cases eval/rag_questions.jsonl --limit 5 --with-llm-judge`
- `python -m scripts.run_agent_eval --mode agent_v2 --limit 5`
