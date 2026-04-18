# Phase 1：LLM 基础与 Prompt Engineering

> 目标：理解大语言模型的工作原理，掌握 Prompt 工程化技术
> 前置要求：完成 Phase 0（能读写 Python，能用 FastAPI + httpx + Pydantic）
> 预计时间：有 AI 基础 3-5 天，零基础 1-2 周

---

## 0. 本文档的使用方式

Phase 1 的核心是理解 LLM 的"脾气"——它能做什么、不能做什么、怎么跟它对话才能拿到好结果。

这是你后续所有 Agent 开发的基础。你不需要懂模型的训练过程和数学公式，但你必须理解：
- LLM 的输入输出是什么
- Token、上下文窗口等核心概念
- 如何设计 System Prompt
- 如何让 LLM 按你要的格式输出
- API 调用的工程细节

**建议**：边读边用你的项目实际调一调 API，改改 prompt，看看效果。理论再好，不如自己跑一遍。

---

## 1. 什么是大语言模型（LLM）

### 1.1 一句话解释

LLM 是一个**文本补全引擎**：你给它一段文字（prompt），它预测接下来最可能出现的文字。

```
输入："今天天气"
↓ LLM 预测
输出："真不错，适合出去走走。"
```

它不是"理解"了你的话然后"思考"出答案，而是根据训练时见过的海量文本，**统计出最可能接在你的输入后面的文字**。

### 1.2 这意味着什么

1. **它没有记忆**：每次 API 调用是独立的。上一轮对话它都忘了，除非你把历史消息一起发过去
2. **它可能编造内容（幻觉）**：它的目标是生成"看起来合理"的文本，不是"正确"的文本
3. **它的回答取决于你怎么问**：同样的问题，不同的措辞/格式可能得到差异巨大的回答
4. **它擅长模式匹配**：如果你给它几个例子（Few-shot），它能学会模式并应用到新输入

### 1.3 主流模型对比

| 模型 | 厂商 | 特点 | 适用场景 |
|------|------|------|----------|
| GPT-4o | OpenAI | 综合能力最强，多模态 | 复杂推理、代码生成 |
| GPT-4o-mini | OpenAI | 便宜快速，能力尚可 | 日常对话、简单任务 |
| Claude 3.5 Sonnet | Anthropic | 长文本处理优秀，代码能力强 | 文档分析、代码审查 |
| DeepSeek V3 | DeepSeek | 开源模型中综合最强，中文好 | 性价比优先的场景 |
| Qwen 2.5 | 阿里 | 中文能力强，开源 | 国内部署、中文任务 |
| Llama 3.1 | Meta | 开源社区活跃 | 自行部署、研究 |

**实际工作建议**：先用 GPT-4o 或 Claude 做效果验证，效果达标后切换到更便宜的模型（GPT-4o-mini、DeepSeek）降本。

---

## 2. Token 与上下文窗口

### 2.1 什么是 Token

LLM 不是按"字"处理文本，而是按 **Token** 处理。Token 是模型的最小处理单位：

```
英文："Hello, world!" → ["Hello", ",", " world", "!"]（4 tokens）
中文："你好世界" → ["你好", "世界"]（2 tokens）或 ["你", "好", "世", "界"]（4 tokens）
```

不同模型的分词方式不同，但有个粗略估计：
- 英文：1 token ≈ 0.75 个单词 ≈ 4 个字符
- 中文：1 token ≈ 1-2 个汉字

### 2.2 为什么 Token 数量重要

1. **上下文窗口限制**：每个模型有最大 token 限制（如 GPT-4o 是 128K tokens）。超过了就无法处理
2. **API 收费按 token 计**：输入 token 和输出 token 分别计费
3. **长度影响质量**：即使没超过限制，过长的 context 也可能导致模型"注意力分散"，忽略中间内容（Lost in the Middle 问题）

### 2.3 上下文窗口

```
┌─────────────────────────────────────┐
│           上下文窗口 (128K)           │
│                                     │
│  System Prompt (500 tokens)         │
│  +                                  │
│  历史对话 (2000 tokens)              │
│  +                                  │
│  当前问题 (100 tokens)               │
│  +                                  │
│  模型回答 (留出空间, ~1000 tokens)    │
│                                     │
│  = 总共使用 ~3600 tokens             │
└─────────────────────────────────────┘
```

**工程含义**：
- 你需要控制发给模型的总 token 数
- 历史对话不能无限累积，需要截断或摘要
- RAG 检索的文档片段不能太长
- 留足够的空间给模型生成回答

### 2.4 如何估算 Token

```python
# 方式 1：用 tiktoken 库（OpenAI 模型的精确计算）
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")
text = "你好，我想了解 AI Agent 的开发"
tokens = enc.encode(text)
print(f"Token 数: {len(tokens)}")  # 精确值

# 方式 2：粗略估算
# 中文：字数 × 0.6~1.5
# 英文：单词数 × 1.3
```

### 2.5 常见坑

- **以为 128K 就是 128K 中文字**：实际上中文 1 字可能消耗 1-3 个 token，128K token ≈ 5-8 万中文字
- **忘记计算 System Prompt 的 token**：如果你的 System Prompt 很长，要记得它也占 token
- **输出 token 更贵**：通常输出 token 的价格是输入 token 的 2-4 倍

---

## 3. Messages 格式与角色

### 3.1 OpenAI 兼容的 Messages 格式

几乎所有 LLM API（不管是 OpenAI、DeepSeek、阿里通义还是你项目用的 xairouter）都遵循这个格式：

```python
messages = [
    {
        "role": "system",
        "content": "你是一个专业的研究助手..."
    },
    {
        "role": "user",
        "content": "什么是 RAG？"
    },
    {
        "role": "assistant",
        "content": "RAG（Retrieval-Augmented Generation）是..."
    },
    {
        "role": "user",
        "content": "它有什么优势？"
    }
]
```

### 3.2 三种角色

| 角色 | 作用 | 类比 |
|------|------|------|
| `system` | 设定模型的身份、规则、约束 | 员工手册 |
| `user` | 用户的输入 | 客户的问题 |
| `assistant` | 模型的回答 | 员工的回答 |

**关键理解**：
- `system` 消息影响模型的整体行为，通常放在最前面且只有一条
- 多轮对话就是把 `user` 和 `assistant` 交替放进 messages 列表
- 模型没有"记忆"，它看到的就是你传入的完整 messages 列表

### 3.3 多轮对话的实现

```python
class ConversationManager:
    """管理多轮对话"""

    def __init__(self, system_prompt: str, max_history: int = 20):
        self.system_message = {"role": "system", "content": system_prompt}
        self.history: list[dict] = []
        self.max_history = max_history

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        """获取要发送给 API 的完整 messages"""
        # 截断历史，只保留最近的 N 条
        recent = self.history[-self.max_history:]
        return [self.system_message] + recent

    async def chat(self, user_input: str) -> str:
        self.add_user_message(user_input)
        messages = self.get_messages()

        # 调用 LLM API
        response = await call_llm(messages)
        assistant_reply = response["choices"][0]["message"]["content"]

        self.add_assistant_message(assistant_reply)
        return assistant_reply
```

---

## 4. API 调用详解

### 4.1 请求格式

```python
import httpx

async def call_chat_api(messages: list[dict]) -> dict:
    url = "https://api.xairouter.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-xxxx",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "temperature": 0.7,   # 可选
        "max_tokens": 1000,   # 可选
        # "stream": False,    # 是否流式
        # "response_format": {"type": "json_object"},  # 强制 JSON 输出
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
```

### 4.2 响应格式

```json
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "gpt-4o-2024-08-06",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "RAG 是检索增强生成的缩写..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 50,
        "completion_tokens": 100,
        "total_tokens": 150
    }
}
```

关键字段解读：
- `choices[0].message.content`：模型的回答文本
- `choices[0].finish_reason`：
  - `"stop"`：正常结束
  - `"length"`：达到 max_tokens 截断了（回答不完整！）
  - `"tool_calls"`：模型想调用工具（后续 Phase 会学到）
- `usage`：token 消耗统计，用于成本监控

### 4.3 在你项目中的体现

`app/services/llm_service.py` 中的 `_call_chat_api`：

```python
async def _call_chat_api(self, messages: list[dict], response_format=None) -> str:
    url = f"{self.settings.llm_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {self.settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": self.settings.llm_model,
        "messages": messages,
    }
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
```

### 4.4 动手练习

```python
"""
练习：在你的项目基础上，写一个脚本直接调用 LLM API：

1. 读取 .env 中的配置
2. 构造一个 messages 列表（system + user）
3. 发送请求
4. 打印：模型回答、token 消耗、finish_reason

提示：你可以直接复用 app/core/config.py 中的 Settings
"""
import asyncio
import httpx
# 你的代码写在这里
```

---

## 5. System Prompt 设计

### 5.1 System Prompt 的作用

System Prompt 就像给员工下达的"工作守则"——它定义了模型应该：
- 扮演什么角色
- 遵循什么规则
- 用什么风格回答
- 在什么情况下拒绝回答

### 5.2 System Prompt 设计原则

#### 原则 1：明确角色

```
❌ 模糊: 你是一个 AI 助手。
✅ 明确: 你是一个专注于 Python 后端开发的技术顾问。
        你的用户是有 1-3 年经验的开发者。
        你的回答应该包含代码示例和最佳实践。
```

#### 原则 2：给出约束和规则

```
✅ 好的约束:
你必须遵循以下规则：
1. 所有回答使用中文
2. 代码示例使用 Python 3.10+
3. 如果不确定某个信息，明确说"我不确定"而不是编造
4. 回答长度控制在 500 字以内
5. 不要讨论政治、宗教等敏感话题
```

#### 原则 3：定义输出格式

```
✅ 当需要结构化输出时:
请按以下 JSON 格式回复，不要包含任何其他内容：
{
    "summary": "一句话摘要",
    "keywords": ["关键词1", "关键词2"],
    "sentiment": "positive/negative/neutral"
}
```

#### 原则 4：给出示例（Few-shot 融入 System Prompt）

```
✅ 带示例:
当用户问技术问题时，请按以下模式回答：

用户：什么是 FastAPI？
助手：FastAPI 是一个用 Python 构建 API 的现代框架。
**核心特点**：
- 性能接近 Node.js/Go
- 基于 Pydantic 的自动数据验证
- 自动生成 API 文档
**快速上手**：
```python
from fastapi import FastAPI
app = FastAPI()
```
```

### 5.3 你项目中的 System Prompt 分析

`app/services/prompt_service.py` 中的 `EXTRACT_SYSTEM_PROMPT`：

```python
EXTRACT_SYSTEM_PROMPT = """你是一个文本分析助手。请从用户提供的文本中提取以下信息：
1. summary: 一句话摘要（不超过50字）
2. keywords: 3-5个关键词
3. sentiment: 情感倾向（positive/negative/neutral）

请严格按照以下JSON格式返回，不要返回任何其他内容：
{
    "summary": "摘要内容",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "sentiment": "positive/negative/neutral"
}"""
```

这个 Prompt 为什么有效：
1. ✅ 明确角色："文本分析助手"
2. ✅ 明确任务：提取 3 个字段
3. ✅ 约束具体："不超过50字"、"3-5个关键词"
4. ✅ 格式明确：给了 JSON 模板
5. ✅ 排除干扰："不要返回任何其他内容"

### 5.4 System Prompt 的常见坑

1. **太长不一定好**：超长的 System Prompt 会浪费 token，且模型可能忽略中间的规则
2. **矛盾的规则**：比如"简洁回答"和"详细说明每个步骤"同时出现
3. **过度依赖 System Prompt**：它是"指导"而非"保证"。模型可能偶尔不遵守，你的代码需要有容错处理

---

## 6. Prompt 工程核心技术

### 6.1 Zero-shot vs Few-shot

**Zero-shot**（零样本）：直接给任务描述，不给示例

```python
messages = [
    {"role": "system", "content": "你是一个情感分析专家"},
    {"role": "user", "content": "分析这句话的情感：这个产品太好用了！"},
]
# 输出："正面情感"
```

**Few-shot**（少样本）：给几个示例，让模型学会模式

```python
messages = [
    {"role": "system", "content": "你是一个情感分析专家"},
    # 示例 1
    {"role": "user", "content": "分析：这个产品太好用了！"},
    {"role": "assistant", "content": '{"sentiment": "positive", "confidence": 0.95}'},
    # 示例 2
    {"role": "user", "content": "分析：包装太差了，到手已经破了"},
    {"role": "assistant", "content": '{"sentiment": "negative", "confidence": 0.90}'},
    # 实际输入
    {"role": "user", "content": "分析：还行吧，没什么特别的"},
]
# 模型学会了格式，输出：{"sentiment": "neutral", "confidence": 0.80}
```

**什么时候用 Few-shot**：
- 输出格式比较复杂时
- 任务有一定歧义性时
- Zero-shot 效果不理想时

**注意**：Few-shot 的示例会消耗 token。通常 2-5 个示例就够了。

### 6.2 Chain of Thought（思维链，CoT）

让模型"一步步思考"，而不是直接给答案。对于需要推理的任务效果显著提升。

```python
# ❌ 直接问（可能出错）
messages = [
    {"role": "user", "content": "一个果园有 3 排苹果树，每排 7 棵，每棵结了 12 个苹果，共多少个？"},
]

# ✅ 加上 CoT 提示
messages = [
    {"role": "user", "content": """一个果园有 3 排苹果树，每排 7 棵，每棵结了 12 个苹果，共多少个？

请一步步思考："""},
]
# 模型输出：
# 第一步：计算总共有多少棵树 = 3 × 7 = 21 棵
# 第二步：计算总共有多少苹果 = 21 × 12 = 252 个
# 答案：252 个
```

**在 Agent 中的应用**：

```python
system_prompt = """你是一个研究助手。当用户提出问题时，请按以下步骤思考：

1. **理解问题**：明确用户想知道什么
2. **分析信息**：现有信息是否足够
3. **推理过程**：一步步推导
4. **得出结论**：给出最终回答
5. **置信度**：对回答的确信程度（高/中/低）

每一步都要明确写出来。"""
```

CoT 的变体：
- **Zero-shot CoT**：在 prompt 末尾加"请一步步思考"即可触发
- **Manual CoT**：在 Few-shot 示例中给出思考过程
- **Self-consistency CoT**：让模型思考多次，取多数一致的答案

### 6.3 Tree of Thoughts（思维树，ToT）

CoT 是线性的一条思路，ToT 允许模型探索多个思路分支：

```python
system_prompt = """你是一个策略分析师。当分析问题时，请：

1. 提出 3 个不同的解题思路
2. 对每个思路进行 2-3 步推演
3. 评估每个思路的优缺点
4. 选择最优思路并给出最终方案

用以下格式：
## 思路 A：[标题]
- 推演：...
- 评估：优点...，缺点...

## 思路 B：[标题]
...

## 最优方案
选择思路 X，因为..."""
```

**实际应用场景**：Agent 选择下一步行动时，可以让模型先生成多个方案再选最优的。

### 6.4 角色扮演（Role Prompting）

给模型一个具体角色，能显著影响输出质量和风格：

```python
# 不同角色产生不同回答
prompts = {
    "安全专家": "你是一个拥有 15 年经验的网络安全专家。请从安全角度审查以下代码：",
    "性能工程师": "你是一个专注于高并发系统的性能工程师。请分析以下代码的性能瓶颈：",
    "代码审查员": "你是一个严格的高级代码审查员。请按照以下标准审查代码：可读性、可维护性、错误处理...",
}
```

### 6.5 Prompt Chaining（提示链）

将复杂任务拆分成多个步骤，每个步骤用一个独立的 Prompt：

```python
async def research_topic(topic: str) -> str:
    # 步骤 1：生成研究大纲
    outline = await call_llm(
        system="你是一个研究规划专家",
        user=f"为以下主题生成一个研究大纲（3-5个要点）：{topic}",
    )

    # 步骤 2：逐一展开要点
    details = []
    for point in parse_outline(outline):
        detail = await call_llm(
            system="你是一个知识渊博的研究员",
            user=f"请详细解释以下研究要点（200字以内）：{point}",
        )
        details.append(detail)

    # 步骤 3：整合成最终报告
    report = await call_llm(
        system="你是一个学术写作专家",
        user=f"请将以下研究内容整合成一篇连贯的报告：\n{chr(10).join(details)}",
    )

    return report
```

**这就是 Agent 架构的雏形**——把复杂任务拆解成多个 LLM 调用的链条。

---

## 7. 结构化输出（Structured Output）

### 7.1 为什么需要结构化输出

LLM 默认输出自然语言文本。但在 Agent 系统中，你需要机器可解析的格式：

```
❌ 自然语言输出（难以代码处理）
"这段文本的关键词是 AI、Agent 和大模型，整体情感偏正面。"

✅ JSON 输出（代码直接解析）
{"keywords": ["AI", "Agent", "大模型"], "sentiment": "positive"}
```

### 7.2 方法 1：在 Prompt 中要求 JSON

你项目的 `EXTRACT_SYSTEM_PROMPT` 就用了这个方法：

```python
system_prompt = """请严格按照以下JSON格式返回，不要返回任何其他内容：
{
    "summary": "摘要内容",
    "keywords": ["关键词1", "关键词2"],
    "sentiment": "positive/negative/neutral"
}"""
```

**优点**：简单，所有模型都支持
**缺点**：模型可能偶尔不遵守（输出解释文字、格式错误等）

### 7.3 方法 2：API 的 response_format 参数

OpenAI 兼容 API 支持强制 JSON 输出：

```python
payload = {
    "model": "gpt-4o",
    "messages": messages,
    "response_format": {"type": "json_object"},  # 强制 JSON
}
```

你项目的 `extract` 方法就用了这个：

```python
content = await self._call_chat_api(
    messages=messages,
    response_format={"type": "json_object"},
)
```

**优点**：模型保证输出合法 JSON
**缺点**：
- 不是所有模型/API 都支持
- 只保证是合法 JSON，不保证 JSON 的 schema 符合你的要求

### 7.4 方法 3：Pydantic + 后处理（你项目的做法）

即使用了 `response_format`，也需要验证 JSON 的内容是否正确：

```python
import json

async def extract(self, text: str) -> dict:
    # 1. 调用 API（强制 JSON 输出）
    content = await self._call_chat_api(
        messages=[...],
        response_format={"type": "json_object"},
    )

    # 2. 解析 JSON
    data = self._safe_parse_json(content)

    # 3. 处理可能的格式问题
    keywords = self._normalize_keywords(data.get("keywords", []))
    sentiment = self._normalize_sentiment(data.get("sentiment", "neutral"))

    # 4. 返回标准化结果
    return {
        "summary": data.get("summary", ""),
        "keywords": keywords,
        "sentiment": sentiment,
        "model": self.settings.llm_model,
    }
```

这个三层防御策略值得学习：
1. **Prompt 要求格式**：大部分情况管用
2. **API 强制 JSON**：防止输出非 JSON
3. **代码后处理/归一化**：防止 JSON 里的值不合法

### 7.5 常见坑

1. **JSON 中文引号**：模型偶尔会输出中文引号 `""` 而不是英文引号 `""`
2. **多余的 Markdown**：模型可能输出 ` ```json ... ``` ` 包裹的 JSON
3. **字段名不一致**：可能返回 `key_words` 而不是 `keywords`
4. **数组变字符串**：`keywords` 可能返回 `"AI, Agent"` 而不是 `["AI", "Agent"]`

这些都需要你在代码中做防御性处理。看 `llm_service.py` 中的 `_normalize_keywords` 方法，它就是处理"关键词格式不确定"的问题。

### 7.6 动手练习

```python
"""
练习：设计一个 Prompt，让 LLM 分析一段代码并以 JSON 格式返回：
{
    "language": "语言名",
    "purpose": "代码用途（一句话）",
    "complexity": "low/medium/high",
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}

然后：
1. 写 System Prompt
2. 用你的项目 API 调用测试
3. 用 Pydantic 模型验证返回的 JSON
4. 处理可能的格式异常
"""
```

---

## 8. 关键参数详解

### 8.1 temperature（温度）

控制输出的"随机性"：

```
temperature = 0    → 最确定，每次输出几乎一样（适合结构化提取）
temperature = 0.3  → 比较确定，偶尔有变化（适合问答）
temperature = 0.7  → 中等随机（适合创意写作）
temperature = 1.0  → 高度随机（适合头脑风暴）
temperature = 2.0  → 极度随机（输出可能不连贯）
```

**Agent 开发建议**：
- 结构化数据提取：`0~0.2`
- 工具选择/推理：`0~0.3`
- 一般对话：`0.5~0.7`
- 创意生成：`0.7~1.0`

### 8.2 max_tokens（最大输出长度）

限制模型最多输出多少 token：

```python
payload = {
    "model": "gpt-4o",
    "messages": messages,
    "max_tokens": 1000,  # 最多输出 1000 token
}
```

**注意**：如果模型的回答被 `max_tokens` 截断，`finish_reason` 会是 `"length"` 而不是 `"stop"`。你的代码应该检查这个值。

### 8.3 top_p（核采样）

另一种控制随机性的方式。通常只调 `temperature` 或 `top_p` 之一，不要同时调两个。

```
top_p = 1.0  → 考虑所有可能（默认）
top_p = 0.1  → 只考虑概率前 10% 的选项
```

### 8.4 stop（停止词）

让模型在遇到特定字符串时停止输出：

```python
payload = {
    "messages": messages,
    "stop": ["\n\n", "---", "END"],  # 遇到这些就停
}
```

**Agent 中的用途**：ReAct 模式中，让模型在 `Observation:` 处停止，等待工具返回结果。

---

## 9. 流式输出（Streaming）

### 9.1 什么是流式输出

非流式：等模型生成完所有文字后一次性返回（用户等很久才看到回答）
流式：模型每生成一个 token 就立刻发送（像打字一样逐字出现）

### 9.2 API 参数

```python
payload = {
    "model": "gpt-4o",
    "messages": messages,
    "stream": True,  # 开启流式
}
```

### 9.3 流式响应格式（SSE）

返回的是 Server-Sent Events 格式，每行一个 JSON chunk：

```
data: {"choices": [{"delta": {"role": "assistant"}, "index": 0}]}
data: {"choices": [{"delta": {"content": "你"}, "index": 0}]}
data: {"choices": [{"delta": {"content": "好"}, "index": 0}]}
data: {"choices": [{"delta": {"content": "！"}, "index": 0}]}
data: [DONE]
```

注意区别：
- 非流式：`choices[0].message.content`（完整内容）
- 流式：`choices[0].delta.content`（增量内容，每次只有一小块）

### 9.4 代码实现

```python
import httpx
import json


async def stream_chat(messages: list[dict]):
    """流式调用 LLM，逐步产出内容"""
    url = "https://api.xairouter.com/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-xxx"}
    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                if line == "data: [DONE]":
                    break
                chunk = json.loads(line[6:])
                content = chunk["choices"][0]["delta"].get("content", "")
                if content:
                    yield content  # 每个 token 都 yield 出去


# 使用
async def main():
    full_response = ""
    async for token in stream_chat([{"role": "user", "content": "你好"}]):
        print(token, end="", flush=True)
        full_response += token
    print()  # 换行
```

### 9.5 FastAPI 中实现流式响应

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async for token in stream_chat(request.message):
            yield f"data: {json.dumps({'content': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

**这是后续 Phase 中会实现的功能**。

---

## 10. 错误处理与重试

### 10.1 LLM API 的常见错误

| HTTP 状态码 | 含义 | 处理方式 |
|-------------|------|----------|
| 400 | 请求格式错误 | 检查 messages 格式 |
| 401 | API Key 无效 | 检查 .env 配置 |
| 403 | 无权限 | 检查 Key 的模型权限 |
| 429 | 请求太频繁（Rate Limit） | 等待后重试 |
| 500 | 服务端错误 | 等待后重试 |
| 503 | 服务过载 | 等待后重试 |

### 10.2 基础重试逻辑

```python
import asyncio
import httpx


async def call_with_retry(
    messages: list[dict],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> dict:
    """带指数退避重试的 API 调用"""
    for attempt in range(max_retries):
        try:
            result = await call_chat_api(messages)
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limit：等待后重试
                delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                print(f"Rate limited, 等待 {delay}s 后重试...")
                await asyncio.sleep(delay)
            elif e.response.status_code >= 500:
                # 服务端错误：等待后重试
                delay = base_delay * (2 ** attempt)
                print(f"服务器错误 {e.response.status_code}, 等待 {delay}s 后重试...")
                await asyncio.sleep(delay)
            else:
                # 客户端错误（400, 401, 403）：直接抛出，重试没意义
                raise
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                print(f"超时，重试第 {attempt + 2} 次...")
            else:
                raise

    raise Exception(f"API 调用失败，已重试 {max_retries} 次")
```

关键点：
- **指数退避**（Exponential Backoff）：每次等待时间翻倍，避免雪崩
- **区分错误类型**：只对可恢复的错误重试（429, 5xx, 超时）
- **不对 4xx 重试**：请求格式错误重试多少次都没用

---

## 11. 成本意识

### 11.1 主流模型定价（2024-2025 参考）

| 模型 | 输入 ($/1M tokens) | 输出 ($/1M tokens) |
|------|-------------------|-------------------|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| DeepSeek V3 | ¥1.0 | ¥2.0 |

### 11.2 成本估算示例

假设你的 Agent 每次执行：
- System Prompt: 500 tokens
- 用户问题: 200 tokens
- 模型回答: 800 tokens
- 每天处理 1000 次请求

用 GPT-4o：
- 输入成本：(500+200) × 1000 / 1M × $2.50 = $1.75/天
- 输出成本：800 × 1000 / 1M × $10.00 = $8.00/天
- 总计 ≈ $9.75/天 ≈ ¥70/天

用 GPT-4o-mini：
- 总计 ≈ $0.51/天 ≈ ¥3.6/天

**实际建议**：
1. 开发阶段用便宜模型（GPT-4o-mini、DeepSeek）
2. 效果验证用强模型（GPT-4o、Claude）
3. 生产环境根据效果和成本权衡选型
4. 加 token 消耗监控和预算告警

### 11.3 省 Token 的技巧

1. **精简 System Prompt**：删除多余的话，一词不多一词不少
2. **控制 max_tokens**：根据任务设置合理的上限
3. **截断历史对话**：只保留最近 N 轮
4. **缓存常见问题**：重复的问题不需要每次都调 API
5. **分级模型策略**：简单任务用便宜模型，复杂任务才用贵模型

---

## 12. Prompt 调试技巧

### 12.1 迭代式开发

Prompt 不是一次性写好的，而是像写代码一样迭代调试：

```
版本 1 → 测试 → 发现问题 → 修改 → 版本 2 → 测试 → ...
```

### 12.2 实用调试方法

**方法 1：打印完整的 messages**

```python
import json

messages = build_messages(user_input)
print(json.dumps(messages, ensure_ascii=False, indent=2))
# 确认发给模型的内容是否正确
```

**方法 2：记录原始响应**

```python
response = await client.post(url, headers=headers, json=payload)
data = response.json()
print(json.dumps(data, ensure_ascii=False, indent=2))
# 查看模型原始返回，包括 finish_reason 和 usage
```

**方法 3：逐步简化 Prompt**

如果输出不符合预期，把 Prompt 拆成最小版本，逐步加回规则，定位是哪条规则导致的。

**方法 4：温度设为 0 后对比**

把 temperature 设为 0，确保输出稳定，方便对比修改前后的效果。

### 12.3 Prompt 版本管理

```python
# 把 Prompt 放在独立文件中管理，而不是硬编码在业务逻辑里
# app/services/prompt_service.py

EXTRACT_SYSTEM_PROMPT_V1 = """..."""
EXTRACT_SYSTEM_PROMPT_V2 = """..."""  # 改进版

# 通过配置切换版本
EXTRACT_SYSTEM_PROMPT = EXTRACT_SYSTEM_PROMPT_V2
```

你的项目已经把 Prompt 放在 `prompt_service.py` 里了，这是正确的做法。

---

## 13. 阶段自检清单

完成 Phase 1 后，请逐项确认：

### 概念理解
- [ ] 我能解释 LLM 的本质是"文本补全"
- [ ] 我能解释 Token 是什么，以及它与费用/上下文窗口的关系
- [ ] 我能解释 System / User / Assistant 三种角色的区别
- [ ] 我能解释 temperature 参数的含义和如何选择
- [ ] 我能解释 Few-shot 和 CoT 的原理和适用场景

### 实操能力
- [ ] 我能用 httpx 直接调用 OpenAI 兼容 API 并解析响应
- [ ] 我能设计一个有效的 System Prompt（有角色、规则、格式）
- [ ] 我能让 LLM 输出结构化 JSON 并用 Pydantic 验证
- [ ] 我能实现基础的重试逻辑（指数退避）
- [ ] 我能估算一个场景的 API 调用成本

### 代码能力
- [ ] 我能读懂项目中 `llm_service.py` 的每一行代码
- [ ] 我能修改 `prompt_service.py` 中的 Prompt 并测试效果
- [ ] 我能添加一个新的 Prompt 模板并通过 API 调用
- [ ] 我能解析流式响应并组装完整内容

---

## 14. 推荐资料

| 资料 | 用途 | 说明 |
|------|------|------|
| [OpenAI API 文档](https://platform.openai.com/docs/api-reference) | API 参考 | 最权威的接口文档 |
| [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) | Prompt 技巧 | 官方最佳实践 |
| [Anthropic Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) | Prompt 技巧 | Claude 的 Prompt 指南，质量极高 |
| [吴恩达 Prompt Engineering 课](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/) | 系统学习 | 免费，1.5 小时 |
| [LLM Visualization](https://bbycroft.net/llm) | 原理可视化 | 直观理解 Transformer |
| [Tiktoken Playground](https://platform.openai.com/tokenizer) | Token 计算 | 在线分词工具 |

---

## 15. 下一步

Phase 1 建立了你与 LLM 打交道的基础能力。接下来：

- **Phase 2（Function Calling / Tool Use）**：让 LLM 不仅能说，还能做——调用搜索引擎、查数据库、执行代码
- **Phase 3（RAG）**：让 LLM 基于你的私有数据回答问题，而不是只靠训练时的知识

你会发现，Prompt Engineering 不是一个阶段的事，它贯穿整个 Agent 开发过程。每加一个新能力，你都需要重新设计 Prompt。所以 Phase 1 学到的技巧会反复用到。
