---
name: 1688-market-research
description: "为1688商品运营分析竞店竞品与市场选品机会，按竞争比较和需求机会分别加载原有规则。"
---

# 1688 竞争与市场研究

路由：`competition`、`market_opportunity`。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

本能力由商品运营负责。输入为当前商品或品类、对比对象或种子词、目标市场、周期及经营约束；按任务选择下列模块。

| 本次需求 | 完整读取 |
|---|---|
| 竞店、同款、价格带与买家流失分析 | [原竞争分析规则](../../../references/business-rules/1688-competition-analyst/RULES.md) |
| 关键词、下游需求、品类与选品机会 | [原市场机会规则](../../../references/business-rules/1688-market-opportunity/RULES.md) |

按各模块交付证据、可比性、候选机会和待核实事项。后续采购、新品或流量工作按当前任务路由交接，分析结果不自行扩大为其他业务动作。

