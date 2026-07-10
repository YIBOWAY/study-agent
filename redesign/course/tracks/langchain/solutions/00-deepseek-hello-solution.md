# Solution 00 — DeepSeek Hello

## 参考行为

```python
from langchain_course.deepseek import run_hello_chat

print(run_hello_chat())
# 非空 str；默认 prompt 倾向短答，不要求与 "pong" 逐字相等
```

配置加载（自动读 `redesign/.env`，**不覆盖**已 export 的环境变量）：

```python
from langchain_course.config import load_deepseek_settings

settings = load_deepseek_settings()
# settings.api_key / base_url / model
```

模型工厂：

```python
from langchain_course.deepseek import build_deepseek_chat_model

model = build_deepseek_chat_model(settings)
# ChatOpenAI(api_key=..., base_url=..., model=..., temperature=0)
```

## 为什么这样设计

- **OpenAI-compatible**：DeepSeek 走 `base_url` + `api_key`，与 `ChatOpenAI` 对齐，换其它兼容端点只改 env。
- **`.env` 可选**：本地学习用 gitignore 的 `.env`；CI / unit 用注入的 `environ=`，不读文件。
- **settings 可注入**：unit 测试传入 `DeepSeekSettings` 或 `environ={...}`。
- **integration 默认 skip**：主 CI / 无 key 贡献者不被 live API 绑架。

## 常见错误

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `DeepSeekConfigError: DEEPSEEK_API_KEY` | 未配置 key | 写 `.env` 或 `export DEEPSEEK_API_KEY=...` |
| `ModuleNotFoundError: langchain_openai` | 未装 optional group | `uv sync --group langchain-course` |
| `ModuleNotFoundError: dotenv` | 未装 python-dotenv | 同上 group（含 `python-dotenv`） |
| import 找不到 `langchain_course` | 未用项目 pytest/pythonpath | 在 `redesign/` 下用 `uv run` |
| 回复很长或不像 pong | 真实模型非确定 | F0 只要求非空；后续 lab 验结构 |
| 误提交 `.env` | 忽略规则被改 | 立刻轮换 key；确认 `.gitignore` 含 `.env` |

## 与 handwritten 对照

| Handwritten | 本 lab |
| --- | --- |
| `FakeModel` 脚本化回复 | 真实 DeepSeek chat |
| 无 API key | 需要 `DEEPSEEK_API_KEY`（`.env` 或 export） |
| 事件轨迹确定性 | 本步只验证连通性；Part 1 起有 `AgentStep` trail |
