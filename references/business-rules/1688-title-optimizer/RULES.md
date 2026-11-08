---
name: 1688-title-optimizer
description: "优化1688商品标题与关键词，并在用户授权范围内应用确认的标题。"
---

# 商品标题优化师

先读取[共用执行约定](../../../references/runtime.md)。优化1688商品标题与关键词，并在用户授权范围内应用确认的标题。

## 任务流程

1. 用户给了商品ID则直接定位；只有描述时先用店内关键词查询候选，避免凭空挑商品或把全部商品当作已授权批量范围。
2. 读当前标题、类目、事实属性和用户偏好，区分仅出方案与实际修改；用户仅想比较标题时停留在方案。
3. 生成保留真实材质、用途、规格的候选，不杜撰认证、品牌授权或极限效果。标题生成接口可能触发服务端生成，先按真实描述确认任务范围。
4. 给出旧标题→新标题及改动理由；用户已经明确指定范围和应用内容时直接按工具规则执行。调用需要 before_check 的执行路径必须先通过检查。
5. 逐项核实返回并尽可能回读；批量部分失败保留每件商品状态，不无差别重试整批。

## 工具与证据

候选工具：`cbu_offer_query_tool`, `tool_search_offer_by_keyword`, `1688_item_title_optimizer_interface`, `cbu_skill_change_subject`, `tool_one_click_spi_before_check`, `tool_one_click_spi_execute`。

执行前读取实时 `describe_tool`；静态[完整Schema](../../../catalog/live-tool-schemas.json)和[工具路由](../../../catalog/tool-routing.json)用于查找。

按需阅读[Accio原始工作流](../../../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/SKILL.md)保留业务规则。其私有CLI、workflow、卡片和调用名称仅为来源，实际执行遵循当前宿主与共用约定。

## 交付

商品链接、原标题/建议标题、关键词理由、已应用或仅草稿状态、回读与失败项。
