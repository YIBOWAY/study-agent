# Chapter 05: Workbench Product

## Goal

这一章补上 Phase 5 的学习路径：前面几章已经有 runtime、research、memory、skills 和 delegation，为什么还需要一个 `WorkbenchSnapshot` product layer，以及它怎样连接 FastAPI 和 React。

学完以后，你应该能看懂这条主线：

```text
research_core runtime/domain objects
  -> research_core.product.WorkbenchSnapshot
  -> FastAPI read endpoints
  -> React Workbench panels
```

预计时间：60 到 75 分钟。

## Before You Start

请先完成：

- `02-research-core-foundations.md`
- `03-memory-and-skills.md`
- `04-multi-agent-delegation.md`

这一章不会做登录、数据库、真实模型、真实检索或 websocket streaming。Phase 5 只建立第一个本地、确定性、可测试的产品 surface。

## The Idea In Plain Language

Product layer 不是把后端对象原样丢给前端。

前面几章的对象是给工程系统用的：

- `RunEvent` 适合 runtime 记录轨迹；
- `Source`、`Evidence`、`Claim`、`Report` 适合研究证据链；
- `MemoryRecord` 适合记忆策略；
- `DelegationTask` 和 `DelegationResult` 适合 child agent orchestration。

但是产品界面需要的是另一种东西：一个稳定的页面快照。

Workbench 打开时，它不想猜“这个对象来自哪个模块”。它只想拿到一个清楚的 record：

```text
project, run, timeline, delegation, sources, report, memory, skills, evals
```

这就是 `WorkbenchSnapshot` 的职责：把内部对象整理成 API 和 UI 都能消费的 JSON-compatible record。

## Why Product Adapters Sit In The Middle

`research_core` 不能直接 import FastAPI 或 React。原因很简单：

```text
core 如果依赖产品框架，测试、课程、CLI、未来 worker 都会被框架绑住。
```

所以 Phase 5 分三层：

| Layer | Folder | Job |
| --- | --- | --- |
| Core product contract | `packages/research_core/src/research_core/product` | 把 runtime/domain 对象变成稳定 snapshot |
| API transport | `apps/api` | 用 FastAPI 暴露 read-only endpoint |
| Web UI | `apps/web` | 用 React 渲染 workbench panels |

边界方向只能往下：

```text
apps/web -> apps/api contract -> research_core.product -> research_core runtime/domain
```

不能反过来：

```text
research_core -> FastAPI
research_core -> React
research_core -> provider SDK
```

## Snapshot Is Not Raw Runtime State

`WorkbenchSnapshot` 和 raw object 最大的区别是：它是产品视角的组合。

| Raw Object | Product Snapshot View |
| --- | --- |
| `RunEvent` | `WorkbenchTimelineItem`，带 title、summary、metadata |
| `Source` + `Evidence` | `WorkbenchSourceItem`，证据和 claim ids 放在同一 panel record |
| `Report` + `ClaimSourceLink` | `WorkbenchReport`，报告和引用链一起给编辑器 |
| `MemoryRecord` | `WorkbenchMemoryItem`，额外提供 `summary_row` 给列表 |
| skill package info | `WorkbenchSkillItem`，额外提供 resource count |
| eval result | `WorkbenchEvalItem`，额外提供 score/status summary |
| delegation result | `WorkbenchDelegationNode`，给 delegation tree |

它也做三件很产品化的事：

1. 校验：blank id/title、坏 metadata、越界 score 会被拒绝。
2. 冻结：内部 dataclass 是 frozen，避免被随手改坏。
3. 复制：`to_record()` 每次返回 plain copy，前端或调用方改 record 不会污染 snapshot。

## Minimal Example

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴：

```python
from research_core.product import build_demo_workbench_snapshot

snapshot = build_demo_workbench_snapshot()
record = snapshot.to_record()

print(record.keys())
print([item["type"] for item in record["timeline"]])
print(record["sources"][0]["evidence"][0]["quote"])
print(record["report"]["claim_source_links"][0]["source_title"])
print(record["memory"][0]["summary_row"])
```

你应该看到这些 panel 都在：

```text
dict_keys(['project', 'run', 'timeline', 'delegation', 'sources', 'report', 'memory', 'skills', 'evals'])
['model_request', 'tool_call', 'delegate_start', 'delegate_finish']
Every report claim keeps an evidence link back to a source.
Workbench Contract Notes
{'id': 'mem_citation_rule', 'title': 'Citation rule', ...}
```

注意：这个例子没有 API key、没有网络、没有真实模型。因为 Phase 5 要先证明产品 contract 本身能离线运行。

## API Boundary

FastAPI app 在 `apps/api/src/research_api/main.py`。

它暴露三个 endpoint：

| Endpoint | Meaning |
| --- | --- |
| `/health` | 服务是否可用 |
| `/api/workbench/snapshot` | 完整 workbench snapshot |
| `/api/workbench/timeline` | 只取 timeline records |

用 TestClient 检查：

```python
from fastapi.testclient import TestClient
from research_api.main import create_app

client = TestClient(create_app())
response = client.get("/api/workbench/snapshot")
data = response.json()

print(response.status_code)
print(data["project"]["title"])
print([item["type"] for item in data["timeline"]])
```

这条路径依然不需要真实 provider。API 只是 transport，它不应该改变 snapshot contract。

## React Workbench Boundary

React app 在 `apps/web`。

它做两件事：

1. fetch `/api/workbench/snapshot`。
2. 如果 API 不可用，就用同一个 `WorkbenchSnapshot` TypeScript shape 的 fallback fixture。

这点很关键：fallback 不是“随便造点假数据”。它必须和 API record 形状一致，否则 UI 通过了，真实 API 一接就坏。

Vite dev server 会把 `/api` proxy 到 FastAPI：

```text
React -> /api/workbench/snapshot -> FastAPI -> WorkbenchSnapshot.to_record()
```

## How To Inspect The Workbench Panels

打开 Workbench 时，不要只看“页面好不好看”。要问每个 panel 背后的 contract 是什么：

| Panel | What To Inspect |
| --- | --- |
| Task composer | `run.question` 和用户下一次任务输入 |
| Run timeline | `timeline` 顺序是否保留 runtime event order |
| Delegation tree | child run、role、status 是否可复盘 |
| Sources and evidence | quote、location、claim ids 是否能连回 report claim |
| Report editor | report summary 和 claim-source links 是否还在 |
| Memory panel | memory kind、importance、tags、summary_row |
| Skills panel | skill name、status、resource count |
| Eval panel | metric、status、score、details |

如果某个 panel 只展示漂亮文字，但丢了 id、source link、event type 或 eval metric，它就不是一个可审计的 research workbench。

## Failure Lab Preview

故意改坏返回的 record：

```python
record = snapshot.to_record()
record["timeline"][0]["metadata"]["tokens"]["prompt"] = 999

fresh = snapshot.to_record()
print(fresh["timeline"][0]["metadata"]["tokens"]["prompt"])
```

你应该看到：

```text
128
```

这说明 `to_record()` 返回的是独立 plain copy。产品层可以被 UI 编辑、过滤、排序，但不会污染 core snapshot。

再故意创建坏 eval：

```python
from research_core.product import WorkbenchEvalItem

WorkbenchEvalItem(
    id="eval_bad",
    title="Bad eval",
    metric="coverage",
    status="passed",
    score=1.5,
)
```

你应该看到：

```text
ValueError: score must be a number between 0 and 1
```

这是 product contract 在保护 UI：如果 score 可以是 1.5，前端百分比、颜色和 eval gate 都会开始撒谎。

## Eval Gate

项目级检查：

```bash
uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q
uv run ruff check packages/research_core/src/research_core/product apps/api/src tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py
cd apps/web && npm install && npm run build
```

核心自查：

```python
record = build_demo_workbench_snapshot().to_record()
assert record["report"]["claim_source_links"][0]["evidence_id"] == record["sources"][0]["evidence"][0]["id"]
assert [item["type"] for item in record["timeline"]] == [
    "model_request",
    "tool_call",
    "delegate_start",
    "delegate_finish",
]
```

## Checkpoint

继续 Phase 6 前，用自己的话回答：

1. 为什么 `WorkbenchSnapshot` 不应该直接放在 FastAPI app 里？
2. 为什么 React fallback fixture 必须和 API record 使用同一个 shape？
3. `to_record()` 为什么要返回 plain copy，而不是内部对象本身？
4. Workbench 里哪两个 panel 最依赖 claim-source link？
5. 如果未来加数据库，应该接在哪一层，而不是塞进 `research_core`？
