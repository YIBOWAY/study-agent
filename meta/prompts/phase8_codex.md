# Phase 8（工程化部署 / 前端 / CI）— Codex GPT-5.5 长任务 Prompt

> 学习方案对照：Phase 8（工程化、部署与生产落地）
> 大项目里程碑：里程碑 8（部署就绪 + Docker Compose + 前端 + API 文档）
> 前置：Phase 7 已完成（~240 tests passing）

---

## 任务总览

把研究助手 Agent 平台从"能跑的本地项目"升级为"可一键启动、可访问、可被其他工程师评审的产品"。这是简历项目的最终形态。

### 学习目标
- SSE/Streaming 流式输出（FastAPI StreamingResponse）
- Docker 化（多 stage 构建 + Docker Compose 编排）
- 轻量级前端（Streamlit，避免引入 React/Vue 复杂度）
- GitHub Actions CI（自动跑 pytest）
- API 文档增强（OpenAPI tags / 示例 / 描述）

### 不做什么
- 不做 K8s（Docker Compose 足够展示）
- 不做云部署脚本（README 中给指引即可）
- 不做完整鉴权系统（只加一个简单的 API Key 中间件作为示意）
- 不引入 React/Vue（Streamlit 即可演示）

---

## 项目当前状态

```
8w-plan/
├── app/                        # ~240 tests, 8+ routers
├── data/                       # qdrant data, memory, traces
├── eval/                       # eval datasets + results
├── scripts/
├── tests/
├── requirements.txt
├── pytest.ini
└── .env / .env.example
```

依赖外部服务（生产时需要）：
- Qdrant: `http://localhost:6333`
- xairouter LLM API
- Cohere Rerank API
- Tavily Search API

---

## Part A: SSE 流式输出

### A.1 LLMService 增加 stream 方法

```python
# app/services/llm_service.py 新增方法（不改既有 chat()）:
#
# async def chat_stream(
#     self,
#     user_message: str,
#     system_prompt: str | None = None,
# ) -> AsyncIterator[str]:
#     """
#     调用 OpenAI 兼容流式接口（stream=True），逐 token yield
#     使用 httpx AsyncClient.stream() 处理 SSE
#     解析每行 "data: {...}" 提取 delta.content
#     遇到 "data: [DONE]" 终止
#     异常时 yield 一段错误标记并结束（不抛异常给调用方）
#     """
```

### A.2 新增 `/api/v1/chat/stream` 端点

```python
# app/api/routes/chat.py 追加:
#
# @router.post("/chat/stream")
# async def chat_stream_endpoint(
#     payload: ChatRequest,
#     llm: LLMService = Depends(...),
# ):
#     async def event_stream():
#         async for chunk in llm.chat_stream(payload.message, payload.system_prompt):
#             # SSE 格式: "data: <json>\n\n"
#             yield f"data: {json.dumps({'content': chunk})}\n\n"
#         yield "data: [DONE]\n\n"
#     return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### A.3 Research streaming（可选但推荐）

```python
# 给 /api/v1/research 增加 ?stream=true 选项
# 流式输出每个 LangGraph 节点完成时的 step 事件
# 用 graph.astream() 而非 graph.ainvoke()
# 每个 chunk 是一个 SSE 事件: data: {"node": "search", "summary": "..."}
```

---

## Part B: API Key 中间件（最简鉴权示意）

### B.1 Settings 扩展

```python
api_key_required: bool = False        # 默认关闭，不破坏开发体验
api_key: str = ""                     # 客户端在 Header "X-API-Key" 中提供
```

### B.2 中间件 — `app/core/auth.py`（新增）

```python
# from fastapi import Header, HTTPException
#
# async def require_api_key(
#     x_api_key: str | None = Header(default=None),
#     settings: Settings = Depends(get_settings),
# ) -> None:
#     if not settings.api_key_required:
#         return
#     if not x_api_key or x_api_key != settings.api_key:
#         raise HTTPException(status_code=401, detail="invalid api key")
#
# 用法: 在敏感 router 上加 dependencies=[Depends(require_api_key)]
# 仅对 /research /tools /memory 启用，/health 永远开放
```

### B.3 测试

`tests/test_auth.py`（新增）：
- `test_no_api_key_when_not_required`: 默认配置下无 key 仍通过
- `test_api_key_required_blocks_missing_key`: 启用后无 key 返回 401
- `test_api_key_required_accepts_valid_key`

---

## Part C: 前端 — Streamlit Demo

### C.1 目录结构

```
8w-plan/
└── frontend/
    ├── app.py                  # 主入口
    ├── pages/
    │   ├── 1_💬_Chat.py
    │   ├── 2_📚_RAG.py
    │   ├── 3_🔬_Research.py
    │   └── 4_📊_Observability.py
    ├── utils/
    │   ├── api_client.py       # 用 httpx 调本项目 API
    │   └── streaming.py        # 处理 SSE 解析
    └── README.md
```

### C.2 核心页面

**`Chat.py`**: 文本输入 + 流式输出展示
**`RAG.py`**: 上传 PDF → 调 `/rag/ingest` → 输入问题 → 调 `/rag/ask`
**`Research.py`**: 输入 topic + 选择 mode（4 种）+ 显示报告 + 显示 step trace 时间线
**`Observability.py`**: 调 `/observability/traces` 和 `/observability/cost`，用 Streamlit 表格 + 图表展示

### C.3 配置

`frontend/app.py` 通过环境变量 `BACKEND_URL` 指向后端（默认 `http://localhost:8000`）。

### C.4 新增 requirements

新增 `frontend/requirements.txt`（与后端独立）：
```
streamlit>=1.32.0
httpx>=0.27.0
pandas>=2.0.0
```

> 注意：后端 `requirements.txt` 不要混入 streamlit。前端是独立部署单元。

---

## Part D: Docker 化

### D.1 后端 Dockerfile — `Dockerfile`（项目根）

```dockerfile
# Multi-stage build
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY app ./app
COPY scripts ./scripts
COPY pytest.ini .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### D.2 前端 Dockerfile — `frontend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY frontend ./
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

### D.3 Docker Compose — `docker-compose.yml`（项目根）

```yaml
version: "3.9"

services:
  qdrant:
    image: qdrant/qdrant:v1.11.3
    ports: ["6333:6333"]
    volumes:
      - qdrant_data:/qdrant/storage

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports: ["8000:8000"]
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL:-https://api.xairouter.com/v1}
      - LLM_MODEL=${LLM_MODEL:-gpt-5.4}
      - EMBEDDING_API_KEY=${EMBEDDING_API_KEY}
      - RERANK_API_KEY=${RERANK_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - QDRANT_URL=http://qdrant:6333
      - TRACING_DB_PATH=/data/traces.db
      - MEMORY_DATA_DIR=/data/memory
    volumes:
      - backend_data:/data
    depends_on:
      - qdrant

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports: ["8501:8501"]
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend

volumes:
  qdrant_data:
  backend_data:
```

### D.4 `.dockerignore`

```
.git
.venv
.review-venv
__pycache__
*.pyc
.pytest_cache
.ruff_cache
data/
docs/
node_modules
```

### D.5 `.env.example` 扩展

确保所有必需的环境变量都列出来（LLM_API_KEY / EMBEDDING_API_KEY / RERANK_API_KEY / TAVILY_API_KEY / API_KEY / API_KEY_REQUIRED 等）。

---

## Part E: CI — GitHub Actions

### E.1 `.github/workflows/test.yml`（项目根，注意是仓库根而非 8w-plan/）

> 如果项目仓库根就是 `8w-plan/`，路径相应调整。

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - name: Install deps
        working-directory: 8w-plan
        run: |
          pip install -r requirements.txt
      - name: Run tests
        working-directory: 8w-plan
        env:
          LLM_API_KEY: dummy-for-tests
          EMBEDDING_API_KEY: dummy-for-tests
        run: |
          python -m pytest -q
```

### E.2 `.github/workflows/lint.yml`（可选）

```yaml
name: lint
on: [push, pull_request]
jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install ruff
      - run: ruff check 8w-plan/app 8w-plan/tests
```

---

## Part F: API 文档增强

### F.1 OpenAPI tags

在 `app/main.py` 中：

```python
app = FastAPI(
    title=settings.app_name,
    description="Research Agent Platform — RAG + Tool Use + Multi-Agent + MCP",
    version="0.8.0",
    openapi_tags=[
        {"name": "health", "description": "Health checks"},
        {"name": "chat", "description": "Basic LLM chat (with optional streaming)"},
        {"name": "rag", "description": "RAG ingest / search / ask"},
        {"name": "tools", "description": "Function calling with built-in tools"},
        {"name": "research", "description": "Research agent (workflow / agent / agent_v2 / multi_agent)"},
        {"name": "memory", "description": "Memory inspection and management"},
        {"name": "mcp", "description": "MCP server inspection"},
        {"name": "eval", "description": "Evaluation runs"},
        {"name": "observability", "description": "Traces and cost"},
    ],
)
```

每个 router 上加 `tags=["xxx"]`。

### F.2 端点示例

为关键端点（`/research`, `/rag/ask`）添加 `examples` 字段（FastAPI 支持在 Body() 中提供示例 payload）。

### F.3 README 增强

`README.md`（项目根）必须包含：

1. 项目一句话介绍 + 架构图（用 Mermaid）
2. 已实现的能力列表（Phase 0-8）
3. 快速开始：
   - 本地: `pip install -r requirements.txt` + 配置 .env + `uvicorn app.main:app`
   - Docker: `docker-compose up`
4. API 概览表格（端点、方法、功能）
5. 4 种 research mode 的对比说明
6. 评估如何运行: `python -m scripts.run_agent_eval --mode agent_v2`
7. 测试如何运行: `python -m pytest -q`
8. 项目结构图
9. 技术决策说明：
   - 为什么不用 langchain-openai
   - 为什么用 LangGraph 但不用 LangChain LLM 封装
   - 为什么 Memory 用 JSON 不用 Redis
   - 为什么 Guardrails 用规则不用 NeMo
10. License + 致谢

---

## Part G: 测试要求

新增测试：

**`tests/test_chat_stream.py`**
- mock httpx AsyncClient.stream，模拟 SSE 响应
- `test_chat_stream_yields_chunks`
- `test_chat_stream_terminates_on_done`
- `test_chat_stream_handles_error`

**`tests/test_chat_stream_endpoint.py`**
- `test_stream_endpoint_returns_sse`
- `test_stream_endpoint_content_type_correct`

**`tests/test_auth.py`**（如 B.3）

**Docker / CI 不进 pytest**，靠 manual + GitHub Actions 验证。

---

## 实现顺序

1. SSE 部分: LLMService.chat_stream + /chat/stream + 测试
2. Auth 部分: Settings + auth.py + 集成到敏感 router + 测试
3. 前端: frontend/ 完整目录（不含测试，是 demo）
4. Docker: Dockerfile (backend) + frontend Dockerfile + docker-compose.yml + .dockerignore
5. CI: .github/workflows/test.yml
6. API tags + 描述完善
7. README.md（项目根）大改
8. 全量 `python -m pytest -q` —— ~240 + ~10 = ~250
9. Manual smoke: `docker-compose up` 跑一次端到端
10. （可选）push 到 GitHub 验证 Actions 跑通

---

## 完成标准

- [ ] 所有旧测试通过 + 新增 SSE / Auth 测试通过
- [ ] `/api/v1/chat/stream` 能流式返回（curl 验证）
- [ ] `docker-compose up` 启动 qdrant + backend + frontend 三服务
- [ ] 浏览器访问 `http://localhost:8501` 看到前端 4 个页面
- [ ] 浏览器访问 `http://localhost:8000/docs` 看到分组的 OpenAPI 文档
- [ ] GitHub Actions CI 配置正确（pytest 在 CI 环境跑通）
- [ ] README 包含所有要素 + 架构图
- [ ] `.env.example` 列出所有必需变量
- [ ] 不引入除 Streamlit + pandas 之外的新后端依赖

---

## Commit Message 模板

```
feat(phase8): production-ready deployment

Streaming:
- Add LLMService.chat_stream using httpx SSE handling
- Add /api/v1/chat/stream endpoint

Auth:
- Add optional X-API-Key middleware (disabled by default)
- Apply to /research /tools /memory routers

Frontend:
- Add Streamlit demo with 4 pages: Chat / RAG / Research / Observability
- Independent requirements.txt and Dockerfile

Deployment:
- Multi-stage backend Dockerfile
- docker-compose.yml orchestrating qdrant + backend + frontend
- .dockerignore + .env.example completion

CI:
- Add GitHub Actions workflow for pytest
- Add ruff lint workflow

Docs:
- Tag-grouped OpenAPI documentation
- Comprehensive README with architecture diagram and quickstart

Tests: ~240 → ~250 (all passing)
Refs: docs/Agent开发完整学习方案.md Phase 8 / Milestone 8
```

---

## 设计哲学

**为什么不上 K8s？**

简历项目的"工程化"展示重点是"可一键启动 + 易于评审"。K8s 配置量大，YAML 复杂，对评审者不友好。Docker Compose 同时演示了多服务编排、网络、卷管理三个核心概念，足够。

**为什么 Streamlit 而非 React？**

前端不是本项目的能力展示重点。Streamlit 用 50 行 Python 就能做出像样的 demo，让评审者快速感受功能。如果你本身有前端能力，可以单独再做 React 版本作为加分项。

**为什么 API Key 默认关闭？**

开发体验优先。生产部署时把 `API_KEY_REQUIRED=true` 设到 .env 即可。这是合理的"开发友好 / 生产严格"切换模式。
