# Solution 00 — DeepSeek Hello

## 参考行为

```python
from langchain_course.deepseek import run_hello_chat

print(run_hello_chat())
# 非空 str；默认 prompt 倾向短答，不要求与 "pong" 逐字相等
```

配置加载：

```python
from langchain_course.config import load_deepseek_settings

settings = load_deepseek_settings()  # 读环境变量
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
- **settings 可注入**：unit 测试传入 `DeepSeekSettings`，不碰真实 env。
- **integration 默认 skip**：主 CI / 无 key 贡献者不被 live API 绑架。

## 常见错误

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `DeepSeekConfigError: DEEPSEEK_API_KEY` | 未 export key | `export DEEPSEEK_API_KEY=...` |
| `ModuleNotFoundError: langchain_openai` | 未装 optional group | `uv sync --group langchain-course` |
| import 找不到 `langchain_course` | 未用项目 pytest/pythonpath | 在 `redesign/` 下用 `uv run`，勿裸 `python` 且无 path |
| 回复很长或不像 pong | 真实模型非确定 | F0 只要求非空；后续 lab 验结构 |

## 与 handwritten 对照

| Handwritten | 本 lab |
| --- | --- |
| `FakeModel` 脚本化回复 | 真实 DeepSeek chat |
| 无 API key | 需要 `DEEPSEEK_API_KEY` |
| 事件轨迹确定性 | 本步只验证连通性，尚无 AgentRunner 等价物 |
