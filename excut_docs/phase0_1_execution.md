# Phase 0 + Phase 1 执行文档（Runbook）

## 1. 环境要求

你当前提供的环境是：

- 本地 `conda` 虚拟环境：`ai-agent`

本阶段建议环境：

- Python `3.10+`（推荐 `3.10` 或 `3.11`）
- pip 可用
- 可以访问一个 OpenAI-compatible 模型接口

## 2. 版本要求

- Python：`>=3.10`
- FastAPI：`0.115.0`
- uvicorn：`0.30.6`
- pydantic：`2.9.2`
- pytest：`8.3.3`

## 3. 依赖安装步骤

先打开终端，进入项目目录：

```bash
cd /e/programs/AI_Agent_program/8w-plan
```

激活 conda 环境：

```bash
conda activate ai-agent
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 4. 环境变量配置步骤

当前项目提供了示例配置文件：

- `.env.example`

你需要复制为 `.env`：

```bash
cp .env.example .env
```

如果是在 Windows 的某些 shell 下 `cp` 不可用，也可以手动复制。

然后修改 `.env` 里的这些项：

```env
LLM_API_KEY=your_real_api_key_here
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=your_model_name
LLM_TIMEOUT=60
```

> `.env` 里的占位值建议保持 ASCII 文本，不要把中文说明直接写在等号右侧，避免把注释当成真实配置读进去。

如果你使用的是标准 OpenAI 接口风格，`LLM_BASE_URL` 通常类似：

```env
LLM_BASE_URL=https://api.openai.com/v1
```

## 5. 项目目录说明

```bash
8w-plan/
├─ app/
│  ├─ api/routes/
│  ├─ core/
│  ├─ schemas/
│  ├─ services/
│  └─ main.py
├─ tests/
├─ scripts/                  # 评估脚本（Phase 2）
├─ eval/                     # 评估数据（Phase 2）
├─ study_docs/
├─ excut_docs/
├─ architecture_docs/
├─ .env.example
├─ requirements.txt
├─ pytest.ini
└─ README.md
```

目录含义：

- `app/main.py`：应用入口
- `app/api/routes/`：接口层
- `app/core/`：配置与日志
- `app/schemas/`：请求与响应结构
- `app/services/`：LLM 调用和业务逻辑
- `tests/`：最小测试
- `study_docs/`：学习文档
- `excut_docs/`：执行文档
- `architecture_docs/`：架构文档

## 6. 初始化步骤

在第一次运行前，确认下面几件事：

1. 已激活 `ai-agent`
2. 已执行 `pip install -r requirements.txt`
3. 已创建 `.env`
4. `.env` 中配置了真实可用的 `LLM_API_KEY`

## 7. 启动步骤

### 方式一：开发模式启动（推荐）

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果启动成功，你会看到类似输出：

```bash
Uvicorn running on http://127.0.0.1:8000
```

### 访问方式

打开浏览器：

- 根路径：`http://127.0.0.1:8000/`
- 健康检查：`http://127.0.0.1:8000/health`
- Swagger 文档：`http://127.0.0.1:8000/docs`

## 8. 测试步骤

运行全部测试：

```bash
python -m pytest -v
```

> **重要**：必须使用 `python -m pytest` 而非 `pytest`，否则会出现 `ModuleNotFoundError: No module named 'app'`。

如果你只想先跑健康检查：

```bash
python -m pytest tests/test_health.py
```

如果只想跑结构化提取接口测试：

```bash
python -m pytest tests/test_extract.py
```

> Phase 2 新增了 57 个测试，详见 `excut_docs/phase2_execution.md`。

## 9. 接口验证步骤

### 9.1 健康检查

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

### 9.2 聊天接口

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"请用中文解释什么是 FastAPI"}'
```

### 9.3 结构化提取接口

```bash
curl -X POST http://127.0.0.1:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"FastAPI 是一个现代 Python Web 框架，性能高，开发快，适合构建 API 服务。"}'
```

预期返回格式类似：

```json
{
  "summary": "FastAPI 是一个高性能、开发效率高的 Python Web 框架。",
  "keywords": ["FastAPI", "Python", "Web 框架", "API 服务"],
  "sentiment": "positive",
  "model": "你的模型名"
}
```

## 10. 常见报错与排查方法

### 报错 1：`LLM_API_KEY is not configured`

原因：
- 你没有创建 `.env`
- 或 `.env` 里没有正确填写 `LLM_API_KEY`

处理方法：
- 检查 `.env` 是否存在
- 检查变量名是否拼写正确

### 报错 2：模型接口 401 / 403

原因：
- API key 无效
- Base URL 不对
- 模型平台权限不足

处理方法：
- 检查 `LLM_API_KEY`
- 检查 `LLM_BASE_URL`
- 检查模型名是否正确

### 报错 3：模型接口 404

原因：
- `LLM_BASE_URL` 不兼容 `/chat/completions`
- 模型名不存在

处理方法：
- 确认你用的是 OpenAI-compatible 接口
- 确认 `LLM_MODEL` 存在

### 报错 4：`ModuleNotFoundError: No module named 'app'`

原因：
- 当前不在 `8w-plan` 根目录下执行命令
- 或使用了 `pytest` 而非 `python -m pytest`

处理方法：
- 先执行：

```bash
cd E:\programs\AI_Agent_program\8w-plan
```

- 使用 `python -m pytest` 而非 `pytest`

### 报错 5：提取接口返回 500

原因：
- 模型返回内容不是合法 JSON
- 或接口本身调用失败

处理方法：
- 先看终端日志
- 检查模型是否支持 `response_format`
- 若平台不支持，后续可改成 prompt 强约束 JSON 输出

## 11. 成功运行的标志

你看到下面这些现象，就说明本阶段基本跑通了：

- `uvicorn` 启动成功
- `GET /health` 返回 `{"status": "ok"}`
- `POST /api/v1/chat` 能返回模型回复
- `POST /api/v1/extract` 能返回结构化字段
- `pytest` 通过
- 浏览器能打开 `/docs`

## 12. 如何验证当前阶段已经完成

请逐项确认：

- [ ] 我已能在 `ai-agent` 环境中启动服务
- [ ] 我已配置好 `.env`
- [ ] 我已能访问 `/docs`
- [ ] 我已能调用聊天接口
- [ ] 我已能调用结构化提取接口
- [ ] 我已跑通测试
- [ ] 我能解释目录结构和主要文件职责

如果这几项都完成了，就说明 `Phase 0 + Phase 1` 已经达到最小可交付状态，可以进入下一阶段。
