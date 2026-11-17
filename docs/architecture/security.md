# Security

- API Key 与 GitHub Token 通过环境配置或用户输入提供；真实 `.env` 不进入发布包。
- GitHub Token 持久化时通过 `app.core.security` 加密，部署时应配置专用加密密钥。
- GitHub 写操作通过 ActionDraft 创建、权限检查及确认接口执行；具体支持范围以 `app/api/routes/action_drafts.py` 为准。
- 当前权限链路依赖演示用户，未提供完整的生产身份认证。请在受控的本地或测试环境评估；公网使用需要补充认证与访问控制。
