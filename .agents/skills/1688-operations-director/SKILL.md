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
| 询盘聊天记录查询或导出 | `chat_export`，复用客户技能的[聊天导出契约](../1688-customer-conversion/references/chat-export.md) |

经营周期、链接方案、观察和投流按加载器输出的[销售增长流程](../../../references/sales-growth-workflow.md)执行。周/月按全店及核心商品曝光、点击率、新客有效询盘、成熟询盘成交定位问题，同时明确整体成交额及新/老/未知拆分；身份与指标见[统一获客口径](../../../references/acquisition-analysis.md)。公司重点产品可按明确目标立项。将目标、策略版本、对象、数据周期、既有行动、授权与预期交付传给执行者，不把全部历史复制给每个子任务。

按[决策与阶段交付](../../../references/sales-growth-workflow.md#决策与阶段交付)确定本轮 `evidence/plan/asset/execution`；有交付契约的路由传 `--deliverable`，把该契约与当前用户范围交给执行者。本店正常优化中有依据的商品动作按[成品审核与应用](../../../references/sales-growth-workflow.md#成品审核与应用)续接制作，不能以“建议改图”收尾；用户批准具体版本后接续应用。明确只查证/只方案等任务仍在指定范围交付。新版行动运行 `operating_state.py check --id <行动ID>`，交接用 `--require handoff`、执行前用 `--require execution`、收尾用 `--require closure`；按就绪状态推进，不把报告、待制作物料或未知生效计作完成。

询盘日常检查按分析协议每轮 `ingest` 扫描到期项；领取前核对策略、同对象问题及全部关联措施，取消或替代无必要的 pending，已派发/未知先对账。没有新证据或仍在正常观察时不重复派单；分析不包含客户维护、触达或销售催办。

按[统一经营验收](../../../references/sales-growth-workflow.md#决策与阶段交付)确认首要问题、必要验证、当前决定和关键依赖；领域报告完成不等于主任务完成，可自行推进的关键依赖由总控续接。核对已选择的商品改动是否已有真实成品。正文先给简短效果/原因/决定及待审对象，过程明细放附录。实际执行、后台回读、人工待办及效果观察分别记录；单次 `action_id` 完成不结束长期 `focus_id`。按[状态契约](../../../references/operating-state.md)保存证据；只有真实启动才能报告已委派。按需使用 `operations_review` 独立复核，不增加常驻角色。
