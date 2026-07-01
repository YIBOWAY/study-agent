# Lab 06: Framework Comparisons

这个 lab 让你把 Chapter 06 的「固定考试」亲手跑一遍：`ComparisonTask` 钉死同一场考试，`FrameworkProfile` 是每个候选的评分卡，`weights` 说明这次决策看重什么，`recommend_profile` 用一个**可逐项复算**的加权分数选出赢家。你要证明三件事：

1. 手写基线 `run_handwritten_task` 真的 driver 了 `AgentRunner`，跑出一条完整 event trail。
2. 赢的那个 `total_score` **不是神谕**——你能用 `sum(score * weight) / sum(weights)` 手算出同一个数。
3. 换考卷的权重，赢家就换人——「哪个框架更好」永远是相对于 task 的。

预计时间：60 到 80 分钟。全程离线、deterministic，不安装也不 import 任何第三方框架。

## Goal

| Tier | 你做什么 | 你要证明 |
| --- | --- | --- |
| L1 Follow | 跑 `run_handwritten_task(build_echo_tool_task())` 看 summary；打一张 recommendation matrix，看两个 task 的赢家 | event trail 完整、`tool_call_count`/`error_count` 对；echo→handwritten、state→langgraph |
| L2 Modify | 复制 echo task 把 `state_resume` 权重抬高，先预测再验证赢家翻盘；手算一个 `total_score`；再打破受控指标面 | 权重改了赢家变 langgraph；by-hand 分数 == 矩阵分数；五道护栏都在契约里失败 |
| L3 Design | 不给 skeleton，为一个**多角色评审场景**从零设计一个新 `ComparisonTask`，预测赢家再验证 | 权重只用受控维度、预测命中、赢家分数可复算 |

## Setup

所有命令默认从 `redesign/` 运行。Part 6 的 Python 块要能 import `course.framework_comparisons`，所以路径开头那个 `.` 是**必需**的（它把 redesign 根放进 `PYTHONPATH`）：

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

保持这个 shell 打开，后面 L1、L2 会复用变量。先确认 focused tests 是绿的：

```bash
PYTHONPATH=.:packages/research_core/src uv run pytest tests/course/test_framework_comparisons.py -q
```

## L1 Follow: Run The Baseline And Read The Matrix

目标：照着跑一遍，先不要改。你要看到两件事：手写基线真的跑出了一条 event trail；同一批 profile 打成矩阵后，两个 task 各选出了不同赢家。

### Step 1: Inspect the handwritten baseline

`run_handwritten_task` 不是文档想象，它真的 driver 了 `AgentRunner` + `FakeModel` + `ToolRuntime`，跑一整轮 model→tool→model：

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

这条 trail 证明手写基线真的跑了一整轮：一次 tool_call、零 error，最后模型解释了 echo 的观察。`echo_tool_trace` 很小，但它足够暴露一个框架最基础的工程问题——你能不能看见完整 event trail、能不能离线复现。

Self-check:

```python
assert summary.event_sequence == task.expected_event_sequence
assert summary.tool_call_count == 1
assert summary.error_count == 0
assert summary.final_answer == "The echo tool returned hello."
```

### Step 2: Build and read the recommendation matrix

把两个 task 和六个候选打成一张矩阵，再让 `recommend_profile` 选出每个 task 的赢家：

```python
from course.framework_comparisons import (
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
)

profiles = default_framework_profiles()
tasks = [build_echo_tool_task(), build_state_resume_task()]
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

两个 task 用的是**同一批** profile，却选出了不同赢家。这不是矛盾——赢家是相对于 task 权重的。再看 echo 赢家的决策记录，它同时写下强项和短板：

```python
echo_winner = recommend_profile(matrix, task_id="echo_tool_trace")
record = echo_winner.to_record()
print("profile_id:", record["profile_id"])
print("total_score:", record["total_score"])
print("strengths:", record["strengths"])
print("tradeoffs:", record["tradeoffs"])
```

Expected output:

```text
profile_id: handwritten
total_score: 0.854
strengths: ['inspectability', 'offline_testing', 'product_boundary']
tradeoffs: ['state_resume', 'multi_agent']
```

`strengths` 是加权维度里得分 `>= 0.80` 的科目，`tradeoffs` 是加权维度里得分 `< 0.55` 的科目。一个只报喜不报忧的选型报告不可信；这张记录诚实地写下了 handwritten 的短板（state/resume、multi-agent 弱）。

Self-check:

```python
assert recommend_profile(matrix, task_id="echo_tool_trace").profile_id == "handwritten"
assert recommend_profile(matrix, task_id="state_resume_workflow").profile_id == "langgraph"
```

### Exercise Feedback - L1 Follow

**Common Errors**:

1. `ModuleNotFoundError: No module named 'course'` - 你可能漏了路径开头那个 `.`。Part 6 必须用 `PYTHONPATH=.:packages/research_core/src`，`.` 让 `course.framework_comparisons` 能被 import。
2. `ModuleNotFoundError: No module named 'research_core'` - 你可能没有从 `redesign/` 运行，或漏了 `packages/research_core/src`。
3. 以为 `run_handwritten_task` 返回一个假 summary - 它真的跑了 `AgentRunner`；`event_sequence` 是从真实 `RunEvent` 抽出来的，不是硬编码。

**Failure Output Interpretation**: 如果 `tool_call_count` 不是 1，说明模型没走 tool（检查 fixture 的 `model_responses`）；如果 `error_count` > 0，说明 event trail 里出现了 `error` 事件，去看完整 `summary.to_record()`。如果两个赢家不对，先分别打印每个 task 的完整排名（见 L2 的 `ranked`）逐行对。

**Where To Go Back**: 回到 Chapter 06 的 Section 1「一场固定考试的四个角色」表，和 Section 2「跑基线，再打一张评分矩阵」，确认 `ComparisonTask` / `FrameworkProfile` / `weights` / `FrameworkRecommendation` 各演什么角色。

**Why Correct Answer Is Correct**: L1 证明了最小契约：手写基线真的可运行、可留痕，矩阵把「同一批 task × 同一批 profile」打成一张可复算的评分表。赢家是相对于 task 权重的——这就是后面两层要亲手拆开的东西。

## L2 Modify: Flip The Winner, Then Reproduce The Score, Then Break The Metric

目标：先预测，再验证。L2 分三步——先改权重看赢家翻盘，再手算一个 `total_score` 证明它不是神谕，最后逐个打破受控的指标面。每个 Break 都要先回答一个诊断问题：这道护栏在守什么？

### Step 1: Raise the state_resume weight (predict-then-verify)

复制 echo fixture，只把 `state_resume` 权重从 0.03 抬到 0.38，其余维度相应压低以腾出权重（`multi_agent` 仍保持 0.02）。先**预测**：echo task 原本是 handwritten 赢，现在把最看重的维度换成 state/resume，谁会翻盘？用加权公式想一想——handwritten 的 state_resume 只有 0.25，langgraph 却有 0.95。

```python
from course.framework_comparisons import ComparisonTask

echo = build_echo_tool_task()
state_heavy_echo = ComparisonTask(
    id="state_heavy_echo",
    title="State-heavy echo",
    system_prompt=echo.system_prompt,
    user_message=echo.user_message,
    model_responses=echo.model_responses,
    tool_name=echo.tool_name,
    tool_description=echo.tool_description,
    tool_argument_name=echo.tool_argument_name,
    required_capabilities=echo.required_capabilities,
    expected_event_sequence=echo.expected_event_sequence,
    weights={
        "inspectability": 0.20,
        "offline_testing": 0.15,
        "typed_contracts": 0.10,
        "product_boundary": 0.10,
        "team_cost": 0.05,
        "state_resume": 0.38,
        "multi_agent": 0.02,
    },
)

state_matrix = build_recommendation_matrix(tasks=[state_heavy_echo], profiles=profiles)
ranked = sorted(
    (row for row in state_matrix if row.task_id == "state_heavy_echo"),
    key=lambda row: (-row.total_score, row.profile_id),
)
for row in ranked:
    print(row.profile_id, row.total_score)
```

Expected output:

```text
langgraph 0.752
pydantic-ai 0.6375
handwritten 0.634
openai-agents-sdk 0.627
llamaindex-workflows 0.608
crewai 0.4895
```

验证了预测：**没有换考生，只换了考卷的权重**，赢家从 handwritten 翻成 langgraph。handwritten 从 0.854 掉到 0.634，因为这次把权重压在了 `state_resume` 上（从 echo 考卷的 0.03 提到 0.38），而 handwritten 在 `state_resume` 上恰恰最弱（0.25）；langgraph 的 `state_resume` 是 0.95，所以反超。这条排序也正是 `recommend_profile` 内部的确定性 tie-break：`sorted(matches, key=lambda i: (-i.total_score, i.profile_id))[0]`。

Self-check:

```python
assert recommend_profile(state_matrix, task_id="state_heavy_echo").profile_id == "langgraph"
```

### Step 2: Reproduce one total_score by hand

赢的数字必须能被复算，否则这场「比较」和「看宣传册」没区别。用公式 `sum(profile.score_for(c) * weights[c]) / sum(weights.values())` 手算 langgraph 在 state_heavy task 上的 `total_score`，再和矩阵给的数字对：

```python
langgraph = next(p for p in profiles if p.id == "langgraph")
weights = state_heavy_echo.weights
by_hand = round(
    sum(langgraph.score_for(c) * weights[c] for c in weights) / sum(weights.values()),
    4,
)
winner = recommend_profile(state_matrix, task_id="state_heavy_echo")
print("by_hand:", by_hand)
print("matrix:", winner.total_score)
print("matches:", by_hand == winner.total_score)
```

Expected output:

```text
by_hand: 0.752
matrix: 0.752
matches: True
```

`by_hand` 和矩阵一字不差。这就是整章的支点：赢的数字不是框架 README 吹出来的，是你自己能复算出来的。

Self-check:

```python
assert by_hand == winner.total_score
```

### Step 3: Break the controlled metric surface

一场比较之所以可信，是因为**指标面是受控的**：乱七八糟的权重和维度进不来。逐个打破护栏——每个 Break 块都自己 `try/except` 捕获，读报错、诊断、再说怎么修。先准备一个复用 echo fixture 只换 weights 的小工具：

```python
def rebuild_with_weights(weights):
    return ComparisonTask(
        id="broken_task",
        title="Broken task",
        system_prompt=echo.system_prompt,
        user_message=echo.user_message,
        model_responses=echo.model_responses,
        tool_name=echo.tool_name,
        tool_description=echo.tool_description,
        tool_argument_name=echo.tool_argument_name,
        required_capabilities=echo.required_capabilities,
        expected_event_sequence=echo.expected_event_sequence,
        weights=weights,
    )


print("helper ready")
```

Expected output:

```text
helper ready
```

**Break A — 权重里出现不存在的维度**。诊断问题：如果放行 `marketing_claims`，谁都能往考卷里塞一科「营销声量」让自己钟意的框架赢，会坏掉什么？

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

Fix: 权重只能用受控的七个 `SCORE_CRITERIA`。

**Break B — 权重是空的**。诊断问题：没有权重，`sum(weights.values())` 会是 0，分数从哪来？

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

Fix: 至少给一个受权重的维度。

**Break C — 权重非正**。诊断问题：0 权重意味着「假装考这科、其实不算分」，这算不算偷偷扭曲结论？

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

Fix: 每个维度的权重必须是正数。

**Break D — 给 profile 问一个不存在的维度**。诊断问题：评分卡和考卷如果用了不同科目，比较还成立吗？

```python
try:
    langgraph.score_for("bogus")
except ValueError as exc:
    print(exc)
```

Expected output:

```text
unknown score criterion 'bogus'
```

Fix: 只查 `SCORE_CRITERIA` 里的维度。

**Break E — 向矩阵要一个不存在的 task**。诊断问题：矩阵里没有这个 task 的任何评分，返回一个默认赢家和直接报错，哪个更诚实？

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

Fix: 只对 `build_recommendation_matrix` 里真实评过分的 task 调 `recommend_profile`。

### Exercise Feedback - L2 Modify

**Common Errors**:

1. 预测赢家时只看「谁的 state_resume 最高」，忘了它是**加权平均**——赢家取决于所有加权维度的综合，不是单科冠军。langgraph 赢是因为它在被抬重的那科强，且其它科没有崩。
2. 手算 `total_score` 时忘了除以 `sum(weights.values())` - 只求 `sum(score * weight)` 得到的是没归一化的数，和矩阵对不上。
3. 把 Break 块写成不捕获异常的裸调用 - 在共享 namespace 的 markdown gate 里，一个未捕获的 `raise` 会中断**整份文件**；每个 Break 必须 `try/except ValueError`。
4. 以为 `weights must not be empty` 会在 `unknown weight criteria` 之前触发 - 空 dict 先通过 unknown 检查（空集合没有未知项），再命中空检查。

**Failure Output Interpretation**: 五条报错各守一层——`unknown weight criteria`（维度受控）、`weights must not be empty`（至少一科）、`... weight must be positive`（权重正数）、`unknown score criterion`（评分卡科目受控）、`no recommendations found for task`（只查真实评过分的 task）。看到某条报错，先问它在守指标面的哪一道门。

**Where To Go Back**: 回到 Chapter 06 的 Section 3「亲手复算那个赢的数字」和 Section 5「打破受控的指标面」，逐条对照本 lab 的五个 Break，以及 [DEEP]「为什么这五道护栏是一体的」——它们都在构造/查询时就失败，指标面一旦不受控，结论就能被任意调参。

**Why Correct Answer Is Correct**: L2 证明你能做三件事：让赢家因权重翻盘并解释原因、把 `total_score` 从「神谕」还原成可复算的加权平均、把五道护栏当成守指标面的门。只要指标面受控且分数可复算，这场比较才是决策记录，不是宣传册。

## L3 Design: Design A New Comparison Task From Scratch

目标：不给 skeleton，你自己为一个**全新场景**设计一个 `ComparisonTask`，先预测赢家再验证。

场景（换一个和前面不同的题目）：**多角色论文互评 crew**。你要评估一个「多个 reviewer 角色分工评审、评审中途可以暂停等人工确认再继续」的工作负载。这次决策最看重两科：`multi_agent`（角色分工协作）和 `state_resume`（暂停/恢复/人工介入）。其余五科给较小的正权重。

你要做的：

- 设计一个新的 `ComparisonTask`（自己的 `id` / `title` / `weights`）。可以复用 echo 的 `system_prompt` / `user_message` / `model_responses` / `tool_*` / `required_capabilities` / `expected_event_sequence`（这些不影响评分，评分只看 `weights` × `profile`），**只自己设计 `weights`**。
- `weights` 只能用受控的七个 `SCORE_CRITERIA`，且让 `multi_agent` 是最大权重、`state_resume` 次之。
- **先预测**哪个 profile 会赢：想一想哪个候选在 `multi_agent` 和 `state_resume` 上同时强、且其它科不崩（提示：langgraph 在这两科分别是 0.80 / 0.95，是同时强的候选；crewai 的 `multi_agent` 更高但其它科普遍偏弱）。把你的预测写下来。
- 用 `build_recommendation_matrix` + `recommend_profile` 验证，并断言矩阵选出的赢家 == 你的预测。

约束：**只能用现有的 `course.framework_comparisons` 契约**，不能新增维度、profile、字段或函数；`weights` 只用七个受控维度。

下面是最低自查模板——注意：这段引用你自己发明的 L3 变量（`l3_task` / `l3_matrix` / `l3_winner` / `l3_predicted` / `l3_winner_profile`），所以它是**设计验收模板，不是直接粘贴运行的完整示例**；可运行参考答案在 solution 里。

```text
# 假设：l3_task 是你为多角色评审场景设计的 ComparisonTask，
# l3_predicted 是你在跑之前写下的赢家预测（一个 profile_id 字符串），
# l3_matrix = build_recommendation_matrix(tasks=[l3_task], profiles=profiles)，
# l3_winner = recommend_profile(l3_matrix, task_id=l3_task.id)，
# l3_winner_profile = next(p for p in profiles if p.id == l3_winner.profile_id)。

# 1. 权重只用受控的七个维度，且 multi_agent 是最重的一项
assert set(l3_task.weights) <= set(SCORE_CRITERIA)
assert l3_task.weights["multi_agent"] == max(l3_task.weights.values())

# 2. 预测命中：你写下的赢家等于矩阵选出的赢家
assert l3_winner.profile_id == l3_predicted

# 3. 赢家的分数可复算（不是神谕），手算等于矩阵值
by_hand = round(
    sum(
        l3_winner_profile.score_for(c) * l3_task.weights[c]
        for c in l3_task.weights
    )
    / sum(l3_task.weights.values()),
    4,
)
assert by_hand == l3_winner.total_score
```

### Exercise Feedback - L3 Design

**Common Errors**:

1. 在 `weights` 里塞一个不在 `SCORE_CRITERIA` 里的维度 - 触发 `unknown weight criteria: ...`；只能用七个受控维度。
2. 预测时只盯 `multi_agent` 单科冠军（crewai）就认定它赢 - 但赢家是加权平均，crewai 其它科普遍偏弱，被 langgraph 反超；预测要按整张加权公式想。
3. 忘了 `expected_event_sequence` / `model_responses` 等字段不影响评分 - 评分只看 `weights` × `profile.score_for(c)`；你唯一要设计的是 `weights`。
4. 以为 L3 有唯一正确答案 - 它考的是不变量：权重受控、预测命中、分数可复算。任何满足这三条的设计都对。

**Failure Output Interpretation**: 如果第 2 条断言失败（预测没命中），说明你对加权平均的直觉需要修正——把每个候选的 `total_score` 全打印出来（像 L2 的 `ranked`），看它是被哪一科拉开的。如果第 1 条断言失败，检查你有没有拼错维度名或多塞了一科。

**Where To Go Back**: 回到 Chapter 06 的 Section 4「任务相对的赢家与确定性 tie-break」，那里演示了同一批 profile 在 echo / state 两张考卷上如何选出不同赢家；把它当模板，换成你的多角色评审考卷。

**Why Correct Answer Is Correct**: L3 不考一个固定答案，而考不变量：权重只用受控维度、赢家预测能命中、`total_score` 能被手算复现。只要这三条成立，你设计的这场考试就是一份可辩护、可复现的选型决策记录。

## Reflection

做完 lab 后，用自己的话回答：

1. 为什么同一批 profile，echo task 是 handwritten 赢、state_heavy task 是 langgraph 赢？换赢家的到底是什么？
2. 手算的 `by_hand` 和矩阵的 `total_score` 一字不差，这件事为什么比「分数是多少」更重要？
3. L2 的五道护栏都在构造/查询时失败。如果它们改成「算完分数后才校验」，一场比较会怎样被人调参成想要的结论？
4. 为什么 `FrameworkProfile` 是课程里的 deterministic 记录，而不是真实框架的 wrapper？把 LangGraph / CrewAI 拖进依赖树来做这场比较会有什么代价？
5. 即使 langgraph 赢了 state/resume task，课程为什么仍把手写 runtime 当产品基线？真实工作负载要变成什么样，「引入框架」才是对的决策？
