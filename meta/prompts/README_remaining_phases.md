# 项目进度同步 & 后续 Codex 长任务 Prompt 路线图

> 生成日期：2026-05
> 参考文档：`docs/Agent开发完整学习方案.md`、`docs/agent-learning-roadmap.md`
> 大项目主线：**智能研究助手 Agent 平台（Research Agent Platform）**

---

## 一、当前已完成进度（截至 Phase 5）

| Phase | 主题 | 状态 | 关键交付物 | 测试数 |
|-------|------|------|-----------|--------|
| Phase 0 | Python 工程基础 + FastAPI 脚手架 | ✅ 完成 | `app/main.py`、`Settings`、pytest 框架 | — |
| Phase 1 | LLM 基础 + Prompt | ✅ 完成 | `LLMService`、`/chat`、`/extract` | — |
| Phase 2 | RAG 全链路 | ✅ 完成 | docling 解析、Qdrant、Cohere rerank、`/rag/*` | — |
| Phase 3 | Tool Use + Function Calling | ✅ 完成 | `ToolRegistry`、5 个内置工具、`/tools/*` | — |
| Phase 4 | Workflow → Agent (LangGraph) | ✅ 完成 | `research/workflow.py`、`research/agent.py` | 135 |
| Phase 5 | Memory / Planning / Reflection / Multi-Agent | ✅ 完成 | `MemoryService`、`agent_v2.py`、`multi_agent/`、`/memory/*` | **179** |

### Phase 5 实现已覆盖的能力

- ✅ 三层记忆（短期会话 / 工作记忆 / 长期 JSON 持久化）
- ✅ Plan-and-Solve 任务分解节点
- ✅ Reflection + 报告修订循环
- ✅ Supervisor 模式 Multi-Agent（Researcher / Analyst / Writer / Reviewer）
- ✅ 4 种 mode：`workflow` / `agent` / `agent_v2` / `multi_agent`
- ✅ Memory 管理 API（GET/DELETE insights、sessions）

### 当前架构与技术栈约束（继续遵守）

- Python 3.11 / `conda env ai-agent`
- FastAPI 0.115.0 + pydantic 2.9.2 + httpx 0.27.2（**唯一 HTTP 客户端**）
- LangGraph 0.6.11（仅用于图编排）
- LLM: xairouter (`gpt-5.4`)、Embedding: `text-embedding-3-large`、Rerank: Cohere `rerank-v3.5`
- Qdrant `phase2_chunks`
- **不引入** langchain-openai / langchain core LLM 封装 / openai SDK / litellm
- 教学项目原则：先手写底层（理解 HTTP、JSON Schema、tool-call loop），再引入第三方封装

---

## 二、对照学习方案的剩余路线

依照 `docs/Agent开发完整学习方案.md`：

| 学习方案 Phase | 大项目里程碑 | 当前状态 | 剩余工作 |
|----------------|-------------|---------|---------|
| Phase 6（多 Agent + MCP + 平台） | 里程碑 6 | 部分完成 | **MCP Server + Client、外部工具接入** |
| Phase 7（评估 / 安全 / 可观测性） | 里程碑 7 | 极少（仅 retrieval hit rate） | **完整 evaluation 体系 + Guardrails + Tracing + Cost** |
| Phase 8（工程化部署） | 里程碑 8 | 无 | **SSE 流式 / Docker Compose / 前端 / CI/CD** |
| Phase 9（可选：微调 + 推理优化） | — | 无 | 可选，本路线不要求实施 |
| Capstone（项目收尾） | 大项目最终交付 | 无 | **README、架构图、博客、简历素材** |

---

## 三、剩余 Codex GPT-5.5 长任务 Prompt 清单

| 序号 | Prompt 文件 | 对应学习方案 | 对应里程碑 | 预计代码量 |
|------|------------|-------------|-----------|-----------|
| 1 | `phase6_codex.md` | Phase 6（MCP 部分） | 里程碑 6 补齐 | ~800 行 + 测试 |
| 2 | `phase7_codex.md` | Phase 7（评估 / 安全 / 可观测） | 里程碑 7 | ~1200 行 + 测试 |
| 3 | `phase8_codex.md` | Phase 8（部署 / 前端） | 里程碑 8 | ~600 行 + 配置 |
| 4 | `capstone_codex.md` | 整合收尾（Part D.5/D.6/D.7） | 大项目交付 | 文档为主 |

执行顺序：**6 → 7 → 8 → capstone**。每个 Phase 的 prompt 都是独立可执行的长任务，Codex 可在单次会话中完成。

---

## 四、给 Codex 的全局执行约束（每个 prompt 都默认遵守）

1. **HTTP 客户端**: 仅使用 `httpx`，禁止引入 `requests` / `aiohttp` / `openai` SDK / `langchain-openai`
2. **LLM 调用**: 必须经过 `app/services/llm_service.LLMService`，不要直接构造 OpenAI 兼容请求
3. **不修改既有代码**: 已有的 workflow.py / agent.py / 任何 Phase 4 之前的测试不得修改
4. **测试要求**: 新增代码必须有 pytest 单元测试，所有外部 API（LLM、HTTP、MCP transport）需 mock
5. **类型注解**: 新文件首行 `from __future__ import annotations`
6. **Conda env**: 所有命令前先 `conda activate ai-agent`
7. **保持向后兼容**: 现有 `/api/v1/*` 端点的请求/响应字段不可缩窄；只能扩展可选字段
8. **避免 Windows 编码问题**: 源文件使用 UTF-8 无 BOM；中文注释允许，但避免在脚本中 print 大量中文
9. **每完成一个阶段运行 `python -m pytest -q` 验证全部测试通过**
10. **commit 粒度**: 每个 Codex 任务结束应提供 git commit message 模板（不自动 commit）

---

## 五、为什么这样切分

- **Phase 6 单独成一个 prompt**: MCP 是一个独立子系统，需要新增 `mcp` Python 包依赖、新建 `app/services/mcp/` 模块、stdio 传输的特殊性使其不适合与其他工作混在一起。
- **Phase 7 独立**: Evaluation / Safety / Observability 三块虽多，但属于"横切关注点"（cross-cutting concerns），需要在已有所有端点上叠加，必须一起做才能避免重复修改。
- **Phase 8 独立**: 部署是工程化收尾，依赖 Phase 7 的 tracing/cost 数据展示，最后做。
- **Capstone 单独**: 文档/简历/博客不涉及代码逻辑，让 Codex 专注于内容生成而非工程实施。

---

## 六、可在 Codex 中如何使用这些 prompt

```
# 推荐做法（以 Phase 6 为例）：
1. 在 Codex 会话中粘贴 phase6_codex.md 的全文
2. 附加: "请按照 prompt 中的实现顺序逐步推进，每个文件创建后运行 pytest 验证"
3. Codex 完成后，在本地：
   conda activate ai-agent
   cd 8w-plan
   python -m pytest -q
4. 验证 179 旧测试 + 新测试全通过
5. 检查 manual smoke test（Phase 6: 启动 MCP server；Phase 7: 跑 eval；Phase 8: docker-compose up）
6. git add . && git commit -m "feat(phase6): MCP server + client integration"
```

每份 prompt 末尾都附有：自检清单、commit message 模板、smoke test 步骤。
