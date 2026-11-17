# Agent 面经 1：简洁版回答

以下回答结合 DevFlow-AI 当前源码整理，适合面试口述。项目实现依据静态阅读核实；实际数据规模与耗时仍需统计。

## 1. 你认为什么是 Agent？它和大语言模型有什么区别？

大语言模型主要负责理解和生成内容；Agent 是围绕模型构建的任务执行系统，能够选择工具、执行操作、读取结果，再决定下一步。项目中的 ChatAgent 就通过“模型决策—工具执行—结果反馈”的循环完成任务。

## 2. Function Calling / Tool Calling 是怎么实现的？

先把工具名称、用途和参数 Schema（参数结构说明）提供给模型；模型返回工具名和参数，后端校验并执行，再把结果交给模型继续处理。项目使用 LangChain 的 `bind_tools` 注册工具，用 LangGraph 管理执行循环。

源码：[ChatAgent._build_agent_graph](../backend/app/services/agents/chat_agent.py#L396)、[ChatAgent._tool_model](../backend/app/services/agents/chat_agent.py#L948)。

## 3. 大模型生成的结构化数据如果不符合要求，你怎么校验？

分三层：JSON 能否解析、字段类型和取值是否合法、内容是否符合业务规则。项目中 Issue 和 PR 分析会先补齐或规范化部分字段，再用 Pydantic 校验；仍然失败就返回规则兜底结果。结构合法也不代表事实正确。

源码：[IssueAgent.run](../backend/app/services/agents/issue_agent.py#L10)。

## 4. Pydantic 这种校验工具你有用过吗？

项目中用它定义接口数据和模型输出结构。通过 `BaseModel` 定义字段，`Literal` 限制枚举值，`Field` 限制数值范围，再通过 `model_validate` 校验。例如置信度必须在 0～1，优先级只能是 P0～P3。

源码：[IssueAnalysisOutput](../backend/app/schemas/analysis.py#L25)。

## 5. MCP 用过吗？了解过吗？

MCP，即 Model Context Protocol，是统一连接 AI 应用与外部工具、数据的协议。项目通过 MCP 调用记忆检索和会话读取工具：客户端启动本地服务进程，完成初始化，再发送 `tools/call` 请求。

源码：[StdioMcpClient.call_tool](../backend/app/services/mcp_client.py#L15)。

## 6. MCP 有哪些传输方式／类型？

标准传输主要有两种：**stdio** 通过本地进程的标准输入输出通信；**Streamable HTTP** 通过 HTTP 连接服务，响应可以使用 SSE（服务器向客户端持续推送事件）流式返回。旧版 HTTP+SSE 已被替代，项目采用 stdio。

参考：[MCP 官方传输规范](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)。

## 7. 你认为 Skill 为什么会出现？为什么会火？核心思想是什么？

模型有通用能力，但具体任务还需要业务流程、操作规范和配套资源。Skill 把这些经验封装成可复用的能力包，降低重复编写流程的成本。核心思想是**渐进式加载**：先提供简介，任务匹配后再加载完整指令，减少无关上下文。

## 8. 既然 Skill 可以描述流程，为什么不用 System Prompt 直接实现？

简单流程可以直接写进 System Prompt（系统提示词）。任务种类增加后，把所有流程放进去会让提示词越来越长，也难以维护。Skill 便于按任务加载、独立修改和复用，最终仍然需要把相关指令提供给模型。

## 9. 一个 Skill 常见的组织格式是什么？

通常是一个目录，包含必需的 `SKILL.md` 和可选的配套资源：

```text
my-skill/
├── SKILL.md       # 元数据与执行指令
├── scripts/       # 可执行脚本
├── references/    # 详细参考资料
└── assets/        # 模板、图片等资源
```

`SKILL.md` 顶部用 YAML 写名称和描述，正文写执行步骤、输入输出要求和注意事项。项目还扩展了版本、触发词和允许工具等字段。

参考：[Agent Skills 格式规范](https://agentskills.io/specification)。

## 10. 如果 Skill 的流程很复杂，一个 SKILL.md 写不下怎么办？

让主文件保留适用场景和主要流程，把详细规则拆到 `references/`，确定性处理放到 `scripts/`，模板等资源放到 `assets/`。项目支持加载被引用的资源，但当前是在 Skill 激活时读取这些资源，并限制数量、大小和路径。

## 11. 在 Skill 内部调用 script／脚本时，一般怎么操作？

在指令中说明脚本路径、参数和预期输出，由 Agent 通过执行工具运行，再根据返回结果继续任务。**写出脚本路径不会自动执行。**项目当前的 Skill 资源加载器只读取脚本内容，不能把它说成已经实现了通用脚本执行能力。

源码：[SkillRegistry._load_referenced_resources](../backend/app/services/skills/registry.py#L245)。

## 12. 你觉得自己对 RAG 了解得多吗？

RAG 是检索增强生成：先从外部知识库找到相关证据，再让模型结合证据回答。我能结合项目说明文档解析、切片、Embedding（文本向量化），以及召回、融合、重排、上下文组装和引用的完整流程。

## 13. 你的 RAG 做过哪些方案和尝试？

项目实现了向量检索、BM25 关键词检索，以及两者加权融合的混合检索，并支持重排、相邻片段补充和上下文压缩。对话前会预检索，Agent 运行中也能调用工具补查。这些是已实现的方案，具体效果提升还需要对照评测。

源码：[search_similar_documents](../backend/app/services/rag/retrieval.py#L560)、[retrieve_knowledge](../backend/app/services/rag/knowledge_base.py#L219)。

## 14. 你的 RAG 数据规模大概有多大？

项目按仓库组织知识库，主要处理 Issue、PR 说明与评论、失败 CI 日志和上传文档。当前没有核实实际入库总量，因此不能报具体规模；应分别统计原始文档数、切片数和成功索引的向量数。

## 15. Chunk 是怎么切分的？Chunk Size 大概是多少？

Chunk 就是用于检索的文本片段。项目优先按标题、段落等结构切分，过长内容再拆分，并保留来源位置。上传文档采用知识库配置，默认 **800 字符、重叠预算 100 字符**；底层通用函数默认是 1600/160，要区分实际调用参数。

源码：[知识库默认配置](../backend/app/db/models.py#L220)、[chunk_document](../backend/app/services/rag/chunking.py#L761)。

## 16. 做一次 RAG 检索大概要多长时间？

当前没有可核实的统一耗时数据，不能直接报毫秒数。代码已记录检索流水线的 `duration_ms`，包含查询向量化、召回、重排和上下文处理，不包含最终回答生成。正式报告时应固定数据规模和配置，分别统计检索与完整问答的 P50、P95（第 50、95 百分位）耗时。

源码：[retrieve_knowledge 耗时统计](../backend/app/services/rag/knowledge_base.py#L219)。
