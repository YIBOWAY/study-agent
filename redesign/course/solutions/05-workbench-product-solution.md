# Solution 05: Workbench Product

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

所有 Python snippets 默认从 `redesign/` 运行。

## Focused Test Check

```bash
uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q
```

期望结果：

```text
13 passed
```

如果数量未来增加，以实际测试数为准；关键是 focused workbench tests 必须全部通过。

## Exercise 1 Solution

Shell:

```bash
PYTHONPATH=packages/research_core/src uv run python
```

Python:

```python
from research_core.product import build_demo_workbench_snapshot

snapshot = build_demo_workbench_snapshot()
record = snapshot.to_record()

assert sorted(record.keys()) == [
    "delegation",
    "evals",
    "memory",
    "project",
    "report",
    "run",
    "skills",
    "sources",
    "timeline",
]
assert record["project"]["title"] == "Research Agent Workbench"
assert record["run"]["status"] == "completed"
assert [item["type"] for item in record["timeline"]] == [
    "model_request",
    "tool_call",
    "delegate_start",
    "delegate_finish",
]
assert record["delegation"][0]["role"] == "evidence-reviewer"
```

What this proves:

- `WorkbenchSnapshot` is a product-shaped contract, not one raw runtime object.
- Timeline order is stable.
- Delegation information is already visible to the product layer.

## Exercise 2 Solution

Shell:

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run python
```

Python:

```python
from fastapi.testclient import TestClient
from research_api.main import create_app

client = TestClient(create_app())

health = client.get("/health")
snapshot_response = client.get("/api/workbench/snapshot")
timeline_response = client.get("/api/workbench/timeline")

assert health.status_code == 200
assert health.json() == {
    "status": "ok",
    "service": "research-workbench-api",
}
assert snapshot_response.status_code == 200
assert timeline_response.status_code == 200
assert timeline_response.json() == snapshot_response.json()["timeline"]
```

What this proves:

- FastAPI is only the transport layer.
- `/api/workbench/snapshot` returns the same product record shape as core.
- `/api/workbench/timeline` preserves snapshot timeline order.

## Exercise 3 Solution

```python
data = snapshot_response.json()
data["timeline"][0]["metadata"]["tokens"]["prompt"] = 999
data["sources"][0]["evidence"][0]["claim_ids"].append("mutated")
data["memory"][0]["summary_row"]["tags"].append("mutated")

fresh_data = client.get("/api/workbench/snapshot").json()

assert fresh_data["timeline"][0]["metadata"]["tokens"]["prompt"] == 128
assert fresh_data["sources"][0]["evidence"][0]["claim_ids"] == ["claim_1"]
assert fresh_data["memory"][0]["summary_row"]["tags"] == [
    "citation",
    "reporting",
]
```

What this proves:

- Returned records are plain copies.
- UI-side edits, sorting, filtering, or draft changes do not mutate the core snapshot.
- This is why `to_record()` matters; the API should not expose live internal objects.

## Exercise 4 Solution

```bash
cd apps/web
npm install
npm run build
```

Expected shape of output:

```text
vite ... building client environment for production...
modules transformed.
✓ built
```

Then:

```bash
cd ../..
rg -n "WorkbenchSnapshot|/api/workbench/snapshot|source-pill|fixture" apps/web/src
```

You should find:

- `WorkbenchSnapshot` in `src/types.ts` and `src/App.tsx`.
- `/api/workbench/snapshot` in `src/App.tsx`.
- `fixture` / `api` data-source display logic in `src/App.tsx`.

What this proves:

- React consumes the same record shape that the API returns.
- The web app can build without real provider credentials.
- The fallback fixture is a deterministic product safety net, not a separate data model.

## Final Takeaway

The important lesson is:

```text
Workbench product code starts with a stable snapshot contract, not with UI decoration.
```

FastAPI and React should be replaceable shells around the same product record. If the record is stable, tests, docs, API, and UI can evolve without turning every phase into a framework rewrite.
