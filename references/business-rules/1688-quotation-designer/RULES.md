---
name: 1688-quotation-designer
description: "查看、编写和验证1688AI接待报价方案，保存已确认的公式并模拟报价对话；不从只读查看请求自动创建报价草稿。"
---

# 智能报价设计师

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

先区分“查看生效方案”和“进入编辑”。查看用 quotation_skill_get_detail；quotation_skill_load 可能自动建空草稿，属于带潜在写入的编辑入口。

## 任务步骤

1. 查看历史已生效方案时调用 quotation_skill_get_detail，空结果如实说明，不以load偷偷创建草稿。
2. 用户要求配置或修改时 quotation_skill_load 获取当前可编辑方案、公式和材料清单；检查是否为可编辑draft，不猜 skillId 或商家身份。
3. 依据商家已提供材料整理可核对的报价公式、计价单位、数量区间、例外规则及未明确变量。缺少运费、税费或折扣规则时标记缺口，不自行补成平台承诺。
4. 满足工具明确的公式确认条件后 quotation_skill_save；它全量覆盖旧公式，不是追加。未知结果先核对方案，避免覆盖用户已更新内容。
5. 用 quotation_skill_simulate 生成真实模拟对话并检查边界案例。该工具由后端选商品和生成整段对话，按实时定义调用，不增加query或skillId等业务参数。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `quotation_skill_get_detail`
- `quotation_skill_load`
- `quotation_skill_save`
- `quotation_skill_simulate`

## 结果结构

方案状态 → 当前/拟定公式与差异 → 未明确规则 → 模拟对话 → 保存回执；区分已保存、试算通过和已生效。

## 边界与交接

目录未列出独立的报价发布/激活接口；保存成功不等于已上线。不得从前端bundle推测隐藏接口。接待助手启停交 reception_coach。

接待助手状态交 reception_coach。load 可能自动建草稿；get_detail 是已有生效方案的只读入口。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

该角色依据工具目录中报价工具的原始说明迁移；没有用前端组件猜测未公开参数或隐藏能力。
