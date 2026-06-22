# Phase 0 + Phase 1 代码导读

## 导读目标

这份文档不是重复学习文档，而是带你按照“真正读代码”的顺序，把当前项目的关键文件串起来。

建议阅读顺序：

1. `app/main.py`
2. `app/api/routes/health.py`
3. `app/api/routes/chat.py`
4. `app/schemas/chat.py`
5. `app/services/prompt_service.py`
6. `app/services/llm_service.py`
7. `app/core/config.py`
8. `app/core/logging.py`
9. `tests/test_health.py`
10. `tests/test_extract.py`

---

## 1. 从入口开始：`app/main.py`

文件位置：`app/main.py`

这个文件是整个后端应用的入口。你可以把它理解为“把所有模块装起来”的地方。

关键点：

- `setup_logging()`：程序启动时先把日志配置好
- `get_settings()`：读取 `.env` 配置
- `FastAPI(...)`：创建 Web 应用对象
- `app.include_router(...)`：把各个接口模块注册进来
- `@app.get("/")`：根路径，只用于快速确认服务已经启动

为什么先看它？
因为它能让你先建立一个总览：

- 应用从哪里开始
- 路由是怎么挂进去的
- 配置和日志在什么时候被加载

你在这里应该重点理解：

> `main.py` 不负责具体业务，它负责“装配”。

这是非常典型、也非常重要的工程化习惯。

---

## 2. 最简单的服务接口：`app/api/routes/health.py`

文件位置：`app/api/routes/health.py`

这是一个最简单的路由模块，只做一件事：

- 提供 `/health` 接口

返回：

```json
{"status": "ok"}
```

它虽然简单，但意义很大：

- 用于确认服务是否存活
- 后续部署时可以作为 health check
- 也是你测试 FastAPI 路由是否正常注册的最快方法

你在这里要建立一个意识：

> 每个服务哪怕最小，也应该有健康检查接口。

---

## 3. 真正的业务入口：`app/api/routes/chat.py`

文件位置：`app/api/routes/chat.py`

这是当前阶段最重要的路由文件，它定义了两个接口：

- `POST /api/v1/chat`
- `POST /api/v1/extract`

### 3.1 先看这句

```python
llm_service = LLMService()
```

这说明：

- 路由层自己不做复杂逻辑
- 它只依赖一个 service 对象

### 3.2 `chat()` 方法

它接收 `ChatRequest`，然后调用：

```python
await llm_service.chat(...)
```

最后把返回结果转成 `ChatResponse`。

你要注意这里的模式：

- 输入先经过 schema 校验
- 业务交给 service
- 输出也经过 schema 约束

### 3.3 `extract()` 方法

这个接口更重要，因为它体现了“工程化 LLM 应用”的最小雏形。

它不是简单聊天，而是：

- 把一段文本交给模型
- 要求模型返回结构化信息
- 程序再把结构化结果返回给调用方

这已经非常接近后续：

- 信息抽取
- 分类
- route decision
- tool planning

这些真实场景。

### 3.4 为什么这里直接 `except Exception`

当前阶段这样写是为了最小可运行。它的优点是：

- 初学者容易理解
- 错误不会静默吞掉

缺点也很明显：

- 错误分类不够细
- 后续应该把配置错误、API 错误、解析错误分开处理

也就是说：

> 这里是当前阶段可接受的最小实现，不是最终生产写法。

---

## 4. 数据契约：`app/schemas/chat.py`

文件位置：`app/schemas/chat.py`

这里定义了 4 个模型：

- `ChatRequest`
- `ChatResponse`
- `ExtractRequest`
- `ExtractResponse`

### 4.1 为什么 schema 很重要

很多新手会直接拿 `dict` 处理请求和响应。但 schema 的价值在于：

- 自动校验输入
- 明确接口契约
- 自动出现在 `/docs` 中
- 让后续重构更安全

### 4.2 你应该重点看什么

- `Field(..., min_length=1)`：输入不能为空
- `system_prompt: str | None`：说明这个字段是可选的
- `keywords: list[str]`：说明我们希望结构化输出里有数组，而不是随便的字符串

当前阶段真正要培养的能力之一，就是：

> 不要把模型输出只当一段文本，而要尽可能把它约束成程序可消费的数据结构。

---

## 5. Prompt 分离：`app/services/prompt_service.py`

文件位置：`app/services/prompt_service.py`

这里看起来很简单，只定义了两个 prompt 常量：

- `CHAT_SYSTEM_PROMPT`
- `EXTRACT_SYSTEM_PROMPT`

为什么要单独放一个文件？

因为这是一个好习惯：

- prompt 不是路由逻辑
- prompt 也不是 HTTP 调用逻辑
- prompt 是一种“行为配置”

后续如果进入 Phase 2/3：

- prompt 会越来越多
- 每种任务会有不同的 system prompt
- 你可能还会做 prompt 版本管理

所以现在就分离出来是对的。

---

## 6. 核心业务层：`app/services/llm_service.py`

文件位置：`app/services/llm_service.py`

这是当前阶段最核心的文件。真正的 LLM 调用和结构化处理都在这里。

### 6.1 `__init__`

```python
self.settings = get_settings()
```

说明这个 service 依赖配置对象。这意味着：

- 模型名来自配置
- API key 来自配置
- 超时时间来自配置
- Base URL 来自配置

这是把“环境差异”与“代码逻辑”分开的关键。

### 6.2 `chat()`

这是最简单的业务方法：

- 读取用户输入
- 组装 `messages`
- 调 `_call_chat_api()`
- 返回 `{reply, model}`

你应该理解的是：

> 这个方法不是在“实现模型”，而是在“封装一次业务可复用的 LLM 调用方式”。

### 6.3 `extract()`

这是当前阶段最值得仔细看的方法。

它做了几件事：

1. 使用特定的 extraction prompt
2. 请求模型以 JSON 格式输出
3. 收到字符串结果后做 JSON 解析
4. 即使解析失败，也做最小兜底
5. 统一输出成稳定字段

这里体现了非常重要的一点：

> 工程里不是追求模型“完美输出”，而是要设计出“即使模型不完美，也能尽量稳定工作”的处理方式。

### 6.4 `_call_chat_api()`

这个方法是底层 HTTP 调用封装。

重点看：

- API key 校验
- payload 构建
- `response_format`
- headers 构建
- `httpx.AsyncClient`
- `response.raise_for_status()`

这一层的意义是：

- 路由不用关心 HTTP 细节
- 上层业务只关心“我要聊天”或“我要抽取”
- 底层统一负责请求模型

### 6.5 `_safe_parse_json()`

这段很重要。它体现了一个成熟工程思路：

- 不要默认模型总是听话
- 不要让一次 JSON 解析失败把整条链路彻底打断

所以当前实现里：

- 如果 JSON 解析成功，正常走
- 如果失败，就返回一个带默认值的兜底结构

### 6.6 `_normalize_keywords()` 和 `_normalize_sentiment()`

这是“输出清洗”的最小示例。

很多初学者会忽视这一层，直接把模型返回原样透传。但后续你做 RAG、Agent、Tool routing 时，输出规范化非常重要。

---

## 7. 配置层：`app/core/config.py`

文件位置：`app/core/config.py`

这一层解决的是：

- 配置从哪里来
- 程序里谁负责读配置
- 如何避免重复创建配置对象

重点：

- `BaseSettings`：自动读取环境变量
- `SettingsConfigDict(env_file=".env")`：告诉程序从 `.env` 读配置
- `@lru_cache`：避免每次都重新创建配置对象

为什么 `@lru_cache` 有意义？

因为配置对象通常应该是全局稳定的，不需要每次重新实例化。

---

## 8. 日志层：`app/core/logging.py`

文件位置：`app/core/logging.py`

这个文件当前看起来很小，但它的位置是对的。

它的作用：

- 根据 `LOG_LEVEL` 初始化日志等级
- 统一日志格式

这为后续加入：

- tracing
- request id
- tool call logs
- latency metrics

留好了入口。

---

## 9. 测试：`tests/test_health.py` 与 `tests/test_extract.py`

### `tests/test_health.py`

这是最小健康检查测试。它的意义是：

- 确认 app 可以被成功导入
- 确认 `/health` 路由存在且返回正确

### `tests/test_extract.py`

这里更值得学，因为它没有真的调用模型 API，而是：

- 用 `AsyncMock` mock 了 `llm_service.extract`
- 只验证接口层行为和响应结构

这能让你理解：

> 测试不一定要每次都连外部服务。很多时候，先保证自己代码的边界是对的，更重要。

---

## 10. 现在这套代码的优点与边界

### 优点

- 结构清晰
- 对初学者友好
- 已具备最小工程化分层
- 后续扩展空间明确

### 边界

- 还没有数据库
- 还没有会话持久化
- 还没有 RAG
- 还没有 Tool Use
- 还没有 workflow / agent state
- 错误处理仍然是最小版本

这不是缺点，而是阶段控制。当前阶段最重要的是把骨架搭稳。

---

## 11. 你读代码时最应该盯住的问题

你在看这套代码时，建议每次问自己这几个问题：

1. 这个文件的职责是什么？
2. 如果删掉这个文件，系统会缺什么？
3. 它应该依赖谁，不应该依赖谁？
4. 后续 RAG / Agent 最可能从哪里接进去？
5. 这里现在为什么写得简单？以后会怎么演进？

如果你能带着这几个问题读一遍代码，你就不是在“抄项目”，而是在真正建立工程感。

---

## 12. 建议你的下一步阅读动作

按这个顺序亲自看一遍：

1. `app/main.py`
2. `app/api/routes/chat.py`
3. `app/schemas/chat.py`
4. `app/services/prompt_service.py`
5. `app/services/llm_service.py`
6. `app/core/config.py`
7. `tests/test_extract.py`

每看完一个文件，试着自己回答：

- 这个文件解决了什么问题？
- 为什么要放在这一层？
- 后面如果加 RAG，我会先改哪里？

这套问题本身，就是你从“会跑代码”进化到“会理解工程”的关键。
