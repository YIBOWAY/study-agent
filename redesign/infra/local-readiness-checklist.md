# Local Readiness Checklist

Run this checklist before publishing a redesign milestone.

## Python

```bash
cd redesign
uv run pytest -q
uv run ruff check .
```

Expected result:

- pytest exits with zero failures,
- Ruff prints `All checks passed!`.

## Web

```bash
cd redesign/apps/web
npm install
npm run build
```

Expected result:

- dependencies install successfully,
- TypeScript and Vite build complete,
- `dist/` is generated locally and then removed before commit.

## Docs Freshness

The full pytest suite includes the docs freshness gate. To run just that gate:

```bash
cd redesign
uv run pytest tests/course/test_docs_freshness.py -q
```

Expected result:

- indexed course/docs Markdown paths all exist,
- missing paths fail with `missing indexed docs paths`.

## Markdown Python Blocks

The full pytest suite executes fenced Python examples from handwritten setup and
Parts 1–7 plus all LangChain track chapter/lab/solution Markdown. Explicit live
examples use `python-live` and stay outside this offline gate. To run it:

```bash
cd redesign
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
```

Expected result:

- selected course Python blocks execute against local `research_core` and
  `langchain_course` APIs,
- marked `Expected output:` text fences match captured stdout.

## Cleanup

Remove generated artifacts before final status checks:

```bash
rm -rf .venv .pytest_cache .ruff_cache
rm -rf apps/web/node_modules apps/web/dist apps/web/tsconfig.tsbuildinfo
find . -type d -name __pycache__ -prune -exec rm -rf {} +
```

Keep `uv.lock`: F3R made it a tracked reproducibility artifact for framework
course dependency groups.

Then check:

```bash
git status --short --branch
git diff --check
```
