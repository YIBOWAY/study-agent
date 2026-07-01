# Part 6: Framework Comparisons — 用一场固定考试为「build 还是 adopt」辩护

> 接 Part 5。你已经把本地论文研究助手做成了一个能打开、能核对出处的工作台。Part 6 换一个更政治、更现实的问题：当有人问「你为什么不直接用 LangChain / CrewAI，非要手写？」，你不能靠感觉回答——你要靠一场固定 task、固定 fixture、固定 metric 的可复现比较，把「继续手写」还是「引入框架」变成一个可审计的技术选型决策。

预计时间：70 到 95 分钟。

## Learner Contract

- **Who this is for**: Beginner Track 和 Engineer Track 都适合。你需要认得 Part 1 的 `AgentRunner`/event trail、Part 2 的 evidence chain，以及「同一批 fixture 才能对比」这个直觉。
- **Before you start**: 先完成 Part 1 的 Agent Kernel、Part 4 的 Delegation、Part 5 的 Workbench Product。
- **You will build**: 一个完全离线的比较 harness：用 `run_handwritten_task` 跑出真实的手写基线，用 `build_recommendation_matrix` 把「同一批 task × 同一批 profile」打成一张评分矩阵，再用 `recommend_profile` 选出每个 task 的赢家。
- **You will be able to explain**: 为什么「每个框架各跑各的 demo」是宣传册不是比较；`ComparisonTask`/`FrameworkProfile`/weights/`FrameworkRecommendation` 各自扮演什么角色；`total_score` 是怎么一分一分算出来的（不是神谕）；为什么同一批 profile 在不同 task 上会选出不同赢家；tie-break 为什么是确定性的。
- **You will prove it works by running**: `PYTHONPATH=.:packages/research_core/src uv run pytest tests/course/test_framework_comparisons.py -q`。
- **Offline guarantee**: 全程 deterministic 本地对象；不安装、不 import 任何第三方框架（PydanticAI / LangGraph / LlamaIndex / OpenAI Agents SDK / CrewAI）。候选框架只是课程里的 deterministic 评分记录。

## 你的本地论文研究助手现在被质疑了：为什么不直接用框架

前五个 Part 之后，助手能跑、能留痕、能核对出处。但在一次架构评审里，同事丢来一句：

> "这些 loop、evidence chain、delegation，LangChain 和 CrewAI 早就封装好了。你为什么要手写？是不是在重复造轮子？"

这是一个真实的技术选型问题，而回答它最容易踩的坑是：**让每个框架各跑一个它最擅长的 demo**。LangGraph 演示一个漂亮的 checkpoint/resume 图，CrewAI 演示一段热闹的多角色对话，手写基线演示一个干净的 event trail——每个都赢了自己的主场。

那不叫比较，叫**看宣传册**。三个 demo 用了三个不同的任务、三套不同的 fixture、三套不同的评价口径，结论完全无法叠加。

Part 6 的解法是把选型变成一场**固定考试**：钉死同一个 task、同一套 fake fixture、同一套带权重的 metric，然后让一个透明的加权分数决定赢家。谁赢不重要，重要的是赢的那个数**能被逐项复算**，评审时你摊开的是一张决策记录，而不是一句「我觉得手写更好」。

> [BIG] **大局观**：Part 1-5 教 runtime 怎么把事做对并留痕；Part 6 教你怎么**为一个技术选型决策辩护**。这一章不产出新 runtime 功能，它产出的是一个可复现的判断流程——把「build vs adopt」从口水战变成有证据的记录。

```text
Local Paper Research Assistant
  [x] Part 1: Agent Kernel, event trail
  [x] Part 2: Research Core, evidence chain
  [x] Part 3: Memory and Skills
  [x] Part 4: Delegation
  [x] Part 5: Workbench Product
  [*] Part 6: Framework Comparisons
      [*] ComparisonTask 钉死同一场考试（task + fixture + weights）
      [*] FrameworkProfile 是每个候选的评分卡（课程记录，不是 wrapper）
      [*] total_score 是透明加权平均，可逐项复算
      [*] 同一批 profile，不同 task 会选出不同赢家
  [ ] Part 7: Production readiness
```

## Section 1 [LIGHT Concept]: 一场固定考试的四个角色

把框架比较想成一次 **build-vs-adopt 技术选型**。你不是在问「哪个框架最强」，而是在问「对**这次决策看重的东西**，哪个候选得分最高」。四个对象各演一个角色：

| Object | Plain-language role | What to inspect |
| --- | --- | --- |
| `ComparisonTask` | 统一考卷：钉死同一个 task、同一套 fake fixture、同一套 weights | `task.weights` |
| `FrameworkProfile` | 评分卡：一个候选在各维度上的 deterministic 分数（课程记录，不是第三方 wrapper） | `profile.score_for(c)` |
| `weights` | 这次决策更看重什么：每个维度的权重 | `task.weights[c]` |
| `FrameworkRecommendation` | 可追溯的决策记录：`total_score` + `strengths` + `tradeoffs` | `winner.to_record()` |
| `run_handwritten_task` | 真实手写基线：用真的 `AgentRunner` + `FakeModel` + `ToolRuntime` 跑一遍 | `summary.event_sequence` |

七个评价维度 `SCORE_CRITERIA` 是这场考试的全部科目：`inspectability`、`offline_testing`、`typed_contracts`、`state_resume`、`multi_agent`、`product_boundary`、`team_cost`。六个候选 `default_framework_profiles` 是全部考生：`handwritten`、`pydantic-ai`、`llamaindex-workflows`、`langgraph`、`openai-agents-sdk`、`crewai`。

> [DD] **设计决策**：`FrameworkProfile` 不是第三方框架的 wrapper，而是课程里的 deterministic 记录。这样才能在**不把 LangGraph / CrewAI 拖进依赖树**的前提下先训练判断力。真要引入某个框架，是后续 phase 的事，要有自己的计划、adapter、测试和文档——而且 adapter 绝不能住进 `research_core`。

### 比较 harness 的数据流

```text
ComparisonTask (+weights)        FrameworkProfile
        |                              |
        +--------------+---------------+
                       v
              _score_profile_for_task
       total = round( sum(score * weight) / sum(weights), 4 )
       strengths = 加权维度里 score >= 0.80 的
       tradeoffs = 加权维度里 score <  0.55 的
                       v
              FrameworkRecommendation
              (total_score + strengths + tradeoffs)
                       v
        recommend_profile(matrix, task_id) -> winner
        tie-break: sorted by (-total_score, profile_id)
```

### total_score 是怎么一分一分算出来的

```text
对每个「出现在 weights 里」的维度 c:
    contribution(c) = profile.score_for(c) * weights[c]

total_score = round( sum(contribution) / sum(weights.values()), 4 )

strengths  = 这些维度里 profile.score_for(c) >= 0.80   （候选在这科很强）
tradeoffs  = 这些维度里 profile.score_for(c) <  0.55   （候选在这科偏弱）
```

> [CHECK] **检查一下**：分数**不是**神谕。它是「每科得分 × 该科权重」求和，再除以权重总和。所以「谁赢」永远能被摊开逐项复算——这正是 Section 3 要亲手做的事。

## Section 2 [FULL Build]: 跑基线，再打一张评分矩阵

这一章所有 Python snippet 都从 `redesign/` 运行，路径开头那个 `.` 是必需的（它把 redesign 根放进 path，`course.framework_comparisons` 才能 import）：

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

### Build: 真实的手写基线

先跑手写基线。它不是一段文档想象，而是真的 driver 了 `AgentRunner`、`FakeModel`、`ToolRuntime`：

```python
from course.framework_comparisons import build_echo_tool_task, run_handwritten_task

task = build_echo_tool_task()
summary = run_handwritten_task(task)

print("event_sequence:", ", ".join(summary.event_sequence))
print("tool_call_count:", summary.tool_call_count)
print("error_count:", summary.error_count)
print("final_answer:", summary.final_answer)
```

Expected output:

```text
event_sequence: model_request, model_response, tool_call, tool_result, model_request, model_response
tool_call_count: 1
error_count: 0
final_answer: The echo tool returned hello.
```

这条 event trail 证明手写基线真的跑了一整轮 model→tool→model：`echo_tool_trace` 很小，但它足够暴露一个框架最基础的工程问题——你能不能看见完整 event trail，能不能离线复现，能不能稳定 debug。

### Build: 同一批 task × 同一批 profile 打成矩阵

现在把两个 task 和六个候选打成一张评分矩阵，再让 `recommend_profile` 选出每个 task 的赢家：

```python
from course.framework_comparisons import (
    build_state_resume_task,
    build_recommendation_matrix,
    default_framework_profiles,
    recommend_profile,
)

tasks = [build_echo_tool_task(), build_state_resume_task()]
profiles = default_framework_profiles()
matrix = build_recommendation_matrix(tasks=tasks, profiles=profiles)

for item in tasks:
    winner = recommend_profile(matrix, task_id=item.id)
    print(item.id, "->", winner.profile_id, winner.total_score)
```

Expected output:

```text
echo_tool_trace -> handwritten 0.854
state_resume_workflow -> langgraph 0.78
```

两个 task 用的是**同一批** profile，却选出了不同赢家。这不是矛盾，正是 Part 6 的核心：赢家是**相对于 task 权重**的。下一节我们不接受这两个数字，我们要把它们算出来。

### 这场考试的全部科目和考生

```python
from course.framework_comparisons.common import SCORE_CRITERIA

print("criteria:", list(SCORE_CRITERIA))
print("profiles:", [profile.id for profile in profiles])
```

Expected output:

```text
criteria: ['inspectability', 'offline_testing', 'typed_contracts', 'state_resume', 'multi_agent', 'product_boundary', 'team_cost']
profiles: ['handwritten', 'pydantic-ai', 'llamaindex-workflows', 'langgraph', 'openai-agents-sdk', 'crewai']
```

## Section 3 [FULL Inspect]: 亲手复算那个赢的数字

v1 的老章节印出 `score 0.854` 就走了，读者只能当它是神谕。这一节我们把它**逐项复算**，证明它是一个可辩护的加权平均。

### Inspect: 手算 handwritten 在 echo task 上的 total_score

`echo_tool_trace` 的权重最看重 `inspectability`（0.30）和 `offline_testing`（0.25），而 handwritten 在这两科都是 0.95。按公式 `sum(score * weight) / sum(weights)` 手算一遍，再和矩阵里的 `total_score` 对比：

```python
profile = next(p for p in profiles if p.id == "handwritten")
weights = task.weights
weight_total = sum(weights.values())

by_hand = round(
    sum(profile.score_for(c) * weights[c] for c in weights) / weight_total,
    4,
)
winner = recommend_profile(matrix, task_id="echo_tool_trace")

print("weight_total:", weight_total)
print("by_hand total_score:", by_hand)
print("matrix total_score:", winner.total_score)
print("matches:", by_hand == winner.total_score)
```

Expected output:

```text
weight_total: 1.0
by_hand total_score: 0.854
matrix total_score: 0.854
matches: True
```

`by_hand` 和矩阵给的分数一字不差。这就是整章的支点：**赢的数字不是框架 README 吹出来的，是你自己能复算出来的**。

> [DEEP] **为什么这重要**：如果分数是一个不可复算的黑箱，那这场「比较」和「看宣传册」没有本质区别——你只是换了个更权威的口气念别人的营销。让 `total_score` 透明可复算，才把选型从「谁嗓门大」变成「谁证据硬」。

### Inspect: strengths 和 tradeoffs 是怎么挑出来的

`strengths` 是加权维度里得分 `>= 0.80` 的科目，`tradeoffs` 是加权维度里得分 `< 0.55` 的科目。手挑一遍，再和 recommendation 记录对齐：

```python
strengths = tuple(
    c for c in SCORE_CRITERIA if c in weights and profile.score_for(c) >= 0.8
)
tradeoffs = tuple(
    c for c in SCORE_CRITERIA if c in weights and profile.score_for(c) < 0.55
)

print("by_hand strengths:", strengths)
print("by_hand tradeoffs:", tradeoffs)
print("record strengths:", winner.strengths)
print("record tradeoffs:", winner.tradeoffs)
```

Expected output:

```text
by_hand strengths: ('inspectability', 'offline_testing', 'product_boundary')
by_hand tradeoffs: ('state_resume', 'multi_agent')
record strengths: ('inspectability', 'offline_testing', 'product_boundary')
record tradeoffs: ('state_resume', 'multi_agent')
```

这张决策记录很诚实：它同时写下 handwritten 的强项（可检查、可离线测、产品边界干净）**和**它的短板（state/resume、multi-agent 弱）。一个只报喜不报忧的选型报告是不可信的。

> [TRAP] **常见误解**：不要以为 `strengths` 就是「分数最高的几科」。它有两个条件：得分 `>= 0.80` **且**这一科在 `weights` 里（也就是这次决策真的看重它）。一个在无关维度上很强的候选，不会因此得到 strengths——因为这场考试根本不考那一科。

## Section 4 [FULL Compare]: 任务相对的赢家与确定性 tie-break

### 为什么 echo task 是 handwritten 赢，state task 是 langgraph 赢

把 echo task 的完整排名摊开，看名次是怎么拉开的：

```python
echo_matches = [row for row in matrix if row.task_id == "echo_tool_trace"]
ranked = sorted(echo_matches, key=lambda row: (-row.total_score, row.profile_id))
for row in ranked:
    print(row.profile_id, row.total_score)
```

Expected output:

```text
handwritten 0.854
pydantic-ai 0.745
langgraph 0.6345
llamaindex-workflows 0.613
openai-agents-sdk 0.6095
crewai 0.4795
```

这个排序正是 `recommend_profile` 内部的 tie-break：`sorted(matches, key=lambda i: (-i.total_score, i.profile_id))[0]`。先按 `total_score` 从高到低，分数相同再按 `profile_id` 字典序——所以选择是**确定性**的，同样的输入永远选出同一个赢家，不会因为字典顺序或运行时机而漂。

再看 state/resume task 为什么翻盘。它把 `state_resume` 的权重抬到 0.45（echo task 只给 0.03），而 langgraph 在这一科是 0.95：

```python
state_task = build_state_resume_task()
langgraph = next(p for p in profiles if p.id == "langgraph")
state_weights = state_task.weights

state_by_hand = round(
    sum(langgraph.score_for(c) * state_weights[c] for c in state_weights)
    / sum(state_weights.values()),
    4,
)
print("state_resume weight:", state_weights["state_resume"])
print("langgraph state_resume score:", langgraph.score_for("state_resume"))
print("langgraph total on state task:", state_by_hand)
```

Expected output:

```text
state_resume weight: 0.45
langgraph state_resume score: 0.95
langgraph total on state task: 0.78
```

同一个 langgraph profile，在 echo task 上只排第三（0.6345），在 state task 上却夺冠（0.78）。**没有换考生，只换了考卷的权重**——这就是「任务相对的赢家」：脱离具体任务谈「哪个框架更好」是没有意义的。

> [CHECK] **检查一下**：小而重 event-trail 的任务奖励 inspectability / offline_testing，手写基线赢；重 checkpoint/resume/human-in-the-loop 的任务奖励 state_resume，LangGraph 值得学习。选型的答案永远是「取决于这次的工作负载看重什么」。

## Section 5 [BREAK/FIX]: 打破受控的指标面

一场比较之所以可信，是因为**指标面是受控的**：乱七八糟的权重和维度进不来。下面逐个打破 `course.framework_comparisons` 的护栏——每个 Break 块都自己 `try/except` 捕获，读报错、诊断、再说怎么修。

先准备一个复用 echo fixture 只换 weights 的小工具：

```python
from course.framework_comparisons import ComparisonTask

base = build_echo_tool_task()


def rebuild_with_weights(weights):
    return ComparisonTask(
        id="broken_task",
        title="Broken task",
        system_prompt=base.system_prompt,
        user_message=base.user_message,
        model_responses=base.model_responses,
        tool_name=base.tool_name,
        tool_description=base.tool_description,
        tool_argument_name=base.tool_argument_name,
        required_capabilities=base.required_capabilities,
        expected_event_sequence=base.expected_event_sequence,
        weights=weights,
    )


print("helper ready")
```

Expected output:

```text
helper ready
```

### Break 1: 权重里出现了不存在的维度

```python
try:
    rebuild_with_weights({"marketing_claims": 1.0})
except ValueError as exc:
    print(exc)
```

Expected output:

```text
unknown weight criteria: marketing_claims
```

Diagnosis: `marketing_claims` 不在七个 `SCORE_CRITERIA` 里。如果放行，任何人都能往考卷里塞一科「营销声量」，然后让自己钟意的框架赢。Fix: 权重只能用受控的七个维度。

### Break 2: 权重是空的

```python
try:
    rebuild_with_weights({})
except ValueError as exc:
    print(exc)
```

Expected output:

```text
weights must not be empty
```

Diagnosis: 没有权重就没有「这次看重什么」，`sum(weights.values())` 会是 0，分数无从算起。Fix: 至少给一个受权重的维度。

### Break 3: 权重非正

```python
try:
    rebuild_with_weights({"inspectability": 0.0})
except ValueError as exc:
    print(exc)
```

Expected output:

```text
inspectability weight must be positive
```

Diagnosis: 0 或负权重意味着「假装考这科、其实不算分」，是一种偷偷扭曲结论的方式。Fix: 每个维度的权重必须是正数。

### Break 4: 给 profile 问一个不存在的维度

```python
try:
    profile.score_for("bogus")
except ValueError as exc:
    print(exc)
```

Expected output:

```text
unknown score criterion 'bogus'
```

Diagnosis: `score_for` 只认七个维度。这道护栏保证评分卡和考卷用的是**同一套科目**，不会各说各话。Fix: 只查 `SCORE_CRITERIA` 里的维度。

### Break 5: 向矩阵要一个不存在的 task

```python
try:
    recommend_profile(matrix, task_id="does_not_exist")
except ValueError as exc:
    print(exc)
```

Expected output:

```text
no recommendations found for task 'does_not_exist'
```

Diagnosis: 矩阵里根本没有这个 task 的任何评分，与其返回一个默认赢家骗你，不如直接报错。Fix: 只对 `build_recommendation_matrix` 里真实评过分的 task 调 `recommend_profile`。

> [DEEP] **为什么这五道护栏是一体的**：它们都在**构造/查询时**就失败，而不是在算完分数后才发现结论漂了。指标面一旦不受控，比较结论就可以被任意「调参」成想要的答案——那就退回了宣传册。把校验钉死在契约里，才让「同一场考试」这句话有牙齿。

## Section 6 [FULL Boundary]: 产品边界与 Eval Gate

Part 6 的所有比较代码都住在 `course/framework_comparisons/`，它只向下依赖 `research_core` 的 runtime 契约，绝不反向污染产品层：

```text
允许：
  course/framework_comparisons -> research_core runtime contracts
  course 报告            -> framework recommendation matrix

禁止：
  research_core -> LangGraph / PydanticAI / CrewAI
  apps/api      -> 某个框架的 shortcut
  apps/web      -> framework-specific runtime object
```

> [DD] **设计决策**：比较代码留在课程目录、候选是 deterministic 记录，意味着你可以随时重跑这场考试而不引入任何网络、API key 或第三方依赖。等 Part 7 真要评估「引入某框架」时，那会是一个独立的、有 approved plan 的 phase：adapter 住在 `research_core` 之外，配自己的测试和文档，绝不是在 core 里偷偷 import 一个 SDK。

### Eval Gate

从 `redesign/` 运行：

```bash
PYTHONPATH=.:packages/research_core/src uv run pytest tests/course/test_framework_comparisons.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
PYTHONPATH=.:packages/research_core/src uv run ruff check course/framework_comparisons tests/course/test_framework_comparisons.py
```

核心自查（沿用本章同一个 Python session 的 `task` / `summary` / `matrix` / `by_hand` 等变量；若另开 shell，先把 Section 2、Section 3 重新跑一遍）：

```python
assert summary.event_sequence == task.expected_event_sequence
assert recommend_profile(matrix, task_id="echo_tool_trace").profile_id == "handwritten"
assert recommend_profile(matrix, task_id="state_resume_workflow").profile_id == "langgraph"
assert by_hand == recommend_profile(matrix, task_id="echo_tool_trace").total_score
print("eval gate self-check passed")
```

Expected output:

```text
eval gate self-check passed
```

## Reflection

继续 Part 7 前，用自己的话回答：

1. 为什么「每个框架各跑一个它最擅长的 demo」是宣传册而不是比较？固定 task / fixture / metric 各自堵住了哪种作弊？
2. handwritten 在 echo task 上的 `total_score` 是 0.854。不看代码，你能只用它的七科得分和权重把这个数字复算出来吗？
3. 同一批 profile，为什么 echo task 选 handwritten、state task 选 langgraph？`state_resume` 权重从 0.03 变到 0.45 意味着什么？
4. `recommend_profile` 的 tie-break 是 `(-total_score, profile_id)`。如果去掉 `profile_id` 这一项，会坏掉什么？
5. **Tradeoff**：LangGraph 在 state/resume 任务上赢了，课程为什么仍然把手写 runtime 当作产品/教学基线？真实工作负载要发生什么变化，「引入框架」才会从加分项变成正确决策——而那时 adapter 又该住在三层的哪一层？
