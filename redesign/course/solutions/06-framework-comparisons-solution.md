# Solution 06: Framework Comparisons

这份 solution 用来校准理解。请先自己完成 Lab 06，再回来对答案。尤其是 L3：这里给的是一个**参考设计**，不是唯一正确答案——任何满足「权重受控、预测命中、分数可复算」这三条不变量的设计都算对。

所有 Python snippets 默认从 `redesign/` 运行。Part 6 的块要能 import `course.framework_comparisons`，所以路径开头那个 `.` 是**必需**的（它把 redesign 根放进 `PYTHONPATH`）：

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

也可以先确认 focused tests 是绿的：

```bash
PYTHONPATH=.:packages/research_core/src uv run pytest tests/course/test_framework_comparisons.py -q
```

期望结果：

```text
6 passed
```

数量未来可能增加，以实际测试数为准；关键是 focused comparison tests 必须全绿。

## Imports

一次把三层用到的名字都 import 好：手写基线的 task 构造器与 runner、比较 harness 的三件套（`build_recommendation_matrix` / `recommend_profile` / `default_framework_profiles`），以及 L2/L3 要自己拼考卷用的 `ComparisonTask` 和受控维度清单 `SCORE_CRITERIA`。

```python
from course.framework_comparisons import (
    ComparisonTask,
    build_echo_tool_task,
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
    run_handwritten_task,
)
from course.framework_comparisons.common import SCORE_CRITERIA

profiles = default_framework_profiles()
```

## L1 Follow Solution

先跑手写基线看它真的 driver 了 `AgentRunner`，再把两个 task 打成一张矩阵，确认同一批 profile 在不同考卷上选出了不同赢家。

```python
task = build_echo_tool_task()
summary = run_handwritten_task(task)

assert summary.event_sequence == task.expected_event_sequence
assert summary.event_sequence == (
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
)
assert summary.tool_call_count == 1
assert summary.error_count == 0
assert summary.final_answer == "The echo tool returned hello."
```

```python
tasks = [build_echo_tool_task(), build_state_resume_task()]
matrix = build_recommendation_matrix(tasks=tasks, profiles=profiles)

echo_winner = recommend_profile(matrix, task_id="echo_tool_trace")
state_winner = recommend_profile(matrix, task_id="state_resume_workflow")

assert echo_winner.profile_id == "handwritten"
assert echo_winner.total_score == 0.854
assert state_winner.profile_id == "langgraph"
assert state_winner.total_score == 0.78

# 决策记录同时写下强项和短板：strengths 是加权维度里 score >= 0.80 的科目，
# tradeoffs 是加权维度里 score < 0.55 的科目。
assert echo_winner.strengths == ("inspectability", "offline_testing", "product_boundary")
assert echo_winner.tradeoffs == ("state_resume", "multi_agent")
```

What This Proves:

- `run_handwritten_task` 不是文档想象：它真的跑了一整轮 `AgentRunner` + `FakeModel` + `ToolRuntime`，`event_sequence` 从真实 `RunEvent` 抽出，一次 `tool_call`、零 `error`。
- 同一批 profile 打成矩阵后，echo 考卷选 `handwritten`、state 考卷选 `langgraph`——赢家是相对于 task 权重的，不是永久冠军。
- 赢家记录诚实：`strengths` 和 `tradeoffs` 同时在场，一份只报喜不报忧的选型报告不可信，而这张记录写下了 handwritten 在 `state_resume` / `multi_agent` 上的短板。

Why This Design:

- 手写基线用**真实** runtime 而不是一个假 summary，是为了让「build 还是 adopt」的比较从第一步就站在可运行的证据上，而不是宣传口径上。
- `strengths >= 0.80` / `tradeoffs < 0.55` 的阈值写死在 `_score_profile_for_task` 里，所以每一份推荐都被迫暴露短板；决策记录不能只有一个总分。
- 两个 task 共用**同一批** profile，才让「赢家不同」有说服力——变的只有考卷权重，考生没换。

## L2 Modify Solution

L2 分三步：改权重让赢家翻盘、手算一个 `total_score` 证明它不是神谕、逐个打破受控的指标面。

### Step 1: Flip the winner by raising state_resume

复制 echo fixture，只把 `state_resume` 权重从 0.03 抬到 0.38，其余压低腾出权重。预测：handwritten 的 `state_resume` 只有 0.25，langgraph 却有 0.95，赢家应翻成 langgraph。

```python
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
state_heavy_winner = recommend_profile(state_matrix, task_id="state_heavy_echo")

assert state_heavy_winner.profile_id == "langgraph"
assert state_heavy_winner.total_score == 0.752
```

### Step 2: Reproduce that total_score by hand

赢的数字必须能被复算，否则这场「比较」和「看宣传册」没区别。用公式 `sum(score * weight) / sum(weights)` 手算 langgraph 在 state_heavy 考卷上的分，再和矩阵给的数字对：

```python
langgraph = next(p for p in profiles if p.id == "langgraph")
weights = state_heavy_echo.weights
by_hand = round(
    sum(langgraph.score_for(c) * weights[c] for c in weights) / sum(weights.values()),
    4,
)

assert by_hand == 0.752
assert by_hand == state_heavy_winner.total_score
```

### Step 3: Break the controlled metric surface

一场比较之所以可信，是因为**指标面是受控的**：乱七八糟的权重和维度进不来。逐个打破护栏——每个 Break 都自己 `try/except ValueError` 捕获，因为在共享 namespace 的 markdown gate 里，一个未捕获的 `raise` 会中断整份文件。先准备一个复用 echo fixture 只换 weights 的小工具：

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
```

**Break A — 权重里出现不存在的维度**。放行 `marketing_claims`，谁都能塞一科「营销声量」让钟意的框架赢。

```python
try:
    rebuild_with_weights({"marketing_claims": 1.0})
except ValueError as exc:
    assert str(exc) == "unknown weight criteria: marketing_claims"
else:
    raise AssertionError("Expected unknown weight criteria to fail")
```

**Break B — 权重是空的**。没有权重，`sum(weights.values())` 会是 0，分数无从算起。

```python
try:
    rebuild_with_weights({})
except ValueError as exc:
    assert str(exc) == "weights must not be empty"
else:
    raise AssertionError("Expected empty weights to fail")
```

**Break C — 权重非正**。0 权重意味着「假装考这科、其实不算分」，是偷偷扭曲结论。

```python
try:
    rebuild_with_weights({"inspectability": 0.0})
except ValueError as exc:
    assert str(exc) == "inspectability weight must be positive"
else:
    raise AssertionError("Expected non-positive weight to fail")
```

**Break D — 给 profile 问一个不存在的维度**。评分卡和考卷必须用同一套科目。

```python
try:
    langgraph.score_for("bogus")
except ValueError as exc:
    assert str(exc) == "unknown score criterion 'bogus'"
else:
    raise AssertionError("Expected unknown score criterion to fail")
```

**Break E — 向矩阵要一个不存在的 task**。矩阵里没评过分的 task，报错比返回一个默认赢家诚实。

```python
try:
    recommend_profile(matrix, task_id="does_not_exist")
except ValueError as exc:
    assert str(exc) == "no recommendations found for task 'does_not_exist'"
else:
    raise AssertionError("Expected missing task to fail")
```

What This Proves:

- 没换考生、只换考卷权重，赢家从 handwritten 翻成 langgraph——「哪个框架更好」永远相对于 task。
- `by_hand` 和矩阵 `total_score` 一字不差（`0.752`），证明赢的数字不是框架 README 吹的，是可复算的**归一化加权平均**。
- 五道护栏各守指标面的一道门，且都在**构造/查询时**失败：维度受控（A）、至少一科（B）、权重正数（C）、评分卡科目受控（D）、只查真实评过分的 task（E）。

Why This Design:

- 预测赢家要按**整张加权公式**想，而不是盯单科冠军：langgraph 赢是因为被抬重的 `state_resume` 强、且其它科没崩，不是因为它某一科最高。
- 手算必须除以 `sum(weights.values())`——只求 `sum(score * weight)` 得到的是没归一化的数，会和矩阵对不上；归一化让不同权重规模的考卷也能横向比。
- 护栏放在**构造/查询时**而不是「算完分数才校验」：只要指标面在源头受控，结论就不可能被事后调参；空 dict 先通过 unknown 检查（空集合没有未知项）再命中空检查，顺序也是确定的。

## L3 Design Solution

这是一个**合法的参考设计，不是唯一正确答案**。任何满足相同不变量的答案都行：`weights` 只用受控的七个 `SCORE_CRITERIA`、`multi_agent` 是最大权重、`state_resume` 次之、预测的赢家等于 `recommend_profile` 选出的赢家、且赢家分数能被手算复现。

场景：**多角色论文互评 crew**——多个 reviewer 角色分工评审，评审中途可以暂停等人工确认再继续。这次决策最看重 `multi_agent`（角色分工协作）和 `state_resume`（暂停/恢复/人工介入）两科，其余五科给较小的正权重。

**先预测再验证**。诱饵是 crewai：它的 `multi_agent` 最高（0.85），但 `state_resume` 只有 0.50，其它科普遍偏弱。langgraph 的 `multi_agent` 是 0.80（略低），但 `state_resume` 高达 0.95，且 inspectability / offline_testing 不崩。既然这场考试把第二重的权重压在 `state_resume` 上，同时强的 langgraph 会在加权平均里反超单科冠军 crewai。预测赢家：`langgraph`。

```python
l3_task = ComparisonTask(
    id="multi_role_review_crew",
    title="Multi-role paper review crew",
    system_prompt=echo.system_prompt,
    user_message=echo.user_message,
    model_responses=echo.model_responses,
    tool_name=echo.tool_name,
    tool_description=echo.tool_description,
    tool_argument_name=echo.tool_argument_name,
    required_capabilities=echo.required_capabilities,
    expected_event_sequence=echo.expected_event_sequence,
    weights={
        "multi_agent": 0.35,
        "state_resume": 0.30,
        "inspectability": 0.10,
        "offline_testing": 0.07,
        "typed_contracts": 0.06,
        "product_boundary": 0.06,
        "team_cost": 0.06,
    },
    notes="Multi-role review that most rewards multi_agent collaboration and pause/resume.",
)
l3_predicted = "langgraph"

l3_matrix = build_recommendation_matrix(tasks=[l3_task], profiles=profiles)
l3_winner = recommend_profile(l3_matrix, task_id="multi_role_review_crew")
l3_winner_profile = next(p for p in profiles if p.id == l3_winner.profile_id)

# 不变量 1：权重只用受控维度，且 multi_agent 最重、state_resume 次之
assert set(l3_task.weights) <= set(SCORE_CRITERIA)
ranked_weights = sorted(l3_task.weights.items(), key=lambda kv: -kv[1])
assert ranked_weights[0][0] == "multi_agent"
assert ranked_weights[1][0] == "state_resume"

# 不变量 2：预测命中——写下的赢家等于矩阵选出的赢家（决胜 crewai 诱饵）
assert l3_winner.profile_id == l3_predicted
crewai_score = next(
    row for row in l3_matrix if row.profile_id == "crewai"
).total_score
assert l3_winner.total_score > crewai_score

# 不变量 3：赢家分数可复算（不是神谕），手算等于矩阵值
l3_by_hand = round(
    sum(l3_winner_profile.score_for(c) * l3_task.weights[c] for c in l3_task.weights)
    / sum(l3_task.weights.values()),
    4,
)
assert l3_by_hand == l3_winner.total_score
```

What This Proves:

- 一个全新场景也能只靠现有 `course.framework_comparisons` 契约设计出来：权重全落在七个受控维度里，`multi_agent` 最重、`state_resume` 次之。
- 预测命中且**决胜诱饵**：langgraph 的 `total_score` 严格大于单科冠军 crewai——加权平均战胜了「谁 multi_agent 最高谁赢」的错觉。
- 赢家分数能被手算复现（`l3_by_hand == l3_winner.total_score`），这场自己设计的考试同样是可辩护、可复现的决策记录。

Why This Design:

- L3 不考一个固定答案，而考不变量：把第二重的权重压在 `state_resume` 上，是刻意制造一个 crewai 的 `multi_agent` 优势不足以翻盘的局面，暴露单科直觉的错误。
- 只自己设计 `weights`、其余字段复用 echo fixture，是因为评分只看 `weights × profile.score_for(c)`；`model_responses` / `expected_event_sequence` 这些不进公式。
- 用 `assert l3_winner.total_score > crewai_score` 显式钉住诱饵，而不是只断言赢家 id，是为了证明这场比较真的顶住了那个最诱人的错误答案。

## Forward Connections

- **为什么手写基线仍是产品/教学基线**：langgraph 赢的是 `state_resume` 权重被抬高的考卷（state 考卷 0.78、state_heavy_echo 0.752），而课程默认考卷更看重 `inspectability` / `offline_testing` / `product_boundary`——那正是 handwritten 的强项（echo 考卷 0.854）。当前产品的真实工作负载是「可留痕、可离线复现、边界清晰」，所以基线不换。框架赢的是**特定权重下的特定考卷**，不是产品目标。
- **为什么指标必须在代码里受控，报告才诚实**：五道护栏（L2 Break A-E）都在构造/查询时失败，所以没有人能事后往考卷里塞 `marketing_claims`、给 0 权重、或对没评过分的 task 编一个赢家。指标面一旦不在代码里锁死，一份选型报告就能被任意调参成想要的结论——`total_score` 的可复算性（L2 Step 2、L3 不变量 3）正是建立在这个受控指标面之上。
- **真要在后续 phase 引入某个框架，需要什么**：这一切的前提是 `FrameworkProfile` 只是课程里的 deterministic 记录，没把 LangGraph / CrewAI 拖进依赖树。真正采纳一个框架是后续 phase 的事，要有自己**获批的计划**、一个住在 `research_core` **之外**的 adapter（`research_core` 不能 import 第三方框架）、覆盖该 adapter 的测试、以及说明「为什么这次工作负载值得这份依赖和团队学习成本」的文档。这场比较训练的是做那个决策的判断力，不是替你提前引入依赖。

## Final Takeaway

框架比较不是从「谁最强」开始，而是从一场钉死的固定考试开始：

```text
Pin the task, fixture, and metric first; then let a reproducible weighted score pick the winner.
```

对这次 redesign，手写 runtime 仍是教学和产品基线。框架在某个 task 的 `state_resume` / `multi_agent` 权重足够高时会赢下那张考卷——但只有当真实工作负载真的变成那个形状、且额外依赖与团队成本值得时，「引入框架」才从一句宣传变成一个可辩护的决策。
