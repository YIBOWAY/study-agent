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

## Cleanup

Remove generated artifacts before final status checks:

```bash
rm -rf .venv .pytest_cache .ruff_cache uv.lock
rm -rf apps/web/node_modules apps/web/dist apps/web/tsconfig.tsbuildinfo
find . -type d -name __pycache__ -prune -exec rm -rf {} +
```

Then check:

```bash
git status --short --branch
git diff --check
```

