---
name: 1688-distribution
description: "按需处理1688分销和用户指定的跨平台采购代发服务，保留各服务适配规则并核验当前真实可用能力。"
---

# 1688 分销与跨平台适配

路由：`distribution`；按服务加 `distribution_1688` / `cross_platform` 条件。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

由当前任务负责人按需使用。输入包含分销目标、商品、目标平台/店铺、用户指定服务、连接状态和授权范围。

| 本次需求 | 完整读取 |
|---|---|
| 1688分销选品、订单或铺货 | [原1688分销规则](../../../references/business-rules/1688-distribution-operator/RULES.md) |
| 大泽、店小宝、DSers等跨平台服务 | [原跨平台分销规则](../../../references/business-rules/1688-cross-platform-distribution/RULES.md)及其引用的服务说明 |

保留各服务的独立参数、条件和任务状态；归入同一入口不代表已接通或允许替换服务。外部动作按原规则及[共用执行协议](../../../references/execution-protocol.md)处理，交付实际服务、对象、任务状态、回执和能力缺口。

