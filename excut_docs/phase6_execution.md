# Phase 6 执行手册：MCP

---

## 0. 前置

```powershell
conda activate ai-agent
python -m pytest tests/test_mcp_*.py tests/test_tool_registry_with_mcp.py -q
# 期望全部通过
```

如果你机器上没装 Node.js，外部 MCP Server 那部分跳过，自连接演示仍可跑。

---

## 1. 第一步：把本项目变成 MCP Server

```powershell
# 单独终端启动 MCP Server（stdio 模式，看似"卡住"实为等输入）
python -m scripts.run_mcp_server
```

> 不要 Ctrl+C，让它就这么挂着。MCP Server 用 stdin/stdout 通信，标准输出会被协议占用，所以 print 的日志看起来像没动静。

---

## 2. 自连接 smoke test：验证能跑通完整握手

新开一个终端：
```powershell
conda activate ai-agent
python -m scripts.smoke_test_mcp
```

预期输出：
```
[smoke] connecting to local MCP server ...
[smoke] discovered tools: ['web_search', 'calculate', 'get_current_time', ...]
[smoke] calling calculate(...): result=4
[smoke] OK
```

这个脚本同时充当**最简单的 MCP Client**，是看协议交互最直观的入口。读它的源码花 5 分钟，比读 spec 一小时管用。

---

## 3. 集成外部 MCP Server（可选，需要 Node.js）

```powershell
# 一次性装个示范用的 filesystem server（Anthropic 官方）
npx -y @modelcontextprotocol/server-filesystem --help
```

然后在 `.env` 加：
```
MCP_EXTERNAL_SERVERS=filesystem:npx -y @modelcontextprotocol/server-filesystem C:\workspace
```

启 FastAPI：
```powershell
uvicorn app.main:app --reload
```

启动日志应能看到：
```
INFO  Connected MCP server 'filesystem' with N tools
```

调用：
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/mcp/servers
Invoke-RestMethod http://localhost:8000/api/v1/mcp/tools
```

应能看到 `mcp__filesystem__read_file`、`mcp__filesystem__list_directory` 等。

---

## 4. 让 Agent 用 MCP 工具

Phase 6 的 ToolRegistry 已经把 MCP 工具混进了同一份 schema：

```powershell
$body = @{
  topic = "总结当前工作目录下的 README"
  mode  = "agent"
  top_k = 3
} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/research -ContentType "application/json" -Body $body
```

Agent 内部的工具循环可能挑出 `mcp__filesystem__read_file` 来读 README，然后总结。

---

## 5. 调试端点：直接打某个 MCP 工具

```powershell
$body = @{ arguments = @{ path = "C:\workspace\README.md" } } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/mcp/tools/mcp__filesystem__read_file/invoke -ContentType "application/json" -Body $body
```

这个端点专门用于绕开 LLM、直接调用工具看返回——做工具开发/排错时很有用。它会过 guardrails 白名单，防止生产被滥用。

---

## 6. 把别的 Client 接进来（Claude Desktop 演示）

如果你装了 Claude Desktop，可以在它的配置（`%APPDATA%\Claude\claude_desktop_config.json`）加：

```json
{
  "mcpServers": {
    "ai-agent-platform": {
      "command": "python",
      "args": ["-m", "scripts.run_mcp_server"],
      "cwd": "E:\\programs\\AI_Agent_program\\8w-plan",
      "env": {
        "PYTHONPATH": "E:\\programs\\AI_Agent_program\\8w-plan"
      }
    }
  }
}
```

重启 Claude Desktop，就能在它内部用我们的 web_search / calculate 等工具——非常直观地说明"MCP 让工具跨厂商可移植"。

---

## 7. 常见踩坑

| 现象 | 原因 | 修复 |
|------|------|------|
| smoke_test 卡死 | server 没启 / cwd 不对 | 确保先跑 `python -m scripts.run_mcp_server` |
| Windows 路径里的 `\` 全没了 | shlex 默认 POSIX 模式 | 已修复（P0.3）：用 `posix=(os.name != "nt")` |
| 外部 server 启动后立刻退出 | npx 找不到包 / npm 网络问题 | 先 `npx -y @modelcontextprotocol/server-filesystem` 看错误 |
| call_tool 返回的 error 是空字符串 | 老代码用 raise，已修 isError=True | 拉取最新主分支 |
| /mcp/tools/.../invoke 401 | 生产环境开了 API_KEY_REQUIRED | 在 header 加 `X-API-Key: <key>` |

---

## 8. 完成本阶段的标志

- [ ] `python -m scripts.run_mcp_server` 能起且不报错
- [ ] `python -m scripts.smoke_test_mcp` 自连成功
- [ ] `pytest tests/test_mcp_*.py` 全绿
- [ ] 能解释 isError=True 的设计意图
- [ ] （选做）成功接一个外部 MCP Server 让 Agent 调用

---

## 9. 进阶练习

1. 实现 MCP Resources：把 RAG 的 chunk 索引以 URI 暴露，让外部 Client 能 list/read
2. 实现 MCP Prompts：把 prompt_service 里的模板暴露出去
3. 给 runtime 加自动重连：连接断了 5 秒后重试，3 次失败标记不可用
4. 把 MCP 调用做单独 trace span（接入 Phase 7 的 TracingService）
