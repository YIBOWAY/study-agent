# Framework Track Version Matrix (F0)

教学轨通过 uv **dependency groups** 安装，不进入默认 `[project].dependencies`。

## Groups（`redesign/pyproject.toml`）

| Group | Packages (lower bounds) | Used by |
| --- | --- | --- |
| `langchain-course` | `langchain-core>=0.3`, `langchain-openai>=0.2`, `python-dotenv>=1.0` | LC track code + labs |
| `langgraph-course` | above + `langgraph>=0.2` | LG track (from F4) |

Install:

```bash
uv sync --group langchain-course
# later:
uv sync --group langgraph-course
```

## DeepSeek defaults

| Setting | Default |
| --- | --- |
| Base URL | `https://api.deepseek.com/v1` |
| Model | `deepseek-chat` |
| Client | `langchain_openai.ChatOpenAI` |

## Upgrade policy

- F0 使用 **lower bounds**，不锁死精确 patch，以便 uv 解析。
- 升级 major/minor 时：重跑 `packages/langchain_course/tests`，并做一次 live hello（若有 key）。
- 若上游 breaking，在对应 phase plan 中改 pin 与 lab，而不是静默改主课。

## Out of tree

- 不把 LC/LG 写进 `packages/research_core` 依赖。
- 主 CI 默认不 `sync` 上述 groups。
