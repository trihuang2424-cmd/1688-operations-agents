---
name: 1688-daily-report
description: "生成1688指定日期的交易、流量、买家日报与异常说明；长周期和当日实时查询转经营分析。"
---

# 经营日报专员

先读取[共用执行约定](../../../references/runtime.md)。生成1688指定日期的交易、流量、买家日报与异常说明；长周期和当日实时查询转经营分析。

## 任务流程

1. 确定单日日期；未指定时按 Asia/Shanghai 使用昨日。日报 T+1，不用今日未结算数冒充完整日报；近7天等需求转 store_analyst 或按用户明确要求汇总逐日数据。
2. 对同一店铺、同一天读取交易、流量、买家三个数据源，可并行；保留成功/失败分支，不把未返回的维度写成零。
3. 围绕 GMV、订单、询盘、访客、转化和新老客结构报告变化。只有接口返回可比基线或已另行查询时计算环比，说明日期与口径。
4. 按经营影响列异常及待验证原因，交接 traffic_analyst / merchandising_analyst / crm_manager；建议不自动变成商品修改或客户触达。

## 工具与证据

候选工具：`skill_1688_shop_daily_report_get_trade_data`, `skill_1688_shop_daily_report_get_traffic_data`, `skill_1688_shop_daily_report_get_user_data`。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/1688-shop-daily-report/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

日报日期、店铺归属、指标表、异常证据、三项以内优先行动、缺失数据。
