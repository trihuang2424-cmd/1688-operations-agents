---
name: 1688-platform-maintenance
description: "按需检查1688网关、店铺和ERP连接及平台组件依赖，处理明确的连接或适配任务，不作为每日独立经营岗位。"
---

# 1688 连接与平台维护

路由：`connections_and_components`；按范围加 `connection` / `platform_components` 条件。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

这是当前任务负责人使用的共享维护能力；仅加载实际相关模块。输入包括故障或维护目标、实际系统、店铺范围、已有错误和用户授权。

| 本次需求 | 完整读取 |
|---|---|
| 网关、店铺、ERP或其他系统连接 | [原连接管理规则](../../../references/business-rules/1688-connection-administrator/RULES.md) |
| 身份审计、聊天卡片、内部组件或平台适配 | [原平台组件规则](../../../references/business-rules/1688-platform-support/RULES.md) |
| 平台业务知识 | [平台规则检索](../1688-platform-knowledge/SKILL.md) |

组件不单独成为每日经营任务，但来源业务流程需要的依赖与条件仍须执行；缺少宿主支持时如实记录。涉及配置写入时按原规则及[共用执行协议](../../../references/execution-protocol.md)处理。交付连接范围、问题依据、实际处理状态和未完成依赖。

