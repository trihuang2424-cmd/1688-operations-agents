---
name: 1688-customer-conversion
description: "查询和导出1688询盘聊天记录，检查询盘与转化变化，维护问题及观察状态；处理客户库、筛选、画像和运营计划，按具体授权进入维护、接待、报价或触达。"
---

# 1688 客户运营与转化

路由：`chat_export`、`conversion_monitoring`、`conversion_analysis`、`customer_conversion`；客户任务按模块加 `crm` / `crm_maintenance` / `inquiry` / `reception` / `quotation` / `outreach` 条件。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

本能力由总控协调。每日轻量监测走 `conversion_monitoring`；需要深入调查时走 `conversion_analysis`，有子代理工具必须实际委派临时专项。聊天记录查询或文件导出走 `chat_export`，只加载对应导出契约，不因导出启动整店或转化诊断。其他明确客户任务沿用 `customer_conversion` 路由。输入包括经营问题、店铺、客户或询盘对象、期间、期望交付和授权范围；路由选择不额外授予维护或触达权限。

业务调用前按加载清单读取[连接和工具](../../../references/runtime.md#连接和工具)；本地状态检查无需连接。优先核对加载结果 `tool_context` 的相关候选，按接口和范围记录成功、缺口与拒绝，不以一次批量失败概括其他能力。真实 `store_ref`、实时 Schema 及来源卡片的业务选择要求继续有效，安装或分析不自动开启计划、发送消息。

| 本次需求 | 完整读取及当前宿主适配 |
|---|---|
| 按日或买家查询询盘聊天、导出聊天明细 | [聊天导出契约](references/chat-export.md)；按当前三项询盘对话查询工具的实时 Schema 取数，核分页、长正文及导出完整性 |
| 每日询盘/转化检查、异常深析、观察到期复查 | [询盘与转化分析](references/conversion-analysis.md)；实际取询盘/CRM数据分别加 `inquiry` / `crm` 条件并读对应完整规则与来源，深析按路由委派 |
| 客户库总览、系统策略卡、高意向/流失预警、AI 帮筛、画像 | [原客户管理规则](../../../references/business-rules/1688-crm-manager/RULES.md) + [查询与筛选](references/crm-query.md)；系统计划还读原触达规则 |
| 标签、自定义属性、客户导入或连接企业系统 | 原客户管理规则 + [客户维护与接入](references/crm-maintenance.md) |
| 人工询盘、业务员表现与转人工分析 | [原询盘分析规则](../../../references/business-rules/1688-inquiry-analyst/RULES.md) |
| AI接待配置、模拟与知识 | [原AI接待规则](../../../references/business-rules/1688-reception-coach/RULES.md) |
| 报价公式、草稿与模拟 | [原报价规则](../../../references/business-rules/1688-quotation-designer/RULES.md) |
| 运营方案、计划状态、话术、优惠券、客户消息或小二提醒 | [原触达规则](../../../references/business-rules/1688-outreach-operator/RULES.md) + [计划与触达](references/crm-outreach.md)；需圈客再读查询模块 |

业务类型共同归入一个入口不改变各自身份、数据和操作条件；多流程任务完整读取对应模块。写入、创建或发送按原规则和[共用执行协议](../../../references/execution-protocol.md)处理。交付各流程证据、已完成动作、状态和交接项。

## 日常分析入口

每日运行先读既有问题、措施与真实数据截止，再做轻量只读检查；有异常、重要新证据或复查到期才进入专项深析。采用[分析协议](references/conversion-analysis.md)及[本地状态工具](../../../references/conversion-state.md)保存同一问题的后续证据、观察条件和真实委派记录。队列请求不等于已启动子 Agent，读到的同一批数据不算新证据。

缺少报价、跟进、样品或线下成交记录时标记未知；新询盘尚未成熟时先观察，不能判成转化失败。默认只读分析不生成每日销售催办、不联系客户、不更新画像/标签、不创建或开启计划，也不修改接待配置或报价。需要这些动作时，按具体任务与已有授权进入下方原模块；这些能力和原规则继续保留。角色约束与本地状态校验不是网关硬权限隔离。

## 客户运营的常用入口

- “打开客户运营 / 看客户库”：只读查询 `customer_stats` 与 `newton_ai_crm_plan_operation(operation=query)`，交付店铺归属、观察时间、库统计、系统/自建计划及真实状态；按需补充最多 20 条脱敏客户示例。没有返回的数值记未知，不能填零。
- “看看高成交意向 / 流失预警”：若指现有卡片，查真实系统计划的 `planType/strategyCode/customerCnt`；若是自由找客，用 `customer_list` 的字段筛选。系统计划覆盖人数不等于全库同类客户总数，平台评分公式不可见。
- “帮我筛近 7 天新买家、采购意愿高、L2 以上”：解析成真实字段、时间范围和比较边界，服务端筛选并用返回总数；金额区分累计、7 天、30 天。不按省市区筛选或分析，不全量导出客户，不分页拼接规避上游限制。这里是客户库范围；用户明确要导出询盘聊天时另按 `chat_export` 的实时工具与范围处理，不把两类数据权限互相泛化。
- “给这批客户做运营方案”：先明确客群/现有计划，准备渠道、内容、券面和数量；新建计划、生成内容、开启计划、实际发送分别按具体授权执行。用户已有充分授权不重复索取；仅安装/查看/分析不构成发送授权。
- “查看跟进效果”：从真实计划回执区分触达/回复/成单客户人数和执行次数，成功受理不等于送达；未知结果先核验同一计划及稳定请求 ID，不能盲目重发。

## 总览文件

需要截图式概览或留档时，用 [离线快照说明](references/snapshot.md) 和 `scripts/crm_snapshot.py` 将查询结果生成白名单 JSON 与静态 HTML。脚本不联网、不执行业务、不显示完整客户记录、不自动刷新；输出必须带店铺和观察时间。普通问答可直接交付表格，无需每次生成文件。

接口差异、来源版本及实测边界见[来源与能力边界](references/provenance.md)。平台系统人群、画像生成与调度继续依赖服务端；不能把本地技能或静态页面描述为离线预测模型、已运行的日常自动营销或完整 MCP App 副本。

