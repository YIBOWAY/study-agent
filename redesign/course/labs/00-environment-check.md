# Lab 00: Environment Check

## Goal

这个 lab 只做一件事：确认你的本地环境能跑课程代码。

不要跳过它。很多“我是不是没理解 Agent”的问题，最后其实只是目录、`PYTHONPATH` 或 Python 环境不对。

预计时间：10 到 15 分钟。

## Step 1: Go To The Redesign Directory

```bash
cd /Users/sunyibo/programs/study-agent/redesign
```

确认当前位置：

```bash
pwd
```

你应该看到：

```text
/Users/sunyibo/programs/study-agent/redesign
```

## Step 2: Check Python Through uv

```bash
uv run python --version
```

你不需要记住具体小版本，但它应该是 Python 3.11 或更高。

## Step 3: Run A Small Test

```bash
uv run pytest tests/research_core/test_fakes.py -q
```

你应该看到测试通过。这个测试证明课程会用到的 `FakeModel` 可以正常工作。

## Step 4: Import The Runtime Package

运行这个 one-shot command：

```bash
PYTHONPATH=packages/research_core/src uv run python - <<'PY'
from research_core.runtime import AgentMessage, MessageRole

message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")
print(message.to_provider_dict())
PY
```

你应该看到：

```text
{'role': 'user', 'content': 'hello'}
```

这说明 Python 找到了本地 `research_core` package，而且最基础的 message contract 能用。

## Step 5: Run The Full Suite

```bash
uv run pytest -q
uv run ruff check .
```

这一步时间会稍长一点。它确认整个 redesign 当前基线是健康的。

## If Something Fails

| Error | Meaning | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'research_core'` | 没有把本地 package 放进 Python 搜索路径 | 确认从 `redesign/` 运行，并使用 `PYTHONPATH=packages/research_core/src` |
| `No such file or directory` | 当前目录不对 | 重新运行 `cd /Users/sunyibo/programs/study-agent/redesign` |
| `command not found: uv` | 本机找不到 `uv` | 先安装或修复 `uv` |
| pytest 有失败 | 当前代码基线不干净 | 先看失败测试名，不要继续后面的课程 |

## Done Means

完成这个 lab 后，你应该确认三件事：

- 能从 `redesign/` 跑命令。
- 能 import `research_core.runtime`。
- 能跑 pytest 和 ruff。

然后再进入 Chapter 01。
