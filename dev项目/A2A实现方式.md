
回答：**中心化调度**。项目内部通过异步函数调用和结构化数据实现 Agent 协作，当前源码中未看到独立的 A2A 协议接入。

## 核心调用链

```text
用户请求 → ChatAgent
  ├─ 单领域任务：调用工具 → 专用 Agent → 返回分析结果
  └─ 跨领域任务：调用 workflow.run_engineering_review
       → WorkflowOrchestrator
       → Planner 生成计划
       → 按依赖调度专用 Agent
       → Observer 检查结果，必要时有限重规划
       → Synthesis 综合报告 → 返回 ChatAgent
```

## 关键实现

1. **统一接口**：Agent 继承 `BaseAgent`，通过 `async run(input_data, context) -> dict` 接收业务数据和辅助上下文，返回结构化结果。
2. **Agent 作为工具**：ChatAgent 将专用 Agent 的调用函数包装成 `StructuredTool`，由模型选择工具；执行结果摘要写入观察记录，供后续模型判断。
3. **计划与调度**：Planner 根据用户请求和可用数据生成 `WorkflowSpec`，记录任务类型、目标、依赖和分析范围。Orchestrator 按 `task_type` 查找执行器，使用 `asyncio.gather()` 并发运行依赖已成功的任务，默认最多并发 3 个。
4. **结果交接**：任务统一返回 `WorkflowTaskResult`，包含状态、摘要、详细输出、证据数量、置信度、引用和错误。协调器收集后交给 Observer、重规划入口和 Synthesis。
5. **冲突与失败处理**：Observer 按规则检查失败、证据不足、低置信度和结论冲突。例如 PR 建议合并但 CI 阻塞时，标记冲突并优先保留 CI 门禁。任务默认超时 90 秒；依赖失败则跳过下游任务；重规划默认最多 1 次，代码上限为 2 次。
6. **过程留档**：计划、检查意见和任务结果分别保存到 `AgentWorkflowRun`、`AgentTaskRun`，便于追踪。

## 实现边界

- ChatAgent 的工具循环使用 LangGraph；工程工作流的依赖与并发由 Orchestrator 自己调度。
- `dependencies` 控制执行顺序，当前不会自动把上游任务输出注入下游输入。
- Planner、Observer 和 Synthesis 当前分别使用条件规则、规则检查和模板组织报告；专用 Agent 可以调用大模型完成分析。

## 源码入口

- [统一接口 BaseAgent](../backend/app/services/agents/base.py#L5)
- [工具注册与工作流入口](../backend/app/api/routes/chat.py#L1286)
- [计划与结果结构](../backend/app/schemas/workflow.py#L26)
- [依赖与并发调度](../backend/app/services/agents/workflow_orchestrator.py#L154)
- [跨 Agent 冲突检查](../backend/app/services/agents/observer_agent.py#L97)

以上依据源码静态核对，未代表真实模型和数据库的端到端验证结果。
