---
name: 1688-buyer-transactions
description: "按需处理1688买家订单、物流、售后和发票相关事务，逐流程核实身份与操作条件，不替代卖家经营分析。"
---

# 1688 买家采购事务

路由：`buyer_transactions`；按对象加 `order` / `fulfillment` / `aftersales` / `invoice` / `procurement_inquiry` 条件。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

由当前任务负责人按需组织。本入口不把买家事务扩为卖家经营能力；对各工具逐项依原规则和当前定义确定身份。输入包括具体问题、订单或业务对象、身份、目标状态及授权。

| 本次需求 | 完整读取 |
|---|---|
| 订单、采购条件、地址或预览 | [原买家订单规则](../../../references/business-rules/1688-buyer-order-assistant/RULES.md) |
| 物流、催办、运踪或预约 | [原履约物流规则](../../../references/business-rules/1688-fulfillment-specialist/RULES.md) |
| 退款、投诉及相关状态 | [原售后规则](../../../references/business-rules/1688-aftersales-specialist/RULES.md) |
| 发票抬头、金额与申请 | [原发票规则](../../../references/business-rules/1688-invoice-assistant/RULES.md) |

同一业务包内仍按独立流程处理，并按[共用执行协议](../../../references/execution-protocol.md)记录外部动作。逐对象交付真实状态、回执、证据和未完成项。

