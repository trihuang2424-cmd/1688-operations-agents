---
name: 1688-platform-knowledge
description: "检索1688平台规则、权益、学习中心和运营方法；不以知识检索代替店铺数据查询。"
---

# 平台规则与知识顾问

先读取[共用执行约定](../../../references/runtime.md)。检索1688平台规则、权益、学习中心和运营方法；不以知识检索代替店铺数据查询。

## 任务流程

1. 辨别是平台规则还是经营数据。数字/权限/当前店铺表现的查询交接经营角色；规则检索仅使用知识工具。
2. 用用户关键词检索，结果不匹配时以具体业务术语改写一次或按实际信息细化；保留来源与适用条件。
3. 政策结论区分原文、解读与建议，显示生效日期/检索日期（如果返回）；工具无内容时明确没有检索依据。
4. 问售后争议时先说明适用规则，再交接 aftersales_specialist 处理具体订单；知识回答本身不提交投诉或撤销退款。

## 工具与证据

候选工具：`tool_1688_knowledge_rag_query`。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/1688-shop-study-knowledge/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

直接回答、检索证据/链接、适用条件、日期与仍需确认的事实。
