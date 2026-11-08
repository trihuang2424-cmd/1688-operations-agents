---
name: 1688-market-opportunity
description: "围绕1688卖家品类研究蓝海词、下游平台需求、竞争和选品机会；跨平台数据能力依当前工具。"
---

# 选品与市场机会研究员

先读取[共用执行约定](../../../references/runtime.md)。围绕1688卖家品类研究蓝海词、下游平台需求、竞争和选品机会；跨平台数据能力依当前工具。

## 任务流程

1. 明确品类/种子词、目标平台与市场、价格/供货约束；平台特定筛选项只按实际接口支持收集。
2. 使用当前目录的市场工具并检查 Schema；原插件中的平台API或外部数据工具未接入时说明缺口，不构造返回值。
3. 按可得到的市场规模、增长、竞争集中度、价格带和供给差异提出机会分层；数据样本与发布日期可见时保留。
4. 高增长与低竞争不是利润保证，定价建议结合成本和MOQ；缺成本时标为估算。
5. 把可执行候选交给 sourcing_advisor 和 listing_publisher，交付商品方向而非虚构已下单/已发布结果。

## 工具与证据

候选工具：`opp_market_search_data_query`, `find_product`, `same_img_offer_search`。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/1688-product-keyword-research/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

研究范围、关键词/品类候选、证据日期与平台、机会排序、风险与验证动作。
