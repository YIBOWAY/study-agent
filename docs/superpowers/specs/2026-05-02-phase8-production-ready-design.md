# Phase 8 Production-Ready Design

## Goal

把当前本地可运行的研究助手平台，升级成可流式输出、可容器化启动、带前端演示、可跑 CI、文档更完整的可评审项目。

## Scope

Phase 8 包含五块：

1. SSE 流式聊天
2. 简单 API Key 保护
3. Streamlit 演示前端
4. Docker / Docker Compose / GitHub Actions
5. OpenAPI 与 README 强化

不做：

- K8s
- 云部署脚本
- 完整鉴权体系
- React / Vue 前端

## Current Constraints

- 当前后端接口和测试已经扩展到 Phase 7，基线是 `252 passed`
- 工作区是脏的，包含大量尚未提交的 Phase 5/6/7 变更，不能回退或覆盖
- 现有核心服务已经带可选 guardrails / tracing，Phase 8 需要在不破坏既有调用的前提下继续扩展
- 真实环境里 Cohere rerank 仍可能返回 `403`，但已有 fail-soft，不应阻塞部署层改造

## Architecture Decisions

### 1. Streaming

采用最小侵入方案：

- 在 `LLMService` 新增 `chat_stream()`，不改现有 `chat()`
- 直接用 `httpx.AsyncClient.stream()` 处理 OpenAI 兼容 SSE
- 路由层新增 `/api/v1/chat/stream`
- 先把聊天流式能力做稳，再给 research 增加一个轻量级 `stream=true`，只输出步骤事件，不流式输出完整 token

原因：

- 这样不会破坏已有 `/chat`
- 测试边界清晰，SSE 解析和 SSE 路由可分别验证
- research 流式如果直接改为 token 流，会明显扩大改动面，不适合这轮

### 2. Auth

采用依赖函数而不是全局中间件：

- 新增 `app/core/auth.py`
- 用 `Depends(require_api_key)` 挂到 `research` / `tools` / `memory`
- `health` 和基础 `chat` 保持开放

原因：

- 改动面小
- 能表达“仅敏感接口需要 key”
- 与用户要求一致，默认关闭，不影响本地开发和现有测试

### 3. Frontend

前端单独放到 `frontend/`：

- `app.py` 做入口
- `pages/` 做 4 个页面
- `utils/api_client.py` 集中处理 API 调用
- `utils/streaming.py` 解析后端 SSE

原因：

- 保持后端依赖干净
- Docker 部署时前后端能独立构建
- Streamlit 适合快速演示，不需要额外 JS 工程化

### 4. Deployment

部署产物分四层：

- 根目录 `Dockerfile`：后端
- `frontend/Dockerfile`：前端
- 根目录 `docker-compose.yml`：编排 qdrant + backend + frontend
- 根目录 `.dockerignore`

CI 采用最小两条 workflow：

- `test.yml` 跑 pytest
- `lint.yml` 跑 ruff

### 5. API Docs

文档增强分两部分：

- `main.py` 增加 title / description / version / tags
- 关键路由增加 examples 和更清晰的 tags

README 重写为“评审友好版”：

- 一句话介绍
- Mermaid 架构图
- 能力列表
- 本地启动和 Docker 启动
- API 总览
- research 模式对比
- 评估、测试、技术决策说明

## File Plan

### Backend

- Modify: `app/services/llm_service.py`
- Modify: `app/api/routes/chat.py`
- Modify: `app/api/routes/research.py`
- Modify: `app/core/config.py`
- Create: `app/core/auth.py`
- Modify: `app/main.py`

### Frontend

- Create: `frontend/app.py`
- Create: `frontend/pages/1__Chat.py`
- Create: `frontend/pages/2__RAG.py`
- Create: `frontend/pages/3__Research.py`
- Create: `frontend/pages/4__Observability.py`
- Create: `frontend/utils/api_client.py`
- Create: `frontend/utils/streaming.py`
- Create: `frontend/requirements.txt`
- Create: `frontend/README.md`
- Create: `frontend/Dockerfile`

### Deployment / CI

- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `.github/workflows/test.yml`
- Create: `.github/workflows/lint.yml`
- Modify: `.env.example`

### Docs / Tests

- Create: `tests/test_chat_stream.py`
- Create: `tests/test_chat_stream_endpoint.py`
- Create: `tests/test_auth.py`
- Modify: relevant route tests if auth wiring changes defaults
- Modify: `README.md`

## Testing Strategy

1. 先写 SSE 服务和路由测试，确认 RED
2. 实现最小流式能力，确认 GREEN
3. 再写 auth 测试，确认默认关闭 / 开启拦截 / 正确 key 放行
4. 前端不进 pytest，但要实际启动并点通主要页面
5. Docker / Compose 不进 pytest，但必须真实 `docker compose up`
6. 最后跑全量 pytest，再跑后端和前端 smoke

## Risks

### 1. `chat_stream()` 的 SSE 解析和 xairouter 兼容性

风险：上游不一定完全按照标准 OpenAI SSE 输出。

缓解：

- 解析时按“只处理 `data:` 行、忽略空行和其他字段”做容错
- 异常时不抛给路由，而是输出一段错误事件并结束

### 2. Research streaming 改动面

风险：如果强行改现有 `run_*` 返回结构，容易破坏 Phase 4/5/7 测试。

缓解：

- 只在路由层为 `stream=true` 单独走流式执行路径
- 旧路径保持不动

### 3. Docker 中的项目数据路径

风险：memory / traces / qdrant 数据丢失或路径不统一。

缓解：

- backend 用 `/data` 卷
- Qdrant 用独立 volume
- `.env.example` 明确相关变量

### 4. API Key 默认关闭时的兼容性

风险：如果把依赖挂错，会影响现有开放接口或测试。

缓解：

- 仅挂到 `research` / `tools` / `memory`
- 新测试覆盖 required=false / true 两种模式

## Approval Basis

用户在任务描述中已经明确指定了：

- 技术路线
- 不做什么
- 文件结构
- 测试要求
- 完成标准

因此本设计直接按该约束执行，不再额外回退做方案分歧确认。
