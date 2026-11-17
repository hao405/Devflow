# 如何让 Agent 不乱写、不越权（精简版）

用户要求评论 PR、关闭 Issue 或打标签时，需要同时控制回答质量和操作权限。**提示词规定应该怎样做，后端决定实际能够做什么。** 项目通过受控工具、范围检查、结构化结果，以及“草稿—确认—执行”链路降低风险。

## 1. 先限制工具和数据范围

- **工具注册表**：ChatAgent（对话 Agent）只能执行后端注册的工具，未知工具会被拒绝；当前对话工具集提供检索、分析和安全草稿，没有任意命令执行、源码写入或草稿确认工具。
- **显式 Skill 的工具白名单**：Skill 是为特定任务提供指令和工具约束的技能包。用户明确指定 Skill 时，执行前检查调用是否在其允许工具列表中，越界返回 `permission_denied`。自动激活 Skill 不走这项显式限制。
- **范围检查**：工作区路径解析后必须位于项目目录内，并过滤已列明的敏感文件；工作流声明目标 ID 时，还会校验目标类型和仓库归属。`claim` 表示任务声明的操作范围，其 `allowed_sources` 字段本身并不自动形成完整权限隔离。

源码：[工具执行入口](../backend/app/services/agents/chat_agent.py#L733)、[显式 Skill 检查](../backend/app/services/agents/chat_agent.py#L1775)、[路径检查](../backend/app/api/routes/chat.py#L426)、[工作流目标检查](../backend/app/api/routes/chat.py#L627)。

## 2. 安全规则怎样落实到一次调用

系统提示词要求写操作先调用安全工具；Skill 的普通说明也会交给模型遵循。其中，显式 Skill 声明的 `tools` 列表会被后端加载，成为执行前白名单检查的依据。

例如，只显式启用 `safety-draft` 时，它允许安全草稿工具和证据检索。模型如果尝试调用 PR 审查，`_complete_tool_call()` 会先检查并返回 `permission_denied`，标记为不可重试，**不会进入工具执行函数**。拒绝信息随后以 `tool_result`（工具执行结果）返回模型。

对应控制逻辑可以简写为：

```text
收到模型提出的工具调用
    ├─ 不符合显式 Skill 白名单 → 拒绝，不执行
    ├─ 工具未注册 → 拒绝，不执行
    └─ 通过检查 → 调用工具，其内部再检查路径、目标等条件
```

因此，安全规则要落地，需要在产生实际操作的调用路径上增加检查和拒绝分支。仅写在提示词中的要求，仍依赖模型遵循。

源码：[安全 Skill 的工具声明](../backend/app/skills/safety-draft/SKILL.md#L8)、[加载声明](../backend/app/services/skills/registry.py#L174)、[执行前拦截](../backend/app/services/agents/chat_agent.py#L741)。

## 3. 约束输出，检查证据与冲突

专用 Agent 使用 Pydantic（数据结构校验库）检查结果。例如 PR 审查限制合入建议的取值、置信度范围，并结合规则兜底；工作流中的 Observer（结果检查 Agent）检查证据缺失、低置信度和 PR/CI 结论冲突。

这些机制能发现部分格式和业务问题，仍需要核对底层证据。**结构合法、置信度较高，都不能证明结论正确。**

源码：[PR 输出校验与兜底](../backend/app/services/agents/pr_review_agent.py#L18)、[Observer 检查](../backend/app/services/agents/observer_agent.py#L14)。

## 4. 安全草稿、人工确认与审计怎样协作

| 组成部分 | 负责什么 | 项目实现 |
| --- | --- | --- |
| 安全检查 | 按动作关键字识别写入或发送风险 | `SafetyAgent` |
| 安全草稿 | 保存操作类型、目标、内容与待确认状态 | `ActionDraft` |
| 确认与权限 | 检查批准权限、草稿状态，再调用执行函数 | `confirm_action_draft()`、`require_permission()` |
| 审计 | 保存触发用户、操作对象与执行结果 | `AuditLog` |

一条 PR 评论草稿的处理链路：

```text
ChatAgent 调用安全工具
    ↓
SafetyAgent 返回风险与确认要求
    ↓
后端保存 ActionDraft，状态为 pending_confirmation（待确认）
    ↓
用户在草稿页审阅，点击确认，调用独立确认接口
    ↓
后端检查 draft:approve 权限与待确认状态
    ↓
调用已支持的 GitHub 操作 → 更新状态并记录审计
```

**模型说“已确认”不会触发写入；实际执行需要调用确认接口。** 当前该接口已支持评论、创建或关闭 Issue、添加标签；`send_report` 只记录状态，尚未接入外部消息渠道。

SafetyAgent 当前不调用大模型，按关键字返回 `requires_confirmation` 等字段。保存待确认草稿的是后端 `check_safety()`；执行时由确认接口检查权限和数据库状态，无批准权限返回 403，状态不符返回 400。风险等级和确认标志本身都不能代替这些执行检查。

源码：[风险检查](../backend/app/services/agents/safety_agent.py#L12)、[对话创建草稿](../backend/app/api/routes/chat.py#L1229)、[确认与执行](../backend/app/api/routes/action_drafts.py#L157)、[支持的操作](../backend/app/api/routes/action_drafts.py#L35)。

## 5. 权限、失败与当前边界

角色权限采用 RBAC（按角色分配权限）：owner、maintainer 可以批准草稿，developer 可以创建草稿，viewer 只能进行相应只读访问。执行成功记为 `executed`，异常记为 `failed`，并保存错误和审计；待确认草稿也可以取消。审计用于追溯，不能阻止错误操作或自动撤销外部写入。

面试时需要说明这些限制：

- `require_permission()` 当前通过 `ensure_demo_user()` 取数据库首个用户，缺省创建 owner，尚未形成真实登录身份和仓库级授权闭环。
- 风险识别依赖关键字；对话草稿还有按最新 PR/Issue 选择目标的逻辑，动作映射与目标绑定仍需加强。人工应核对具体对象和内容，不能认为所有写入口都已完整校验。
- 待确认状态检查能挡住已完成草稿的串行重复执行，但当前确认逻辑未见并发锁或幂等机制，不能保证并发请求只写入一次。

源码：[角色与演示用户](../backend/app/services/permissions.py#L9)。上述为源码核验结论，未执行真实 GitHub 写入验证。

## 面试口述版

> 项目通过分层控制降低 Agent 乱写和越权风险。模型只能调用注册工具，显式 Skill 有执行前白名单检查，路径和工作流目标也有范围校验。对话侧的安全工具负责生成可审阅草稿；执行草稿要通过独立接口检查批准权限和状态，执行后记录结果与审计。结构化输出和 Observer 帮助发现格式、证据与结论冲突。当前仍是演示身份体系，目标绑定和并发幂等还需完善，因此不能把它描述成完整的生产权限系统。


