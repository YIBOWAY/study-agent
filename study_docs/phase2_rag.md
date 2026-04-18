# Phase 2：RAG 基础与工程实现

> 目标：理解 RAG 全链路并掌握工程实现——文档解析 → 分块 → 向量化 → 检索 → Reranking → 生成
> 前置要求：完成 Phase 0（Python 工程基础）和 Phase 1（LLM + Prompt）
> 预计时间：有工程经验 1-2 周，零基础 2-3 周

---

## 0. 为什么需要 RAG

LLM 有两个根本性缺陷：

1. **知识截止**：模型的训练数据有截止时间，它不知道之后发生的事
2. **幻觉**：当不确定时，它倾向于编造看起来合理但不正确的内容

RAG（Retrieval-Augmented Generation，检索增强生成）的解决思路很直接：

> 不让模型凭记忆回答，而是先从你的文档库中检索相关内容，把检索到的内容塞进 Prompt，让模型基于这些内容回答。

```
用户提问 → 检索相关文档片段 → 把片段+问题一起发给 LLM → LLM 基于片段回答
```

类比：如果 LLM 是一个学生——
- 不用 RAG = 闭卷考试（只能靠记忆，可能瞎编）
- 用 RAG = 开卷考试（可以翻书，答案有据可查）

---

## 1. RAG 全链路概览

一个完整的 RAG 系统分为两个阶段：

### 1.1 离线阶段（Indexing / 索引构建）

```
原始文档（PDF/Word/HTML）
    ↓ 文档解析
纯文本 / Markdown
    ↓ 分块（Chunking）
文本片段列表
    ↓ 向量化（Embedding）
向量列表
    ↓ 存储
向量数据库（Qdrant）
```

### 1.2 在线阶段（Query / 查询）

```
用户问题
    ↓ 向量化
查询向量
    ↓ 向量检索（Top-K）
候选文档片段
    ↓ Reranking（精排）
最相关片段
    ↓ 构造 Prompt（问题 + 上下文）
    ↓ 调用 LLM
最终回答（带来源引用）
```

**你的项目完整实现了这两个阶段。** 接下来逐一讲解每个环节。

---

## 2. 文档解析（Document Parsing）

### 2.1 问题

PDF 不是纯文本——它包含字体、排版、表格、图片等复杂结构。直接按字节读取会得到乱码。你需要一个解析器把 PDF 转成结构化文本。

### 2.2 常见解析工具对比

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| **docling** | IBM 出品，支持 PDF/Word/PPT/HTML，输出 Markdown，表格保持结构 | 通用文档解析（你的项目使用） |
| PyPDF2 / pdfplumber | 轻量，只处理 PDF | 简单纯文本 PDF |
| Unstructured | 功能全面，支持多种格式 | 复杂文档处理流水线 |
| LlamaParse | LlamaIndex 的云服务 | 对解析质量要求高的场景 |

### 2.3 你的项目实现

`document_parser_service.py` 使用 docling 将 PDF 转为 Markdown：

```python
class DocumentParserService:
    def __init__(self, converter=None):
        if converter is None:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
        self.converter = converter

    def parse_pdf(self, file_bytes: bytes, filename: str) -> list[ParsedSection]:
        # 1. 校验输入
        # 2. 写入临时文件（docling 需要文件路径）
        # 3. 调用 converter.convert()
        # 4. 导出为 Markdown
        # 5. 清理临时文件（即使出错也要清理）
        ...
```

**关键设计点**：

1. **延迟导入 docling**：`from docling.document_converter import DocumentConverter` 放在 `__init__` 里而非文件顶部，避免未安装时整个模块 import 失败
2. **依赖注入**：`converter` 参数可注入 mock，测试时不需要真的安装 docling
3. **临时文件安全清理**：用 `try/finally` 确保即使转换失败也会删除临时文件，防止磁盘泄漏
4. **输入校验**：空文件、非 PDF 文件名在调用 converter 之前就拦截

### 2.4 为什么输出 Markdown 而不是纯文本

Markdown 保留了文档的结构信息（标题层级、表格、列表），这些信息在后续分块和检索时很有价值。比如：
- 按标题分块时，可以利用 `#` 标记
- 表格内容保持结构化，LLM 更容易理解
- 列表层级关系不会丢失

---

## 3. 文本分块（Chunking）

### 3.1 为什么需要分块

LLM 的上下文窗口有限。如果一篇文档有 50 页，全部塞进 Prompt 会：
1. 超过 token 限制
2. 即使没超过，模型也会"注意力分散"，忽略中间内容
3. 检索时无法精确定位到具体段落

所以需要把文档切成小块（chunk），每块作为独立的检索单元。

### 3.2 分块策略

| 策略 | 原理 | 优劣 |
|------|------|------|
| **固定大小滑动窗口** | 按字符数切割，相邻块有重叠 | 简单通用，你的项目使用 |
| 按句子/段落 | 以句号/换行分割 | 保持语义完整，但块大小不均匀 |
| 递归字符分割 | LangChain 的 RecursiveCharacterTextSplitter，按 `\n\n` → `\n` → ` ` → `` 逐级分割 | 兼顾语义和大小 |
| 按标题/节 | 利用 Markdown 标题结构 | 适合结构化文档 |
| 语义分块 | 用 Embedding 计算相邻句子相似度，在语义跳变处切割 | 质量最高但最慢 |

### 3.3 你的项目实现

`chunking_service.py` 实现了**固定大小滑动窗口**分块：

```python
class ChunkingService:
    def __init__(self, chunk_size=None, chunk_overlap=None, settings=None):
        self.chunk_size = chunk_size or settings.rag_chunk_size    # 默认 800
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap  # 默认 120
```

**滑动窗口原理**：

```
原文：ABCDEFGHIJKLMNOPQRSTUVWXYZ（假设 chunk_size=10, overlap=3）

Chunk 1: ABCDEFGHIJ   （位置 0-9）
Chunk 2:        HIJKLMNOPQ   （位置 7-16，与 Chunk 1 重叠 HIJ）
Chunk 3:               OPQRSTUVWX   （位置 14-23，与 Chunk 2 重叠 OPQ）
Chunk 4:                      VWXYZ   （位置 21-25，最后一块可能不足 chunk_size）
```

**为什么需要 overlap（重叠）**：

如果一个关键信息刚好被切在两个 chunk 的边界处，没有重叠的话，两个 chunk 都只有一半信息，检索到任何一个都无法完整回答。重叠保证边界附近的信息不会丢失。

### 3.4 Chunk 元数据

每个 chunk 不仅保存文本，还保存元数据：

```python
class ChunkRecord(BaseModel):
    chunk_id: str           # 唯一标识（document_id-section_index-chunk_index）
    document_id: str        # 所属文档
    source_name: str        # 文件名
    text: str               # 分块文本
    page_number: int | None # 页码（用于引用来源）
    section_title: str | None  # 章节标题
```

**为什么元数据重要**：回答用户问题时，你不仅要给出答案，还要告诉用户"这个信息来自哪个文件的第几页"。

### 3.5 Chunk 大小的权衡

```
太大（比如 2000 字符）：
  ✅ 上下文完整，语义连贯
  ❌ 检索精度下降（一个大块里可能只有一小部分相关）
  ❌ 占用更多 token

太小（比如 100 字符）：
  ✅ 检索精度高
  ❌ 丢失上下文，语义不完整
  ❌ 需要检索更多块才能凑够信息

经验值：
  - 通用文档：500-1000 字符
  - 技术文档：300-800 字符
  - FAQ 类短文本：100-300 字符
```

你的项目默认 800 字符 + 120 重叠，是一个合理的起点。

### 3.6 动手练习

```python
"""
练习：用你的 ChunkingService，对以下文本进行分块，观察：
1. chunk_size=20, overlap=5 时生成几个 chunk？
2. chunk_size=20, overlap=0 时呢？
3. 检查重叠部分是否正确
"""
from app.schemas.rag import ParsedSection
from app.services.chunking_service import ChunkingService

text = "RAG是检索增强生成的缩写。它通过在生成之前检索相关文档来增强大语言模型的回答质量。"
sections = [ParsedSection(text=text, section_title="RAG介绍", page_number=1)]

# 你的代码写在这里
```

---

## 4. 向量化（Embedding）

### 4.1 什么是 Embedding

Embedding 是把文本转成一个固定长度的浮点数数组（向量），使得**语义相近的文本，向量也相近**。

```
"如何提高代码质量" → [0.12, -0.34, 0.56, ..., 0.78]  （3072 维）
"怎样写出更好的程序" → [0.11, -0.33, 0.55, ..., 0.77]  （非常接近！）
"今天天气怎么样" → [0.89, 0.23, -0.67, ..., 0.12]  （距离很远）
```

两个向量的"距离"（通常用余弦相似度）可以衡量语义相似程度：
- 余弦相似度接近 1.0 → 语义非常接近
- 余弦相似度接近 0.0 → 语义无关
- 余弦相似度接近 -1.0 → 语义相反

### 4.2 主流 Embedding 模型

| 模型 | 厂商 | 维度 | 特点 |
|------|------|------|------|
| **text-embedding-3-large** | OpenAI | 3072 | 质量高，支持降维（你的项目使用） |
| text-embedding-3-small | OpenAI | 1536 | 便宜，质量尚可 |
| BGE-M3 | BAAI(智源) | 1024 | 开源，多语言，可本地部署 |
| Jina Embeddings v3 | Jina AI | 1024 | 开源，支持多种任务类型 |
| Cohere embed-v4 | Cohere | 1024 | 商用，自带分类能力 |

### 4.3 你的项目实现

`embedding_service.py` 调用 OpenAI 兼容的 Embedding API：

```python
class EmbeddingService:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # 构造请求
        payload = {
            "input": texts,                              # 支持批量
            "model": self.settings.embedding_model,      # text-embedding-3-large
            "dimensions": self.settings.embedding_dimensions,  # 3072
        }
        # 发送请求并解析响应
        ...

    async def embed_query(self, text: str) -> list[float]:
        # 单条文本的便捷方法
        embeddings = await self.embed_texts([text])
        return embeddings[0]
```

**关键设计点**：

1. **API Key 回退**：如果没配 `EMBEDDING_API_KEY`，自动使用 `LLM_API_KEY`，减少配置负担
2. **批量处理**：`embed_texts` 接受列表，一次请求可以向量化多段文本，比逐条调用高效得多
3. **严格响应校验**：逐项检查 API 返回的 `data` 列表和 `embedding` 字段，防止静默错误

### 4.4 Embedding 的成本

Embedding API 按 token 计费，但比 LLM 便宜得多：

| 模型 | 价格 ($/1M tokens) |
|------|-------------------|
| text-embedding-3-large | $0.13 |
| text-embedding-3-small | $0.02 |

1M tokens ≈ 50-80 万中文字。对于大多数项目来说，Embedding 成本几乎可以忽略。

### 4.5 常见坑

1. **Query 和 Document 用同一个 Embedding 模型**：不要用模型 A 向量化文档，用模型 B 向量化查询，它们的向量空间不同
2. **维度要一致**：如果文档用 3072 维，查询也必须是 3072 维
3. **文本长度限制**：Embedding 模型有 token 上限（text-embedding-3-large 是 8191 tokens），超长文本需要先分块再向量化

---

## 5. 向量数据库（Vector Store）

### 5.1 为什么需要向量数据库

普通数据库（MySQL、PostgreSQL）擅长精确匹配：`WHERE name = 'Agent'`。

向量数据库擅长**近似最近邻搜索**（ANN）：给一个查询向量，快速找到数据库中最相似的 K 个向量。

### 5.2 主流向量数据库对比

| 数据库 | 特点 | 适用场景 |
|--------|------|----------|
| **Qdrant** | Rust 实现，高性能，API 友好（你的项目使用） | 生产级部署 |
| ChromaDB | Python 实现，入门简单 | 快速原型 |
| FAISS | Facebook 出品，纯 C++ 库，无服务模式 | 研究/嵌入式 |
| Milvus | 分布式架构，处理十亿级向量 | 大规模生产 |
| Pinecone | 全托管云服务 | 不想运维 |
| pgvector | PostgreSQL 插件 | 已有 PG 基础设施 |

### 5.3 你的项目实现

`vector_store_service.py` 封装了 Qdrant 的核心操作：

```python
class VectorStoreService:
    def __init__(self, settings=None, client=None):
        self.client = client or AsyncQdrantClient(
            url=self.settings.qdrant_url,      # http://localhost:6333
            api_key=self.settings.qdrant_api_key,
        )

    async def ensure_collection(self):
        """确保集合存在，不存在则创建"""
        # 检查集合列表
        # 如果不存在，创建，配置向量维度和距离函数
        await self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config=VectorParams(
                size=self.settings.embedding_dimensions,  # 3072
                distance=Distance.COSINE,                 # 余弦相似度
            ),
        )

    async def upsert_chunks(self, chunks, vectors):
        """批量写入向量和元数据"""
        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={...chunk 的元数据...},
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        await self.client.upsert(collection_name=..., points=points)

    async def search(self, query_vector, top_k, document_id=None):
        """向量搜索，可选按 document_id 过滤"""
        ...
```

**关键设计点**：

1. **异步客户端**：使用 `AsyncQdrantClient`，不阻塞 FastAPI 的事件循环
2. **幂等创建集合**：`ensure_collection` 先检查再创建，重复调用不会出错
3. **过滤条件**：`search` 支持传入 `document_id` 过滤，实现"只在某个文档内搜索"
4. **payload 存储元数据**：向量旁边存了 text、source_name、page_number 等，搜索结果直接带上下文

### 5.4 距离函数选择

| 距离函数 | 适用场景 | 说明 |
|----------|----------|------|
| **Cosine** | 通用文本检索 | 衡量方向相似度，忽略向量长度（你的项目使用） |
| Dot Product | 向量已归一化时 | 等价于 Cosine，但计算更快 |
| Euclidean | 需要考虑绝对距离时 | 很少用于文本检索 |

### 5.5 启动 Qdrant

```bash
# Docker 方式（推荐）
docker run -p 6333:6333 qdrant/qdrant

# 或者用 Docker Compose
# docker-compose.yml 中配置 qdrant 服务
```

Qdrant 启动后，你的代码通过 `http://localhost:6333` 连接。

---

## 6. 检索（Retrieval）

### 6.1 检索流程

```
用户问题 → embed_query → 查询向量 → vector_store.search(top_k) → 候选结果
```

`retrieval_service.py` 组合了 embedding 和 vector_store：

```python
class RetrievalService:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    async def retrieve(self, query, top_k, document_id=None):
        query_vector = await self.embedding_service.embed_query(query)
        return await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            document_id=document_id,
        )
```

**为什么单独抽一个 RetrievalService**：将"查询向量化"和"向量搜索"的组合逻辑封装起来，RAGService 不需要关心这些细节。后续如果要加混合检索（语义+关键词），只改 RetrievalService 即可。

### 6.2 Top-K 的选择

Top-K 决定初次检索返回多少个候选结果：

```
Top-K 太小（如 3）：可能漏掉相关内容
Top-K 太大（如 100）：噪音太多，Reranking 成本高

经验值：
  - 简单问答：Top-K = 10-20
  - 复杂分析：Top-K = 20-50
  - 你的项目默认：Top-K = 20
```

### 6.3 检索策略对比

| 策略 | 原理 | 优劣 |
|------|------|------|
| **语义检索** | 用 Embedding 计算向量相似度（你的项目使用） | 理解语义同义词，但可能漏掉精确关键词匹配 |
| 关键词检索 | BM25 / TF-IDF 统计关键词频率 | 精确匹配强，但不理解语义 |
| **混合检索** | 语义 + 关键词结合 | 兼顾两者优点（生产推荐） |

**常见坑**：只用语义检索时，用户搜"RFC 7231"，语义检索可能返回"HTTP 协议规范"相关内容但不是 RFC 7231 本身。关键词检索在这种精确匹配场景更可靠。

---

## 7. Reranking（精排）

### 7.1 为什么需要 Reranking

向量检索的 Top-K 结果质量参差不齐。Embedding 模型是对文本做"粗粒度"的语义表示，一个 3072 维向量要压缩整段文本的含义，必然有信息损失。

Reranker 是一个更精细的模型，它接收 (query, document) 对，逐一评估相关性打分。这比向量检索更准确，但也更慢——所以先用向量检索粗筛（Top-20），再用 Reranker 精排（Top-5）。

```
向量检索 (Top-20, 快但粗) → Reranker (Top-5, 慢但精)
```

### 7.2 主流 Reranker

| 模型 | 厂商 | 特点 |
|------|------|------|
| **rerank-v3.5** | Cohere | 商用 API，质量高（你的项目使用） |
| BGE-Reranker-v2-m3 | BAAI(智源) | 开源，可本地部署 |
| Jina Reranker v2 | Jina AI | 开源，多语言 |
| ColBERT | Stanford | 学术模型，token 级别交互 |

### 7.3 你的项目实现

`rerank_service.py` 调用 Cohere Rerank API：

```python
class RerankService:
    async def rerank(self, query, candidates, final_k):
        # 构造请求
        payload = {
            "model": "rerank-v3.5",
            "query": query,
            "documents": [c.text for c in candidates],  # 候选文本列表
            "top_n": final_k,                            # 只返回前 N 个
        }
        # 发送请求
        # 解析响应：每个结果包含 index（原列表位置）和 relevance_score
        # 用 relevance_score 更新 SearchResult 的 score
        ...
```

**关键设计点**：

1. **只传 text**：Reranker 只需要文本内容，不需要向量
2. **返回原始索引**：Reranker 返回 `index` 指向原始候选列表的位置，通过这个映射回完整的 SearchResult
3. **严格校验**：检查 index 范围、relevance_score 类型，防止 API 返回异常数据
4. **空列表处理**：候选为空时直接返回空列表，不发请求

### 7.4 成本考量

Cohere Rerank 按搜索次数计费（每次搜索最多 1000 个文档）。免费额度通常够开发使用，生产环境需要付费计划。

---

## 8. RAG 编排层

### 8.1 你的项目实现

`rag_service.py` 是整个 RAG 系统的"指挥官"，编排所有子服务：

```python
class RAGService:
    def __init__(self, parser, chunker, embedding_service, vector_store,
                 retrieval_service, rerank_service, llm_service, settings):
        # 所有子服务通过构造函数注入

    async def ingest_pdf(self, file_bytes, filename):
        """离线阶段：文档 → 分块 → 向量化 → 存储"""
        document_id = uuid4().hex
        sections = self.parser.parse_pdf(file_bytes, filename)
        chunks = self.chunker.chunk_sections(document_id, filename, sections)
        vectors = await self.embedding_service.embed_texts([c.text for c in chunks])
        await self.vector_store.upsert_chunks(chunks, vectors)
        return {"document_id": document_id, "chunk_count": len(chunks)}

    async def search(self, query, top_k, document_id=None):
        """在线阶段：检索 + Reranking"""
        retrieved = await self.retrieval_service.retrieve(query, top_k, document_id)
        reranked = await self.rerank_service.rerank(query, retrieved, top_k)
        return {"results": reranked}

    async def ask(self, query, top_k, final_k, document_id=None):
        """在线阶段：检索 + Reranking + LLM 生成"""
        retrieved = await self.retrieval_service.retrieve(query, top_k, document_id)
        reranked = await self.rerank_service.rerank(query, retrieved, final_k)
        context = self._build_context(reranked)
        prompt = f"Question: {query}\n\nContext:\n{context}"
        response = await self.llm_service.chat(prompt, system_prompt=RAG_SYSTEM_PROMPT)
        return {"answer": response["reply"], "sources": reranked}
```

### 8.2 Context 构建

`_build_context` 把检索结果格式化为 LLM 能理解的上下文：

```
[1] report.pdf (page 3)
Revenue grew 20% year over year, driven by strong demand...

[2] report.pdf (page 7)
Operating expenses decreased by 5%, contributing to margin expansion...
```

编号和来源信息让 LLM 可以在回答中引用具体来源。

### 8.3 RAG 专用 System Prompt

```python
RAG_SYSTEM_PROMPT = """You are a grounded RAG assistant.
Answer the user's question using only the provided context.
If the context is insufficient, say you do not have enough information.
Cite the provided sources naturally when helpful and do not invent facts."""
```

关键约束：
- **只基于上下文回答**：减少幻觉
- **信息不足就说不知道**：比瞎编要好
- **引用来源**：可追溯

---

## 9. API 端点设计

### 9.1 三个 RAG 端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/rag/ingest` | POST (multipart) | 上传 PDF 文件，触发索引构建 |
| `/api/v1/rag/search` | POST (JSON) | 语义搜索，返回相关片段 |
| `/api/v1/rag/ask` | POST (JSON) | 检索 + 生成，返回回答和来源 |

### 9.2 请求/响应模型

```python
# 搜索请求
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=20, ge=1, le=50)
    document_id: str | None = None          # 可选：限定搜索范围

# 问答请求
class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=20, ge=1, le=50)   # 初检数量
    final_k: int = Field(default=5, ge=1, le=10)   # Rerank 后保留数量
    document_id: str | None = None

    @model_validator(mode="after")
    def validate_final_k(self):
        if self.final_k > self.top_k:
            raise ValueError("final_k must be <= top_k")
        return self
```

**model_validator 的作用**：`final_k` 不能大于 `top_k`（你不可能从 20 个里精排出 30 个）。这种跨字段校验用 `@model_validator` 实现。

### 9.3 错误处理

路由层统一用 try/except 包裹，对外只暴露通用错误信息：

```python
except Exception as exc:
    logger.exception("Unexpected error while searching RAG index")
    raise HTTPException(status_code=500, detail="Failed to search RAG index.")
```

**安全考虑**：不把内部错误信息（如数据库连接字符串、API Key）暴露给客户端。

---

## 10. RAG 评估

### 10.1 为什么需要评估

你改了 chunk_size、换了 Embedding 模型、调了 Top-K——效果变好了还是变差了？没有评估，你就是在盲调。

### 10.2 Retrieval Hit Rate

你的项目实现了最基础的评估指标——**检索命中率**：

```python
def compute_retrieval_hit_rate(cases, result_batches):
    """在检索结果中能找到预期内容的比例"""
    hits = 0
    for case, results in zip(cases, result_batches):
        if any(case.expected_substring in result_text for result_text in results):
            hits += 1
    return hits / len(cases)
```

示例：
- 3 个测试问题
- 2 个在检索结果中找到了预期内容
- Hit Rate = 2/3 = 66.7%

### 10.3 评估用例格式

`eval/sample_questions.jsonl`：

```json
{"question": "How did revenue change?", "expected_substring": "Revenue grew 20%", "document_id": "doc-id"}
```

### 10.4 运行评估

```bash
python -m scripts.run_rag_eval --cases eval/sample_questions.jsonl --top-k 5
```

### 10.5 更完善的评估框架（了解即可）

| 指标 | 含义 |
|------|------|
| Hit Rate | 检索结果中包含正确答案的比例 |
| MRR (Mean Reciprocal Rank) | 正确答案在结果列表中的平均排名 |
| NDCG | 考虑排名位置的综合评分 |
| Faithfulness | 回答是否忠于检索到的上下文（RAGAS 指标） |
| Answer Relevancy | 回答是否切题（RAGAS 指标） |
| Context Precision | 检索到的内容是否精确相关（RAGAS 指标） |

你当前实现了 Hit Rate，这是一个很好的起点。

---

## 11. 配置管理扩展

Phase 2 在 `Settings` 中新增了大量配置项：

```python
# Embedding
embedding_api_key: str = ""           # 独立 key，空则回退到 llm_api_key
embedding_base_url: str = ""          # 独立 URL，空则回退到 llm_base_url
embedding_model: str = "text-embedding-3-large"
embedding_dimensions: int = 3072
embedding_timeout: int = 60

# Qdrant
qdrant_url: str = "http://localhost:6333"
qdrant_api_key: str = ""
qdrant_collection: str = "phase2_chunks"

# Cohere Rerank
rerank_api_key: str = ""
rerank_base_url: str = "https://api.cohere.com/v2"
rerank_model: str = "rerank-v3.5"

# RAG 行为
rag_chunk_size: int = 800
rag_chunk_overlap: int = 120
rag_top_k: int = 20
rag_final_k: int = 5
```

加了 `@model_validator` 校验：
- `rag_chunk_overlap < rag_chunk_size`
- `rag_final_k <= rag_top_k`

---

## 12. 测试策略

Phase 2 的测试有几个值得学习的模式：

### 12.1 Fake 对象 vs Mock

测试 RAGService 时没有用 `unittest.mock`，而是手写了 Fake 类：

```python
class FakeParser:
    def parse_pdf(self, file_bytes, filename):
        return [ParsedSection(text="...", ...)]

class FakeEmbedding:
    async def embed_texts(self, texts):
        return [[0.1, 0.2], [0.3, 0.4]]
```

**优点**：
- 比 Mock 更直观，能看到 Fake 返回什么数据
- 类型检查更友好
- 测试代码更像文档

### 12.2 参数化测试

```python
@pytest.mark.parametrize("payload, error_match", [
    ({}, "data"),
    ({"data": "not-a-list"}, "data"),
    ({"data": [{}]}, "embedding"),
])
async def test_embed_texts_malformed_payload(mock_client, payload, error_match):
    ...
```

一个测试函数覆盖多种异常场景，避免写重复代码。

### 12.3 编排顺序验证

```python
def test_ingest_pdf_orchestrates_dependencies_in_order(self):
    # 验证 parser → chunker → embedder → vector_store 的调用顺序
    assert call_order == ["parser", "chunker", "embedder", "ensure_collection", "upsert"]
```

确保 RAGService 按正确顺序调用各子服务。

---

## 13. 阶段自检清单

### 概念理解

- [ ] 我能画出 RAG 的完整数据流（离线 + 在线）
- [ ] 我能解释 Embedding 的作用和向量相似度的含义
- [ ] 我能解释为什么需要 Chunking，以及 overlap 的意义
- [ ] 我能解释向量检索和 Reranking 分别解决什么问题
- [ ] 我能解释为什么 RAG 能减少幻觉

### 实操能力

- [ ] 我能启动 Qdrant 并通过 API 创建集合
- [ ] 我能上传 PDF 并触发完整的 Ingest 流程
- [ ] 我能调用 /search 和 /ask 端点并理解返回结果
- [ ] 我能修改 chunk_size/overlap 并观察对检索结果的影响
- [ ] 我能运行评估脚本并解读 Hit Rate

### 代码能力

- [ ] 我能读懂 rag_service.py 的编排逻辑
- [ ] 我能写一个新的 Service（比如 keyword_search_service）并集成到检索链
- [ ] 我能添加新的评估指标（比如 MRR）
- [ ] 我能为新 Service 写单元测试（使用 Fake 对象或 Mock）

---

## 14. 推荐资料

| 资料 | 用途 | 说明 |
|------|------|------|
| [RAG from Scratch (LangChain)](https://github.com/langchain-ai/rag-from-scratch) | RAG 原理 | 14 个视频，从零讲解 RAG |
| [Qdrant 官方文档](https://qdrant.tech/documentation/) | 向量数据库 | API 参考和教程 |
| [OpenAI Embedding Guide](https://platform.openai.com/docs/guides/embeddings) | Embedding 使用 | 官方最佳实践 |
| [Cohere Rerank 文档](https://docs.cohere.com/docs/reranking) | Reranking | API 参考 |
| [RAGAS 文档](https://docs.ragas.io/) | RAG 评估 | 完整评估框架 |
| [Chunking Strategies (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/) | 分块策略 | 各种策略对比 |

---

## 15. 下一步

Phase 2 让你的系统从"只能聊天"升级为"能基于私有文档回答问题"。接下来：

- **Phase 3（Function Calling / Tool Use）**：让 Agent 不仅能检索文档，还能调用外部工具（搜索引擎、数据库、API）
- 你会发现 RAG 本身也可以作为 Agent 的一个"工具"——Agent 在需要查文档时调用 RAG，需要搜索时调用搜索引擎

RAG 系统的优化是一个持续过程。即使进入后续阶段，你仍然可以回来调整分块策略、尝试混合检索、升级 Reranker。
