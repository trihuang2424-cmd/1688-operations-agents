# 客户库、系统客群与 AI 帮筛

本文件是当前 MCP 桥接的执行适配。进入任务仍须读取[客户管理完整规则](../../../../references/business-rules/1688-crm-manager/RULES.md)及其引用的来源；来源 CLI、AW 和 Slot 仅为研究资料，不在本项目运行。连接、店铺选择和授权遵循[共用约定](../../../../references/runtime.md)。

## 选择查询

| 用户要什么 | 当前候选工具与口径 |
|---|---|
| 客户总量、近 7 天新增 | `customer_stats`；主账号为全店，子账号为自己名下可见客户，写清范围 |
| 截图中的高成交意向、流失预警卡片 | `newton_ai_crm_plan_operation` 的 `operation=query`；读取系统计划、当前客群日期、人数、状态和实际动作配置 |
| 按高意愿、流失风险、金额等条件查人 | `customer_list`；自然语言转换成明确字段条件，与系统计划分别报告 |
| 有多少人符合条件 | `customer_list` 只查最小页，以服务端 `recordCount` 作为匹配总数 |
| 新标签、未知自定义属性 | `customer_attr_field_config`；仅需全部属性定义和生效状态时用 `customer_attr_list_all` |
| 单客画像和跟进 | `customer_ai_profile(action=query)`、`get_followup_record_by_buyer`、`get_order_info_by_buyer` |
| 全店买家画像与新老客构成 | `get_customer_profile`；核对周期和统计口径，不与 CRM 库总人数混用 |

首次业务查询前调用 `bridge_status(check_gateway=true)`，只用网关真实返回的 `store_ref`。按工具名 `search_tools`，再对本次将用的工具 `describe_tool`；以下例子是已核验契约示意，不能代替本轮 live Schema。通过 `call_tool` 调用，不直连前端 HTTP，不注入 `NEWTON_SHOP_LOGIN_ID` 等身份字段。

2026-10-28 的历史调查查到系统计划 `inquiry_convert` 和 `churn_recall`。卡片人数只是该计划的覆盖人数，不是全库“高意愿/流失”字段人数，也不证明评分公式。计划名、ID、人数、日期、配置版本都重新查询，不把调查报告里的 867、100、9 固化为当前值。建议动作存在不等于计划已开启、配置已保存或客户已触达。

## 条件与金额

| 表述 | 字段/含义 |
|---|---|
| 高采购意愿 | `user_interest_level` 为“高意愿”；空值是未评估，不是低意愿 |
| 流失风险 | `lost_status` 为“即将流失”或“已流失”；没有原因字段时不能编造原因 |
| 历史有成交 / 从未成交 | `source=ORDER` / `source=INQUIRY`；从未下单不能用空日期作比较 |
| 近 7 天询盘未转化 | 最近询盘时间在 7 天内，且近 7 天支付订单数 `pay_mord_cnt_1w <= 0`；不是“历史从未成交” |
| 累计、历史、总金额；金额未给周期 | `pay_ord_amt_std_all` |
| 近 30 天、近一个月、近期成交金额 | `recent_30d_purchase_amount` |
| 近 7 天支付/成交金额 | `pay_ord_amt_1w` |

沿用同一追问的金额字段，除非用户改变周期；对用户写明所用口径。只有 `recent_30d_purchase_amount` 是来源规则支持排序的金额字段，累计金额不能冒充其排序。其他可排序字段为 `last_inquiry_time`、`last_order_time`、`gmt_create`，执行前核对 live 定义。

“L3 以上”按来源规则不含 L3，“L3 及以上”包含 L3；在结果说明边界。同字段多值一次 `in` 表达，`in/not in` 的 `value` 是 JSON 数组字符串；跨字段 OR 没有已核验支持，不拆查询后冒充一个精确总人数。`site_flag` 只表示来源，不表示客户质量或是否有效。商家自建“高意向”标签与平台采购意愿不同。

## 已核验参数形态

条件计数的业务 `arguments` 示例：

```json
{
  "pageNum": 1,
  "pageSize": 1,
  "filters": [
    {"field":"user_interest_level","op":"in","value":"[\"高意愿\"]"},
    {"field":"pay_ord_amt_std_all","op":">","value":"10000"}
  ]
}
```

需要有限示例时把 `pageSize` 设为不超过 20，按支持字段增加 `sorts`，如 `[{"field":"last_inquiry_time","order":"desc"}]`。全店统计与字段配置业务参数为 `{}`；店铺选择放在桥接 `store_ref`，不写进自造内部身份字段。系统计划列表的历史已验证查询形态是 `{"operation":"query"}`；指定计划用 `{"operation":"query","planId":"本次真实查询取得的ID"}`，若 live 契约变化先处理差异。

未知属性只查询一次配置，使用返回的真实 `attrKey`，不加 `attr_` 前缀；仅需要确认最新标签时更新配置，不把它作为每次普通查询的固定前置。缺字段时交付缺口，不近似替代。首次成功查询直接使用；明确参数/网络等错误最多按来源规则修正重试 3 次。空结果诊断最多 3 次、每个子条件一次且 `pageSize=1`，不能反复拉原始页探测。

## 画像不等于刷新

查询已有画像：`{"loginId":"本次查询取得的完整客户标识","action":"query"}`。`refresh` 会触发服务商 LLM 重新生成，有配额且耗时，只有用户要求更新/重新生成画像或该动作已明确获授权时使用；读取画像的请求不自动授权刷新。`sellerNote` 仅在刷新生效。画像、跟进摘要和平台标签分别标注来源，不把模型总结当原始事实。

## 交付与数据边界

给出店铺归属、可见范围、时间与金额口径、明确条件、服务端总人数、聚合结论和最多 20 条脱敏示例。没有服务端总数时说明缺失，不能以当前页长度或 `recent7dNewCount` 代替条件人数。

禁止完整客户明细导出及通过分页拼接绕过；不能为报告读取全库后另存完整 JSON/CSV。站内客户 `site_flag=Y` 的手机号必须隐藏；未知来源的联系方式也不要未经核验直接展示。禁止按省、市、区筛选、展示、分析或分组，不能用其他工具或字段绕过。网关直调不带原 CLI 输出保护，执行者须在用户可见表格、文件、日志与交接前应用同样限制。

`LOGINID_..._LOGINID` 在业务内部原样传递，普通回复用脱敏别名；不展示原始回包、认证信息或客户画像原文。筛人完成只产生客群与分析；需要计划或触达再进入[计划与触达](crm-outreach.md)，不能因客户意愿高自动发消息。
