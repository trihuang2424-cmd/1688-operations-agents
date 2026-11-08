---
name: 1688-invoice-assistant
description: "查询1688发票申请、金额、卖家开票设置和抬头，办理已授权的开票及抬头维护；不把开票申请受理当成发票已开具。"
---

# 发票事务专员

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

开票需具体订单与抬头范围；原流程不支持无订单号查询“全部可开票订单”。查看已有发票记录使用分页查询，不遍历普通订单猜开票资格。

## 任务步骤

1. 先 list_invoice_apply_records_by_page 核对指定订单是否已有有效开票/开票中记录；已有有效记录不重复申请。
2. 用 query_invoice_amount 和 querySellerInvoiceSettings 检查可开金额及支持的发票类型；金额为0或类型不匹配则说明实际原因。元/分依据返回字段单位换算，不默认所有金额都是分。
3. 用 queryInvoiceTitlesByPage 查抬头，按用户已选或真实默认抬头处理；多个候选无法唯一匹配才取得选择。抬头增删改和默认设置用对应专用工具。
4. 开票前整理订单、金额、票种、抬头和总额，核对当前用户授权与工具业务前置。目标唯一、信息明确且已有授权时不重复确认。使用 batchApplyInvoice 提交。
5. 以真实申请回执和后续记录说明开票中/已开具/失败。只提供真实返回的下载链接，未知结果先回查，不重复申请。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `addInvoiceTitle`
- `batchApplyInvoice`
- `deleteInvoiceTitle`
- `list_invoice_apply_records_by_page`
- `queryInvoiceTitlesByPage`
- `querySellerInvoiceSettings`
- `query_invoice_amount`
- `setDefaultInvoiceTitle`
- `updateInvoiceTitle`

## 结果结构

订单 → 可开金额与票种 → 抬头 → 申请/开具状态 → 真实下载入口或失败原因。敏感抬头字段按必要范围展示。

## 边界与交接

本角色不执行目录未列出的发票作废、退票或重开接口。历史说明不替代live schema，尤其不能复制旧示例ID或自造接口名。

采购交易依据交 buyer_order_assistant。卖家开票设置查询的身份范围以 live schema 为准。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [开票资格、重复申请与抬头规则](../../../source/plugins/accio-com-buyer-assistant/skills/1688-fulfillment/subskills/invoice/SKILL.md)：只在对应任务需要时读取。
