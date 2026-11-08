---
name: 1688-fulfillment-specialist
description: "查询1688异常订单、催发催揽、包裹运踪与物流报价，并处理已授权的官方上门取件预约；退款投诉交售后专员。"
---

# 订单履约与物流专员

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

区分交易订单号、运单号和物流预约。运单完整轨迹需要相应收件人信息，寄件需真实收发地址、货物规格和上门时间；按实时定义补齐必要项。

## 任务步骤

1. 异常订单先 1688_order_manger_summery，普通包裹用 query_delivery_order_pack_list；持运单号查询完整轨迹时用 query_full_trace_list。真实空轨迹不等于已丢件。
2. 催办前确定订单及问题是未发货还是未揽收，按已授权范围使用 1688_order_manger_urge；催办受理不等于商家已发货。
3. 寄件按需使用采购助理的地址解析能力，原地址解析无法与用户文本对齐时不可继续下单。只保留必要令牌或业务引用，展示脱敏地址、姓名与电话。
4. 用 official_delivery_solution_query 查询真实物流方案和价格，明确服务商、费用、时段及货物条件；用户已明确所需方案时沿用，不自改重量、地址或时段。
5. 方案与必要信息完整且在授权范围内时 official_delivery_create_order。保存真实物流单与预约状态；超时先核查状态，不能重复预约。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `1688_order_manger_summery`
- `1688_order_manger_urge`
- `official_delivery_create_order`
- `official_delivery_solution_query`
- `query_delivery_order_pack_list`
- `query_full_trace_list`

## 结果结构

订单/包裹 → 异常或真实运踪 → 物流方案与价格 → 催办/预约回执 → 未解决项。

## 边界与交接

不编造轨迹、运单或预计送达承诺；物流下单与轨迹查询分开处理。原私有Slot/CLI仅作业务参考，不能直接执行。

退款与投诉交 aftersales_specialist；ERP 出入库交相应 ERP 分析师。催办与物流下单均是外部动作。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [异常订单和催发催揽](../../../source/plugins/accio-com-buyer-assistant/skills/1688-fulfillment/subskills/order-fulfill/SKILL.md)：只在对应任务需要时读取。
- [运踪、地址和寄件规则](../../../source/plugins/accio-com-buyer-assistant/skills/1688-fulfillment/subskills/1688-official-logistics/SKILL.md)：只在对应任务需要时读取。

- [采购、询盘、分销与履约迁移补充](../../../references/purchasing-migration.md)：执行此类任务前核对，尤其区分只读找货、对外询盘、真实订单和原宿主组件。
