# 当前角色与能力索引

更新：2026-10-30。默认3个核心角色，总控即主Agent；旧31个名称作为能力别名保留。业务规则原字节保存，不再按一个技能建立一个岗位。

完整周/月经营诊断与重点产品跟踪按[销售增长运营流程](../references/sales-growth-workflow.md)，月度复盘复用总控，当前任务路由共24条。

## 核心角色

| 角色 | 入口 | 职责 |
|---|---|---|
| 运营总控（主Agent） | [根 AGENTS.md](../AGENTS.md) | 经营目标、周期策略、任务分派、跨域协调、行动观察与结果验收；不再启动总控子Agent |
| 商品运营 | [product_operations](../agents/product_operations/AGENTS.md) | 商品诊断、标题属性方案、图片、新品准备、竞争与市场研究 |
| 流量与投放运营 | [traffic_operations](../agents/traffic_operations/AGENTS.md) | 自然/搜索/推荐/广告渠道分析、行业对照及投放建议；写入能力单独验证 |

复核 `operations_review` 按需运行；`conversion_analysis` 在询盘异常、重要新事实或复查到期时实际委派，复用现有客户技能。两者均不计入三个核心岗位。每日轻量检查由总控按 `conversion_monitoring` 路由完成，详见[分析流程](../.agents/skills/1688-customer-conversion/references/conversion-analysis.md)。这些原生配置没有单独覆盖模型或连接，实际继承由宿主决定；注册文件存在不等于本次已真实启动。

## 能力模块

| 能力 | 负责人 | 技能入口 | 激活方式 |
|---|---|---|---|
| 运营周期管理 | operations_director | [operating_cycle](../.agents/skills/1688-operations-director/SKILL.md) | core |
| 经营分析 | operations_director | [business_analysis](../.agents/skills/1688-business-analysis/SKILL.md) | core |
| 商品诊断与优化 | product_operations | [product_optimization](../.agents/skills/1688-product-operations/SKILL.md) | core |
| 竞争与市场研究 | product_operations | [market_research](../.agents/skills/1688-market-research/SKILL.md) | on_demand |
| 新商品准备与发布 | product_operations | [listing](../.agents/skills/1688-listing-publisher/SKILL.md) | on_demand |
| 流量与投放分析 | traffic_operations | [traffic_analysis](../.agents/skills/1688-traffic-operations/SKILL.md) | core |
| 平台规则检索 | operations_director | [platform_knowledge](../.agents/skills/1688-platform-knowledge/SKILL.md) | shared |
| 连接与平台维护 | operations_director | [platform_maintenance](../.agents/skills/1688-platform-maintenance/SKILL.md) | shared |
| 客户转化 | operations_director | [customer_conversion](../.agents/skills/1688-customer-conversion/SKILL.md) | on_demand |
| ERP与库存数据 | operations_director | [erp_inventory](../.agents/skills/1688-erp-inventory/SKILL.md) | on_demand |
| 采购研究 | operations_director | [procurement_research](../.agents/skills/1688-procurement-research/SKILL.md) | on_demand |
| 买家采购事务 | operations_director | [buyer_transactions](../.agents/skills/1688-buyer-transactions/SKILL.md) | on_demand |
| 分销 | operations_director | [distribution](../.agents/skills/1688-distribution/SKILL.md) | on_demand |
| 商品视觉 | product_operations | [image](../agents/image-agent/.agents/skills/1688-image-design/SKILL.md) | on_demand |
| 经营报告呈现 | operations_director | [reporting](../.agents/skills/1688-business-analysis/SKILL.md) | shared |

## 旧名称兼容映射

30个旧项目入口已逐字移至[归档区](../archive/legacy-agent-entries/README.md)，文件名改为 `ENTRY.md`，不作为当前执行入口。总控入口统一为根 `AGENTS.md`，`agents/` 仅有商品、流量两个领域目录和图片模块；原业务条款引用旧角色名称时，按下表解析责任，不恢复旧岗位。

| 旧角色 | 当前负责人 | 能力 | 保留规则 |
|---|---|---|---|
| operations_director | operations_director | operating_cycle | [原文](../references/business-rules/1688-operations-director/RULES.md) |
| store_analyst | operations_director | business_analysis | [原文](../references/business-rules/1688-store-analyst/RULES.md) |
| daily_report | operations_director | business_analysis | [原文](../references/business-rules/1688-daily-report/RULES.md) |
| profit_analyst | operations_director | business_analysis | [原文](../references/business-rules/1688-profit-analyst/RULES.md) |
| merchandising_analyst | product_operations | product_optimization | [原文](../references/business-rules/1688-merchandising-analyst/RULES.md) |
| title_optimizer | product_operations | product_optimization | [原文](../references/business-rules/1688-title-optimizer/RULES.md) |
| product_editor | product_operations | product_optimization | [原文](../references/business-rules/1688-product-editor/RULES.md) |
| competition_analyst | product_operations | market_research | [原文](../references/business-rules/1688-competition-analyst/RULES.md) |
| market_opportunity | product_operations | market_research | [原文](../references/business-rules/1688-market-opportunity/RULES.md) |
| listing_publisher | product_operations | listing | [原文](../references/business-rules/1688-listing-publisher/RULES.md) |
| traffic_analyst | traffic_operations | traffic_analysis | [原文](../references/business-rules/1688-traffic-analyst/RULES.md) |
| platform_knowledge | operations_director | platform_knowledge | [原文](../references/business-rules/1688-platform-knowledge/RULES.md) |
| connection_administrator | operations_director | platform_maintenance | [原文](../references/business-rules/1688-connection-administrator/RULES.md) |
| platform_support | operations_director | platform_maintenance | [原文](../references/business-rules/1688-platform-support/RULES.md) |
| crm_manager | operations_director | customer_conversion | [原文](../references/business-rules/1688-crm-manager/RULES.md) |
| inquiry_analyst | operations_director | customer_conversion | [原文](../references/business-rules/1688-inquiry-analyst/RULES.md) |
| reception_coach | operations_director | customer_conversion | [原文](../references/business-rules/1688-reception-coach/RULES.md) |
| quotation_designer | operations_director | customer_conversion | [原文](../references/business-rules/1688-quotation-designer/RULES.md) |
| outreach_operator | operations_director | customer_conversion | [原文](../references/business-rules/1688-outreach-operator/RULES.md) |
| erp_jushuitan_analyst | operations_director | erp_inventory | [原文](../references/business-rules/1688-erp-jushuitan-analyst/RULES.md) |
| erp_jackyun_analyst | operations_director | erp_inventory | [原文](../references/business-rules/1688-erp-jackyun-analyst/RULES.md) |
| sourcing_advisor | operations_director | procurement_research | [原文](../references/business-rules/1688-sourcing-advisor/RULES.md) |
| company_due_diligence | operations_director | procurement_research | [原文](../references/business-rules/1688-company-due-diligence/RULES.md) |
| buyer_order_assistant | operations_director | buyer_transactions | [原文](../references/business-rules/1688-buyer-order-assistant/RULES.md) |
| fulfillment_specialist | operations_director | buyer_transactions | [原文](../references/business-rules/1688-fulfillment-specialist/RULES.md) |
| aftersales_specialist | operations_director | buyer_transactions | [原文](../references/business-rules/1688-aftersales-specialist/RULES.md) |
| invoice_assistant | operations_director | buyer_transactions | [原文](../references/business-rules/1688-invoice-assistant/RULES.md) |
| distribution_operator | operations_director | distribution | [原文](../references/business-rules/1688-distribution-operator/RULES.md) |
| cross_platform_distribution | operations_director | distribution | [原文](../references/business-rules/1688-cross-platform-distribution/RULES.md) |
| creative_studio | product_operations | image | [原文](../references/business-rules/1688-creative-studio/RULES.md) |
| report_designer | operations_director | reporting | [原文](../references/business-rules/1688-report-designer/RULES.md) |

[任务路由](task-routing.json)是现行业务入口；[工具目录](tool-routing.json)保留205项快照，不是全部接口已验证可用的承诺。
