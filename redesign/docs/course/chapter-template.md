# Part N: [能力名称]

Use this as the reusable authoring template for a course Part. Replace every bracketed placeholder before publishing. Keep the Part narrative fully offline: static paper fixtures, deterministic fake models/retrievers, and no API keys.

## Learner Contract

- **Who this is for**: [Beginner Track / Engineer Track / both, and what kind of learner will benefit]
- **Before you start**: [exact earlier Part, lab, glossary page, or reference page to read first]
- **Expected time**: [for example, 60-90 minutes]
- **You will build**: [the concrete capability added to the local paper research assistant]
- **You will be able to explain**: [2-3 mechanism-level ideas in plain language]
- **You will prove it works by running**: [the Part-specific eval command plus the global pytest/ruff gate]
- **Offline guarantee**: [name the fake model, fixture, or deterministic adapter used instead of a real network/provider]

## Section Map

Each Part should have 3-5 teaching sections plus the Eval Gate. Label the section type and cycle intensity while drafting so reviewers can see the teaching rhythm.

| Section Type | Cycle Intensity | Required Cycle | Use When |
|--------------|-----------------|----------------|----------|
| Concept Section | [LIGHT] | Problem -> Explore -> Inspect -> Connect | Introduce 2-3 new ideas through a concrete research-assistant scenario |
| Build Section | [FULL] | Problem -> Explore -> Build -> Inspect -> Modify -> Break -> Fix -> Reflect | Implement the new capability and include L1/L2/L3 exercises |
| Inspection Section | [LIGHT] | Inspect -> Connect -> Reflect | Read event trails, object relationships, architecture, or data flow |
| Break & Fix Section | [FULL] | Break -> Fix -> Inspect -> Reflect | Turn a likely learner failure into a diagnosis lab |
| Product Section | [LIGHT] | Inspect -> Connect -> Reflect | Connect the capability to the Workbench UI/API/product object |
| Gate Section | [LIGHT] | Reflect -> Connect | Close with eval commands, L3 checkpoint, reflection, and discussion |

Use [FULL] for sections where the learner writes or repairs the mechanism. Use [LIGHT] for sections that build intuition, connect the mechanism to the Workbench, or close the Part. The default template below embeds Break -> Fix inside the Build Section; split it into a standalone [FULL Break & Fix] section when the failure lab needs more room.

## Callout Format

Use ASCII tags as the primary marker. Emoji may be added after the tag, but never replace it.

> [BIG] **大局观**：[当前概念和前后 Part 的关系]

> [DD] **设计决策**：为什么选择这个接口/边界？
>
> **选了**：[描述当前方案]
> **没选**：[描述替代方案]
> **因为**：[解释取舍，尤其是 beginner/offline/deterministic 影响]

> [TRAP] **常见陷阱**：[初学者容易误解的地方，以及怎么发现自己掉进去了]

> [CHECK] **检查一下**：[要求学习者在继续前用自己的话解释一个机制]

> [DEEP] **深入一点**：[可选高级内容；初学者可以跳过，不影响完成 eval gate]

## Required ASCII Diagram Formats

Use ASCII diagrams so the course works in terminal, plain Markdown, and git diff. Include at least two diagrams per Part; the Architecture Map is required in the opener.

### Architecture Map

Show where this Part sits in the whole local paper research assistant. Mark the current Part with `[*]`.

```text
Local Paper Research Assistant
  [ ] Paper fixtures
  [ ] Source ingestion
  [*] [current Part capability]
  [ ] Memory / skills
  [ ] Delegation
  [ ] Workbench UI
  [ ] Diagnostics / policy
```

### Object Relationship Diagram

Show core objects, their inputs, outputs, and dependencies.

```text
[Input Object]
      |
      v
[Core Object] --depends on--> [Policy / Runtime / Fixture]
      |
      v
[Output Object]
```

### Event Flow Timeline

Show one run as an ordered event sequence.

```text
t0  user_request      -> [what arrived]
t1  context_built     -> [what state was prepared]
t2  model_response    -> [what the fake model returned]
t3  tool_call         -> [what deterministic tool ran]
t4  final_output      -> [what the learner should inspect]
```

### Data Flow Diagram

Show how data moves between objects or layers.

```text
[Paper Fixture] -> [Retriever] -> [Evidence] -> [Claim] -> [Report]
        ^                                             |
        |                                             v
        +---------------- [Eval Assertion] <----------+
```

## 你的本地论文研究助手现在需要 [新能力]

[一句话描述这个 Part 解决什么问题，以及它如何推进"本地论文研究助手"这条叙事线。]

> [BIG] **大局观**：[这个 Part 在完整研究助手中的位置；点名上一个 Part 已经有什么、下一个 Part 会缺什么]

```text
[ASCII Architecture Map - 当前 Part 用 [*] 高亮]
```

## Section 1 [LIGHT Concept]: [概念名称] - 为什么需要这个

### Problem Hook

[给一个研究者使用本地论文研究助手时会真实遇到的场景。先让学习者感受痛点，不要先讲抽象名词。]

### Explore

[让学习者运行或阅读一个最小现有方案，观察它哪里不够。示例必须能离线运行。]

### 概念：人话版

[用 2-3 个新概念解释这个痛点。先讲人话，再给正式术语。]

> [CHECK] **检查一下**：[让学习者用自己的话解释这个概念。如果解释不出来，指出应该回到哪个小节。]

### Inspect

[查看 event sequence、object relationship、data flow，或者一个小型 trace。]

```text
[ASCII Object Relationship Diagram or Event Flow Timeline]
```

### Connect

[说明这个概念如何帮助本地论文研究助手获得本 Part 的新能力。]

> [DD] **设计决策**：[为什么这个概念用当前接口或边界表达]
>
> **选了**：[当前设计]
> **没选**：[替代设计]
> **因为**：[取舍理由]

## Section 2 [FULL Build]: Build [具体机制]

### Problem

[说明现在要补上的最小机制，以及如果不补会出现什么可观察问题。]

### Explore

[展示起点代码、fixture、trace、失败输出或空白接口。]

### Build

Provide copy-pasteable snippets that run from `redesign/`. Python shell snippets must use:

```bash
PYTHONPATH=packages/research_core/src uv run python
```

### L1 Follow 练习

[给代码骨架，让学习者跟着填关键行并运行。]

#### Exercise Feedback - L1 Follow

**Common Errors**:
1. [错误 1] - 原因：[为什么常见]
2. [错误 2] - 原因：[为什么常见]

**Failure Output Interpretation**: [如果输出不对，错误信息或 event trail 通常长什么样；从哪一项开始排查。]

**Where To Go Back**: [卡住时回到正文哪个小节、哪个概念、哪张图。]

**Why Correct Answer Is Correct**: [正确答案证明了什么；它排除了哪种错误理解。]

### Inspect The Trail

[让学习者检查 event sequence / data flow / assertion output，确认机制真的发生了。]

```text
[ASCII Event Flow Timeline]
```

### Modify

[要求学习者改一行、一个参数或一个 fixture，并先预测结果。]

> [TRAP] **常见陷阱**：[这里最容易把"代码能跑"误解成"机制正确"的地方。]

### L2 Modify 练习

[给修改任务：预测 -> 修改 -> 运行 -> 比较。]

#### Exercise Feedback - L2 Modify

**Common Errors**:
1. [错误 1] - 原因：[为什么常见]
2. [错误 2] - 原因：[为什么常见]

**Failure Output Interpretation**: [如果输出和预测不一致，怎样读失败输出、event trail 或 assertion diff。]

**Where To Go Back**: [卡住时回到正文哪个小节重新理解因果关系。]

**Why Correct Answer Is Correct**: [正确答案为什么能解释这次变化；它排除了哪种错误理解。]

### Break

[故意弄坏一个具体位置。破坏必须产生可检查的输出：失败 eval、structured error、rejected write、event trail 缺项等。]

### Fix

[给诊断方向，不直接跳到答案。说明应该先看哪个 artifact。]

### Reflect

[用 1-2 个问题让学习者说清楚：刚刚的 bug 为什么会发生，当前设计如何让它可诊断。]

## Section 3 [LIGHT Inspection]: Inspect [事件/对象/数据流]

### Inspect

[放大观察本 Part 最关键的 event trail、object relationship 或 data flow。]

```text
[ASCII Data Flow Diagram]
```

### Connect

[把观察结果连回本地论文研究助手：这个数据/事件最终帮助研究者做什么？]

> [DEEP] **深入一点**：[高级实现细节或替代设计。初学者可以跳过，跳过后仍能完成 eval gate。]

### Reflect

[一个短问题，确认学习者能把图和代码对应起来。]

## Section 4 [LIGHT Product]: 接入你的 Workbench

### Inspect

[说明这个能力会在 Workbench 的哪个 screen、panel、API record、timeline event 或 domain object 中出现。]

### Connect

[解释为什么研究者需要在界面里看到这个状态，而不是只看终端输出。]

### Reflect

[要求学习者描述：如果这个 UI 状态错了，研究者会误判什么？]

## Section N [LIGHT Gate]: Eval Gate

### Passing Standard

[列出通过标准。每条标准都要能被离线命令、fixture、assertion、trace 或手动 inspection 验证。]

### Commands

Run from `redesign/`.

```bash
uv run pytest -q [Part-specific test path or eval fixture]
uv run pytest -q
uv run ruff check .
```

If this Part has a runnable lesson snippet, also include the exact command:

```bash
PYTHONPATH=packages/research_core/src uv run python [path-or--c-snippet]
```

### Failure Output Interpretation

[贴近本 Part 说明：pytest 失败、assertion diff、event trail 缺项、ruff 错误各自意味着什么。]

## Checkpoint

### L3 Design 练习

[给需求描述，不给代码骨架。学习者需要自己设计实现，并通过 Eval Gate。]

#### Exercise Feedback - L3 Design

**Common Errors**:
1. [设计错误 1] - 为什么它看起来对但其实有问题：[...]
2. [设计错误 2] - 为什么它看起来对但其实有问题：[...]

**Failure Output Interpretation**: [如果设计没通过 eval gate，优先看哪条失败输出；它通常暗示哪种设计误解。]

**Where To Go Back**: [卡住时回到哪张图、哪个设计决策、哪个 Build 小节。]

**Why Correct Answer Is Correct**: [正确设计满足了哪些约束；它排除了哪些错误边界或错误因果关系。]

### Reflection

1. [设计决策问题 1：为什么当前边界适合本地、离线、可测试的研究助手？]
2. [设计决策问题 2：如果未来接入真实 provider，这个边界哪里需要扩展，哪里不应该动？]
3. [机制理解问题：让学习者用自己的话解释最关键的对象/事件/数据流。]

### Discussion

1. [适合 self-study 或团队讨论的问题：当前设计牺牲了什么，换来了什么？]
2. [适合工程判断的问题：什么时候应该选择替代方案？]

---

**完成这个 Part 后，你的本地论文研究助手现在可以 [新能力]。**

**Next: Part N+1 会遇到 [下一个痛点]，所以接下来要让助手学会 [下一个能力]。**
