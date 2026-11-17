# DevFlow-AI 项目总结文档 · v1.0.1

本目录收录项目学习总结、面试口述与 PR/CI 自测材料。本次重点核对并更新第 4、5、8 章：会话记忆、上下文压缩与缓存、多 Agent 共享上下文和结果交接。其他章节保留已有笔记；少量文件仍是提纲或占位，不代表完整模块说明。

## 阅读目录

- [0 PR与CI扫盲：从基本概念到DevFlow源码](0%20PR%E4%B8%8ECI%E6%89%AB%E7%9B%B2%EF%BC%9A%E4%BB%8E%E5%9F%BA%E6%9C%AC%E6%A6%82%E5%BF%B5%E5%88%B0DevFlow%E6%BA%90%E7%A0%81.md)
- [1 知识库切分与向量入库](1%20%E7%9F%A5%E8%AF%86%E5%BA%93%E5%88%87%E5%88%86%E4%B8%8E%E5%90%91%E9%87%8F%E5%85%A5%E5%BA%93.md)
- [2 多 agent 角度理解](2%20%E5%A4%9A%20agent%20%E8%A7%92%E5%BA%A6%E7%90%86%E8%A7%A3.md)
- [3 ChatAgent 怎样调度工具并完成回答（Function calling)](3%20ChatAgent%20%E6%80%8E%E6%A0%B7%E8%B0%83%E5%BA%A6%E5%B7%A5%E5%85%B7%E5%B9%B6%E5%AE%8C%E6%88%90%E5%9B%9E%E7%AD%94%EF%BC%88Function%20calling%29.md)
- [4 会话记忆与 memoryhub](4%20%E4%BC%9A%E8%AF%9D%E8%AE%B0%E5%BF%86%E4%B8%8E%20memoryhub.md)
- [5 解析上下文预算与渐进式压缩](5%20%E8%A7%A3%E6%9E%90%E4%B8%8A%E4%B8%8B%E6%96%87%E9%A2%84%E7%AE%97%E4%B8%8E%E6%B8%90%E8%BF%9B%E5%BC%8F%E5%8E%8B%E7%BC%A9.md)
- [6 解析MCP与 Skill怎样进入 ChatAgent](6%20%E8%A7%A3%E6%9E%90MCP%E4%B8%8E%20Skill%E6%80%8E%E6%A0%B7%E8%BF%9B%E5%85%A5%20ChatAgent.md)
- [7  Issue、PR与 CI专用 Agent 怎样工作](7%20%20Issue%E3%80%81PR%E4%B8%8E%20CI%E4%B8%93%E7%94%A8%20Agent%20%E6%80%8E%E6%A0%B7%E5%B7%A5%E4%BD%9C.md)
- [8 多 agent 协作与协同模式](8%20%E5%A4%9A%20agent%20%E5%8D%8F%E4%BD%9C%E4%B8%8E%E5%8D%8F%E5%90%8C%E6%A8%A1%E5%BC%8F.md)
- [9 多 agent 工程工作流怎么调度](9%20%E5%A4%9A%20agent%20%E5%B7%A5%E7%A8%8B%E5%B7%A5%E4%BD%9C%E6%B5%81%E6%80%8E%E4%B9%88%E8%B0%83%E5%BA%A6.md)
- [10  如何让 agent 不乱写，不越权](10%20%20%E5%A6%82%E4%BD%95%E8%AE%A9%20agent%20%E4%B8%8D%E4%B9%B1%E5%86%99%EF%BC%8C%E4%B8%8D%E8%B6%8A%E6%9D%83.md)
- [11 SSE、工具轨迹与 Agent 状态展示](11%20SSE%E3%80%81%E5%B7%A5%E5%85%B7%E8%BD%A8%E8%BF%B9%E4%B8%8E%20Agent%20%E7%8A%B6%E6%80%81%E5%B1%95%E7%A4%BA.md)
- [11 流式响应与执行轨迹怎样生成](11%20%E6%B5%81%E5%BC%8F%E5%93%8D%E5%BA%94%E4%B8%8E%E6%89%A7%E8%A1%8C%E8%BD%A8%E8%BF%B9%E6%80%8E%E6%A0%B7%E7%94%9F%E6%88%90.md)
- [12 Agent Eval 不能只看回答像不像](12%20Agent%20Eval%20%E4%B8%8D%E8%83%BD%E5%8F%AA%E7%9C%8B%E5%9B%9E%E7%AD%94%E5%83%8F%E4%B8%8D%E5%83%8F.md)
- [13 DevFlow AI是怎样驾驭 Agent](13%20DevFlow%20AI%E6%98%AF%E6%80%8E%E6%A0%B7%E9%A9%BE%E9%A9%AD%20Agent.md)
- [14 项目数据库与企业级后端面试教程](14%20%E9%A1%B9%E7%9B%AE%E6%95%B0%E6%8D%AE%E5%BA%93%E4%B8%8E%E4%BC%81%E4%B8%9A%E7%BA%A7%E5%90%8E%E7%AB%AF%E9%9D%A2%E8%AF%95%E6%95%99%E7%A8%8B.md)
- [A2A实现方式](A2A%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md)
- [DEV FLOW 项目背景与价值](DEV%20FLOW%20%E9%A1%B9%E7%9B%AE%E8%83%8C%E6%99%AF%E4%B8%8E%E4%BB%B7%E5%80%BC.md)
- [agent 面经 1](agent%20%E9%9D%A2%E7%BB%8F%201.md)
- [对话能力怎样组成研发工作台](%E5%AF%B9%E8%AF%9D%E8%83%BD%E5%8A%9B%E6%80%8E%E6%A0%B7%E7%BB%84%E6%88%90%E7%A0%94%E5%8F%91%E5%B7%A5%E4%BD%9C%E5%8F%B0.md)
- [PR 与 CI 理解自测（下载后用浏览器打开）](11%20PR%E4%B8%8ECI%E7%90%86%E8%A7%A3%E8%87%AA%E6%B5%8B.html)
- [压缩边界补充笔记](assets/%28%29.md)

## 本版本核验说明

- 源码入口已改为仓库相对链接；原配图中的流程与字段说明改为文字、表格和 Mermaid，发布包不包含截图文件。
- 共享上下文、本轮任务结果、持久化会话和审核后项目知识分别说明；依赖不自动传递上游输出。
- 微压缩与循环内投影分别说明；v1.0.1 没有接入服务端 `cache_edits`，不能保证本地清理后全部 KV 复用。
- 代码版 v1.0.1 曾完成 224 项后端本地测试；本次文档补充仅核对相关源码、引用和打包，不重复宣称真实外部环境验证。
- 部分原笔记保留较长教程和扩展知识，阅读时以其中标注的实现边界为准。

文档补充版附于 [v1.0.1 Release](https://github.com/hao405/Devflow/releases/tag/v1.0.1)，原代码发布标签保留。
