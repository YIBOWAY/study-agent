# 简历样例与面试准备

> 复制下面段落到简历"项目经历"章节，按需调整数字。

---

## 1. 简历项目段落（中文版）

### Production-Grade AI Agent 系统 ｜ 个人项目（2025）

**技术栈**：Python 3.11、FastAPI、LangGraph、Qdrant、MCP、httpx、Pydantic v2、Streamlit、Docker、GitHub Actions

**项目简介**：从零构建端到端 AI Agent 应用，覆盖 RAG / Function Calling / Workflow / Multi-Agent / MCP / 评估 / 安全 / 可观测性 / 容器化部署 9 大模块，**263 个单元/集成测试全部通过**。

**核心成果**：
- 设计三层 RAG 流水线（chunking → Qdrant HNSW → Cohere rerank，rerank 失败软降级），将检索 Top-5 命中率从 0.62 提升到 0.86；
- 用 LangGraph 实现 5 节点 Multi-Agent（plan→researcher→analyst→writer→reviewer），引入条件路由 + 迭代/修订上限，避免无限循环；
- 自建 MCP server 并集成外部 stdio MCP（filesystem 等），用 namespacing `mcp__server__tool` + `CallToolResult.isError` 严格遵守协议规范；
- Guardrails 三层防护（prompt injection 拦截 / PII 脱敏 / 工具白名单），覆盖 input/output/tool_call 全链路；
- 自研 Tracing（SQLite + ContextVar）+ CostCalculator，实现 LLM 调用链可视化与成本聚合；
- 多阶段 Dockerfile（运行镜像 ~350MB）+ docker-compose 一键部署 backend/frontend/qdrant 三服务；
- RAG 评估三大指标（faithfulness、context precision、answer relevance）+ Agent 评估（success rate、迭代数、关键词覆盖）打通批量评测脚本与 REST 端点。

**项目链接**：github.com/<your-id>/ai-agent ｜ Demo：streamlit cloud / 自部署

---

## 2. 简历项目段落（英文版）

### Production-Grade AI Agent System ｜ Personal Project (2025)

**Stack**: Python 3.11, FastAPI, LangGraph, Qdrant, MCP, httpx, Pydantic v2, Streamlit, Docker, GitHub Actions

**Highlights**:
- Built an end-to-end AI Agent platform covering RAG, Function Calling, Workflow, Multi-Agent, MCP, Eval, Safety, Observability, and Docker deployment, with **263 passing tests**.
- Designed a three-stage RAG pipeline (chunking → Qdrant HNSW → Cohere rerank with fail-soft fallback), boosting top-5 retrieval hit-rate from 0.62 to 0.86.
- Implemented a 5-node Multi-Agent workflow with LangGraph (plan/research/analyze/write/review), guarded by iteration & revision caps.
- Built a custom MCP server and integrated external stdio MCP servers via tool namespacing and strict `CallToolResult.isError` propagation.
- Three-layer Guardrails (prompt-injection filter, PII redaction, tool whitelist) wired through input/output/tool-call paths.
- Self-built tracing (SQLite + ContextVar) plus a cost calculator, exposing nested LLM call trees and aggregated USD spend.
- Multi-stage Dockerfile (~350MB runtime) and a 3-service `docker compose` for one-command deployment.

---

## 3. 短版（一行）

> 用 LangGraph + FastAPI 自建 Production-Grade AI Agent 系统（RAG / Multi-Agent / MCP / Eval / Guardrails / Tracing / Docker），263 测试全过，docker-compose 一键部署。

---

## 4. 面试 Top-10 问题与答题要点

### Q1：你的 RAG 是怎么做的？为什么选 Qdrant？

要点：
- chunk 用 token 数 + overlap，不是按字符；做了 metadata 透传（来源、页码）；
- 检索：双引擎，先 HNSW Top-N，再 Cohere rerank Top-K，K 可调；
- rerank 失败软降级（前 K），避免上游抖动阻塞业务；
- Qdrant：轻量、Rust 写、HNSW 内置、grpc/http 双协议、单机就能跑；对比 Milvus 太重，Pinecone 是云服务有 vendor lock-in。

### Q2：ReAct Agent 和 Multi-Agent 的区别？什么时候选哪个？

- ReAct：单 LLM 一直 reason→act→observe 循环，简单任务高效；
- Multi-Agent：多个 LLM 各司其职（计划/研究/写作/审查），适合需要批判性反思和角色分工的复杂任务；
- 选型：用户输入短、单一目标 → ReAct；输入是开放主题、需要长报告 → Multi-Agent；
- 都加迭代上限避免死循环。

### Q3：MCP 是什么？跟 OpenAI Function Calling 区别？

- MCP = Model Context Protocol，跨进程标准化"模型如何用工具"；
- Function Calling 是 OpenAI 私有协议，每家厂商都有自己版本；MCP 把工具部分独立成 server，**一次写好到处可用**；
- MCP 用 stdio/sse 传输，工具调用走 JSON-RPC；
- 我们项目里 MCP server 同时暴露给本地 LLM 调用和未来其它 client 调用。

### Q4：怎么评估 RAG 好不好？

- 三指标：
  - **Faithfulness**：答案是否能从检索片段推出（防幻觉）；
  - **Context Precision**：检索片段里有用的占比；
  - **Answer Relevance**：答案与问题相关性。
- 实现：用同一个 LLM 当 judge（response_format=json_object 强制结构化），跑批返回每题分数 + summary。
- 局限：单 judge 有偏，进阶可上 panel + bootstrap CI。

### Q5：你的 Guardrails 防得住真的攻击吗？

老实说：
- 防得住 80% 的"已知模式"（指令注入关键词、明文 PII、工具白名单外调用）；
- 防不住的：obfuscated prompt、跨语言注入、社会工程；
- 工业上要叠 LLM-based moderation + 人审 + 用户行为分析。
- 我们项目把 guardrails 设计成**多层 + 可关闭**，方便 A/B 比较影响。

### Q6：Tracing 怎么自己做的？为什么不直接用 LangSmith？

- LangSmith 是 SaaS，要走 token 出墙，且和 LangChain 强耦合；
- 自做：`asynccontextmanager` + `ContextVar` 维护当前 trace_id，子节点 set parent_id，写 SQLite；
- 后续可以无缝切 OpenTelemetry，把 SQLite 换 OTLP exporter；
- 收益：每条 trace 自包含成本/迭代/工具列表，方便业务回溯。

### Q7：成本怎么控？怎么算？

- 在 LLMService 调用结束写 trace 节点时把 `prompt_tokens / completion_tokens / model` 都记下；
- CostCalculator 维护单价表（按 model）；
- `/observability/cost-summary?days=N` 聚合 SQL；
- 成本控制策略：cache（同 prompt → 同 answer）、降模型（gpt-4o-mini 替代 4o）、限制 max_tokens、迭代上限。

### Q8：为什么不直接用 LangChain 的 ChatModel？

- LangChain 抽象多、breaking change 多、底层换 model 时屡屡踩坑；
- 我们只用 httpx 直连 OpenAI 兼容 API，**控制权 100% 在自己**；
- LangGraph 单独用作流程编排（不依赖 LangChain 的 LLM 抽象），耦合度低。

### Q9：Multi-Agent 会不会陷入循环？怎么设计退出条件？

- 两层防护：
  - 硬性 `max_iterations` / `max_revisions`（写在配置）；
  - 条件路由 `route_after_review`：reviewer 判 ok 就走 save，否则 revise，但 revise 次数到顶强制 save；
- LangGraph 的 `END` 节点必须每条路径都能到达，编译时检查。

### Q10：上线前你还会补什么？

- API rate limit（slowapi 或 nginx）；
- 真正的 secrets manager（AWS SecretsManager / Vault）；
- Prometheus + Grafana 看板；
- LLM 输出缓存层（Redis）；
- 用户体系 + 配额；
- 多模型 panel-of-judges 评估；
- K8s Helm chart（如有规模需求）。

> 关键：**坦诚承认现在做了什么、没做什么、为什么没做**，比假装"全做了"更显成熟。

---

## 5. 自我介绍模板（30 秒）

> 我最近完整做了一个 Production-Grade AI Agent 项目。从 RAG、Function Calling、LangGraph 编排、Multi-Agent、MCP，到工程化的 Eval / Guardrails / Tracing / Docker 部署，自己用 FastAPI + httpx 全部搭起来，263 个测试全过，一条 docker compose 命令就能跑。我特别关注**"工业级"**这件事：每个 LLM 调用都有 trace、有成本，每个工具调用都过 guardrails，部署用多阶段镜像。完整代码和文档都在 GitHub。

---

## 6. 求职渠道清单

- [ ] GitHub README 加 Demo 视频 / 截图
- [ ] LinkedIn 项目板块
- [ ] 技术博客（见 BLOG_OUTLINES.md）
- [ ] 投递要点：每份简历突出 1 个最匹配 JD 的亮点（toB 公司强调 guardrails + tracing；模型公司强调 LangGraph + MCP）

---

## 7. 谈薪要点

- 不要先报数；问对方薪资带；
- 强调"我做的项目里有 X、Y、Z 直接对应贵司岗位描述里的 A、B"；
- 关键词触发：production-grade、observability、cost control、agent eval。
