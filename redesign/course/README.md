# Course Start Here

这套课程的目标不是让你背 Agent 名词，而是让你亲手做出一个能观察、能测试、能失败后复盘的研究型 Agent 系统。你会从一个最小的离线 Agent loop 开始，慢慢走到 memory、skills、delegation、workbench product 和 production readiness。

## Who This Is For

这份课程适合三类读者：

- 你会一点 Python，但还没有系统做过 Agent 工程。
- 你用过 ChatGPT、Claude 或 Codex，但不清楚一个 Agent runtime 内部怎么跑。
- 你已经会写业务代码，想把 Agent 从 demo 做成可测试、可维护、可上线的系统。

如果你是完全零基础，也可以读，但请先走 Beginner Track。遇到 Python、terminal、pytest、JSON 这些词不要硬扛，先看参考页。

## Beginner Track

推荐顺序：

1. 读 `reference/python-terminal-primer.md`，弄清楚 terminal、`uv`、Python shell、`PYTHONPATH` 是什么。
2. 读 `reference/agent-kernel-glossary.md`，先把课程里的高频词看一遍。
3. 读 `chapters/00-before-agent-kernel.md`，建立第一张心智地图。
4. 做 `labs/00-environment-check.md`，确认本机环境可以跑。
5. 读 `chapters/01-agent-kernel-foundations.md`。
6. 做 `labs/01-agent-runner-lab.md`。
7. 对答案时看 `solutions/01-agent-runner-solution.md`，不要一开始就看。

## Engineer Track

如果你已经熟悉 Python 项目、pytest 和基础 Agent 概念，可以直接从 Chapter 01 开始。建议仍然扫一眼 glossary，因为本项目里的词有明确边界：`AgentMessage` 不是 provider message，`RunEvent` 不是普通 log，`FakeModel` 也不是 mock 的随手替代品。

## How To Run Commands

所有课程命令默认从 `redesign/` 目录运行：

```bash
cd /Users/sunyibo/programs/study-agent/redesign
```

测试整个 redesign 项目：

```bash
uv run pytest -q
uv run ruff check .
```

打开能 import `research_core` 的 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

为什么要写 `PYTHONPATH`？因为 `pytest` 会从 `pyproject.toml` 读取 package path，但普通 `uv run python` 不会自动继承这份 pytest 配置。课程里所有 Python shell 示例都显式写出来，避免新手卡在 import 上。

## How To Study One Chapter

每章都按这个节奏学：

1. 先看目标，知道这一章要解决什么问题。
2. 再看“人话版心智模型”，不要急着背类名。
3. 跑最小例子，只确认它能动。
4. 打印 event sequence，看系统实际发生了什么。
5. 故意弄坏一次，观察错误事件。
6. 最后看 solution，用答案检查你的理解。

这套课里“失败”不是坏事。失败后还能留下清楚的事件轨迹，才是可维护 Agent 系统的起点。

## Common Stuck Points

| Symptom | Usually Means | What To Do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'research_core'` | Python shell 没找到本地 package | 从 `redesign/` 运行，并使用 `PYTHONPATH=packages/research_core/src uv run python` |
| `zsh: command not found: uv` | 本机没有可用的 `uv` 命令 | 先安装或修复 `uv`，再继续课程 |
| `AssertionError` | 你的实际结果和课程期望不一致 | 打印变量，看 event sequence 哪一步不同 |
| `unknown tool 'echo'` | 模型请求了一个没有注册的 tool | 先注册 `ToolDefinition(name="echo", ...)` |
| Python shell 里粘贴多行代码乱了 | 交互模式不适合大段代码 | 使用 lab 里的 one-shot command，或把代码放进临时 `.py` 文件 |

## Course Map

Current beginner-ready materials:

- `reference/python-terminal-primer.md`
- `reference/agent-kernel-glossary.md`
- `chapters/00-before-agent-kernel.md`
- `labs/00-environment-check.md`
- `solutions/00-environment-check-solution.md`
- `chapters/01-agent-kernel-foundations.md`
- `labs/01-agent-runner-lab.md`
- `solutions/01-agent-runner-solution.md`

Future chapters should keep the same promise: explain the idea in plain language, show the smallest runnable version, inspect the event trail, break it deliberately, and give the learner a concrete checkpoint.
