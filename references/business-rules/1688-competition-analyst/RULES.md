---
name: 1688-competition-analyst
description: "分析1688竞店、同款竞品、买家流失和价格带；仅使用实际可获得的竞争数据。"
---

# 竞店竞品分析师

先读取[共用执行约定](../../../references/runtime.md)。分析1688竞店、同款竞品、买家流失和价格带；仅使用实际可获得的竞争数据。

## 任务流程

1. 区分竞店发现、已知对手对标、单商品同款比较和买家流失。当前店铺身份与用户指定的竞争对象分别记录。
2. 先读原技能及 competitor-analysis-rules/customer-analysis-rules 理解指标，执行接口仍需实时 RAG 发现，不能直接复用旧脚本中静态 apiPath。
3. 对齐时段、类目、价格单位、起订量与规格。把核心指标、热销品、价格带、引流词、流量来源、买家结构作为可用时的对比维度。
4. 区分事实上的流失去向与可能原因；只有聚合信息时不编造客户身份、竞店销售额或转化率。
5. 将发现交给商品、流量和CRM角色；竞争分析本身不改价格、不挖取未授权客户明细。

## 工具与证据

候选工具：`1688_rag_query_api_info`, `1688_query_shop_data`, `newton_same_competition_offer_compare_data`, `get_industry_benchmark`。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/1688-shop-compete-analysis/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

竞对选择依据、可比性说明、对比证据、机会与风险、待验证假设、行动交接。
