# Phase 0 + Phase 1 学习文档（已拆分）

> ⚠️ 本文档已拆分为两个更详细的独立文档，请查阅：
>
> - **[Phase 0：Python 工程基础](phase0_python_engineering.md)** — Python、FastAPI、Pydantic、异步、项目结构、测试
> - **[Phase 1：LLM 基础与 Prompt Engineering](phase1_llm_and_prompt.md)** — LLM 原理、API 调用、Prompt 设计、结构化输出、流式输出

---

*以下为旧版内容，仅供归档参考。*

---

## 1. 当前阶段的学习目标（旧版）

这一阶段对应 8 周计划中的前两周，目标不是做复杂 Agent，而是打下后面所有阶段都会用到的基础：

- 学会用 Python 搭一个最小可运行的后端项目
- 学会用 `FastAPI` 提供 HTTP API
- 学会用 `.env` 管理配置
- 学会把 LLM API 接进后端服务
- 学会让模型输出结构化结果，并由程序解析
- 学会理解“接口层 / schema 层 / service 层 / config 层”的分工

## 2. 当前阶段为什么重要

后续的 RAG、Tool Use、Workflow、Agent，本质上都不是凭空出现的，它们都建立在一个基本事实之上：

> 你必须先会把一个 AI 能力放进一个清晰的、可运行的、可维护的服务里。

很多初学者一上来就学 LangChain、LangGraph、Multi-Agent，但连：

- 配置怎么读
- API 怎么起
- 请求怎么校验
- 模型输出怎么解析
- 出错怎么排查

都没真正打通。这样后面一旦复杂度上来，就会完全失控。

## 3. 核心概念解释

### 3.1 FastAPI 是什么

`FastAPI` 是一个 Python Web 框架，用来快速搭建后端 API。你可以把它理解成：

- 浏览器、前端、脚本发请求给它
- 它负责接收请求
- 调用内部业务逻辑
- 再把结果返回给客户端

在这一阶段里，它就是我们承载 LLM 能力的“服务壳”。

### 3.2 Schema 是什么

在 `app/schemas/chat.py` 里，我们定义了请求和响应的数据结构。它的作用是：

- 限制输入格式
- 帮你做基础校验
- 让接口更清晰
- 自动生成 OpenAPI 文档

例如：

- `ChatRequest` 规定聊天接口至少要有 `message`
- `ExtractResponse` 规定结构化提取结果必须有 `summary / keywords / sentiment / model`

### 3.3 Service 是什么

`service` 层是业务逻辑层。这里最核心的是 `app/services/llm_service.py`。

它负责：

- 拼装请求给模型的 `messages`
- 调用 LLM API
- 解析模型返回结果
- 对结构化提取的结果做兜底处理

为什么不把这些逻辑直接写到 route 里？
因为 route 层应该尽量轻，只负责：

- 接收请求
- 调 service
- 返回响应

这样以后你要替换模型供应商、加重试、加 tracing，都能集中改 service 层。

### 3.4 Structured Output 是什么

这一阶段你要掌握的一个关键能力，就是：

> 不只是让模型“回答一句话”，而是让它输出程序能消费的数据结构。

在这个项目里，`/api/v1/extract` 接口就是最小示例。

它要求模型返回 JSON，然后程序把 JSON 解析成：

- 摘要 `summary`
- 关键词 `keywords`
- 情感倾向 `sentiment`

这就是后续做：

- 信息抽取
- 工单分类
- RAG 后处理
- Tool routing
- Planner 决策

的基础。

## 4. 底层原理 / 系统逻辑

这一阶段的调用链是：

1. 用户向 `/api/v1/chat` 或 `/api/v1/extract` 发请求
2. `route` 层接收请求并做 schema 校验
3. `route` 调用 `LLMService`
4. `LLMService` 根据任务选择 prompt
5. `LLMService` 用 `httpx` 请求 OpenAI-compatible 接口
6. 模型返回结果
7. 程序将结果转成统一 response schema
8. 返回给客户端

这套链路已经具备后续所有复杂系统的基本骨架。

## 5. 关键技术点逐条讲解

### 5.1 配置管理

文件：`app/core/config.py`

这里使用 `pydantic-settings` 从 `.env` 读取配置。这样做的原因是：

- API key 不应该硬编码到代码里
- 模型名、Base URL、超时时间应该能灵活修改
- 后续部署到不同环境时，配置可以分离

### 5.2 日志初始化

文件：`app/core/logging.py`

为什么现在就加日志？
因为后面你调 API、加 RAG、加 Tool Use 时，排查问题都离不开日志。现在就建立日志意识，后面会轻松很多。

### 5.3 路由层设计

文件：

- `app/api/routes/health.py`
- `app/api/routes/chat.py`

`health.py` 很简单，但很重要。健康检查是服务化的第一步。

`chat.py` 则展示了两个典型接口：

- 一个是自由文本聊天
- 一个是结构化提取

这两个接口已经足够覆盖你当前阶段要掌握的基本模式。

### 5.4 LLM 调用封装

文件：`app/services/llm_service.py`

这里最重要的不是“调用成功”，而是理解为什么要封装成类：

- 方便后续扩展更多方法
- 方便统一处理 headers / timeout / model
- 方便以后加 retry / tracing / metrics

### 5.5 Prompt 分离

文件：`app/services/prompt_service.py`

虽然现在 prompt 很短，但我们仍然把它从 service 里分离出来。原因是：

- 后续 prompt 会越来越多
- prompt 是可调试资产，不应该埋在业务代码里
- 后续可以扩展成 prompt registry

## 6. 代码如何对应这些知识点

- `app/main.py`
  - 对应：FastAPI 应用入口、路由注册
- `app/core/config.py`
  - 对应：配置分离、环境变量管理
- `app/core/logging.py`
  - 对应：日志基础
- `app/schemas/chat.py`
  - 对应：请求/响应 schema、结构化数据定义
- `app/api/routes/chat.py`
  - 对应：接口设计、请求处理、错误返回
- `app/services/llm_service.py`
  - 对应：LLM API 调用、结构化输出处理
- `tests/test_health.py`
  - 对应：接口最小测试
- `tests/test_extract.py`
  - 对应：mock 掉 LLM 调用后的结构化验证

## 7. 初学者最容易犯的错误

### 错误 1：把所有逻辑都写在 `main.py`

这样短期看起来快，长期会完全无法维护。当前项目把配置、路由、schema、service 分开，就是为了避免后面重写。

### 错误 2：直接把 API key 写死在代码里

这会带来安全问题，也会让你后续切环境非常痛苦。

### 错误 3：只返回自然语言，不做结构化输出

如果你以后要做分类、抽取、路由、工具调用，结构化输出是必须掌握的。

### 错误 4：不写测试

这个阶段不需要写很多测试，但至少要有“服务起得来”“关键接口 schema 没坏”的最小验证。

### 错误 5：一开始就接数据库和前端

这会把当前阶段复杂度拉高。当前阶段最重要的是把后端和 LLM 调用链路打通，而不是把所有东西都加进来。

## 8. 学完这一阶段后我应该会什么

完成这一阶段后，你应该具备这些能力：

- 能独立起一个 FastAPI 后端
- 能管理 API key 和模型配置
- 能调用一个 OpenAI-compatible LLM API
- 能做最小结构化输出
- 能理解 route / schema / service / config 的边界
- 能为下一阶段接入 RAG 做准备

## 9. 自检题 / 检查清单

你可以自测以下问题：

1. `FastAPI` 在这个项目里扮演什么角色？
2. 为什么 `.env` 比硬编码 API key 更合理？
3. `schema` 和 `service` 为什么要分开？
4. `/api/v1/extract` 为什么比普通 chat 更接近工程化？
5. 如果模型返回的 JSON 格式不合法，当前代码是怎么处理的？
6. 如果以后要支持 RAG，最可能先改哪些文件？

检查清单：

- [ ] 我能运行 `/health`
- [ ] 我能成功调用 `/api/v1/chat`
- [ ] 我能成功调用 `/api/v1/extract`
- [ ] 我知道配置文件在哪里
- [ ] 我能解释每个目录的职责
- [ ] 我能跑通 pytest

## 10. 下一阶段会如何使用这一阶段的成果

下一阶段（Phase 2：RAG 与 Tool Use）会直接建立在本阶段代码之上：

- 在 `services` 层新增检索服务
- 在 `schemas` 层新增 RAG 请求与响应结构
- 在 `routes` 层增加知识库问答接口
- 在 `core` 或 `services` 层新增向量库 / 文档处理相关配置

也就是说，这一阶段不是一次性练习，而是整个后续项目的“第一层地基”。
