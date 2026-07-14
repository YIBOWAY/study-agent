# LangChain 并行教学轨

这是与 handwritten 主课（R1–R9）**并行**的 LangChain 完整镜像轨入口。  
**不替代** `course/` 主线，也不进入 `research_core` 产品路径。

## 你在学什么

用 **真实 LangChain Core 执行路径**重做「本地论文研究助手」：
`BaseChatModel/BaseTool`、`Document/BaseRetriever`、LCEL Runnable、message
history、parallel workers、callback 与执行前 approval，最后做真实-loop Capstone。

顺序约定（设计已定）：

1. 先完整学完本轨 Parts 1–7 + Capstone（F1–F3）
2. 再进入 [LangGraph 轨](../langgraph/README.md)（F4–F5）

## 与主课的关系

| | Handwritten 主课 | 本轨 |
| --- | --- | --- |
| 代码 | `packages/research_core` | `packages/langchain_course` |
| 材料 | `course/chapters` 等 | `course/tracks/langchain/` |
| 模型 | 默认 `FakeModel` 离线 | 默认 **DeepSeek 真实 API** |
| 依赖 | 主 CI 必装 | optional：`uv sync --group langchain-course` |

对照靠**同一场景与验收语义**，不共享 Python import。禁止 `langchain_course` ↔ `research_core` 互相 import。  
概念映射见 [reference/handwritten-mapping.md](reference/handwritten-mapping.md)。

## 环境与 `.env`

| 变量 | 必需 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 是（跑 live lab） | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | 否 | 默认 `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 否 | 默认 `deepseek-chat` |
| `RUN_DEEPSEEK_TESTS` | 否 | 设为 `1` 才跑 live integration 测试 |

推荐把 key 放在 **`redesign/.env`**（已 gitignore），不要提交：

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=...
```

`load_deepseek_settings()` 会自动读取 `.env` / `.env.local`（**不覆盖**已在 shell 里 export 的变量）。

## 安装与命令

在 `redesign/` 下：

```bash
uv sync --group langchain-course

# 无 key 的 unit 测试（配置 + mock + Parts 1–7）
uv run pytest packages/langchain_course/tests -q

# LC Capstone 参考实现
uv run pytest course/tracks/langchain/capstone/solution -q

# 主课 suite（应仍离线全绿）
uv run pytest -q

# 一次 hello（读 .env 或环境变量）
PYTHONPATH=packages/langchain_course/src uv run python -c "from langchain_course.deepseek import run_hello_chat; print(run_hello_chat())"

# live integration（可选，hello + Capstone tool smoke）
RUN_DEEPSEEK_TESTS=1 uv run pytest \
  packages/langchain_course/tests \
  course/tracks/langchain/capstone/solution -m integration -q

# 全部 LC 章节 / Lab / Solution 的离线 Python 块
uv run pytest tests/course/test_markdown_python_blocks.py -q
```

`pytest` 会从 `pyproject.toml` 读取 `packages/langchain_course/src`；普通
`uv run python` 不会读取 pytest 的这项配置，所以课程里的 shell 示例会显式写
`PYTHONPATH=packages/langchain_course/src`。

## 学习路径（当前）

| 步骤 | 材料 | 状态 |
| --- | --- | --- |
| 0 | [labs/00-deepseek-hello.md](labs/00-deepseek-hello.md) | F0 完成 |
| 1 | [chapters/01-agent-kernel-langchain.md](chapters/01-agent-kernel-langchain.md) → [labs/01-tool-calling-agent-lab.md](labs/01-tool-calling-agent-lab.md) | F1 完成 |
| 2 | [chapters/02-research-core-langchain.md](chapters/02-research-core-langchain.md) → [labs/02-evidence-chain-lab.md](labs/02-evidence-chain-lab.md) | F3R 补全：Document/Retriever/Runnable |
| 3 | [chapters/03-memory-skills-langchain.md](chapters/03-memory-skills-langchain.md) → [labs/03-memory-skills-lab.md](labs/03-memory-skills-lab.md) | F3R 补全：message history + policy |
| 4 | [chapters/04-delegation-langchain.md](chapters/04-delegation-langchain.md) → [labs/04-delegation-lab.md](labs/04-delegation-lab.md) | F3R 补全：RunnableParallel + budgets |
| 5 | [chapters/05-workbench-langchain.md](chapters/05-workbench-langchain.md) → [labs/05-workbench-lab.md](labs/05-workbench-lab.md) | F3R 教学闭环 |
| 6 | [chapters/06-comparisons-langchain.md](chapters/06-comparisons-langchain.md) → [labs/06-comparisons-lab.md](labs/06-comparisons-lab.md) | F3R 真实 LC baseline |
| 7 | [chapters/07-production-langchain.md](chapters/07-production-langchain.md) → [labs/07-production-lab.md](labs/07-production-lab.md) | F3R callbacks + pre-tool approval |
| Capstone | [capstone/README.md](capstone/README.md) | F3R 真实 tool loop + optional live smoke |

## 当前进度

- [x] F0：包脚手架 + DeepSeek 配置 + hello + `.env` 支持
- [x] F1：Parts 1–2（agent kernel + evidence chain）
- [x] F2：Parts 3–4（memory/skills + multi-worker delegation）
- [x] F3：Parts 5–7 + Capstone
- [x] F3R：真实 LC 原语、教学闭环、Capstone 与 Markdown 门禁补全

## 诚实边界

- 真实 API **非确定性**；lab 优先验结构/工具是否调用，少用全文相等。
- 有费用与限流；控制步数与上下文。
- 本轨不宣称替代产品 runtime；产品仍以 handwritten `research_core` 为准。
- Part 1 **不依赖 LangGraph**（`bind_tools` 手写可观察 loop）。
- 版本矩阵见 [reference/version-matrix.md](reference/version-matrix.md)。
- 原语速查见 [reference/langchain-primitives.md](reference/langchain-primitives.md)。
- 复习检查点见 [reference/study-checkpoints.md](reference/study-checkpoints.md)。
- 排障见 [reference/troubleshooting.md](reference/troubleshooting.md)。

## 设计文档

- [并行轨设计](../../../docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md)
- [F0 计划](../../../docs/plans/2026-07-10-phase-f0-langchain-langgraph-scaffold.md)
- [F1 计划](../../../docs/plans/2026-07-10-phase-f1-langchain-parts-1-2.md)
- [F2 计划](../../../docs/plans/2026-07-10-phase-f2-langchain-parts-3-4.md)
- [F3 计划](../../../docs/plans/2026-07-10-phase-f3-langchain-parts-5-7-capstone.md)
- [F3R 补全计划](../../../docs/plans/2026-07-14-phase-f3r-langchain-teaching-completion.md)
