# Production Readiness Notes

Phase 7 treats production readiness as a set of contracts that can be tested
offline before any real cloud or database is introduced.

## Readiness Boundary

Current production-readiness work includes:

- observability diagnostics from `RunEvent` trajectories,
- append-only JSONL run-event persistence,
- approval policy decisions for tool/action review,
- sandbox policy decisions for path and network access,
- docs freshness checks for course and docs indexes,
- local deployment/readiness instructions.

Current production-readiness work does not include:

- real OAuth or enterprise auth,
- real cloud deployment,
- real database migrations,
- real provider SDKs,
- real A2A transport,
- production secrets management.

Those are deferred until the offline contracts are stable enough to teach and
test clearly.

## Local Verification

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm install && npm run build
git diff --check
```

The Python checks verify runtime, research, memory, skill, delegation, product,
framework-comparison, production, and docs-freshness contracts. The web build
verifies the Workbench TypeScript surface still compiles against its product
record shape.

## Generated Artifacts

The verification commands may create local generated artifacts. Do not commit
them:

- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- `uv.lock`
- `apps/web/node_modules/`
- `apps/web/dist/`
- `apps/web/tsconfig.tsbuildinfo`
- Python `__pycache__/` directories

Local agent/tool state such as `.codegraph/` and `.claude/` is also ignored.

## Deployment Shape

The local product still has two deployable surfaces:

- `apps/api`: FastAPI transport over `research_core.product`.
- `apps/web`: React Workbench consuming the Workbench snapshot API or matching
  deterministic fallback data.

Deployment adapters should keep this direction:

```text
research_core contracts -> research_core.product -> apps/api -> apps/web
```

Do not put domain logic, provider calls, approval shortcuts, persistence
shortcuts, or sandbox exceptions into FastAPI handlers or React components.

## Readiness Questions

Before adding real infrastructure, answer these with tests or docs:

- Observability: can a run explain what happened and where it failed?
- Persistence: can event records be appended and read back without mutation?
- Approval: can a risky action be blocked or routed to human review?
- Sandbox: can file/network boundaries be explained before execution?
- Freshness: can learners trust that indexed course/docs paths exist?

