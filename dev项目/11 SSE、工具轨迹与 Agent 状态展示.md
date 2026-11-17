# SSE、工具轨迹与 Agent 状态展示（核心精简版）

用户问“最近 CI 为什么失败”时，Agent 可能先检索资料、再调用分析工具，最后组织回答。页面需要展示正在做什么、工具是否完成，以及答案如何返回。项目通过 **SSE 传输事件，前端根据事件更新工具轨迹与回复状态**。

## 1. SSE 怎样把执行过程送到页面

SSE（Server-Sent Events，服务端事件推送）让服务端沿同一个 HTTP 响应持续返回文本事件。项目使用 `fetch` 发送 POST 请求，后端通过 `StreamingResponse`（流式响应）返回 `text/event-stream`。

```text
首页 askAgent() 发送 /api/chat/stream 请求
    ↓
后端组装上下文，遍历 ChatAgent.run_stream()
    ↓
encode_sse() 将事件编码为 event、data 和空行
    ↓
前端 apiPostStream() 读取并解析 → 更新页面状态
```

一次网络读取可能只有半条事件，也可能包含多条。前端使用 `TextDecoder` 解码，将内容暂存在 `buffer`，按空行分出完整事件，保留未完成部分，再解析 `data` 中的 JSON。

源码：[流式接口](../backend/app/api/routes/chat.py#L1790)、[事件编码](../backend/app/services/agents/chat_agent.py#L2084)、[前端流读取](../frontend/lib/api.ts#L38)。

## 2. 页面主要接收哪些事件

| 事件 | 表示什么 | 首页怎样处理 |
| --- | --- | --- |
| `thought` | 模型在调用工具时给出的公开说明，可缺省 | 加入“公开思路”记录 |
| `tool_use` | 准备调用哪个工具、参数是什么 | 新增 `running` 工具记录 |
| `tool_result` | 本次工具的状态与结果摘要 | 更新对应记录为完成或失败 |
| `delta` | 一段回答文本 | 追加到答案正文 |
| `final` | 本轮最终结果，可带工具轨迹与结束信息 | 用完整答案与轨迹更新消息，结束等待 |

进入 LangGraph（状态图编排框架）工具循环时，后端通过节点事件，在工具开始时发送 `tool_use`，在节点返回后发送 `tool_result`。“公开思路”是模型返回的可见文本，不能当作完整内部推理过程。

源码：[工具节点事件转发](../backend/app/services/agents/chat_agent.py#L418)、[首页事件处理](../frontend/app/page.tsx#L2131)。

## 3. 工具轨迹与 Agent 状态怎样展示

主要展示逻辑在首页的 `askAgent()` 与 `ChatTraceInline`。简化的 `/chat` 页面只追加文本并在结束时展示最终 JSON。

工具开始事件中的 `id`，与结果事件中的 `tool_use_id` 对应。前端按这个 ID 找到原来的记录并更新，避免把一次调用画成两次。开始时显示工具名和参数，结束后更新为结果摘要；还可展示 Skill（任务技能包）的名称、版本等信息。

`responsePending` 表示当前回复是否仍在等待。`ChatTraceInline` 根据它和工具记录，显示“回复中”“执行中”“几个失败”或“已完成”；回复期间展开轨迹，正常收尾后默认折叠。

**传输结束、工具成功、任务完成是不同状态。** 后端 `completion` 可区分完成、受阻、预算耗尽、带工具错误结束，但当前首页未完整使用该字段；跳过的任务也可能被显示为完成。

源码：[按 ID 更新工具记录](../frontend/app/page.tsx#L2032)、[状态展示](../frontend/app/page.tsx#L3552)、[后端结束信息](../backend/app/services/agents/chat_agent.py#L634)。

## 4. 轨迹怎样保存，当前有哪些边界

正常收尾时，后端先保存回答、`tool_calls` 与消息元数据中的 `agent_events`，提交数据库后发送 `final`。重新加载历史消息时，前端根据保存的事件重建轨迹，因此展示不完全依赖当前浏览器内存。

- **文本分段发送**：当前普通对话先取得完整答案，再拆成 `delta`，尚不能据此宣称模型逐 token（文本生成单位）实时输出。
- **工作流内部进度**：确认计划执行接口先等待整个工作流返回，再发送各任务结果，内部任务尚未逐个实时推送。
- **停止与恢复**：停止按钮通过 `AbortController` 中断前端请求；不能保证所有后台操作已取消或回滚。当前读取逻辑也未实现自动重连与断点续传。

源码：[保存与发送 final](../backend/app/api/routes/chat.py#L1695)、[答案分段](../backend/app/services/agents/chat_agent.py#L2075)、[工作流结果发送时机](../backend/app/api/routes/chat.py#L1518)、[停止请求](../frontend/app/page.tsx#L2004)。

## 面试口述版

> 项目通过 SSE 展示 Agent 的执行过程。后端把工具开始、工具结果、回答片段和最终结果编码成事件，前端通过 POST 请求读取响应流，处理事件分包，再用调用 ID 更新同一条工具轨迹。正常结束时保存答案和事件，历史页面可以重建轨迹。当前答案采用生成后分段发送，多 Agent 内部结果也存在批量返回的情况；界面状态还需进一步与后端结束信息对齐。

以上依据当前源码整理，未验证真实部署中的代理缓冲、断线和取消行为。
