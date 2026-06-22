# Phase 8 执行手册：从本机到容器

---

## 0. 前置

```powershell
# 装 Docker Desktop（Windows），确认：
docker --version
docker compose version
```

确保上一阶段所有测试通过：
```powershell
conda activate ai-agent
python -m pytest -q
# 期望 263 passed
```

---

## 1. 准备 .env

复制示例：
```powershell
Copy-Item .env.example .env
```

编辑 `.env`，至少填：
```
LLM_API_KEY=sk-xxxxx
EMBEDDING_API_KEY=sk-xxxxx
TAVILY_API_KEY=tvly-xxxxx
RERANK_API_KEY=cohere-xxxxx   # 可选

# 容器内 Qdrant 用服务名
QDRANT_URL=http://qdrant:6333
```

> **坑点**：本机跑时 `QDRANT_URL=http://localhost:6333`，进 docker-compose 必须改成 `http://qdrant:6333`，否则 backend 容器找不到。

---

## 2. 单容器先跑通 backend

```powershell
docker build -t agent-backend:dev .
docker run --rm -p 8000:8000 --env-file .env agent-backend:dev
```

另开终端：
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```

> 这一步只验证镜像 OK，Qdrant 等依赖暂不满足，rag 接口会失败正常。

---

## 3. docker-compose 全栈启动

```powershell
docker compose up -d
docker compose ps
```

预期 3 个服务都是 `Up`：
```
NAME                    STATUS
agent-qdrant            Up (healthy)
agent-backend           Up
agent-frontend          Up
```

看实时日志：
```powershell
docker compose logs -f backend
```

应该能看到：
- `[mcp] runtime initialized`（若配置了 external servers）
- `Application startup complete`

### 3.1 验证

```powershell
# 后端
Invoke-RestMethod http://localhost:8000/api/v1/health

# 前端：浏览器打开
start http://localhost:8501
```

---

## 4. 在容器里跑评估

进入 backend 容器：
```powershell
docker compose exec backend bash

# 容器内
python -m scripts.run_rag_eval --cases eval/rag_questions.jsonl --top-k 5
exit
```

输出 `eval/results/...json` 通过 volume mount 也在宿主可见（如果挂了 eval 目录的话；默认不挂，需要 `docker compose cp`）。

---

## 5. 数据持久化验证

```powershell
docker compose down            # 不加 -v，保留卷
docker compose up -d
# 之前 ingest 的文档应该还在
Invoke-RestMethod http://localhost:8000/api/v1/rag/search?query=test
```

如果加 `-v`：
```powershell
docker compose down -v   # 危险！会删 qdrant_data + backend_data
```

---

## 6. 升级流程

```powershell
git pull
docker compose build
docker compose up -d --force-recreate backend frontend
```

只升级一个服务：
```powershell
docker compose up -d --force-recreate --no-deps backend
```

---

## 7. 流式接口实测

### 7.1 chat 流式

```powershell
curl -N -X POST http://localhost:8000/api/v1/chat/stream `
  -H "Content-Type: application/json" `
  -d '{\"prompt\": \"用三句话讲讲什么是 RAG\"}'
```

应看到逐 chunk 输出 `data: {"type": "delta", ...}`。

### 7.2 research 流式

在 Streamlit 的"研究流"页面输入主题、选 mode=multi_agent，能看到节点逐个亮起。

---

## 8. CI 本地预演

GitHub Actions 跑前先在本机模拟：
```powershell
# 干净环境
python -m venv .ci-venv
.\.ci-venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
deactivate
Remove-Item -Recurse -Force .ci-venv
```

跟 `.github/workflows/ci.yml` 的步骤一致，本地先过这关，push 之后 CI 不会红。

---

## 9. 上线前 checklist

```powershell
# 1. 跑全量测试
pytest -q                                                # 263 passed

# 2. 镜像构建
docker compose build

# 3. 关闭 debug
(Get-Content .env) -replace 'APP_DEBUG=true','APP_DEBUG=false' | Set-Content .env

# 4. 开启 auth & guardrails
Add-Content .env "API_KEY_REQUIRED=true"
Add-Content .env "API_KEY=$(New-Guid)"
Add-Content .env "GUARDRAILS_ENABLED=true"

# 5. 重启
docker compose down; docker compose up -d

# 6. smoke test
Invoke-RestMethod -Headers @{ 'X-API-Key'=$env:API_KEY } http://localhost:8000/api/v1/health
```

---

## 10. 常见踩坑

| 现象 | 原因 | 修复 |
|------|-----|-----|
| backend 启动后立刻 exit 0 | env 文件路径错 / 必填字段缺 | `docker compose logs backend` 看 settings 报错 |
| backend 报 `Connection refused` 到 qdrant | `QDRANT_URL=localhost` | 改 `qdrant`（service 名） |
| frontend 调不通 backend | `BACKEND_URL=localhost:8000` | 改 `http://backend:8000` |
| MCP server 启不来 | npx 在 slim 镜像没装 node | base 镜像换 node:20-slim 或在 Dockerfile 里 `apt install nodejs npm` |
| compose down 误删数据 | 加了 `-v` | 只用 `docker compose down`（不带 -v） |
| Streamlit reload 慢 | 多页应用每页重启 | 升级 streamlit 到 ≥1.30 |
| SSE 间断卡顿 | 反代 buffering | Nginx `proxy_buffering off; proxy_read_timeout 600s` |
| 镜像构建慢 | requirements.txt 改一行就重装 | 把 `COPY requirements.txt ./` 单独一层（已实施）|
| 容器内 traces.db 看不到 | 没挂卷 | docker-compose 已挂 `backend_data:/data` |
| pytest 在容器里 ImportError | 镜像没拷 tests/ | 默认不拷（生产不需要），要测试用本机 venv |

---

## 11. 完成本阶段你应当能演示

- [ ] `git clone` 后 `docker compose up -d` 一条命令起服务
- [ ] 浏览器看 Streamlit 8 个页面都能交互
- [ ] curl SSE 接口能看流式输出
- [ ] 关闭再起，之前 ingest 的文档/记忆/trace 都还在
- [ ] `.github/workflows/ci.yml` push 后 PR 能看到绿勾
- [ ] README 里写明部署 + secrets 注入 + 升级 + 回滚步骤

---

## 12. 项目正式收尾

到这一步，整个 8 阶段学习路线和主线项目就都完成了。建议同步：

1. 整理 `study_docs/PROJECT_SHOWCASE.md`（产品验收清单）
2. 写 README 顶部的 quickstart 三步走（clone / .env / docker compose up）
3. 在 GitHub release 打 v1.0 tag，附 demo 视频
4. 写技术博客 / 简历项目段落
