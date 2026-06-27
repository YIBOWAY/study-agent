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
8. 读 `chapters/02-research-core-foundations.md`，理解 source、evidence、claim、report 的证据链。
9. 做 `labs/02-source-evidence-claim-lab.md`，再看 `solutions/02-source-evidence-claim-solution.md`。
10. 读 `chapters/03-memory-and-skills.md`，理解 memory policy 和 skill progressive disclosure。
11. 做 `labs/03-memory-skill-runtime-lab.md`，再看 `solutions/03-memory-skill-runtime-solution.md`。
12. 读 `chapters/04-multi-agent-delegation.md`，理解 child context isolation 和 budget accounting。
13. 做 `labs/04-delegation-runtime-lab.md`，再看 `solutions/04-delegation-runtime-solution.md`。
14. 读 `chapters/05-workbench-product.md`，理解 product adapter、FastAPI API 和 React Workbench 的边界。
15. 做 `labs/05-workbench-product-lab.md`，再看 `solutions/05-workbench-product-solution.md`。
16. 读 `chapters/06-framework-comparisons.md`，理解如何用同一任务和指标比较框架。
17. 做 `labs/06-framework-comparisons-lab.md`，再看 `solutions/06-framework-comparisons-solution.md`。

## Engineer Track

如果你已经熟悉 Python 项目、pytest 和基础 Agent 概念，可以直接从 Chapter 01 开始。建议仍然扫一眼 glossary，因为本项目里的词有明确边界：`AgentMessage` 不是 provider message，`RunEvent` 不是普通 log，`FakeModel` 也不是 mock 的随手替代品。

## How To Run Commands

所有课程命令默认从 `redesign/` 目录运行。如果你在仓库根目录，先进入 redesign 子项目：

```bash
cd redesign
```

如果你从别的目录打开终端，就先 `cd` 到本仓库，再进入 `redesign/`。

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
- `chapters/02-research-core-foundations.md`
- `labs/02-source-evidence-claim-lab.md`
- `solutions/02-source-evidence-claim-solution.md`
- `chapters/03-memory-and-skills.md`
- `labs/03-memory-skill-runtime-lab.md`
- `solutions/03-memory-skill-runtime-solution.md`
- `chapters/04-multi-agent-delegation.md`
- `labs/04-delegation-runtime-lab.md`
- `solutions/04-delegation-runtime-solution.md`
- `chapters/05-workbench-product.md`
- `labs/05-workbench-product-lab.md`
- `solutions/05-workbench-product-solution.md`
- `chapters/06-framework-comparisons.md`
- `labs/06-framework-comparisons-lab.md`
- `solutions/06-framework-comparisons-solution.md`
- `framework_comparisons/reports/echo-tool-task.md`
- `framework_comparisons/reports/recommendation-matrix.md`

## Implementation Coverage

| Runtime phase | Code status | Course status |
| --- | --- | --- |
| Phase 0: Scaffold | Complete | Chapter 00, Lab 00, Solution 00 |
| Phase 1: Agent Kernel | Complete | Chapter 01, Lab 01, Solution 01 |
| Phase 2: Research Core | Complete | Chapter 02, Lab 02, Solution 02 |
| Phase 3: Memory and Skills | Complete | Chapter 03, Lab 03, Solution 03 |
| Phase 4: Multi-Agent Delegation | Complete | Chapter 04, Lab 04, Solution 04 |
| Phase 5: Workbench Product | Complete | Chapter 05, Lab 05, Solution 05 |
| Phase 6: Framework Comparisons | In Progress | Chapter 06, Lab 06, Solution 06, and comparison reports |
| Phase 7: Production Readiness | Pending | Pending until production contracts exist |

Future chapters should keep the same promise: explain the idea in plain language, show the smallest runnable version, inspect the event trail, break it deliberately, and give the learner a concrete checkpoint.
