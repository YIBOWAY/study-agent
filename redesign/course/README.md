# 本地论文研究助手 — 从零构建一个可观察的 Agent 系统

这门课不是让你先背一堆 Agent 名词，再猜它们有什么用。你会从零构建一个完全离线的本地论文研究助手：它能接收研究问题，按步骤运行，留下可检查的 event trail，并逐步长出证据链、记忆、委派、Workbench 和生产边界。

现在先把范围说清楚：Phase R1 已经把课程入口和 Part 1 改成项目驱动学习，Phase R2 已经把 Part 2 改成同一套学习方式，Phase R3 已经把 Part 3 改成同一套学习方式，Phase R4 已经把 Part 4 改成同一套学习方式，Phase R5 已经把 Part 5 改成同一套学习方式。Parts 6-7 仍是当前 v1 材料，等 R6-R7 继续改写后，才会完整符合新的 Part 教学结构。Capstone 现在还是占位页，完整项目练习会在 R8 补齐。也就是说，R1/R2/R3/R4/R5 让你看清“终点是什么”以及“前五部分怎么学”，不是在宣称整套课程已经全部重写完成。

Part 1 还不会真的检索论文，也不会产出真实引用报告。它先训练最底层的能力：让助手跑一次，调用工具，留下轨迹，并让你能解释每一步发生了什么。后面的论文检索、证据抽取、记忆和界面，都会接在这条轨迹上。

```text
Setup
  -> Part 1: Agent Kernel, inspectable event trail
  -> Part 2: Research Core, evidence chain
  -> Part 3: Memory and Skills
  -> Part 4: Delegation
  -> Part 5: Workbench Product
  -> Part 6: Framework Comparisons
  -> Part 7: Production Readiness
  -> Capstone: complete offline paper research assistant (planned R8)
```

## Who This Is For

这份课程适合这些读者：

- 你会一点 Python，但还没有系统做过 Agent 工程。
- 你用过 ChatGPT、Claude 或 Codex，但不清楚一个 Agent runtime 内部怎么跑。
- 你已经会写业务代码，想把 Agent 从 demo 做成可测试、可维护、可观察的系统。
- 你想要一个完整、可演示的项目，而不是零散概念、单点脚本或只会聊天的玩具 demo。

如果你是完全零基础，也可以读，但请先走 Beginner Track。遇到 Python、terminal、pytest、JSON、dict/list 这些词不要硬扛，先回看 reference 材料。

## Beginner Track

按 Part 学，不要跳着把后面的章节当成互不相关的文章。每个 Part 都是在给同一个本地论文研究助手加能力。

| Step | Content | 你的助手获得的能力 |
| --- | --- | --- |
| Setup | 先读 [reference/python-terminal-primer.md](reference/python-terminal-primer.md) 和 [reference/agent-kernel-glossary.md](reference/agent-kernel-glossary.md)。再做 [labs/00-environment-check.md](labs/00-environment-check.md)，做完后对照 [solutions/00-environment-check-solution.md](solutions/00-environment-check-solution.md)。 | 你获得运行环境、命令行和术语准备；助手本身还没有新增 runtime 能力。 |
| Part 1: Agent Kernel, R1 rewritten | 先读 [chapters/00-before-agent-kernel.md](chapters/00-before-agent-kernel.md)，再读 [chapters/01-agent-kernel-foundations.md](chapters/01-agent-kernel-foundations.md)。然后做 [labs/01-agent-runner-lab.md](labs/01-agent-runner-lab.md)，尝试后再看 [solutions/01-agent-runner-solution.md](solutions/01-agent-runner-solution.md)。 | 助手获得最小 think-act-observe loop：能接收问题、请求工具、记录 `model_request` / `tool_call` / `tool_result` / `error` 等 event，并让你检查这次 run 到底怎么发生。 |
| Part 2: Research Core, R2 rewritten | 读 [chapters/02-research-core-foundations.md](chapters/02-research-core-foundations.md)。做 [labs/02-source-evidence-claim-lab.md](labs/02-source-evidence-claim-lab.md)，再对照 [solutions/02-source-evidence-claim-solution.md](solutions/02-source-evidence-claim-solution.md)。 | 助手开始理解 source -> evidence -> claim -> report 的证据链，并练习 L1/L2/L3 evidence-chain 设计。 |
| Part 3: Memory and Skills, R3 rewritten | 读 [chapters/03-memory-and-skills.md](chapters/03-memory-and-skills.md)。做 [labs/03-memory-skill-runtime-lab.md](labs/03-memory-skill-runtime-lab.md)，再对照 [solutions/03-memory-skill-runtime-solution.md](solutions/03-memory-skill-runtime-solution.md)。 | 助手获得可检查的 memory notebook、write/recall policy、skill package manifest 和 progressive disclosure，并练习 L1/L2/L3 memory-skill 设计。 |
| Part 4: Multi-Agent Delegation, R4 rewritten | 读 [chapters/04-multi-agent-delegation.md](chapters/04-multi-agent-delegation.md)。做 [labs/04-delegation-runtime-lab.md](labs/04-delegation-runtime-lab.md)，再对照 [solutions/04-delegation-runtime-solution.md](solutions/04-delegation-runtime-solution.md)。 | 助手获得 child context isolation、budget accounting、parent delegation event trail 和 unresolved-conflict visibility，并练习 L1/L2/L3 delegation policy 设计。 |
| Part 5: Workbench Product, R5 rewritten | 读 [chapters/05-workbench-product.md](chapters/05-workbench-product.md)。做 [labs/05-workbench-product-lab.md](labs/05-workbench-product-lab.md)，再对照 [solutions/05-workbench-product-solution.md](solutions/05-workbench-product-solution.md)。 | 助手获得 product adapter、FastAPI 只读 API 和 React Workbench 边界：raw domain objects 经 `from_*` adapters 组成 `WorkbenchSnapshot`，referential validation 守住引用完整性，并练习 L1/L2/L3 snapshot 设计。 |
| Part 6: Framework Comparisons, current v1 until R6 | 读 [chapters/06-framework-comparisons.md](chapters/06-framework-comparisons.md)。做 [labs/06-framework-comparisons-lab.md](labs/06-framework-comparisons-lab.md)，再对照 [solutions/06-framework-comparisons-solution.md](solutions/06-framework-comparisons-solution.md)。 | 你获得用同一任务和指标比较框架的方法。注意：这是当前 v1 材料，还没有完成 R6 的项目驱动重写。 |
| Part 7: Production Readiness, current v1 until R7 | 读 [chapters/07-production-readiness.md](chapters/07-production-readiness.md)。做 [labs/07-production-readiness-lab.md](labs/07-production-readiness-lab.md)，再对照 [solutions/07-production-readiness-solution.md](solutions/07-production-readiness-solution.md)。 | 助手获得 observability、persistence、approval、sandbox 和 docs freshness 等生产边界。注意：这是当前 v1 材料，还没有完成 R7 的项目驱动重写。 |
| Capstone: placeholder, planned R8 | 读 [capstone/README.md](capstone/README.md)，只把它当作课程终点预告。 | 当前只是完整项目的说明和占位，不是 starter、rubric 或参考答案。R8 会补齐完整本地论文研究助手 Capstone。 |

## Engineer Track

如果你已经熟悉 Python 项目、pytest 和基础 Agent 概念，可以这样走：

1. 扫一遍 [reference/agent-kernel-glossary.md](reference/agent-kernel-glossary.md)，确认课程里的词边界。
2. 读 [chapters/00-before-agent-kernel.md](chapters/00-before-agent-kernel.md) 的项目叙事和心智模型。
3. 从 [chapters/01-agent-kernel-foundations.md](chapters/01-agent-kernel-foundations.md) 开始跑 Part 1。
4. 做 [labs/01-agent-runner-lab.md](labs/01-agent-runner-lab.md)，只在自己试过以后看 [solutions/01-agent-runner-solution.md](solutions/01-agent-runner-solution.md)。
5. 继续 Part 2 到 Part 5 时，按 R2/R3/R4/R5 的 lab 做完整练习；继续 Parts 6-7 时，记住它们还是 current v1 材料。

## How To Run Commands

这份 README 放在 `redesign/course/`，但所有课程命令默认从它的上一级 `redesign/` 目录运行。如果你在仓库根目录，先进入 redesign 子项目：

```bash
cd redesign
```

如果你从别的目录打开终端，就先 `cd` 到本仓库，再进入 `redesign/`。可以用 `pwd` 确认当前路径最后一段是 `redesign`。

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

## How To Study One Part

每个 Part 都按 Build -> Inspect -> Break -> Fix -> Reflect 的节奏学。不要只读完文字，也不要只跑到 final answer。

1. **Orient**：先看这个 Part 给本地论文研究助手增加什么能力，以及它现在是 R1/R2/R3/R4/R5 rewritten 还是 current v1。
2. **Build**：从最小可运行例子开始，照着代码跑一遍，不要先改。
3. **Inspect**：打印 `event_type_sequence(...)`，确认这次 run 的步骤是不是你预期的步骤。
4. **Inspect deeper**：用 `events_to_records(...)` 看 payload，特别是 `tool_call`、`tool_result`、`error` 里的具体值。
5. **Break**：故意弄坏一个地方，比如工具名、JSON 形状、handler 逻辑或预期 sequence。
6. **Diagnose**：先读 event trail，再读异常。判断问题发生在 model response、tool-call parsing、tool registry、handler，还是 final model response。
7. **Fix**：只修一个最小原因，然后重新运行同一个检查。
8. **Practice**：做 lab 的 L1 Follow、L2 Modify、L3 Design。L3 要自己设计，不要只复制参考形状。
9. **Compare**：自己尝试后再看 solution。solution 是用来校准理解的，不是用来跳过练习的。
10. **Reflect**：用自己的话写下：这个 Part 让助手多会了什么，哪些中间证据证明它真的发生了，final answer 单独不能证明什么。

这套课里“失败”不是坏事。失败后还能留下清楚的事件轨迹，才是可维护 Agent 系统的起点。

## Common Stuck Points

| Symptom | Usually Means | What To Do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'research_core'` | Python shell 没找到本地 package | 从 `redesign/` 运行，并使用 `PYTHONPATH=packages/research_core/src uv run python` |
| `zsh: command not found: uv` | 本机没有可用的 `uv` 命令 | 先安装或修复 `uv`，再继续课程 |
| `AssertionError` | 你的实际结果和课程期望不一致 | 不要只看报错行；打印变量和 event sequence，找是哪一步不同 |
| `unknown tool 'echo'` 或 `unknown_tool` | model 请求了一个没有注册的 tool，或 JSON 里的工具名和注册表不一致 | 检查 `ToolDefinition(name=...)` 和 JSON 里的 `"name"` 是否完全一样，并确认 `AgentRunner(model=model, tools=tools)` 用的是同一个 `ToolRuntime` |
| Python shell 里粘贴多行代码乱了 | 交互模式不适合大段代码，或缩进被破坏 | 使用 lab 里的 one-shot command，或把代码放进临时 `.py` 文件 |
| final answer 是对的，但 L3 还是不该算通过 | final answer 可能只是 scripted response，不能证明中间工具真的跑了 | 同时检查 event sequence、`tool_result` payload 和中间值，例如 `tool_values == [7, 14]` |
| L3 calculator 看起来跑通，但题目仍然不通过 | 你可能只注册了 happy-path 会用到的 `add` 和 `multiply` | 题目要求完整 tool surface，就注册并断言 `add`、`subtract`、`multiply`、`divide` 四个工具 |
| `tool_values` 不对，但 sequence 是对的 | 工具调用顺序对了，但参数或 handler 逻辑不对 | 检查第二次 tool-call JSON 是否真的用了第一次结果，例如 `{"a": 7, "b": 2}` |
| `'dict' object has no attribute 'payload'` | 你把 `events_to_records(...)` 返回的 dict record 当成了 `RunEvent` | record 用 `records[3]["payload"]` |
| `'RunEvent' object is not subscriptable` | 你把原始 `RunEvent` 当成了 dict | 原始 event 用 `result.events[3].payload` |
| 只看到两个 events | model 返回了普通文本，runtime 没有进入工具流程 | 检查第一条 `FakeModelResponse(content=...)` 是否是 tool-call JSON 字符串，并且顶层 key 是 `"tool_call"` |

## Course Map

### Part 1: R1 Project-Driven Entry

- [chapters/00-before-agent-kernel.md](chapters/00-before-agent-kernel.md): Part 1 Section 1，先建立本地论文研究助手的心智模型。
- [chapters/01-agent-kernel-foundations.md](chapters/01-agent-kernel-foundations.md): Part 1 Sections 2-5，构建、检查、打坏、修复最小 Agent loop。
- [labs/01-agent-runner-lab.md](labs/01-agent-runner-lab.md): Part 1 动手练习。
- [solutions/01-agent-runner-solution.md](solutions/01-agent-runner-solution.md): Part 1 参考答案和设计解释。

### Part 2: R2 Project-Driven Research Core

- [chapters/02-research-core-foundations.md](chapters/02-research-core-foundations.md): Part 2 正文，从“回答找不到出处”的问题进入 source -> evidence -> claim -> report 证据链。
- [labs/02-source-evidence-claim-lab.md](labs/02-source-evidence-claim-lab.md): Part 2 动手练习，包含 L1 Follow、L2 Modify、Break/Fix、L3 Design。
- [solutions/02-source-evidence-claim-solution.md](solutions/02-source-evidence-claim-solution.md): Part 2 参考答案、断言解释和设计理由。

### Part 3: R3 Project-Driven Memory And Skills

- [chapters/03-memory-and-skills.md](chapters/03-memory-and-skills.md): Part 3 正文，从“助手没有笔记本，下次不能接着研究”的问题进入 memory notebook 和 skill package。
- [labs/03-memory-skill-runtime-lab.md](labs/03-memory-skill-runtime-lab.md): Part 3 动手练习，包含 L1 Follow、L2 Modify/Break/Fix、L3 Design。
- [solutions/03-memory-skill-runtime-solution.md](solutions/03-memory-skill-runtime-solution.md): Part 3 参考答案、断言解释、L3 参考设计和不变量。

### Part 4: R4 Project-Driven Delegation

- [chapters/04-multi-agent-delegation.md](chapters/04-multi-agent-delegation.md): Part 4 正文，从“把研究任务外包给 child 但不能泄露 context、超预算或吞失败”的问题进入 delegation runtime。
- [labs/04-delegation-runtime-lab.md](labs/04-delegation-runtime-lab.md): Part 4 动手练习，包含 L1 Follow、L2 Modify/Break-Fix、L3 Design。
- [solutions/04-delegation-runtime-solution.md](solutions/04-delegation-runtime-solution.md): Part 4 参考答案、断言解释、L3 参考设计和不变量。

### Part 5: R5 Project-Driven Workbench Product

- [chapters/05-workbench-product.md](chapters/05-workbench-product.md): Part 5 正文，从“研究员看不懂代码，要一个能打开、能核对出处的工作台”的问题进入 product adapter、`WorkbenchSnapshot` 和三层边界。
- [labs/05-workbench-product-lab.md](labs/05-workbench-product-lab.md): Part 5 动手练习，包含 L1 Follow、L2 Modify/Break-Fix、L3 Design。
- [solutions/05-workbench-product-solution.md](solutions/05-workbench-product-solution.md): Part 5 参考答案、断言解释、L3 参考设计和不变量。

### Parts 6-7: Current v1 Materials

这些文件现在可以读、可以做，但还没有完成 R6-R7 的项目驱动重写。

- Part 6: [chapters/06-framework-comparisons.md](chapters/06-framework-comparisons.md), [labs/06-framework-comparisons-lab.md](labs/06-framework-comparisons-lab.md), [solutions/06-framework-comparisons-solution.md](solutions/06-framework-comparisons-solution.md)
- Part 7: [chapters/07-production-readiness.md](chapters/07-production-readiness.md), [labs/07-production-readiness-lab.md](labs/07-production-readiness-lab.md), [solutions/07-production-readiness-solution.md](solutions/07-production-readiness-solution.md)

### Capstone

- [capstone/README.md](capstone/README.md): 当前 Capstone 占位页。它说明最终项目会是什么，但现在不要把它当成已经完成的 starter、rubric 或 solution。完整 Capstone 计划在 R8 补齐。

### Framework Reports

- [framework_comparisons/reports/echo-tool-task.md](framework_comparisons/reports/echo-tool-task.md): echo-tool shared task report。
- [framework_comparisons/reports/recommendation-matrix.md](framework_comparisons/reports/recommendation-matrix.md): framework recommendation matrix。

## Current Rewrite Status

实现状态和教学重写状态不是一回事。很多 runtime/product 代码已经存在，Parts 2-5 已完成 R2/R3/R4/R5 教学重写，Parts 6-7 也有 current v1 学习材料；但新的项目驱动教学法会继续通过 R6-R9 完成。

| Phase | Teaching status |
| --- | --- |
| R1 | 当前入口页、roadmap、template、Capstone placeholder，以及 Part 1 项目驱动材料 |
| R2 | 已把 Part 2 改成 source -> evidence -> claim -> report 的项目驱动学习结构 |
| R3 | 已把 Part 3 改成 Memory notebook、Skill package、Break/Fix 和 L3 invariants 的项目驱动学习结构 |
| R4 | 已把 Part 4 改成 child context isolation、budget accounting、delegate event trail、unresolved conflicts 的项目驱动学习结构 |
| R5 | 已把 Part 5 改成 product adapter、`WorkbenchSnapshot`、referential validation 和三层 core/API/UI 边界的项目驱动学习结构，并把 Part 5 纳入 markdown 代码块门禁 |
| R6-R7 | 计划继续把 Parts 6-7 改成同一套 Build -> Inspect -> Break -> Fix -> Reflect 学习结构 |
| R8 | 计划补齐完整 Capstone：fixtures、starter、solution、rubric、trajectory、report、reflection |
| R9 | 计划补齐参考材料、troubleshooting、设计决策索引、讨论题和 glossary 更新 |

学习时用一个简单判断：如果你正在 Parts 1-4，就按 R1/R2/R3/R4 新结构认真做完整循环；如果你正在 Parts 5-7，就把它们当作有效的 current v1 材料，同时知道后续还会被重新组织成更强的项目驱动版本。
