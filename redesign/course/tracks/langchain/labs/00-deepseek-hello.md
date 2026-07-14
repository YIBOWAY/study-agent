# Lab 00 — DeepSeek Hello（LangChain 轨）

## 目标

配置 DeepSeek（推荐 `.env`），用 `langchain_course` 完成一次真实 chat，确认 optional 依赖与 API key 可用。

## 前置

- 已在 `redesign/` 目录
- 有 DeepSeek API key
- 已读 [../README.md](../README.md)

## 步骤

### 1. 安装 optional 依赖

```bash
uv sync --group langchain-course
```

### 2. 配置密钥（推荐 `.env`）

```bash
cp .env.example .env
# 编辑 .env：
# DEEPSEEK_API_KEY=你的key
# 可选：
# DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
# DEEPSEEK_MODEL=deepseek-chat
```

也可以临时 export（会覆盖 `.env` 里同名变量）：

```bash
export DEEPSEEK_API_KEY=你的key
```

> `.env` 已在 `.gitignore` 中，**禁止提交**真实 key。

### 3. 跑 unit（不需要 key）

```bash
uv run pytest packages/langchain_course/tests/test_config.py packages/langchain_course/tests/test_deepseek_hello.py -q
```

期望：config 与 mock 测试通过；`test_run_hello_chat_live` **skip**（除非你设了 `RUN_DEEPSEEK_TESTS=1`）。

### 4. 一次 hello chat

```bash
PYTHONPATH=packages/langchain_course/src uv run python -c "from langchain_course.deepseek import run_hello_chat; print(run_hello_chat())"
```

期望：打印模型回复（非空字符串）。默认 prompt 要求回复 `pong` 一类短答；模型可能略有发挥，**有非空文本即过**。

### 5. 故意弄坏配置（可选）

若本机没有 export key，可临时移开 `.env` 再测；或：

```bash
env -u DEEPSEEK_API_KEY PYTHONPATH=packages/langchain_course/src uv run python -c "
from langchain_course.config import load_deepseek_settings
load_deepseek_settings(load_dotenv=False, environ={})
"
```

期望：抛出 `DeepSeekConfigError`，信息提到 `DEEPSEEK_API_KEY`。

## 检查点

- [ ] `uv sync --group langchain-course` 成功
- [ ] `.env` 已创建且未提交
- [ ] unit 测试在无 key 时可通过（integration skip）
- [ ] `run_hello_chat()` 返回非空
- [ ] 缺 key 时错误可读

## 下一步

对照 [../solutions/00-deepseek-hello-solution.md](../solutions/00-deepseek-hello-solution.md)。  
继续 Part 1：[../chapters/01-agent-kernel-langchain.md](../chapters/01-agent-kernel-langchain.md)。
