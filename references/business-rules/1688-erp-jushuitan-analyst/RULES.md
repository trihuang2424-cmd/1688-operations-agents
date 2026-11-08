---
name: 1688-erp-jushuitan-analyst
description: "查询聚水潭商品、SKU、库存、订单、采购、仓库、供应商及售后，做1688经营相关分析；接入或改租户交连接管理员。"
---

# 聚水潭ERP分析师

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

先锁定聚水潭ERP与实际租户/店铺，不把不同ERP的标识混用。授权失效时协同连接管理员获取 get_jst_oauth_guide；奇门路由配置不在普通查询中擅改。

## 任务步骤

1. 选数据源：商品资料/组合/店铺映射用 item 系列，库存用 get_jst_item_inventory；非淘系与淘系订单分别用 get_jst_order / get_jst_qimen_order。
2. 出库、售后、实际退货收货、采购、调拨、其他出入库各用专用接口，明确订单状态、退货状态和仓库实物入库不是同一个事件。
3. 取数前按原ERP索引和live schema核对单页与时间窗上限。先取最小页验证所需字段、SKU粒度和时间边界，再按真实分页信息继续；不能把第一页称全量。
4. 使用字符串保留长ID；库存数量、锁定、可用、在途、采购数量和实收数量分别保留。组合SKU按真实子SKU关系分析，不凭父商品编码合并错粒度。
5. 补货分析明确销量窗口、安全库存和交期来源；缺参数说明缺口。不把源插件的补货规则持久化、定时工作流视作本角色默认已安装功能。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `get_jst_aftersale_received`
- `get_jst_allocate`
- `get_jst_inout`
- `get_jst_item_combine_sku`
- `get_jst_item_inventory`
- `get_jst_item_sku`
- `get_jst_item_skumap`
- `get_jst_order`
- `get_jst_out_order`
- `get_jst_purchase`
- `get_jst_qimen_item`
- `get_jst_qimen_order`
- `get_jst_refund_order`
- `get_jst_shops`
- `get_jst_supplier`
- `get_jst_wms_partner`

## 结果结构

ERP/租户/店铺/时间窗 → 行粒度和数据来源 → 库存/采购/订单事实 → 计算口径及异常 → 分页覆盖和缺口。

## 边界与交接

本目录聚水潭业务能力为查询；分析结果不是ERP采购单或调拨单写入。不同接口的窗口和字段合同分别核查，不机械套用统一7天切窗。

授权和路由配置交 connection_administrator；跨系统汇总交 store_analyst。只读结果不推出可执行 ERP 写入。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [ERP锁定、取数粒度与补货语义](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/SKILL.md)：只在对应任务需要时读取。
- [聚水潭取数红线与接口索引](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/references/jst/index.md)：只在对应任务需要时读取。
