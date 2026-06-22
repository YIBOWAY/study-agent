# 主线大项目验收：Production-Grade AI Agent

> 一句话介绍：从零搭建的端到端 AI Agent 应用，覆盖 RAG / Function Calling / Workflow / Multi-Agent / MCP / Eval / Safety / Observability / Docker 部署九大模块。

---

## 1. 项目数据快览

| 指标 | 数值 |
|------|------|
| 代码模块 | `app/` 30+ 文件，~6500 行 |
| 测试用例 | **263 passed**（pytest 8.3.3） |
| 路由数量 | 9 个路由器，30+ 端点 |
| 工具数量 | 4 本地 + N 个 MCP（可扩） |
| Docker 服务 | 3（qdrant + backend + frontend） |
| 学习文档 | study_docs 9 篇 + architecture_docs 9 篇 + excut_docs 9 篇 |

---

## 2. 八阶段交付清单（对应学习方案 D.1 主线项目）

### Phase 0 - 工程基础
- [x] Python 包结构 + Pydantic Settings + structlog
- [x] httpx 异步客户端 + 重试封装
- [x] pytest + asyncio_mode + 测试组织
- [x] CLI 助手 (`scripts/cli_chat.py`)

### Phase 1 - LLM 与 Prompt
- [x] `LLMService.chat / chat_with_messages / extract / stream_chat`
- [x] 系统/用户角色分离
- [x] Structured Output (extract → Pydantic)
- [x] SSE 流式 (`/api/v1/chat/stream`)

### Phase 2 - RAG
- [x] 文档加载 + 切分 (`splitting.py`)
- [x] Embedding + Qdrant 入库
- [x] HNSW 检索 + Cohere rerank（fail-soft）
- [x] `/rag/ingest`, `/rag/search`, `/rag/ask`

### Phase 3 - Tool Use / Function Calling
- [x] `ToolRegistry` 动态注册
- [x] 4 本地工具：web_search、calculate、get_current_time、execute_python（沙箱）
- [x] `/tools/schemas`, `/tools/invoke`, `/tools/run`（多轮）

### Phase 4 - Workflow Agent
- [x] LangGraph DAG (`research/graph.py`)
- [x] ReAct Agent (`research/agent.py`)
- [x] `/research?mode={workflow|agent_v2}` 统一入口

### Phase 5 - Memory + Multi-Agent
- [x] `MemoryService`：会话短期 + 长期 JSON 检索
- [x] `multi_agent/graph.py`：plan → researcher → analyst → writer → reviewer 5 节点
- [x] 条件路由 + 迭代/修订上限
- [x] `/research?mode=multi_agent`

### Phase 6 - MCP
- [x] 自建 MCP server (`mcp/server.py`，内置 4 工具)
- [x] MCPRuntime 拉起多个 stdio 子进程，namespacing `mcp__server__tool`
- [x] CallToolResult.isError + asyncio.wait_for 超时
- [x] `/mcp/list`, `/mcp/invoke` + guardrails 联动

### Phase 7 - Eval + Safety + Observability
- [x] RAG 三大指标（faithfulness / context_precision / answer_relevance）
- [x] Agent eval（success_rate / iterations / latency / keyword coverage）
- [x] Guardrails 三层：input / output / tool_call（白名单 + PII 脱敏）
- [x] Tracing（SQLite + ContextVar 嵌套 trace）
- [x] CostCalculator + `/observability/cost-summary`
- [x] X-API-Key auth

### Phase 8 - 部署
- [x] 多阶段 Dockerfile（builder + runtime）
- [x] docker-compose（qdrant + backend + frontend）
- [x] Streamlit 8 页前端 + SSE 客户端
- [x] `.github/workflows/ci.yml` 跑 pytest
- [x] 数据卷持久化 + .env.example

---

## 3. 一图看懂全栈

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Streamlit (8 pages)                           │
│   Chat / RAG / Tools / Research / Memory / Eval / Obs / MCP         │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ httpx (REST + SSE)
┌─────────────────────────────────▼───────────────────────────────────┐
│                       FastAPI Backend                               │
│  ┌────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ /chat      │ │ /rag    │ │ /tools   │ │/research │ │ /memory  │ │
│  └─────┬──────┘ └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│        │            │            │            │            │       │
│        ▼            ▼            ▼            ▼            ▼       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Cross-cutting: Guardrails │ Tracing │ Auth │ CostCalculator │ │
│  └──────────────────────────────────────────────────────────────┘ │
│        │            │            │            │            │       │
│  ┌─────▼──┐  ┌──────▼─────┐  ┌──▼────────┐  ┌▼───────┐  ┌▼─────┐ │
│  │LLMSvc  │  │RAG (Qdrant)│  │ToolRegistry│  │LangGraph│  │MemSvc│ │
│  └────────┘  └────────────┘  └─────┬──────┘  └────────┘  └──────┘ │
│                                    │                              │
│                                    ▼                              │
│                       ┌──────────────────────────┐                │
│                       │ MCPRuntime (stdio child) │                │
│                       └──────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 验收 Demo 脚本（建议录屏）

```powershell
# 1. 启动
docker compose up -d
start http://localhost:8501

# 2. RAG: 在 RAG 页上传一篇 PDF / .md，提问
# 3. Tools: 在 Tools 页执行 calculate("3*7+5")
# 4. Research mode=multi_agent: "分析一下 LangGraph 与 LangChain 的差异"
#    → 看 SSE 节点流：plan → research → analyze → write → review
# 5. Memory: 第二轮提问"我们刚才聊到了什么", 验证记忆生效
# 6. Eval: 触发 RAG eval，看 faithfulness 等三指标
# 7. Observability: 看刚才 multi_agent 的 trace 树和 cost
# 8. Safety: 故意发 prompt injection，看被拦
```

---

## 5. 关键工程亮点（面试可讲）

| 亮点 | 说明 |
|------|------|
| **httpx-only**，不依赖 LangChain 的 ChatModel | 显式控制每一次 LLM 调用、retry、token 统计 |
| **统一 LLMService.chat 接口**，但 graph 节点从 service 拿 | 业务层切换模型零侵入 |
| **MCP runtime 单例 + namespace 隔离** | 多个外部 server 不会撞名 |
| **Guardrails 三层**贯穿 input/output/tool | 在路由 + service 双层兜底 |
| **Tracing 用 ContextVar + asynccontextmanager** | 自动维护父子关系，不污染业务签名 |
| **CallToolResult.isError = True 而不是 raise** | 符合 MCP 规范，不破坏 server 端循环 |
| **fail-soft rerank** | 上游 cohere 抖动不阻塞主链路 |
| **多阶段 Dockerfile** | runtime 镜像 350MB，可分发 |

---

## 6. 已知短板与未来工作

> 学习项目特意保留这些"未做事项"作为求职时谈论"如何在生产化加固"的素材。

| 短板 | 改进方向 |
|------|---------|
| Memory 用 JSON + token overlap | 换 Qdrant 长期记忆 + 定期摘要 |
| Tracing 用 SQLite | 换 OpenTelemetry → Tempo / Honeycomb |
| Cost 单价是占位值 | 接厂商真实计费 + 月度 budget alert |
| Guardrails 是规则匹配 | 加入 LLM-based moderation（如 OpenAI Moderation API） |
| 没有用户系统 | 接 OIDC（Auth0 / Authentik） |
| 没接 K8s | 写 Helm chart |
| 没做微调 | 学习路线 Phase 9 标记可选 |
| Eval 是单模型 judge | 多模型 panel + bootstrap 置信区间 |

---

## 7. 学习路线对照表

| 学习方案章节 | 是否完成 | 文档定位 |
|-------------|---------|---------|
| A. 工程基础 | ✅ | study_docs/phase0_python_engineering.md |
| B.1 LLM API 与 Prompt | ✅ | phase1_llm_and_prompt.md |
| B.2 RAG 双引擎 | ✅ | phase2_rag.md |
| B.3 Function Calling / Tool Use | ✅ | phase3_tool_use.md |
| B.4 Workflow / Agent | ✅ | phase4_workflow_agent.md |
| B.5 Memory / Multi-Agent | ✅ | phase5_memory_multi_agent.md |
| B.6 MCP | ✅ | phase6_mcp.md |
| C. Eval / Safety / Observability | ✅ | phase7_eval_safety_observability.md |
| D.1 主线项目 | ✅ | 本文件 |
| D.2 工程化部署 | ✅ | phase8_production_deployment.md |
| D.3 简历项目段落 | ✅ | RESUME_SAMPLE.md |
| D.4 面试问题准备 | ✅ | RESUME_SAMPLE.md（面试题章节） |
| D.5 技术博客 3-5 篇 | ✅ 提供大纲 | BLOG_OUTLINES.md |
| D.6 微调（可选） | ⏳ 未做 | 规划在 Phase 9 |
| D.7 求职行动 | — | 同学者负责 |

---

## 8. README 引用建议

把以下三段加入仓库根 `README.md` 顶部：

```markdown
## Quickstart
git clone ... && cd 8w-plan
cp .env.example .env  # 填 LLM/Embedding/Tavily 三个 key
docker compose up -d
open http://localhost:8501

## Tests
conda activate ai-agent && pytest -q   # 263 passed

## Docs
学习路线: study_docs/
架构设计: architecture_docs/
执行手册: excut_docs/
项目验收: study_docs/PROJECT_SHOWCASE.md
```

---

## 9. 验收标志

- [x] 263 个测试通过
- [x] docker compose up 一条命令拉起全栈
- [x] 8 个 Streamlit 页面全部可交互
- [x] SSE 流式 chat 与 multi_agent 都通
- [x] 所有阶段三件套文档（study + architecture + excut）齐全
- [x] PROJECT_SHOWCASE / RESUME / BLOG 三件套
- [x] 目录整洁（meta/ 收纳 prompts + code_docs；scripts/ 因 `python -m` 调用保留）

**结论：主线大项目交付完成，可作为求职作品提交。**
