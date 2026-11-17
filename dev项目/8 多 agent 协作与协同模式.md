# 多 Agent 协作与共享记忆（v1.0.1）

“判断 PR 能否合并”需要同时考虑代码风险、CI 和历史证据。项目让专用 Agent 分工分析，再集中检查与综合。分工和并行可以帮助组织复杂任务，但当前没有性能或质量实验能证明多 Agent 必然优于单 Agent。

## 1. 谁负责组织协作

| 对象 | 实际职责 |
| --- | --- |
| `WorkflowSpec` | 保存目标、任务、依赖、并发上限等计划信息，本身不执行任务 |
| `PlannerAgent` | 根据用户请求和可用数据，按条件规则制定或补充计划 |
| `WorkflowOrchestrator` | 调度任务，处理失败，集中收集结果并决定是否继续 |
| `ObserverAgent` | 按规则检查证据缺口、低置信度、失败和结论冲突 |
| `SynthesisAgent` | 根据结构化结果与检查意见组织最终报告 |

ChatAgent 的 LangGraph 图负责对话与工具循环；这里的任务依赖和批次并发由 Orchestrator 自己实现。当前也没有独立接入 A2A（Agent 之间互通的一类协议）来运行这条协作链。

源码：[计划结构](../backend/app/schemas/workflow.py#L37)、[编排入口](../backend/app/services/agents/workflow_orchestrator.py#L37)。

## 2. 共享记忆究竟共享什么

首先，后端组装会话摘要、近期消息和证据，并读取本次仓库数据。各专项执行函数从这些共同材料中准备输入，再补充各自需要的内容。例如 PR Agent 的 `ci_summary` 来自预先读取的 CI 数据，不是 CI Agent 本轮生成的根因结论。

其次，各任务返回 `WorkflowTaskResult`，包含任务 ID、状态、摘要、详细输出、证据数量、置信度和引用。编排器维护本轮 `task_results`，传给 Observer、重规划的 Planner 与 Synthesis。这是集中管理的工作记忆。

**依赖成功只意味着可以开始执行。** 调用执行器时传入 `task`、`spec` 和 `context`，没有自动注入 `completed` 中的上游输出。因此 RAG 新找到的证据，也不会自动送回已成功的 PR Agent 重新分析。

源码：[共同上下文与专项输入](../backend/app/api/routes/chat.py#L592)、[结果结构](../backend/app/schemas/workflow.py#L48)、[依赖调度与执行](../backend/app/services/agents/workflow_orchestrator.py#L154)。

## 3. 结果如何检查、持久化与复用

PR 建议合并而 CI 报告阻塞时，Observer 会记录跨 Agent 冲突，Synthesis 根据阻塞项给出暂缓建议。这是规则检查，不能保证业务结论一定正确。

重规划默认最多 1 次，代码上限为 2 次；达到上限、没有触发条件或新旧任务图相同都会停止。结束后仍可能缺证据或存在阻塞，不能描述为“反复运行直到问题解决”。

外层流程把计划、检查意见和各任务输出写入 `AgentWorkflowRun`、`AgentTaskRun`，再封存本轮对话并更新会话工作记忆。持久化不代表下次自动加载所有任务输出；长期记忆候选通过审核后，才经相应路径进入项目知识检索。

源码：[检查冲突](../backend/app/services/agents/observer_agent.py#L97)、[有限重规划](../backend/app/services/agents/workflow_orchestrator.py#L41)、[工作流留档](../backend/app/api/routes/chat.py#L890)。

## 面试口述版

> 项目采用中心化协作：后端统一准备共同背景，专用 Agent 返回统一结构化结果，由编排器集中汇总，Observer 检查，Synthesis 综合。跨轮记忆依靠会话记录、摘要和审核后的项目知识。当前依赖主要控制执行顺序，上游结果尚未自动注入下游，补检索也没有自动触发专项分析反馈，这是后续改进方向。

更完整的调度边界见 [工程工作流调度](9%20多%20agent%20工程工作流怎么调度.md)，协议区别见 [A2A 实现方式](A2A实现方式.md)。
