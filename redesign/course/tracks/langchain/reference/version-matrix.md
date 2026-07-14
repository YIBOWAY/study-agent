# Framework Track Version Matrix (F0)

教学轨通过 uv **dependency groups** 安装，不进入默认 `[project].dependencies`。

## Groups（`redesign/pyproject.toml`）

| Group | Packages (lower bounds) | Used by |
| --- | --- | --- |
| `langchain-course` | `langchain-core>=1.4,<2`, `langchain-openai>=1.3,<2`, `python-dotenv>=1.0` | LC track code + labs |
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

## Verified baseline（2026-07-14）

- `langchain-core==1.4.9`
- `langchain-openai==1.3.4`
- `python-dotenv==1.2.2`
- Python 3.12.13（项目仍声明支持 3.11+）

`uv.lock` 随仓库提交，课程重现默认使用锁定结果；上面的 dependency range
用于表达可接受的 1.x API 家族，不允许无审查跨 major。

## Upgrade policy

- 同一 1.x 范围升级时：更新 lock、重跑 package/Markdown/Capstone tests。
- 跨 major 时：先新增 phase plan，再更新课程和 version boundary。
- 有 key 时补一次 live hello + live Capstone tool smoke。
- 若上游 breaking，在对应 phase plan 中改 pin 与 lab，而不是静默改主课。

## Out of tree

- 不把 LC/LG 写进 `packages/research_core` 依赖。
- 主 CI 默认不 `sync` 上述 groups。
