# Capstone: 本地论文研究助手

当前状态：这是一个占位页。Phase R1 先把课程终点和学习路线讲清楚，完整 Capstone 会在 Phase R8 补齐。

现在不要把这里当成已经完成的项目需求、starter code 或参考答案。等 Phase R8 完成后，这里才会变成可以正式练习和验收的 Capstone 项目入口。

## Capstone 是什么

Capstone 会把前 7 个 Part 学到的能力整合成一个完整的离线项目：本地论文研究助手。

它最终会做到：

- 接收一个研究问题。
- 从本地 paper fixture 里检索相关论文材料，不访问真实网络。
- 从 source 中提取可以检查的 evidence。
- 生成带引用的 cited report。
- 使用 memory 记住前面查过的内容和中间结论。
- 把复杂问题 delegation 给 child agents。
- 通过 Workbench UI 查看 sources、timeline、report 和运行状态。
- 留下 inspectable event trails，让每一次 run 都可以复盘。

这套设计的重点不是做一个联网 demo，而是让你能在完全离线、可重复、可测试的环境里，看清一个研究型 Agent 从问题到证据、从证据到报告、从一次运行到可复盘系统的完整过程。

## 学习路线

建议按顺序完成：

1. Part 1: [00-before-agent-kernel.md](../chapters/00-before-agent-kernel.md) - Section 1：先建立心智模型和项目叙事起点；然后读 [01-agent-kernel-foundations.md](../chapters/01-agent-kernel-foundations.md) - Sections 2-5：动手搭出 Agent build loop。
2. Part 2: [02-research-core-foundations.md](../chapters/02-research-core-foundations.md) - source、evidence、claim、report 怎么连成证据链。
3. Part 3: [03-memory-and-skills.md](../chapters/03-memory-and-skills.md) - memory 和 skill 如何参与运行。
4. Part 4: [04-multi-agent-delegation.md](../chapters/04-multi-agent-delegation.md) - child agents 如何分工。
5. Part 5: [05-workbench-product.md](../chapters/05-workbench-product.md) - Workbench UI 如何观察运行过程。
6. Part 6: [06-framework-comparisons.md](../chapters/06-framework-comparisons.md) - 如何用同一个任务比较框架。
7. Part 7: [07-production-readiness.md](../chapters/07-production-readiness.md) - 如何补上可观测、可持久化、可审批、可复盘的生产边界。
8. Capstone: [course/capstone/](./) - 把上面 7 个 Part 串成完整的本地论文研究助手。

## Phase R8 会补什么

Phase R8 计划把 `course/capstone/` 补成下面这样的结构：

```text
course/capstone/
|-- README.md
|-- rubric.md
|-- paper_fixtures/
|-- starter/
|   |-- agent_starter.py
|   `-- test_starter.py
`-- solution/
    |-- agent.py
    |-- test_run.py
    |-- trajectory.jsonl
    |-- report.md
    `-- reflection.md
```

这些文件的角色会是：

- `README.md`: Capstone 的项目说明和练习入口。
- `rubric.md`: 评分标准，帮助你判断自己的实现是否达标。
- `paper_fixtures/`: 离线论文数据集。
- `starter/`: 给学习者起步用的代码骨架。
- `solution/`: 参考实现。
- `trajectory.jsonl`: 一次完整运行留下的事件轨迹。
- `report.md`: Agent 生成的示例研究报告。
- `reflection.md`: 对关键设计决策的复盘。

## 现在该怎么用这个页面

现在你只需要把它当成课程终点预告：

1. 先按 `course/README.md` 里的顺序学完 Part 1 到 Part 7。
2. 学每一 Part 时，都留意它最终会怎样服务于本地论文研究助手。
3. 等 Phase R8 完成后，再回到这里做完整 Capstone。
