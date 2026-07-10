# LangGraph 并行教学轨

这是与 handwritten 主课 **并行** 的 LangGraph 完整镜像轨入口。  
**不替代** 主课；**不** import `research_core`。

## 学习顺序（强制）

1. 先完成 [LangChain 轨](../langchain/README.md)（F0 hello + F1–F3 Parts 1–7 + Capstone）
2. 再系统学习本轨（F4–F5）

LangChain 是本轨的教学前置：图编排建立在你已熟悉的 tool / message / RAG 心智之上。

## 当前进度（F0）

F0 **仅占位**：

- 包路径：`packages/langgraph_course`（版本标记包；图代码从 F4 起写）
- optional 依赖：`uv sync --group langgraph-course`（含 `langgraph` + LC 生态）
- 完整 Parts / Capstone：**尚未交付**

请先去 LC 轨做 [Lab 00 DeepSeek Hello](../langchain/labs/00-deepseek-hello.md)。

## 边界

| 禁止 | 说明 |
| --- | --- |
| import `research_core` | 框架原生重写，零混合 |
| 被 `apps/*` 依赖 | 教学 artifact，非产品 |
| 跳过 LC 直接写 LG Capstone | 设计顺序：先 LC 后 LG |

## 设计文档

- [并行轨设计](../../../docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md)
- [F0 计划](../../../docs/plans/2026-07-10-phase-f0-langchain-langgraph-scaffold.md)
