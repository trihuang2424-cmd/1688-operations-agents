---
name: 1688-erp-inventory
description: "按实际连接查询聚水潭或吉客云ERP商品、库存、订单与成本等数据，保留各系统授权、字段和统计口径。"
---

# 1688 ERP与库存数据

路由：`erp_inventory`；按实际系统加 `jushuitan` / `jackyun` 条件。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

由当前经营任务负责人按需使用，不为每个ERP分别建立常驻角色。输入需包含业务问题、实际连接系统、店铺或租户、对象与时间范围。

| 实际系统 | 完整读取 |
|---|---|
| 聚水潭 | [原聚水潭规则](../../../references/business-rules/1688-erp-jushuitan-analyst/RULES.md) |
| 吉客云 | [原吉客云规则](../../../references/business-rules/1688-erp-jackyun-analyst/RULES.md) |

两套规则保留各自适配，不相互套用。连接问题进入[连接与平台维护](../1688-platform-maintenance/SKILL.md)；库存预警同时遵守[库存预警字段与校验](../../../references/stock-warning-contract.md)。交付数据覆盖、系统与对象对应、统计口径、原始证据和未完成项，供商品或投流判断使用。

