---
name: 1688-procurement-research
description: "按需研究1688货源、供应商与企业背景，合并检索入口并完整保留找货、图搜和背调各自业务规则。"
---

# 1688 采购与供应商研究

路由：`procurement_research`；按模块加 `sourcing` / `company` 条件。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

这是由当前任务负责人按需使用的采购研究能力。输入包括采购目标、商品或供应商线索、规格数量、市场与供货约束、授权及交付要求。

| 本次需求 | 完整读取 |
|---|---|
| 找货、图搜、供应商与采购研究 | [原采购研究规则](../../../references/business-rules/1688-sourcing-advisor/RULES.md) |
| 企业主体与背调报告 | [原企业背调规则](../../../references/business-rules/1688-company-due-diligence/RULES.md)；来源于采购研究时同时保留采购模块的相关要求 |

共享背调入口只统一调用组织，不省略任一来源的适用条件。有差异时并列保留并核验。报告提交等操作结合[共用执行协议](../../../references/execution-protocol.md)，交付真实候选、证据、报告状态及未完成项；后续订单进入[买家采购事务](../1688-buyer-transactions/SKILL.md)。

