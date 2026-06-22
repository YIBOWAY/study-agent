# Phase 5 执行手册

> 跟着这个跑一遍，能让你**亲手验证** Memory 跨会话保留 + 多 Agent 协作 + SSE 流式。

---

## 0. 前置检查

```powershell
conda activate ai-agent
cd e:\programs\AI_Agent_program\8w-plan
python -m pytest tests/test_memory_service.py tests/test_multi_agent_graph.py -q
# 期望：全部通过
```

---

## 1. Memory 入门：先用单测看清行为

```powershell
python -m pytest tests/test_memory_service.py -v
```

重点观察这些用例：
- `test_session_isolated_by_id` — 不同 session_id 互不干扰
- `test_session_expires_after_ttl` — TTL 过期后读不到
- `test_save_and_retrieve_insight` — 关键词命中时能查到
- `test_max_insights_evicts_oldest` — 容量上限的 FIFO 行为

---

## 2. 启动后端 + 看 Memory 端点

```powershell
# Terminal 1
uvicorn app.main:app --reload --port 8000
```

```powershell
# Terminal 2 — 创建一些 insight
$body = @{
  topic = "RAG chunking 策略"
  mode  = "workflow"
  top_k = 5
  session_id = "demo-1"
} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/research -ContentType "application/json" -Body $body
```

跑一次研究，再看 memory：
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/memory/sessions/demo-1
Invoke-RestMethod http://localhost:8000/api/v1/memory/insights
```

切到一个新 session_id 但同主题，应能看到上一轮 insight 被注入：
```powershell
$body.session_id = "demo-2"
Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/research -ContentType "application/json" -Body ($body | ConvertTo-Json)
```

---

## 3. 多 Agent 模式实操

```powershell
$body = @{
  topic = "Embedding 模型选型对比"
  mode = "multi_agent"
  top_k = 5
  max_iterations = 3
  session_id = "demo-multi"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/research -ContentType "application/json" -Body $body
```

返回里观察：
- `agents_involved`：4 个角色都参与了
- `plan`：planner 拆出的子问题列表
- `analysis`：analyst 的中间分析
- `review_verdict`：reviewer 的最终判定
- `iterations_used`：研究循环次数（≤ max_iterations）

---

## 4. 对比四种模式跑同一主题

```powershell
foreach ($mode in @("workflow","agent","agent_v2","multi_agent")) {
  $body = @{ topic="向量检索 vs 关键词检索"; mode=$mode; top_k=5; max_iterations=2 } | ConvertTo-Json
  $t0 = Get-Date
  $r = Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/research -ContentType "application/json" -Body $body
  $dt = ((Get-Date) - $t0).TotalSeconds
  "[$mode] {0:N1}s  iter={1}  search={2}  report={3} chars" -f $dt, $r.iterations_used, $r.search_result_count, $r.report.Length
}
```

预期观察：
- workflow 最快、报告最短
- agent / agent_v2 时间相近、覆盖更全
- multi_agent 最慢但结构最完整（plan + analysis + report + review）

---

## 5. SSE 流式：用 curl 看实时事件

```powershell
curl.exe -N "http://localhost:8000/api/v1/research/stream?topic=Reranker%20%E5%8E%9F%E7%90%86&mode=multi_agent&top_k=5"
```

应该看到一行一行的 `data: {"type":"update",...}` 实时打印，最后一条是 `data: {"type":"final",...}`。

---

## 6. 前端联调（可选，需要 Phase 8 frontend）

```powershell
cd frontend
streamlit run app.py
# 浏览器打开 http://localhost:8501
# 在"研究流"页面输入主题，能看到节点级别的实时进度
```

---

## 7. 常见踩坑

| 现象 | 原因 | 修复 |
|------|------|------|
| `session_id` 传了但下一次没读到 insight | TTL 过期 / 不同 session_id | 30 min 内复用同 id；或调高 `MEMORY_SESSION_TTL` |
| multi_agent 跑 3 分钟没出 | iteration 死循环 | 检查 `route_after_analysis` 是否正确返回字符串 "write" / "research_more" |
| SSE 浏览器不刷新 | data 行没有双 `\n\n` | 检查 streaming.py 的 yield 格式 |
| Memory JSON 损坏 | 进程崩溃中途写入 | 删 `data/memory/long_term.json` 重启即可 |
| `pytest test_memory_service.py` 在 Windows 卡住 | 临时目录权限 | 用 pytest 的 `tmp_path` fixture，不要硬编码路径 |

---

## 8. 进阶练习

1. **改 Memory 检索为向量**：把 `_tokenize` 替换成 embedding，用余弦相似度排序。看准确率提升多少。
2. **加一个 Critic 角色**：在 reviewer 之后再加一个"事实核查"角色，专门判断报告里有无 grounding 缺失。
3. **session 持久化**：当前 session 重启就丢，加一个 sqlite 落盘。
4. **Memory 自动总结**：当 insight 数量超过阈值时，让 LLM 把旧 insight 合并归纳成更短的"高层洞见"。

---

## 9. 完成本阶段的标志

- [ ] 4 种 mode 都能跑通
- [ ] 同一 session_id 第二次问能看到 prior_insights 注入
- [ ] SSE 流式接口能看到节点级进度
- [ ] `pytest tests/test_memory_*.py tests/test_multi_agent_*.py` 全绿
- [ ] 能解释为什么 multi_agent 比 agent 慢但更稳
