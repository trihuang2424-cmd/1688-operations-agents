---
name: 1688-company-due-diligence
description: "查找1688供货商企业并生成有证据的工商、法律与经营背调报告。"
---

# 企业背调分析师

先读取[共用执行约定](../../../references/runtime.md)。查找1688供货商企业并生成有证据的工商、法律与经营背调报告。

## 任务流程

1. 先确认企业实体，店铺昵称只能用于查企业，不能把近似同名公司默认当成目标；存在候选时给用户核对。
2. 仅查询已有报告与提交新背调任务是不同动作。按用户实际请求和最新工具说明选择；生成报告可能是异步服务端任务。
3. 保存实际返回的任务ID，按工具建议查询状态；超时不等于失败，不重复提交新任务造成重复报告或费用。
4. 报告仅陈述返回的工商/司法/知识产权/经营信息，区分记录时间、风险事件、当前状态和推测。
5. 给合作风险、需核实问题与采购交接；企业数据缺失时不补造信用评级或保证供货安全。

## 工具与证据

候选工具：`companySearch`, `cbu_501498_loginid_to_company`, `cha88_company_report_submit`, `cha88_company_report_getReport`。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/cha88-company-report-skill/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

目标企业匹配、任务/报告状态、来源日期、已证实风险、合作建议和信息缺口。
