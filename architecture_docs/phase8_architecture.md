# Phase 8 架构文档：生产部署

---

## 1. 部署架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│                  docker-compose.yml (单机部署)                        │
│                                                                      │
│  ┌──────────────────┐    ┌────────────────────┐    ┌──────────────┐ │
│  │  Streamlit       │    │   FastAPI Backend   │    │   Qdrant     │ │
│  │  (frontend)      │───▶│   (backend)         │───▶│   (向量库)   │ │
│  │  :8501           │    │   :8000             │    │   :6333      │ │
│  │                  │    │                     │    │              │ │
│  │  - 8 个 page      │    │  - 9 个路由器        │    │  - HNSW      │ │
│  │  - SSE 客户端    │    │  - lifespan: MCP    │    │  - persist   │ │
│  │                  │    │  - guardrails       │    │              │ │
│  │                  │    │  - tracing          │    │              │ │
│  └──────────────────┘    └─────────┬───────────┘    └──────────────┘ │
│         │ httpx                     │                                 │
│         │ BACKEND_URL=              │ stdio (lifespan 启动)            │
│         │ http://backend:8000       ▼                                 │
│                              ┌───────────────────┐                    │
│                              │ MCP 子进程         │                    │
│                              │ (npx ... 等)      │                    │
│                              └───────────────────┘                    │
│                                                                      │
│  Volumes:                                                            │
│  - qdrant_data   → /qdrant/storage                                   │
│  - backend_data  → /data (memory + traces.db)                        │
└──────────────────────────────────────────────────────────────────────┘

外部依赖（不入 compose）：
  - LLM API:        https://api.xairouter.com/v1
  - Embedding API:  上游
  - Rerank API:     https://api.cohere.com/v2
  - 网络搜索:        https://api.tavily.com
```

---

## 2. 镜像分层

### 2.1 backend 镜像（多阶段）

```
Stage 1 (builder, 800 MB+):
├── python:3.11-slim
├── 装 build-essential
├── pip install -r requirements.txt
└── 输出: /opt/venv

Stage 2 (runtime, ~350 MB):
├── python:3.11-slim
├── COPY --from=builder /opt/venv
├── COPY app/ scripts/ eval/
└── CMD uvicorn app.main:app
```

省了：build-essential、pip cache、源码 .pyc。

### 2.2 frontend 镜像（单阶段）

依赖少（streamlit + httpx），单阶段已足够。

---

## 3. 路由层全景

| 前缀 | 路由器 | 说明 |
|------|--------|------|
| `/api/v1/health` | health.py | 健康检查（含依赖探活） |
| `/api/v1/chat`, `/api/v1/extract`, `/api/v1/chat/stream` | chat.py | LLM 直连 / Structured Output / 流式 |
| `/api/v1/rag/{ingest,search,ask}` | rag.py | RAG 全链路 |
| `/api/v1/tools/{schemas,invoke,run}` | tools.py | 本地工具 + MCP 工具调用 |
| `/api/v1/research`, `/api/v1/research/stream` | research.py | 4 种 mode + SSE |
| `/api/v1/memory/...` | memory.py | 会话/长期记忆 |
| `/api/v1/mcp/...` | mcp.py | MCP server 与工具列表 |
| `/api/v1/eval/{rag,agent,last}` | eval.py | 批量评估 |
| `/api/v1/observability/{traces,traces/{id},cost-summary}` | observability.py | 链路与成本 |

`app/main.py` 在 lifespan 钩子里：
1. 连接所有外部 MCP server
2. 把 runtime 注入 ToolRegistry（research_routes / tools_routes 共用）
3. 退出时 `shutdown_mcp_runtime()` 干净关闭子进程

---

## 4. 配置项汇总（Settings → 环境变量）

### 4.1 LLM / 第三方
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
- `EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`
- `RERANK_API_KEY`, `RERANK_BASE_URL`, `RERANK_MODEL`, `RERANK_FAIL_SOFT`
- `TAVILY_API_KEY`, `TAVILY_BASE_URL`

### 4.2 基础设施
- `QDRANT_URL`, `QDRANT_COLLECTION`
- `MEMORY_DATA_DIR`
- `TRACING_DB_PATH`

### 4.3 安全
- `API_KEY_REQUIRED`, `API_KEY`
- `GUARDRAILS_ENABLED`, `GUARDRAILS_STRICT_MODE`
- `GUARDRAILS_ALLOWED_TOOLS`, `GUARDRAILS_ALLOWED_MCP_TOOLS`

### 4.4 观测
- `TRACING_ENABLED`

### 4.5 业务
- `TOOL_CALL_TIMEOUT`
- `MCP_SERVER_NAME`, `MCP_SERVER_VERSION`, `MCP_EXTERNAL_SERVERS`
- `MULTI_AGENT_MAX_ITERATIONS`, `MULTI_AGENT_MAX_REVISIONS`

---

## 5. 数据持久化

| 数据 | 路径 | 备份策略 |
|------|------|---------|
| 向量索引 | `qdrant_data` 卷 → `/qdrant/storage` | `docker run --rm -v qdrant_data:/from -v $PWD:/to alpine tar czf /to/qdrant.tgz /from` |
| Memory | `backend_data` 卷 → `/data/memory/long_term.json` | 同上策略对 backend_data |
| Tracing | `backend_data` 卷 → `/data/traces.db` | 同上 |

> 生产建议：JSON / SQLite 并不是真正的生产存储。流量稍大就应该换 Postgres + Object Storage。

---

## 6. 启动顺序与失败模式

```
docker compose up -d
   │
   ├── qdrant 启动     (8s)
   ├── backend 启动    (4s, depends_on qdrant 但只等启动不等健康)
   │     ├── 跑 lifespan
   │     │    ├── init_mcp_runtime (若 MCP_EXTERNAL_SERVERS 非空)
   │     │    └── 连接 Qdrant 客户端（懒加载）
   │     └── uvicorn 接受请求
   └── frontend 启动   (3s, depends_on backend)
```

### 失败模式

| 场景 | 现象 | 修复 |
|------|------|------|
| Qdrant 还没起 backend 就请求 | 第一次 `/rag/search` 504 | 用 `healthcheck` + `condition: service_healthy`（compose v2 ）|
| MCP 子进程 spawn 失败 | lifespan 抛异常，backend crash | 已用 try/except 包裹，单个 server 失败不影响其它 |
| LLM API 限流 | 业务接口偶发 5xx | 在 LLMService 加 backoff 重试（已实现 1 次重试） |
| 磁盘满 | trace 写入失败 | 加监控告警 + max_trace_age_days 清理 |

---

## 7. 升级 / 回滚

```bash
# 升级
git pull origin main
docker compose build
docker compose up -d --force-recreate backend frontend

# 回滚到上一个 commit
git checkout <prev_sha>
docker compose build && docker compose up -d --force-recreate
```

进阶：用 `image: registry/agent:${TAG}` + CI 推 tag = git sha，回滚只改 .env 中的 TAG。

---

## 8. 性能与扩容

| 瓶颈 | 解法 |
|------|------|
| LLM 延迟 | 不能内部解决；缓存 prompt+answer |
| Qdrant 内存 | 查询打分类型 (HNSW)，分片 |
| Python GIL | uvicorn `--workers 4` |
| SSE 长连接 | Nginx `keepalive_timeout 600s` |
| Tracing 写入慢 | SQLite WAL 模式 / 队列异步写 |

---

## 9. CI/CD（已加 `.github/workflows/`）

最小工作流：
1. push → checkout → setup-python 3.11 → pip install → pytest
2. （可扩）docker build & push
3. （可扩）部署 hook

---

## 10. 安全 checklist（上线前）

- [ ] `.env` 不在 git，`.env.example` 在
- [ ] `API_KEY_REQUIRED=true`
- [ ] `GUARDRAILS_ENABLED=true`，`GUARDRAILS_ALLOWED_MCP_TOOLS` 显式列出
- [ ] `APP_DEBUG=false`
- [ ] 所有路由都过了 `Depends(get_auth)`
- [ ] CORS 限制 origin
- [ ] 反代加 rate limit
- [ ] 镜像扫描（trivy / docker scout）

---

## 11. 已知限制 / 未做事项

- 没有 K8s manifest（docker-compose 已够本项目）
- 没有 Prometheus/Grafana（可作进阶练习）
- 没有蓝绿/金丝雀发布（小项目用不上）
- 前端没做用户系统（Streamlit 内置 auth 较弱，生产建议接入 Auth0 / Clerk）
