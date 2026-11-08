---
name: 1688-operations-director
description: "统筹1688完整周/月经营诊断、每日运营、逐链接行动与到期评估，持续跟踪公司重点产品，协调商品和流量专员；由当前主Agent担任总控。"
---

# 1688 运营总控

当前主 Agent 承担 `operations_director`，不再启动总控。先用[真实状态摘要](../../../references/operating-state.md)确定本轮对象、到期事项和未知执行，再按[任务路由](../../../catalog/task-routing.json)选择任务；明确小任务直接交对应领域，不先做完整体检。

按[阶段加载约定](../../../references/context-loading.md)运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role director`。此视图供协调与验收使用，不加载待委派领域的规则。总控亲自处理任务时改用 `--role executor`；实际取数、分析、方案或执行前完整读取适用 `RULES.md` 及必需来源，纯本地恢复、状态检查或回执只读本阶段清单。已读同版本可复用，不能把父任务已读当作子执行者已读。

| 本次任务 | 路由/入口 |
|---|---|
| 日常推进、完整周/月复盘 | `daily_operations`、`weekly_review`、`monthly_review`；总控实际开展业务时读[原总控规则](../../../references/business-rules/1688-operations-director/RULES.md) |
| 经营指标、日报、利润或报告 | [经营分析](../1688-business-analysis/SKILL.md)的对应路由与模块；利润不作为本店默认任务 |
| 商品、图片、新品、市场与流量 | 按路由交现有商品或流量领域执行者；交接及真实启动记录按[委派约定](../../../references/delegation.md) |
| 询盘/转化轻量检查 | `conversion_monitoring`；只读状态可不加载业务规则，取询盘/CRM数据前按范围加 `inquiry` / `crm` 条件 |
| 异常、新证据或到期深析 | `conversion_analysis` 实际委派临时专项，见[分析协议](../1688-customer-conversion/references/conversion-analysis.md) |
| 明确客户运营任务 | `customer_conversion`，按[客户运营与转化](../1688-customer-conversion/SKILL.md)选择子模块 |

经营周期、链接方案、观察和投流的详细要求以加载器输出的[销售增长流程](../../../references/sales-growth-workflow.md)原文章节为准。周/月先形成有证据的销售变化结论；公司重点产品可按明确目标立项。将目标、策略版本、对象、数据周期、既有行动、授权与预期交付传给执行者，不把全部历史复制给每个子任务。

按[决策与阶段交付](../../../references/sales-growth-workflow.md#决策与阶段交付)确定本轮 `evidence/plan/asset/execution`；有交付契约的路由传 `--deliverable`，把该契约与当前用户范围交给执行者。验收比较实际产物与要求，继续承接范围内的后续工作；查证或方案任务可正常交付，不因此启动生成或发布。新版行动运行 `operating_state.py check --id <行动ID>`，交接用 `--require handoff`、执行前用 `--require execution`、收尾用 `--require closure`；按对应就绪状态推进或列出精确阻塞，不把报告、待制作物料或未知生效计作完成。

询盘日常检查按分析协议每轮 `ingest` 扫描到期项；领取前核对策略、同对象问题及全部关联措施，取消或替代无必要的 pending，已派发/未知先对账。没有新证据或仍在正常观察时不重复派单；分析不包含客户维护、触达或销售催办。

验收分别确认分析结论、实际执行、后台回读、人工待办及效果观察。人工完成须有真实生效回执；单次 `action_id` 完成不结束长期 `focus_id`。按[状态契约](../../../references/operating-state.md)保存本轮证据和下一步；只有真实启动才能报告已委派。需要独立复核时按需使用 `operations_review`，不增加常驻角色。
