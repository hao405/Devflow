拆分的依据是可独立验收的责任


| 专用 Agent        | 它关心的问题            | 主要输入                          | 主要输出                |
| --------------- | ----------------- | ----------------------------- | ------------------- |
| `IssueAgent`    | 问题是否清楚？多紧急？交给谁？   | Issue 描述、标签、相似问题、团队信息         | 分类、优先级、复杂度、负责人、行动项  |
| `PRReviewAgent` | 代码改动有什么风险？还缺什么验证？ | PR 描述、文件、diff、Review 评论、CI 摘要 | 分级发现、阻塞项、测试建议、合入建议  |
| `CIDebugAgent`  | 哪个环节失败？可能为什么？     | Workflow Run、Jobs、Steps、日志    | 失败类型、首个错误、根因判断、修复步骤 |
## `IssueAgent`
IssueAgent 的目标，是把模糊的问题整理成可以推进的任务。
点击 Issue 页面的“分析”后，后端会先准备这些材料：

```
Issue 本身
＋相似 Issue 候选
＋当前仓库代码线索
＋项目文档
＋相关会话证据
＋团队成员画像
```

## PRReviewAgent 
PRReviewAgent 的目标，是把代码改动转化成可执行的审查结论。
它先调用 `chunk_pr_files()` 对 patch 分块，再结合 PR 信息和上下文调用模型。规则兜底会检查：

- 是否修改认证、权限、支付、数据库迁移等敏感文件。
- 是否存在失败 CI。
- 是否有需要确认处理状态的 Review 评论。
- 改动是否较大。
- 是否缺少明显的测试文件。

它先调用 `chunk_pr_files()` 对 patch 分块，再结合 PR 信息和上下文调用模型。规则兜底会检查：

- 是否修改认证、权限、支付、数据库迁移等敏感文件。
- 是否存在失败 CI。
- 是否有需要确认处理状态的 Review 评论。
- 改动是否较大。
- 是否缺少明显的测试文件。

输出中，每条审查发现都有：

```
severity         P1 / P2 / P3
title            问题是什么
evidence         判断依据
required_action  需要完成什么动作
blocking         是否阻塞
```

### CIDebugAgent 
CIDebugAgent 的目标，是把失败流水线变成有证据的排查路线。

```
找到失败 Job
    ↓
找到失败 Step
    ↓
提取首个关键错误块
    ↓
分类：test / build / lint / dependency / permission / environment / unknown
    ↓
提取日志中的相关文件
    ↓
生成可能根因、修复步骤和合并阻塞判断
```


你可以用下面这段作为面试口述底稿：

我按研发协作中的决策对象，把分析能力拆成 Issue、PR 和 CI 三类专用 Agent。

Issue Agent 负责问题分诊，判断优先级、复杂度、负责人以及是否具备开发条件；PR Agent 根据 diff、评论和 CI 摘要输出分级风险与合入建议；CI Agent 根据失败 Job、Step 和日志输出诊断与修复路线。

实现上，三类 Agent 统一提供 run(input_data, context) 接口，采用领域提示词、规则兜底、结果修正和 Pydantic 校验。ChatAgent 通过工具调用选择这些能力；跨领域问题由 WorkflowOrchestrator 按依赖并发调度，再由 Observer 检查冲突和门禁，Synthesis 汇总统一结论。

这样的拆分便于分别维护和评测。代价是增加调用成本，也要求编排层处理证据完整性、结果冲突和任务失败。当前专用 Agent 主要执行固定分析流程，进一步自主检索和多轮验证仍有扩展空间。