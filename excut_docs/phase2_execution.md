# Phase 2 RAG 系统执行文档（Runbook）

## 1. 前置条件

Phase 0+1 环境已正常运行（参考 `excut_docs/phase0_1_execution.md`）。

额外需要：
- Docker（用于运行 Qdrant）
- 可用的 Embedding API（OpenAI 兼容）
- 可用的 Cohere Rerank API Key

## 2. Phase 2 新增依赖

在 Phase 0+1 的基础上，额外安装：

```bash
cd E:\programs\AI_Agent_program\8w-plan
conda activate ai-agent
pip install qdrant-client docling python-multipart
```

> **注意**：`docling` 是重量级包（包含 torch、transformers 等），首次安装约需 3-5 分钟，磁盘占用 1GB+。

验证安装：

```bash
python -c "import qdrant_client; print(qdrant_client.__version__)"
python -c "from docling.document_converter import DocumentConverter; print('docling OK')"
```

## 3. 启动 Qdrant

### 方式一：Docker（推荐）

```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

验证：

```bash
curl http://localhost:6333/healthz
```

预期返回 `ok` 或空 body + 200 状态码。

### 方式二：Docker Compose

在项目根目录创建 `docker-compose.yml`：

```yaml
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

启动：

```bash
docker compose up -d
```

### Qdrant Dashboard

浏览器访问 `http://localhost:6333/dashboard` 可查看集合和数据。

## 4. 环境变量配置

在 `.env` 中追加以下配置：

```env
# ─── Embedding ───
# 可选：为空时使用 LLM_API_KEY
EMBEDDING_API_KEY=
# 可选：为空时使用 LLM_BASE_URL
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072
EMBEDDING_TIMEOUT=60

# ─── Qdrant ───
QDRANT_URL=http://localhost:6333
# 本地 Docker 无密码时留空
QDRANT_API_KEY=
QDRANT_COLLECTION=phase2_chunks

# ─── Cohere Rerank ───
RERANK_API_KEY=your_cohere_api_key_here
RERANK_BASE_URL=https://api.cohere.com/v2
RERANK_MODEL=rerank-v3.5

# ─── RAG 行为 ───
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=20
RAG_FINAL_K=5
```

> **注意**：`.env` 里的注释请单独写一行，不要写成 `KEY=值 # 注释`。对于 `QDRANT_API_KEY` 这类会进入 HTTP Header 的配置，中文注释如果被一起复制进去，会在启动时触发 `UnicodeEncodeError`。

**最小必填项**：
- `RERANK_API_KEY`（Cohere 免费注册即可获得）
- Qdrant 本地运行时 `QDRANT_URL` 保持默认即可
- Embedding 配置为空时自动回退到 LLM 配置

## 5. 启动服务

```bash
cd E:\programs\AI_Agent_program\8w-plan
conda activate ai-agent
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果 Windows 报 `WinError 10013`，通常不是代码问题，而是 `8000` 端口已被其他程序占用。可改用：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

确认 Swagger 文档中出现 RAG 相关端点；如果使用 `8000` 端口则访问 `http://127.0.0.1:8000/docs`，如果改用 `8001` 则访问 `http://127.0.0.1:8001/docs`。

## 6. 接口验证

### 6.1 上传 PDF（Ingest）

使用 curl：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest \
  -F "file=@/path/to/your/document.pdf;type=application/pdf"
```

使用 PowerShell：

```powershell
$filePath = "C:\path\to\your\document.pdf"
$form = @{ file = Get-Item $filePath }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/rag/ingest" -Method Post -Form $form
```

预期返回：

```json
{
  "document_id": "a1b2c3d4e5f6...",
  "filename": "document.pdf",
  "chunk_count": 42
}
```

> 首次 ingest 会自动创建 Qdrant 集合。可在 Qdrant Dashboard 验证。

### 6.2 语义搜索（Search）

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "你的搜索问题", "top_k": 10}'
```

限定某个文档：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "你的搜索问题", "top_k": 10, "document_id": "之前返回的document_id"}'
```

预期返回：

```json
{
  "results": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "source_name": "document.pdf",
      "text": "匹配到的文本片段...",
      "page_number": 3,
      "score": 0.92
    }
  ]
}
```

### 6.3 检索增强问答（Ask）

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "你的问题", "top_k": 20, "final_k": 5}'
```

预期返回：

```json
{
  "answer": "根据文档内容，...",
  "sources": [...],
  "model": "gpt-5.4",
  "rerank_model": "rerank-v3.5"
}
```

## 7. 运行测试

```bash
cd E:\programs\AI_Agent_program\8w-plan
python -m pytest -v --tb=short
```

> **重要**：必须使用 `python -m pytest` 而非 `pytest`，否则会出现 `ModuleNotFoundError: No module named 'app'`。

只运行 Phase 2 测试：

```bash
python -m pytest tests/test_document_parser_service.py tests/test_chunking_service.py tests/test_embedding_service.py tests/test_vector_store_service.py tests/test_retrieval_service.py tests/test_rerank_service.py tests/test_rag_service.py tests/test_rag_schemas.py tests/test_evaluation_service.py -v
```

预期结果：78/78 通过（包含 Phase 0+1 的 2 个测试）。

## 8. 运行评估

```bash
cd E:\programs\AI_Agent_program\8w-plan
python -m scripts.run_rag_eval --cases eval/sample_questions.jsonl --top-k 20 --final-k 5
```

> 需要 Qdrant 运行中且已 ingest 过相关文档。`sample_questions.jsonl` 中的 `document_id` 需要替换为实际值。

完整评估（含 LLM-as-judge 指标，会消耗 API 调用）：

```bash
python -m scripts.run_rag_eval --cases eval/sample_questions.jsonl --top-k 20 --final-k 5 --judge
```

### 自定义评估用例

编辑 `eval/sample_questions.jsonl`，每行一个 JSON：

```json
{"question": "公司去年营收增长多少？", "expected_substring": "20%", "reference_answer": "营收同比增长20%", "document_id": "你的document_id"}
{"question": "主要成本变化如何？", "expected_substring": "运营成本下降", "reference_answer": "运营成本同比下降5%", "document_id": "你的document_id"}
```

## 9. 完整工作流示例

```
1. 启动 Qdrant
   docker start qdrant

2. 启动服务
   uvicorn app.main:app --reload

3. 上传 PDF
   POST /api/v1/rag/ingest → 得到 document_id

4. 搜索验证
   POST /api/v1/rag/search → 确认检索结果合理

5. 问答验证
   POST /api/v1/rag/ask → 确认回答准确、有来源引用

6. 评估
   python -m scripts.run_rag_eval --top-k 20 --final-k 5 → 查看 Hit Rate + Citation 指标
   python -m scripts.run_rag_eval --top-k 20 --final-k 5 --judge → 加上 LLM-as-judge 指标
```

## 10. 常见报错与排查

### 报错 1：`ModuleNotFoundError: No module named 'docling'`

原因：未安装 docling。

```bash
pip install docling
```

### 报错 2：`Connection refused` (Qdrant)

原因：Qdrant 未启动或端口不对。

```bash
docker ps | findstr qdrant    # 检查容器是否运行
docker start qdrant           # 启动容器
curl http://localhost:6333/healthz  # 验证连接
```

### 报错 3：`401 Unauthorized` (Embedding API)

原因：Embedding API Key 无效。

排查：
- 检查 `.env` 中 `EMBEDDING_API_KEY`（如果设置了）
- 如果未设置 `EMBEDDING_API_KEY`，检查 `LLM_API_KEY` 是否有 Embedding 权限
- 检查 `EMBEDDING_BASE_URL` 是否正确

### 报错 4：`401 Unauthorized` (Cohere Rerank)

原因：Cohere API Key 无效。

排查：
- 检查 `.env` 中 `RERANK_API_KEY`
- 到 Cohere 官网确认 Key 有效
- 免费额度是否已用完

### 报错 5：`ValidationError: final_k must be <= top_k`

原因：请求中 `final_k` 大于 `top_k`。

修复：确保 `final_k <= top_k`（如 `top_k=20, final_k=5`）。

### 报错 6：`415 Unsupported Media Type` (Ingest)

原因：上传的文件不是 PDF 格式，或 content_type 不是 `application/pdf`。

修复：确认上传的是 PDF 文件，curl 中用 `type=application/pdf`。

### 报错 7：整个 app 启动失败，`ImportError` 指向 docling/qdrant_client

原因：`rag.py` 路由文件在 import 时实例化 `RAGService`，触发全依赖链 import。

修复：安装所有依赖 `pip install qdrant-client docling python-multipart`。

### 报错 8：`ModuleNotFoundError: No module named 'app'`（运行测试时）

原因：使用了 `pytest` 而非 `python -m pytest`。

修复：

```bash
python -m pytest -v
```

## 11. Qdrant 数据管理

### 查看集合信息

```bash
curl http://localhost:6333/collections/phase2_chunks
```

### 清空集合（重新 ingest 前）

```bash
curl -X DELETE http://localhost:6333/collections/phase2_chunks
```

下次 ingest 会自动重建集合。

### 查看数据量

```bash
curl http://localhost:6333/collections/phase2_chunks | python -m json.tool
```

关注 `points_count` 字段。
