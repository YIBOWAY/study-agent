# Phase 8：工程化部署与生产落地

> 目标：把项目从"localhost demo"升级到"任何人 docker compose up 就能跑的可分享产品"
> 前置要求：Phase 7 完成
> 预计时间：3-5 天

---

## 0. 从 demo 到 production 还差什么

跑得动 ≠ 上得了线。差距在：

| 维度 | demo | production |
|------|------|-----------|
| 启动方式 | 手动 `uvicorn app.main:app --reload` | `docker compose up -d` |
| 配置 | 写死在代码 | 环境变量 + .env |
| 依赖服务 | 本地装 Qdrant | docker-compose 编排 |
| 前端 | 没有 / Postman | Streamlit / React UI |
| 流式输出 | print | SSE / WebSocket |
| 重启 | 改代码退 reload | 镜像版本号 + 蓝绿 |
| 错误响应 | 500 暴露堆栈 | 业务态错误码 + log |
| CI | 没有 | GitHub Actions 跑 pytest |

Phase 8 把以上全部补齐。

---

## 1. 后端工程化

### 1.1 FastAPI 应用结构（已完整）

```
app/
├── main.py             # FastAPI 入口 + lifespan + 路由注册
├── core/
│   ├── config.py       # Pydantic Settings（从 env 读）
│   ├── logging.py
│   └── auth.py         # API Key 中间件
├── api/
│   ├── dependencies.py # Depends 工厂
│   └── routes/
│       ├── health, chat, rag, tools, research,
│       │   memory, mcp, eval, observability
└── services/           # 业务层（无 FastAPI 依赖）
```

**关键约定**：`services/` 模块不能 import `fastapi` —— 让业务逻辑可以在脚本/CLI/测试里独立跑。

### 1.2 流式输出（SSE）

`/api/v1/chat/stream`、`/api/v1/research/stream` 用 `StreamingResponse` + `text/event-stream`：

```python
async def event_gen() -> AsyncIterator[str]:
    async for chunk in llm.stream_chat(...):
        yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

return StreamingResponse(event_gen(), media_type="text/event-stream")
```

> **生产坑**：Nginx 反代时必须关 buffering：`proxy_buffering off;` 否则前端要等很久才看到第一个 chunk。

### 1.3 健康检查

`/api/v1/health` 不仅返 `{ "status": "ok" }`，还检查：
- Qdrant 可达
- Memory dir 可写
- Tracing DB 可写

让 Docker / k8s 的 readiness probe 真有意义。

---

## 2. 容器化

### 2.1 多阶段 Dockerfile

```Dockerfile
# Builder：装依赖到 venv
FROM python:3.11-slim AS builder
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install -r requirements.txt -i 清华镜像

# Runtime：只复制 venv + app 代码
FROM python:3.11-slim AS runtime
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY scripts ./scripts
COPY eval ./eval
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

收益：
- 镜像不含 build-essential / pip cache，体积省一半
- venv 路径固定，运行时启动快

### 2.2 docker-compose.yml

三服务编排：
- `qdrant` — 向量数据库
- `backend` — FastAPI 服务
- `frontend` — Streamlit UI

`.env` 的 LLM_API_KEY 等 secrets 用 `${VAR:-default}` 格式注入，不写死在 yml。

数据持久化：
- `qdrant_data` 卷：向量索引
- `backend_data` 卷：`/data/memory` + `/data/traces.db`

### 2.3 .dockerignore

务必忽略：
```
.venv/
.review-venv/
__pycache__/
.pytest_cache/
.ruff_cache/
data/
docs/
*.md
.git/
```

否则 build context 几百 MB，每次构建都慢得让人怀疑人生。

---

## 3. 前端：Streamlit 多页应用

```
frontend/
├── app.py              # 首页（项目介绍 + 健康指标）
├── requirements.txt    # streamlit + httpx
├── Dockerfile          # 单阶段
├── pages/
│   ├── 1_💬_Chat.py
│   ├── 2_📚_RAG.py
│   ├── 3_🛠️_Tools.py
│   ├── 4_🔬_Research.py     # 含 SSE 流式
│   ├── 5_🧠_Memory.py
│   ├── 6_📊_Evaluation.py
│   ├── 7_👁️_Observability.py
│   └── 8_⚙️_MCP.py
└── utils/
    └── api_client.py   # 集中封装 httpx 调后端
```

为什么不上 React？
- Streamlit 0 前端经验也能 2 天交付
- 数据展示（DataFrame、JSON、流式文本）原生支持
- 真的需要更花哨再上 Next.js / Vite

> **生产建议**：Streamlit 适合**内部工具 / demo / 评估面板**。面向 C 端建议换 React/Vue + 后端只暴露 REST/SSE。

---

## 4. CI/CD（`.github/workflows/`）

最小可用配置：

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: pytest -q
```

可扩展：
- ruff/mypy 静态检查
- docker build & push（tag = git sha）
- 部署 hook（push 到 prod server）

---

## 5. 部署形态选择

| 选型 | 适合 | 缺点 |
|------|-----|------|
| **单机 docker-compose** ✅ 本项目默认 | 个人/小团队/演示 | 不能横向扩 |
| 云厂商容器服务（ECS/ACI/Cloud Run） | 中等流量 | 冷启动 |
| Kubernetes | 大流量 / 多副本 | 运维成本高 |
| Serverless（Vercel/Modal） | 稀疏调用 | LangGraph 长任务不友好 |

> **求职建议**：把 docker-compose 跑通 + 给 README 加部署章节，已经超过 80% 求职者。K8s 不是必须，能讲清楚 trade-off 就行。

---

## 6. 配置管理与 Secrets

### 6.1 三层配置

1. **代码默认值**（`Settings` 字段的 default）
2. **`.env` 文件**（覆盖默认）
3. **环境变量**（覆盖 .env）

### 6.2 Secrets 红线

- `.env` 永远不进 Git（`.gitignore` 已加）
- `.env.example` 存模板（无真值），随仓库走
- 生产用 **vault/secret manager**（HashiCorp Vault、AWS SecretsManager、k8s Secret）

---

## 7. 可观测性（生产视角）

| 关注点 | 怎么做 |
|--------|--------|
| 请求量 / 错误率 | Prometheus exporter + Grafana 看板 |
| 延迟分布 P50/P95/P99 | 同上 |
| 单次链路 | 已有 /observability/traces |
| 业务指标（成本/迭代） | trace 表 SQL 聚合 |
| 告警 | Grafana alert / PagerDuty |
| 日志聚合 | stdout JSON → Loki / ELK |

本项目暂未上 Prometheus，留作课后练习（约 30 行代码 + prometheus-fastapi-instrumentator）。

---

## 8. 升级 / 回滚

```
docker compose pull
docker compose up -d --force-recreate
# 失败回滚：
docker compose down
docker tag agent-backend:prev agent-backend:latest
docker compose up -d
```

更稳妥：用 git tag 打镜像 tag，`compose.override.yml` 切换 image: tag。

---

## 9. 完成本阶段你应当能回答

- [ ] 多阶段 Dockerfile 比单阶段省了什么、为什么省？
- [ ] SSE 与 WebSocket 选型理由？为什么本项目选 SSE？
- [ ] `docker-compose up` 后 backend 启动比 qdrant 快怎么办？（depends_on 不等健康）
- [ ] 前端用 Streamlit 在哪些场景不合适？
- [ ] 生产环境 LLM_API_KEY 应该怎么管（不能写 .env）？
- [ ] /api/v1/health 应该返回什么才算"健康"？

---

## 10. 推荐资料

| 主题 | 资源 |
|------|------|
| Dockerfile 最佳实践 | docs.docker.com/develop/develop-images/dockerfile_best-practices |
| 多阶段构建 | docs.docker.com/build/building/multi-stage |
| FastAPI 部署 | fastapi.tiangolo.com/deployment/ |
| Streamlit 多页 | docs.streamlit.io/library/get-started/multipage-apps |
| GitHub Actions Python | docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python |
