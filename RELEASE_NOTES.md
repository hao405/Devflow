# DevFlow AI v1.0.0

首个主体源码发布版本，基于本地 DevFlow-AI 项目筛选整理。

## 发布内容

- FastAPI 后端、Next.js 前端及其依赖清单和锁文件。
- ChatAgent、专用分析 Agent、工作流调度、RAG、记忆、Skill、工作区代码检索、GitHub 同步及操作草稿相关实现。
- 现有后端测试、Docker 配置、必要运行脚本与精简后的启动和架构文档。
- VERSION、后端 API 版本与前端 package/lock 版本统一为 1.0.0。
- 部署副本移除了个人服务器绝对路径与私人项目挂载，并统一默认前后端访问地址。
- 发布工作流按 VERSION 创建 Git Tag、GitHub Release、主体源码 ZIP 与 SHA-256 校验文件。

## 验证

- 后端现有测试：217 passed。测试使用 SQLite、空外部 API 凭证与测试替身；与 Milvus 行为有关的测试使用模拟存储。
- 前端 `npm run build`：成功，包括类型检查与页面生成；存在既有 React Hooks 依赖警告和 Browserslist 数据更新提示。
- 已进行 Python 语法检查、发布文件筛选、已配置敏感值匹配及常见凭证格式扫描。
- 发布前未验证真实模型、PostgreSQL、Milvus、GitHub 写操作或 Linux Docker 部署的完整端到端链路。

## 当前边界

- 当前本地源码没有 `docs/datas/evals/` 中的固定基准及其知识材料，因此发布包不包含这些数据；可按接口准备自有基准。自动文档冒烟测试不能代替固定质量基线。
- 本地 Qwen Embedding 需要可选依赖和首次模型下载。
- 权限实现仍使用演示用户，公网部署需要补充生产身份认证与访问控制。
- 不包含个人简历、学习笔记与图片、环境密钥、运行数据库、上传知识文件、依赖环境、构建缓存、日志或备份。
