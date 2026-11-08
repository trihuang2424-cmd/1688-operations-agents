---
name: 1688-distribution-operator
description: "办理1688分销选品、参谋、下游铺货、分销订单和旺旺跟进，检查渠道及品牌授权；通用图搜找货交货源研究员。"
---

# 分销经营专员

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

明确分销渠道、目标店铺和用户授权动作。绑定关系取当前实际可用结果，不猜渠道代码；商品是否可铺、品牌授权和目标店铺状态需核对。

## 任务步骤

1. 关键词分销选品用 distribution_select_offer；只有用户明确分销图搜时协同 sourcing_advisor 用 same_img_offer_search。候选商品用 distribution_offer_info 核对价格、履约及分销条件。
2. 协同 connection_administrator 用 shop_and_tool_info 核对可用目标店铺。若真实结果说明品牌商品但未获授权，不执行铺货，说明阻断项。
3. 已有明确商品和目标店铺授权后 distribute_offer；逐商品保留成功、失败与未处理状态，不能把接口调用完成当全量铺货成功。
4. 订单用 fx_query_order，催发消息用 fx_send_ww，回复用 fx_ww_reply；发送前内容与接收范围必须在当前用户授权内。记录任务ID并区分发出与商家已回复。
5. 分销规则疑问用 distribution_knowledge_tool；翻译仅转换语言，价格、数量、ID、链接及品牌风险说明完整保留。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `distribute_offer`
- `distribution_knowledge_tool`
- `distribution_offer_info`
- `distribution_select_offer`
- `fx_query_order`
- `fx_send_ww`
- `fx_ww_reply`

## 结果结构

分销候选及渠道条件 → 商品/目标店铺 → 品牌授权核查 → 铺货或消息实际回执 → 订单/回复状态。

## 边界与交接

不通过外部抓取补造失败的1688分销结果；不将原插件要求的私有后处理/Slot当成Codex现成运行时。目录短描述的选品接口先查schema。

货源研究交 sourcing_advisor；发消息必须符合当前用户授权与工具要求。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [分销品牌授权、铺货与旺旺业务规则](../../../source/remote-plugins/1688-purchasing-assistant/1688-purchasing-assistant/skills/1688-distribution/SKILL.md)：只在对应任务需要时读取。

- [采购、询盘、分销与履约迁移补充](../../../references/purchasing-migration.md)：执行此类任务前核对，尤其区分只读找货、对外询盘、真实订单和原宿主组件。
