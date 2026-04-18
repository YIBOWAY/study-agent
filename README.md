# Phase 0 + Phase 1 - Minimal LLM Backend

这是 8 周计划中 `Phase 0 + Phase 1` 的最小可交付项目。

目标：
- 建立 Python / FastAPI 工程基础
- 打通 LLM API 调用链路
- 完成结构化输出的最小实践
- 为后续 RAG / Tool Use / Agent 阶段保留清晰扩展点

## Features

- `GET /health`：健康检查
- `POST /api/v1/chat`：基础聊天接口
- `POST /api/v1/extract`：结构化提取接口
- `.env` 配置管理
- 标准化日志
- 基础测试

## Quick Start

1. 激活你的 conda 环境：`ai-agent`
2. 安装依赖：
   - `pip install -r requirements.txt`
3. 复制环境变量：
   - 将 `.env.example` 复制为 `.env`
4. 启动服务：
   - `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

## Docs

- 学习文档：`study_docs/phase0_1_learning.md`
- 执行文档：`excut_docs/phase0_1_execution.md`
- 架构文档：`architecture_docs/phase0_1_architecture.md`

## Suggested Learning Order

1. 先看 `app/main.py`
2. 再看 `app/api/routes/chat.py`
3. 然后看 `app/services/llm_service.py`
4. 最后结合文档理解配置、日志、测试
