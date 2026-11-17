# 微压缩与 KV Cache：当前实现与边界

## 解决什么问题

Agent 连续读取文件、搜索代码后，旧工具结果会占据上下文。微压缩的目标是减少这些内容；KV Cache 是模型服务缓存已计算的 Key/Value 张量，用来复用相同输入前缀的计算。两者有关，但“减少输入”不自动等于“提高缓存命中”。

普通前缀缓存要求前缀匹配。假设输入依次是系统规则、当前问题、工具结果 A、工具结果 B。若把 A 替换成短摘要，A 之前未变的前缀仍可能命中；A 及后续部分不能按原来的完整前缀直接复用。具体命中还取决于服务商的缓存粒度、存活时间和路由。

## 项目实际有两条压缩路径

`ContextAssembler` 在上下文压力升高时调用 `microcompact_messages()`。该函数保留近期消息，只对较旧、符合工具结果角色和工具名提示、且足够长的内容，生成占位说明与问题相关摘录。它复制消息后改写正文，不会操作模型服务的缓存。

一个调用边界是：组装器先筛选 user/assistant 消息，而该函数主要识别 tool/tool_result。因此常规对话记录中的独立工具正文不能直接经过这条路径。不要将它描述为已经覆盖所有工具轨迹的微压缩，也不能把 assistant 最终答案当作旧工具正文清理。

实际 Agent 循环还使用 `_runtime_tool_context()`，把运行状态中的工具观察投影成受预算限制的模型输入。所谓“投影”，就是保留状态中的记录，仅为模型生成一份较短视图。注意这些观察本身可能已经经过 `_summarize_observation()` 截取，不能声称它们总是完整工具原文。

源码：[历史筛选与组装](../../backend/app/services/chat_memory.py#L490)、[微压缩函数](../../backend/app/services/context_compression.py#L492)、[循环内投影](../../backend/app/services/agents/chat_agent.py#L1477)。

## v1.0.1 的缓存友好改动

原来的单条观察预算会随观察数量增加而缩小，导致每次新增结果都可能重新截短旧结果。现在固定单条投影预算：正常追加且未超预算时，已有条目的投影保持不变，并把当前用户问题放在动态观察之前。

超预算时，按时间顺序批量省略旧观察，通常将保留内容压到预算的约 75%，留出追加余量；至少保留最新一条，必要时进一步缩短。`runtime_observation_start` 记录本轮已经省略的位置，避免旧结果下次重新出现。原有状态记录不因这次投影被覆写，但这次本地清理仍可能损失动态部分的缓存复用。

这是一种本地预算策略，不是按工具 ID 精准清理服务端缓存。75% 是实现中的留余量选择，尚没有真实模型成本或质量实验支持最优性；批量省略也可能让旧证据不再直接出现在模型输入中。

缓存统计同时识别 LangChain 的 `cache_read`、OpenAI 风格的 `prompt_tokens_details.cached_tokens` 和 DeepSeek 的 `prompt_cache_hit_tokens`。参数存在或本地 token 估算下降，都不能证明服务端命中。

## `cache_edits` 能否直接接入

当前项目使用 OpenAI 兼容的 Chat Completions 调用，模型决策会将观察序列化进 HumanMessage；没有发送 `cache_edits`，也没有实现服务端定点编辑协议。

若服务商提供经过确认的定点编辑扩展，适配层需要保留稳定的工具调用 ID 和原始消息块，另行发送编辑指令，处理重放、失败和服务端回执，不能仅凭字段名猜测请求格式。公开的 Claude `context_management` 工具清理是另一项能力，其文档明确说明清理会使相应缓存前缀失效，不应与“无损保留全部 KV”的说法混用。

参考：[DeepSeek 缓存规则](https://api-docs.deepseek.com/guides/kv_cache/)、[Claude Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)。

## 面试口述

项目保留运行记录，通过预算投影控制模型实际看到的工具上下文。v1.0.1 减少正常追加时对旧投影的改写，并在超预算时批量清理，降低频繁改变前缀的机会。当前实现没有服务端 `cache_edits`，也不能保证清理后全部 KV 继续复用；效果需要结合真实缓存命中、延迟、费用和任务质量评测。
