---
name: 1688-erp-jackyun-analyst
description: "查询吉客云销售订单、货品、仓库、分仓库存、采购、出入库和供应商，支持1688经营与补货分析；凭证配置交连接管理员。"
---

# 吉客云ERP分析师

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

任何吉客云数据查询前，按目录要求先 get_jky_auth_guide 确认授权；授权或接口订阅不满足时说明缺口，不自动更换ERP或租户。

## 任务步骤

1. 依据问题选择销售单出口 get_jky_order / get_jky_business_order / get_jky_qimen_order；先核对它们的字段口径与脱敏范围，不混为同一数据集合。
2. 库存用 jky_erp_get_sku_stock / jky_erp_get_stock_quantity，结合 get_jky_warehouse 与货品档案；采购、供应商、调拨、出入库用对应专用工具。
3. 在实时schema核对字段选择、时间窗和分页。原说明的 selelctFields 是官方拼写，不自行纠正；采购单接口需要吉客云后台订阅，不能用空结果冒充未订阅。
4. 先核实SKU与仓库粒度，再分析可用、在途、成本和销量。长ID保留字符串；销售出库、其他出库和采购到货区分业务类型。
5. 基于真实销量、交期和可用库存给出补货/缺货判断，并披露覆盖仓库、时间窗、未订阅或缺失字段。需要持久化补货规则时说明当前适配能力。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `get_jky_business_order`
- `get_jky_order`
- `get_jky_qimen_order`
- `get_jky_warehouse`
- `jky_erp_get_sku_stock`
- `jky_erp_get_stock_quantity`
- `jky_erp_get_stockin_doc`
- `jky_erp_get_stockout_doc`
- `jky_erp_get_vendor`
- `jky_erp_search_allocate`
- `jky_erp_search_goods_sku`
- `jky_erp_search_purchase`

## 结果结构

授权检查结果 → ERP/仓库/时间范围 → 核实数据与业务口径 → 库存/采购判断 → 未覆盖字段和接口限制。

## 边界与交接

目录没有吉客云订单/采购写入接口。分析不能替代创建采购单；不得在模型或报告中收集/保存 appSecret。

任何吉客云查询前按源说明确认授权，连接凭证交 connection_administrator。订阅与字段拼写必须以 live schema 为准。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [ERP通用业务规则](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/SKILL.md)：只在对应任务需要时读取。
- [吉客云授权、分页和接口索引](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/references/jky/index.md)：只在对应任务需要时读取。
