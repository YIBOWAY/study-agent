# Phase 0：Python 工程基础

> 目标：建立 Agent 开发所需的 Python 工程化能力
> 前置要求：无，零基础可读
> 预计时间：有编程经验 3-5 天，零基础 1-2 周

---

## 0. 本文档的使用方式

这份文档不是 Python 语法手册，而是从"Agent 开发需要什么 Python 能力"出发，只教你需要的部分。

每个知识点会按以下结构组织：
1. **是什么**：用最简单的语言解释概念
2. **为什么 Agent 开发需要它**：让你理解为什么学
3. **代码示例**：能跑的示例
4. **动手练习**：你必须自己写的部分
5. **常见坑**：初学者最容易犯的错误

**建议**：每个代码示例都自己敲一遍，不要复制粘贴。出了错再排查，比读十遍文档有用。

---

## 1. Python 基础语法速通

### 1.1 变量与数据类型

Python 中变量不需要声明类型，直接赋值：

```python
name = "Research Agent"        # 字符串 str
version = 1                    # 整数 int
temperature = 0.7              # 浮点数 float
is_active = True               # 布尔值 bool
keywords = ["AI", "Agent"]     # 列表 list
config = {"model": "gpt-4o"}   # 字典 dict
```

**为什么 Agent 开发需要它**：
- 字符串：prompt 就是字符串
- 字典：API 请求和响应都是 JSON → 在 Python 中就是字典
- 列表：messages 是列表，搜索结果是列表
- 布尔值：控制流程分支（Agent 要不要继续搜索？要不要调用工具？）

### 1.2 字符串操作

字符串是你跟 LLM 打交道最多的类型：

```python
# f-string（格式化字符串）—— 你会大量使用
user_name = "张三"
prompt = f"你好，{user_name}，请问有什么需要帮助的？"

# 多行字符串 —— System Prompt 通常是多行的
system_prompt = """你是一个专业的研究助手。
请遵循以下规则：
1. 用中文回答
2. 给出信息来源
3. 如果不确定，明确说明"""

# 常用方法
text = "  Hello, World!  "
text.strip()          # 去首尾空白 → "Hello, World!"
text.lower()          # 转小写
text.split(",")       # 按逗号分割 → ["  Hello", " World!  "]
"，".join(["A", "B"]) # 用逗号连接 → "A，B"

# 检查内容
"Agent" in "AI Agent Development"  # True
text.startswith("Hello")            # 去掉空格后才 True
```

**常见坑**：
- f-string 里如果要包含花括号本身，要用 `{{` 和 `}}`
- JSON 字符串里有大量花括号，跟 f-string 混用时容易出错

### 1.3 列表与字典

```python
# ---- 列表 ----
messages = []
messages.append({"role": "user", "content": "你好"})
messages.append({"role": "assistant", "content": "你好！"})

# 列表推导式（后面会大量用到）
numbers = [1, 2, 3, 4, 5]
doubled = [n * 2 for n in numbers]           # [2, 4, 6, 8, 10]
evens = [n for n in numbers if n % 2 == 0]   # [2, 4]

# 切片
first_three = messages[:3]   # 取前三条
last_one = messages[-1]      # 取最后一条

# ---- 字典 ----
config = {
    "model": "gpt-4o",
    "temperature": 0.2,
    "max_tokens": 1000,
}

# 访问
model_name = config["model"]           # 如果 key 不存在会报错
model_name = config.get("model", "")   # 如果不存在返回默认值 ""

# 修改/新增
config["stream"] = True

# 遍历
for key, value in config.items():
    print(f"{key} = {value}")

# 字典推导式
raw = {"Name": "GPT-4o", "Temp": "0.7"}
cleaned = {k.lower(): v for k, v in raw.items()}
# → {"name": "GPT-4o", "temp": "0.7"}
```

**为什么 Agent 开发需要它**：
- `messages` 列表是 LLM API 的核心输入格式
- API 返回的 JSON 解析后就是嵌套字典
- 工具定义、配置、状态管理全是字典

### 1.4 条件与循环

```python
# 条件判断
sentiment = "positive"

if sentiment == "positive":
    print("正面")
elif sentiment == "negative":
    print("负面")
else:
    print("中性")

# 在 Agent 中的典型用法：判断模型是否要调用工具
response_message = {"tool_calls": [{"function": {"name": "search"}}]}

if response_message.get("tool_calls"):
    # 模型想调用工具，执行工具调用
    print("需要调用工具")
else:
    # 模型直接给出回答
    print("直接回答")

# for 循环
keywords = ["AI", "Agent", "LLM"]
for kw in keywords:
    print(f"关键词: {kw}")

# while 循环 —— Agent 的核心循环
max_steps = 10
step = 0
while step < max_steps:
    # action = agent.think_and_act()
    # if action == "done": break
    step += 1
```

### 1.5 函数

```python
# 基础函数
def greet(name: str) -> str:
    return f"你好，{name}"

# 带默认参数
def call_llm(message: str, temperature: float = 0.7, model: str = "gpt-4o") -> str:
    # ... 调用 API
    return "模型回复"

# 调用方式
result = call_llm("你好")                          # 使用默认参数
result = call_llm("你好", temperature=0.2)          # 覆盖部分参数
result = call_llm("你好", model="deepseek-chat")    # 关键字参数

# *args 和 **kwargs —— 框架源码里经常见到
def flexible_function(*args, **kwargs):
    print(f"位置参数: {args}")
    print(f"关键字参数: {kwargs}")

flexible_function(1, 2, name="test", value=42)
# 位置参数: (1, 2)
# 关键字参数: {'name': 'test', 'value': 42}
```

**为什么 Agent 开发需要函数**：你的整个项目就是由函数和类组成的。每个 Agent 步骤（搜索、分析、写作）都是一个函数。

---

## 2. 面向对象编程（OOP）

### 2.1 为什么需要 OOP

当你看到项目中的 `LLMService` 类时，你可能会问：为什么不直接用函数？

答案是：当多个函数需要**共享状态**（比如 API key、模型名、连接配置）时，用类把它们组织在一起更清晰。

```python
# 不用类：每个函数都要传一堆参数
def chat(api_key, base_url, model, message):
    ...

def extract(api_key, base_url, model, text):
    ...

# 用类：共享配置放在 __init__ 里，方法只关心自己的参数
class LLMService:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def chat(self, message: str) -> str:
        # self.api_key, self.model 已经可用
        ...

    def extract(self, text: str) -> dict:
        ...
```

### 2.2 类的基础语法

```python
class Agent:
    """一个最简单的 Agent 示例"""

    def __init__(self, name: str, model: str = "gpt-4o"):
        """构造函数：创建对象时自动调用"""
        self.name = name          # 实例属性
        self.model = model
        self.memory = []          # 每个 Agent 实例有自己的记忆

    def think(self, user_input: str) -> str:
        """Agent 思考"""
        self.memory.append({"role": "user", "content": user_input})
        # ... 调用 LLM
        response = f"[{self.name}] 正在思考: {user_input}"
        self.memory.append({"role": "assistant", "content": response})
        return response

    def get_memory_count(self) -> int:
        """获取记忆条数"""
        return len(self.memory)


# 使用
agent = Agent(name="研究助手", model="deepseek-chat")
reply = agent.think("什么是 RAG？")
print(reply)
print(f"记忆条数: {agent.get_memory_count()}")
```

### 2.3 继承

继承让你基于已有的类创建新的类，避免重复代码：

```python
class BaseService:
    """所有 Service 的基类"""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _make_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


class ChatService(BaseService):
    """聊天服务，继承基础服务"""
    def chat(self, message: str) -> str:
        headers = self._make_headers()  # 直接用父类的方法
        # ... 发请求
        return "回复"


class EmbeddingService(BaseService):
    """Embedding 服务，也继承基础服务"""
    def embed(self, text: str) -> list[float]:
        headers = self._make_headers()  # 同样可用
        # ... 发请求
        return [0.1, 0.2, 0.3]
```

**为什么 Agent 开发需要继承**：
- LangChain 里的 `BaseTool`、`BaseRetriever` 等都是通过继承来扩展的
- 你自定义工具时需要继承框架提供的基类

### 2.4 常见坑

1. **忘记 `self`**：类方法的第一个参数必须是 `self`
2. **混淆类属性和实例属性**：在 `__init__` 里用 `self.xxx = yyy` 定义的是实例属性
3. **过度使用继承**：不是所有东西都需要继承关系，组合（一个类持有另一个类的实例）往往更灵活

---

## 3. 异步编程（asyncio）

### 3.1 什么是异步

想象你在餐厅点餐：
- **同步**：你点了一道菜，站在厨房窗口等它做好，再点下一道
- **异步**：你一次点好所有菜，服务员叫号时你再去取

在 Agent 开发中：
- 调用 LLM API 需要等几秒
- 搜索网络需要等几秒
- 查向量数据库需要等一会儿

如果用同步方式，每个操作都要等前一个完成。用异步方式，可以同时发出多个请求。

### 3.2 基础语法

```python
import asyncio


# 普通函数
def sync_greet(name: str) -> str:
    return f"Hello, {name}"


# 异步函数（协程）—— 加了 async 关键字
async def async_greet(name: str) -> str:
    return f"Hello, {name}"


# 模拟一个耗时操作（比如调用 API）
async def call_api(name: str, delay: float) -> str:
    print(f"[{name}] 开始调用...")
    await asyncio.sleep(delay)  # 模拟网络等待（不会阻塞其他任务）
    print(f"[{name}] 调用完成")
    return f"{name} 的结果"


# 串行执行（慢）
async def serial_calls():
    result1 = await call_api("搜索", 2.0)
    result2 = await call_api("分析", 1.5)
    result3 = await call_api("总结", 1.0)
    # 总耗时 ≈ 2 + 1.5 + 1 = 4.5 秒
    return [result1, result2, result3]


# 并行执行（快）
async def parallel_calls():
    results = await asyncio.gather(
        call_api("搜索", 2.0),
        call_api("分析", 1.5),
        call_api("总结", 1.0),
    )
    # 总耗时 ≈ max(2, 1.5, 1) = 2 秒
    return results


# 运行异步函数
asyncio.run(parallel_calls())
```

### 3.3 async/await 的规则

```python
# 规则 1：async 函数必须用 await 调用
async def fetch_data():
    return "data"

# ❌ 错误：直接调用只会得到一个协程对象，不是结果
result = fetch_data()  # <coroutine object fetch_data at 0x...>

# ✅ 正确：用 await
result = await fetch_data()  # "data"

# 规则 2：await 只能在 async 函数内部使用
# ❌ 错误
def normal_function():
    data = await fetch_data()  # SyntaxError!

# ✅ 正确
async def async_function():
    data = await fetch_data()  # OK

# 规则 3：最外层用 asyncio.run() 启动
async def main():
    data = await fetch_data()
    print(data)

asyncio.run(main())
```

### 3.4 在项目中的应用

看你项目中的 `llm_service.py`：

```python
# 这是一个异步方法
async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
    prompt = system_prompt or CHAT_SYSTEM_PROMPT
    # await 表示"等待这个异步操作完成"
    content = await self._call_chat_api(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ]
    )
    return {"reply": content, "model": self.settings.llm_model}
```

FastAPI 天然支持 async，所以你的路由函数也是 `async def`：

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await llm_service.chat(user_message=request.message)
    return ChatResponse(**result)
```

### 3.5 常见坑

1. **忘记 await**：调用异步函数但没加 await，得到的是协程对象而非结果
2. **在同步函数里 await**：会直接报语法错误
3. **混用同步和异步 HTTP 客户端**：用了 `async def` 的函数里应该用 `httpx.AsyncClient`，而不是 `requests`（requests 是同步的，会阻塞事件循环）

### 3.6 动手练习

```python
"""
练习：写一个异步函数，模拟同时调用 3 个 API：
- search_api：耗时 2 秒
- analyze_api：耗时 1.5 秒
- summarize_api：耗时 1 秒

要求：
1. 用 asyncio.gather 并行调用
2. 打印总耗时
3. 验证总耗时接近 2 秒而非 4.5 秒
"""
import asyncio
import time

# 你的代码写在这里
```

---

## 4. 类型标注（Type Hints）

### 4.1 什么是类型标注

Python 是动态类型语言，变量不需要声明类型。但类型标注让代码更清晰、IDE 能帮你检查错误：

```python
# 不加类型标注 —— 看不出参数和返回值是什么
def process(data, threshold):
    ...

# 加了类型标注 —— 一目了然
def process(data: list[str], threshold: float) -> dict[str, int]:
    ...
```

### 4.2 常用类型标注

```python
from typing import Any

# 基础类型
name: str = "Agent"
count: int = 10
score: float = 0.95
active: bool = True

# 容器类型（Python 3.10+ 可以直接用小写）
tags: list[str] = ["AI", "Agent"]
config: dict[str, Any] = {"model": "gpt-4o", "temperature": 0.7}
coordinates: tuple[float, float] = (39.9, 116.4)

# 可选值（值可能是 None）
api_key: str | None = None        # Python 3.10+ 语法
# 或者用 Optional
from typing import Optional
api_key: Optional[str] = None     # 等价写法

# 函数参数和返回值
def search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    ...

# 异步函数
async def fetch(url: str) -> str:
    ...
```

### 4.3 为什么 Agent 开发需要类型标注

1. **Pydantic 依赖它**：Pydantic 用类型标注来验证数据，没有类型标注就无法工作
2. **FastAPI 依赖它**：请求参数类型、响应模型都通过类型标注定义
3. **IDE 智能提示**：加了类型标注后，IDE 能准确提示可用的方法和属性
4. **代码可读性**：看到函数签名就知道怎么调用，不需要翻文档

### 4.4 常见坑

- `str | None` 语法需要 Python 3.10+。如果你用的是 3.9，需要写 `Optional[str]`
- `list[str]` 语法需要 Python 3.9+。更老的版本需要 `from typing import List` 然后用 `List[str]`
- 类型标注**不会在运行时强制检查**，它只是给开发者和工具看的提示。真正要强制校验需要用 Pydantic

---

## 5. Pydantic —— 数据验证的基石

### 5.1 什么是 Pydantic

Pydantic 是一个数据验证库。你定义一个模型类，它自动帮你：
- 检查数据类型是否正确
- 检查必填字段是否存在
- 转换兼容类型（比如把字符串 `"42"` 转成整数 `42`）
- 在类型不对时抛出清晰的错误

### 5.2 基础用法

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息")
    temperature: float = Field(default=0.7, ge=0, le=2, description="生成温度")
    model: str = Field(default="gpt-4o", description="模型名称")


# ✅ 正确的数据
request = ChatRequest(message="你好")
print(request.message)      # "你好"
print(request.temperature)  # 0.7（使用默认值）
print(request.model)        # "gpt-4o"（使用默认值）

# ✅ 类型自动转换
request = ChatRequest(message="你好", temperature="0.5")
print(request.temperature)  # 0.5（字符串被转成 float）

# ❌ 缺少必填字段 → 报错
try:
    request = ChatRequest()  # message 是必填的
except Exception as e:
    print(e)
# validation error: message field required

# ❌ 值不合法 → 报错
try:
    request = ChatRequest(message="", temperature=5.0)
except Exception as e:
    print(e)
# message: String should have at least 1 character
# temperature: Input should be less than or equal to 2
```

### 5.3 嵌套模型

```python
from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, str]


class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = []
    model: str
    usage_tokens: int


# 嵌套数据会被递归验证
response = LLMResponse(
    content=None,
    tool_calls=[
        {"name": "search", "arguments": {"query": "AI Agent"}},
    ],
    model="gpt-4o",
    usage_tokens=150,
)

print(response.tool_calls[0].name)  # "search"
```

### 5.4 模型转字典 / JSON

```python
request = ChatRequest(message="你好")

# 转字典
data = request.model_dump()
# {'message': '你好', 'temperature': 0.7, 'model': 'gpt-4o'}

# 转 JSON 字符串
json_str = request.model_dump_json()
# '{"message":"你好","temperature":0.7,"model":"gpt-4o"}'

# 从字典创建
data = {"message": "测试", "temperature": 0.3}
request = ChatRequest(**data)
# 或者
request = ChatRequest.model_validate(data)
```

### 5.5 为什么 Agent 开发离不开 Pydantic

1. **FastAPI 的请求/响应校验**：你项目里的 `ChatRequest`、`ExtractResponse` 都是 Pydantic 模型
2. **Structured Output**：LLM 返回 JSON 后，用 Pydantic 模型验证和解析
3. **配置管理**：`pydantic-settings` 从 `.env` 文件读取配置
4. **LangChain/LangGraph**：这些框架的工具定义、状态定义底层都用 Pydantic
5. **API 文档自动生成**：FastAPI 根据 Pydantic 模型自动生成 Swagger 文档

### 5.6 在项目中的体现

你项目里的 `app/schemas/chat.py`：

```python
class ExtractResponse(BaseModel):
    summary: str         # 必填字符串
    keywords: list[str]  # 必填，字符串列表
    sentiment: str       # 必填字符串
    model: str           # 必填字符串
```

当 LLM 返回了非法数据（比如 `keywords` 不是列表），Pydantic 会报错，避免脏数据流入系统。

### 5.7 动手练习

```python
"""
练习：定义一个 Pydantic 模型 AgentConfig，包含：
- name: 字符串，必填，至少 1 个字符
- model: 字符串，默认 "gpt-4o"
- temperature: 浮点数，默认 0.7，范围 0-2
- max_iterations: 整数，默认 10，最小 1，最大 100
- tools: 字符串列表，默认空列表

然后：
1. 创建一个合法实例，打印各字段
2. 尝试创建一个 temperature=5 的实例，观察报错
3. 把实例转成字典，打印
"""
```

---

## 6. 虚拟环境管理

### 6.1 为什么需要虚拟环境

假设你有两个项目：
- 项目 A 需要 `langchain==0.2.0`
- 项目 B 需要 `langchain==0.3.5`

如果安装在全局 Python 里，两个版本会冲突。虚拟环境为每个项目创建独立的 Python 包空间。

### 6.2 conda 虚拟环境（你当前使用的）

```bash
# 创建环境
conda create -n my-agent python=3.11

# 激活环境
conda activate my-agent

# 安装包
pip install fastapi uvicorn pydantic

# 查看已安装的包
pip list

# 导出依赖
pip freeze > requirements.txt

# 从 requirements.txt 安装
pip install -r requirements.txt

# 退出环境
conda deactivate

# 列出所有环境
conda env list
```

### 6.3 venv（Python 自带的轻量方案）

```bash
# 创建
python -m venv .venv

# 激活（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活（Linux/Mac）
source .venv/bin/activate

# 安装包
pip install -r requirements.txt
```

### 6.4 常见坑

1. **忘记激活环境**：安装的包跑到全局 Python 里了
2. **IDE 没识别虚拟环境**：VS Code 右下角确认 Python 解释器指向虚拟环境
3. **requirements.txt 没锁版本**：写 `fastapi==0.115.0` 而不是 `fastapi`，否则别人安装时版本可能不同

---

## 7. FastAPI 基础

### 7.1 什么是 FastAPI

FastAPI 是一个用 Python 快速构建 Web API 的框架。它的核心优势：
- **快**：性能接近 Node.js/Go
- **类型安全**：基于 Pydantic 自动验证请求数据
- **自动文档**：访问 `/docs` 就能看到 Swagger UI
- **原生异步**：天然支持 `async/await`

### 7.2 最小示例

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello, World"}


@app.get("/health")
def health():
    return {"status": "ok"}
```

启动：`uvicorn main:app --reload`

- `main`：文件名（main.py）
- `app`：FastAPI 实例变量名
- `--reload`：代码修改后自动重启

### 7.3 请求和响应

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()


# 定义请求体
class QuestionRequest(BaseModel):
    question: str
    context: str | None = None


# 定义响应体
class AnswerResponse(BaseModel):
    answer: str
    confidence: float


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest) -> AnswerResponse:
    if len(request.question) < 2:
        raise HTTPException(status_code=400, detail="问题太短")

    # 这里实际会调用 LLM
    return AnswerResponse(
        answer=f"你问的是：{request.question}",
        confidence=0.95,
    )
```

### 7.4 路由组织（Router）

当接口多了之后，不应该全写在一个文件里：

```python
# app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {"status": "ok"}


# app/api/routes/chat.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["llm"])

@router.post("/chat")
async def chat(...):
    ...


# app/main.py —— 把所有 router 装配到 app 上
from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.chat import router as chat_router

app = FastAPI()
app.include_router(health_router)
app.include_router(chat_router)
```

**这就是你项目中的组织方式**。

### 7.5 为什么 Agent 开发需要 FastAPI

Agent 不是一个独立运行的脚本，而是一个可以被调用的**服务**。FastAPI 提供：
- HTTP 接口：前端/其他系统可以调用你的 Agent
- 请求验证：自动拦截非法请求
- 流式响应（SSE）：后续实现 Agent 实时输出
- WebSocket：后续实现双向通信
- 自动文档：团队协作和调试的利器

---

## 8. 配置管理与 .env

### 8.1 为什么不能把密钥写在代码里

```python
# ❌ 绝对不要这样做
api_key = "sk-abc123..."

# 原因：
# 1. 推到 GitHub 后全世界都能看到你的 key
# 2. 不同环境（开发/测试/生产）key 不同，代码里改来改去很痛苦
# 3. 违反安全最佳实践
```

### 8.2 使用 .env + pydantic-settings

```python
# .env 文件（不提交到 Git）
LLM_API_KEY=sk-abc123...
LLM_MODEL=gpt-4o
LLM_TIMEOUT=60

# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_timeout: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",           # 从哪个文件读
        env_file_encoding="utf-8",
        case_sensitive=False,      # 环境变量不区分大小写
        extra="ignore",            # 忽略多余的环境变量
    )
```

Pydantic-settings 的工作流程：
1. 定义 `Settings` 类，每个字段名对应一个环境变量
2. 优先级：环境变量 > .env 文件 > 默认值
3. 自动做类型转换（`"60"` → `int(60)`）

### 8.3 .env.example 的作用

`.env` 包含真实密钥，不能提交到 Git。但团队成员需要知道应该配置哪些变量。所以：
- `.env.example`：提交到 Git，包含变量名和示例值（不含真实密钥）
- `.env`：本地创建，填入真实值
- `.gitignore`：把 `.env` 加进去

### 8.4 在项目中的体现

你的 `.env.example`：
```
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.xairouter.com/v1
LLM_MODEL=gpt-5.4
```

你的 `app/core/config.py` 用 `get_settings()` + `@lru_cache` 确保全局只读一次配置。

---

## 9. HTTP 客户端（httpx）

### 9.1 为什么用 httpx 而不是 requests

| 对比 | requests | httpx |
|------|----------|-------|
| 同步 | ✅ | ✅ |
| 异步 | ❌ | ✅ |
| HTTP/2 | ❌ | ✅ |
| API 相似度 | — | 跟 requests 几乎一样 |

因为我们用了 `async def`，所以需要异步 HTTP 客户端。httpx 是目前最好的选择。

### 9.2 基础用法

```python
import httpx

# 同步请求（简单脚本用）
response = httpx.get("https://httpbin.org/get")
print(response.status_code)  # 200
print(response.json())

# 异步请求（FastAPI 服务里用）
async with httpx.AsyncClient(timeout=30) as client:
    response = await client.post(
        "https://api.example.com/chat/completions",
        headers={"Authorization": "Bearer sk-xxx"},
        json={"model": "gpt-4o", "messages": [...]},
    )
    response.raise_for_status()  # 如果状态码不是 2xx，抛异常
    data = response.json()
```

### 9.3 在项目中的体现

`llm_service.py` 中的 `_call_chat_api` 方法：

```python
async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
```

关键点：
- 用 `async with` 管理连接生命周期
- `timeout` 防止请求无限等待
- `raise_for_status()` 把 HTTP 错误码转成异常
- `response.json()` 把 JSON 字符串解析成字典

---

## 10. 项目结构设计

### 10.1 为什么项目结构重要

Agent 项目会越来越复杂。如果一开始就把所有代码堆在一个文件里，后面加 RAG、Tool Use、多 Agent 时会完全乱掉。

### 10.2 当前项目结构解读

```
8w-plan/
├── app/                          # 应用代码
│   ├── __init__.py               # 标记这是一个 Python 包
│   ├── main.py                   # 应用入口：创建 app、注册路由
│   ├── api/                      # 接口层
│   │   ├── __init__.py
│   │   └── routes/               # 按功能分文件
│   │       ├── __init__.py
│   │       ├── health.py         # GET /health
│   │       └── chat.py           # POST /api/v1/chat, POST /api/v1/extract
│   ├── core/                     # 基础设施层
│   │   ├── __init__.py
│   │   ├── config.py             # 配置读取
│   │   └── logging.py            # 日志初始化
│   ├── schemas/                  # 数据结构定义
│   │   ├── __init__.py
│   │   └── chat.py               # 请求/响应 Pydantic 模型
│   └── services/                 # 业务逻辑层
│       ├── __init__.py
│       ├── llm_service.py        # LLM 调用封装
│       └── prompt_service.py     # Prompt 管理
├── tests/                        # 测试
│   ├── test_health.py
│   └── test_extract.py
├── .env                          # 本地配置（不提交 Git）
├── .env.example                  # 配置模板（提交 Git）
└── requirements.txt              # 依赖列表
```

### 10.3 分层的核心原则

```
请求进来 → routes（接口层）→ services（业务层）→ 外部系统（LLM API）
                ↓                    ↓
           schemas（校验）       core（配置/日志）
```

- **routes** 只做：接收请求 → 调 service → 返回响应
- **services** 只做：业务逻辑（调 API、处理数据）
- **schemas** 只做：定义数据结构和校验规则
- **core** 只做：基础设施（配置、日志、数据库连接）

好处：后续你加 RAG 功能时，只需要：
- 在 `services/` 加一个 `rag_service.py`
- 在 `schemas/` 加 RAG 相关的请求/响应模型
- 在 `routes/` 加 RAG 接口

不需要改已有的代码。

---

## 11. 测试基础（pytest）

### 11.1 为什么需要测试

你修了一个 bug，但不确定有没有弄坏其他功能。跑一下测试，如果全绿，就可以放心了。

### 11.2 最小测试示例

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

关键点：
- `TestClient` 模拟 HTTP 请求，不需要真的启动服务
- `assert` 如果条件为 False 会报错
- 函数名以 `test_` 开头，pytest 才能识别

### 11.3 使用 Mock

当你测试一个接口，但不想真的调用 LLM API（避免花钱、网络波动导致测试不稳定），就需要 Mock：

```python
from unittest.mock import AsyncMock, patch


@patch("app.api.routes.chat.llm_service.extract", new_callable=AsyncMock)
def test_extract_endpoint(mock_extract):
    # 告诉 mock：当 extract 被调用时，返回这个假数据
    mock_extract.return_value = {
        "summary": "这是摘要",
        "keywords": ["AI"],
        "sentiment": "neutral",
        "model": "mock",
    }

    response = client.post(
        "/api/v1/extract",
        json={"text": "一段测试文本"},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "这是摘要"
```

### 11.4 运行测试

```bash
# 运行全部测试
python -m pytest

# 显示详细信息
python -m pytest -v

# 只运行某个文件
python -m pytest tests/test_health.py

# 只运行某个测试函数
python -m pytest tests/test_health.py::test_health_check_returns_ok
```

**注意**：要在项目根目录（`8w-plan/`）下运行，否则 Python 找不到 `app` 模块。

---

## 12. Git 基础

### 12.1 最小必会命令

```bash
# 初始化仓库
git init

# 查看状态
git status

# 添加文件到暂存区
git add .                    # 添加所有修改
git add app/services/        # 添加指定目录

# 提交
git commit -m "feat: add chat endpoint"

# 查看提交历史
git log --oneline

# 推送到远程
git push origin main
```

### 12.2 .gitignore

告诉 Git 哪些文件不要追踪：

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# 环境配置
.env

# IDE
.vscode/
.idea/

# 操作系统
.DS_Store
Thumbs.db
```

### 12.3 提交信息规范

```
feat: 新功能
fix: 修 bug
docs: 文档修改
refactor: 重构（不改功能）
test: 添加或修改测试
chore: 杂项（依赖更新等）

示例：
feat: add /api/v1/extract endpoint
fix: handle JSON parse error in extract service
docs: add phase0 learning doc
```

---

## 13. 装饰器（Decorator）

### 13.1 什么是装饰器

装饰器是一个"包裹"函数的函数，可以在不修改原函数代码的情况下添加额外行为：

```python
import time


def timer(func):
    """记录函数执行时间的装饰器"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} 耗时 {elapsed:.2f}s")
        return result
    return wrapper


@timer
def slow_function():
    time.sleep(1)
    return "done"


slow_function()
# 输出: slow_function 耗时 1.00s
```

### 13.2 你已经在用装饰器了

```python
@app.get("/health")          # FastAPI 路由装饰器
def health_check():
    ...

@router.post("/chat")        # Router 路由装饰器
async def chat():
    ...

@lru_cache                   # 缓存装饰器
def get_settings():
    ...
```

### 13.3 为什么 Agent 开发需要理解装饰器

- FastAPI 的路由定义全靠装饰器
- LangChain 的 `@tool` 装饰器用来定义工具
- 很多框架用装饰器做缓存、重试、日志等横切关注点
- 读框架源码时经常遇到

---

## 14. 上下文管理器

### 14.1 什么是上下文管理器

用 `with` 语句管理资源的开启和关闭：

```python
# 文件操作
with open("data.txt", "r") as f:
    content = f.read()
# 文件自动关闭，即使发生异常

# HTTP 客户端
async with httpx.AsyncClient() as client:
    response = await client.get("https://...")
# 连接自动关闭
```

### 14.2 为什么重要

Agent 开发中有大量需要"打开→使用→关闭"的资源：
- HTTP 连接
- 数据库连接
- 文件句柄
- 向量数据库客户端

忘记关闭会导致资源泄漏。`with` 语句保证即使出错也会正确关闭。

---

## 15. 生成器（Generator）

### 15.1 什么是生成器

生成器是一种"惰性"序列，每次只产出一个值，而不是一次性把所有值放在内存里：

```python
# 普通函数：一次性返回所有结果
def get_all_numbers(n):
    result = []
    for i in range(n):
        result.append(i)
    return result  # 如果 n=10亿，内存爆了

# 生成器：每次只产出一个
def generate_numbers(n):
    for i in range(n):
        yield i  # 暂停，返回一个值，下次调用继续

# 使用
for num in generate_numbers(10):
    print(num)
```

### 15.2 为什么 Agent 开发需要生成器

**流式输出**：LLM 生成回答时不是一下子全出来，而是一个 token 一个 token 地输出。这就是生成器的典型场景：

```python
async def stream_chat(message: str):
    """模拟 LLM 流式输出"""
    response = await client.post(
        url,
        json={"messages": [...], "stream": True},
        # 注意这里不用 response.json()，而是逐块读取
    )
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            chunk = json.loads(line[6:])
            content = chunk["choices"][0]["delta"].get("content", "")
            if content:
                yield content  # 每生成一个 token 就输出一次
```

后续做 Agent 时，你会大量使用流式输出来改善用户体验。

---

## 16. 阶段自检清单

完成 Phase 0 后，请逐项确认：

### 概念理解
- [ ] 我能解释什么是虚拟环境，为什么需要它
- [ ] 我能解释 `async/await` 的基本含义
- [ ] 我能解释 Pydantic 的作用
- [ ] 我能解释为什么配置要放在 `.env` 里而不是代码里
- [ ] 我能解释 `routes`、`schemas`、`services`、`core` 各层的职责边界

### 实操能力
- [ ] 我能创建和激活 conda 虚拟环境
- [ ] 我能安装 `requirements.txt` 中的依赖
- [ ] 我能启动 FastAPI 服务并访问 `/docs`
- [ ] 我能运行 `python -m pytest` 并看到测试通过
- [ ] 我能用 Git 提交代码

### 代码能力
- [ ] 我能写一个 Pydantic 模型并验证数据
- [ ] 我能写一个 FastAPI 路由（GET 和 POST）
- [ ] 我能写一个简单的异步函数
- [ ] 我能用 httpx 发送异步 HTTP 请求
- [ ] 我能用 `@patch` 写一个 mock 测试

---

## 17. 推荐资料

| 资料 | 用途 | 说明 |
|------|------|------|
| [Python 官方教程](https://docs.python.org/zh-cn/3/tutorial/) | Python 基础 | 中文版，权威 |
| [FastAPI 官方文档](https://fastapi.tiangolo.com/zh/) | FastAPI 全部功能 | 有中文版，教程质量极高 |
| [Pydantic V2 文档](https://docs.pydantic.dev/latest/) | 数据验证 | 注意看 V2 版本 |
| [Real Python: Async IO](https://realpython.com/async-io-python/) | asyncio 入门 | 图文并茂，非常清晰 |
| [httpx 文档](https://www.python-httpx.org/) | HTTP 客户端 | 简洁实用 |
| [Pro Git 中文版](https://git-scm.com/book/zh/v2) | Git 学习 | 看前三章即可 |

---

## 18. 下一步

Phase 0 的所有内容都是为了让你能读懂和修改当前项目代码。当你完成上面的自检清单后，就可以进入 Phase 1（LLM 基础与 Prompt Engineering），开始真正接触大语言模型。

Phase 1 会用到你在 Phase 0 学到的所有能力：
- 用 FastAPI 提供 API
- 用 Pydantic 定义请求/响应
- 用 httpx 调用 LLM API
- 用 asyncio 处理异步调用
- 用 .env 管理 API Key
