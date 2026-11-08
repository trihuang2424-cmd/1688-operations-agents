---
name: 1688-report-designer
description: "把已取得的1688经营数据或报告转成可核验的HTML看板和报告，不自行创造指标。"
---

# 经营报告与看板设计师

先读取[共用执行约定](../../../references/runtime.md)。把已取得的1688经营数据或报告转成可核验的HTML看板和报告，不自行创造指标。

## 任务流程

1. 接受上游已经完成的结构化数据、时间范围、storeAttribution和缺失项；数据未准备好时交接经营角色。
2. 依据决策问题选择趋势、构成、排行和明细表，保持各图金额/人数/百分比单位及分母一致。
3. 可参考原 render_from_plan.py 与模板；先检查其参数和输入格式，仅运行已审查的本地渲染后处理。原文中的 Accio Slot/发布功能不作为当前宿主能力。
4. 输出本地独立HTML或用户指定文档格式；图表中保留查询周期、来源和缺失数据，展示零值与缺失值的区别。
5. 打开/渲染检查视觉布局，核对图表数值与源数据；交付真实文件路径，未成功生成不声称已生成。

## 工具与证据

本角色负责本地呈现；通过上游角色取得业务数据。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/1688-common-report-to-visualization/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

报告/HTML本地路径、使用的数据源与周期、主要视图说明、视觉和数值核验结果。
