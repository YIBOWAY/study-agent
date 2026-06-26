# Solution 00: Environment Check

这份 solution 不是为了让你抄答案，而是帮你判断自己看到的结果是否正常。

## Working Directory

Command:

```bash
pwd
```

Expected shape:

```text
/Users/sunyibo/programs/study-agent/redesign
```

如果不是这个目录，后面的路径大概率会错。

## Python Version

Command:

```bash
uv run python --version
```

Expected shape:

```text
Python 3.11.x
```

或者更高版本。项目要求是 Python 3.11+。

## FakeModel Test

Command:

```bash
uv run pytest tests/research_core/test_fakes.py -q
```

Expected shape:

```text
... passed
```

具体 passed 数可能随着项目增长变化。关键是 exit code 为 0，并且没有 failure。

## Runtime Import

Command:

```bash
PYTHONPATH=packages/research_core/src uv run python - <<'PY'
from research_core.runtime import AgentMessage, MessageRole

message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")
print(message.to_provider_dict())
PY
```

Expected output:

```text
{'role': 'user', 'content': 'hello'}
```

这说明：

- `research_core.runtime` 能被 import。
- `AgentMessage` 能创建。
- `MessageRole.USER` 会转成 provider-facing 的 `"user"`。

## Full Verification

Command:

```bash
uv run pytest -q
uv run ruff check .
```

Expected shape:

```text
... passed
All checks passed!
```

如果 full suite 通过，你就可以开始 Chapter 01。 如果 full suite 不通过，先不要把失败归因到你对 Agent 的理解，优先看测试输出里第一个失败。
