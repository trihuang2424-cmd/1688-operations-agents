---
name: 1688-business-analysis
description: "分析1688单日日报、完整周/月销售对比、长周期经营与成本利润，并呈现已取得的经营数据；按任务分别读取统计口径和报告规则。"
---

# 1688 经营分析

路由：`daily_metrics`、`period_analysis`、`profit_analysis`、`report_rendering`。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

本能力由运营总控负责；需要独立取数或较重分析时依委派约定交给有限范围的分析任务，不恢复日报、利润、报表等旧岗位。输入包括店铺、问题、目标日期或周期、现有数据及预期交付。

| 本次需求 | 完整读取 |
|---|---|
| 店铺经营、长周期、健康与退款口径 | [原经营分析规则](../../../references/business-rules/1688-store-analyst/RULES.md) |
| 指定单日或默认昨日的日报 | [原日报规则](../../../references/business-rules/1688-daily-report/RULES.md) |
| 收入、退款、成本与利润核算 | [原成本利润规则](../../../references/business-rules/1688-profit-analyst/RULES.md) |
| 已取得数据的HTML、图表或报告呈现 | [原报告呈现规则](../../../references/business-rules/1688-report-designer/RULES.md) |

多种需求分别加载适用模块，不因工具相同省略统计口径。总控亲自做经营分析也使用 `--role executor`；仅将商品/流量事项交接出去时，使用 `director` 清单，不先读取领域规则。

周/月复盘在计划或评估阶段按[完整周期与比较基线](../../../references/sales-growth-workflow.md#完整周期与比较基线)及[经营结论](../../../references/sales-growth-workflow.md#经营结论)形成销售变化结论，再决定逐链接行动。恢复相关[对象状态](../../../references/operating-state.md)，沿用固定基线与既有观察条件；缺失不补零，相关变化不强行归因。取数和解读涉及广告时加 `ads` 条件，读取[广告经营决策修正规则](../../../references/ad-decision-policy.md)，其限定修正优先于来源中的相反条款。

固定日报/周报/月报使用[本地报告模板与渲染说明](references/report-templates.md)，沿用既有版式更新真实数据，保留区间、截止、店铺、口径、缺失项与行动状态。渲染器只校验呈现，不取数或计算经营指标，不执行输入代码。日报仍为单日 T+1；周报支持明确指定的历史区间；月报仅用 Asia/Shanghai 划分且取数时已结束的完整自然月。周/月取数须支持对应区间，不能套用日报接口。非标准报告或完整文稿可视化按原报告呈现规则处理。
