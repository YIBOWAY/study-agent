# Lab 05: Workbench Product

## Goal

这个 lab 会带你亲手跑四种情况：

1. 直接 inspect `WorkbenchSnapshot` record。
2. 用 FastAPI TestClient 调 `/api/workbench/snapshot`。
3. 故意 mutate 返回 record，证明 product contract 不会被污染。
4. 构建 React/Vite workbench，确认 UI 能消费这个 shape。

预计时间：45 到 60 分钟。

## Setup

所有命令默认从 `redesign/` 运行：

```bash
cd redesign
```

先确认 Python 侧测试是绿的：

```bash
uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q
```

你应该看到 focused tests 全部通过。

## Exercise 1: Inspect The Snapshot Record

打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴：

```python
from research_core.product import build_demo_workbench_snapshot

snapshot = build_demo_workbench_snapshot()
record = snapshot.to_record()

print(sorted(record.keys()))
print(record["project"]["title"])
print(record["run"]["status"])
print([item["type"] for item in record["timeline"]])
print(record["delegation"][0]["role"])
```

自查：

```python
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
```

## Exercise 2: Call The API With TestClient

退出上一个 shell，重新打开带 API path 的 shell：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run python
```

粘贴：

```python
from fastapi.testclient import TestClient
from research_api.main import create_app

client = TestClient(create_app())

health = client.get("/health")
snapshot_response = client.get("/api/workbench/snapshot")
timeline_response = client.get("/api/workbench/timeline")

print(health.status_code, health.json())
print(snapshot_response.status_code)
print(timeline_response.json()[0]["type"])
```

自查：

```python
assert health.json() == {
    "status": "ok",
    "service": "research-workbench-api",
}
assert snapshot_response.status_code == 200
assert timeline_response.status_code == 200
assert timeline_response.json() == snapshot_response.json()["timeline"]
```

## Exercise 3: Mutate The Returned Record

还在同一个 shell 里，粘贴：

```python
data = snapshot_response.json()
data["timeline"][0]["metadata"]["tokens"]["prompt"] = 999
data["sources"][0]["evidence"][0]["claim_ids"].append("mutated")
data["memory"][0]["summary_row"]["tags"].append("mutated")

fresh_data = client.get("/api/workbench/snapshot").json()

print(fresh_data["timeline"][0]["metadata"]["tokens"]["prompt"])
print(fresh_data["sources"][0]["evidence"][0]["claim_ids"])
print(fresh_data["memory"][0]["summary_row"]["tags"])
```

你应该看到：

```text
128
['claim_1']
['citation', 'reporting']
```

自查：

```python
assert fresh_data["timeline"][0]["metadata"]["tokens"]["prompt"] == 128
assert fresh_data["sources"][0]["evidence"][0]["claim_ids"] == ["claim_1"]
assert fresh_data["memory"][0]["summary_row"]["tags"] == [
    "citation",
    "reporting",
]
```

## Exercise 4: Build The Web Workbench

退出 Python shell，运行：

```bash
cd apps/web
npm install
npm run build
```

你应该看到 Vite build 成功，并且类似：

```text
modules transformed
✓ built
```

回到 `redesign/`：

```bash
cd ../..
```

检查 React 代码确实使用了 snapshot shape 和 API path：

```bash
rg -n "WorkbenchSnapshot|/api/workbench/snapshot|source-pill|fixture" apps/web/src
```

## Reflection

做完以后，回答：

1. 为什么 `apps/api` 需要 `PYTHONPATH=apps/api/src:packages/research_core/src`，而只 import core 的 shell 只需要 `packages/research_core/src`？
2. 为什么 API test client 比手动开 server 更适合作为课程第一步？
3. Exercise 3 证明了 `to_record()` 的哪个产品性质？
4. React fallback fixture 如果缺少 `evals` 或 `skills`，会暴露什么风险？
5. 如果你要给 Workbench 加一个新的 panel，应该先改 Python snapshot contract 还是先写 CSS？
