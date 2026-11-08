# 采购、询盘、分销与履约迁移规则

本说明依据 `source/remote-plugins/1688-purchasing-assistant/1688-purchasing-assistant/` 0.0.9 及买家插件已安装副本。业务意图可迁移；原宿主命令、协议和鉴权字段不能直接照搬。调用与授权遵循 [共用执行约定](runtime.md)。字段以当前 `describe_tool` 为准，2026-10-25 的完整 Schema 快照见 [live-tool-schemas.json](../catalog/live-tool-schemas.json)。

## 找货、找工厂、榜单

- 旧名 `ali_1688_source_suppliers_infos` 在当前目录对应 `1688_source_suppliers_infos`；按名称发现并读取 Schema 后调用，不能拼旧接口地址。供应商商品词用中文；翻页保存关键词和真实页码。
- 原 `1688-product-find` / `1688-sourcing` 把 `tags="4306497"` 用于严选品池，当前快照 `find_product` 接受 `tags`。仅在执行这一原技能的严选品池流程且最新 Schema 仍接受时保留；普通找货需求不能无依据增加用户未要求的筛选。普通默认返回 10、原比价流程召回 20 后确定性筛选；用户明确数量优先，受工具实际限制约束。
- 普通图片找同款走 `find_product`；用户明确要求分销图搜才进入 `same_img_offer_search`。链接搜索用真实商品 ID 或官方详情返回的图，不臆造图片 URL。
- 原后处理脚本负责字段映射和排序，选择运行前确认它只接收已取得的数据，不启动旧 HTTP/认证后端。英文报告需要语言参数和动态标题译文，数字、币种、商品 ID、链接保持原值。静态 HTML 的询盘或铺货按钮依赖原宿主，复制文件不等于按钮已接通；交付时标明可用范围。
- `leaderboard_tools` 当前使用 `param` 对象。`queryType` 按 DISCOVERY / CATEGORY / ITEM / SCENE / KEYWORD / LEADERBOARD / SUB 选择；取商品时 `includeItems=true`。`subLimit` 控子榜数，`topN` 控每个榜商品数，`pageNo` 不是子榜翻页。继续下钻用真实 `subName`。只读查询不能被当成榜单编辑能力。

## 询盘与商品分销

- `1688_procurement_digital_human_tool` 创建对外采购询盘。原协议要求中文 `offerName`、纯数字字符串 `count`、中文 `demand`，当前 Schema 还可含 `imageUrl`。数量单位在需求中保留语义，不把单位放进数字字段。参数完整不代表自动取得发送授权；用户明确要求发询盘且范围完整时可沿用授权，单纯找货/比价不能触发发布。
- 分销候选先 `distribution_offer_info` 核对品牌和渠道；`isBrandOffer=true` 且 `isBrandAuth=false` 的商品不可进入铺货提交。`shop_and_tool_info` 结果用于选出未过期工具和有效店铺，不用显示名称猜 `shopCode`、`appKey` 或渠道。
- `distribute_offer` 按已明确的商品、目标店铺、工具与渠道执行。信息变更需补齐对应决定，既有明确授权不重复询问。商品查询不是铺货成功，任务受理不是完成。
- `fx_query_order` 是分销订单范围；`fx_send_ww` 会向商家发消息，需用户明确的消息发送授权；`fx_ww_reply` 查询同一任务回执。只读催发建议不得顺手发送。
- 第三方大泽/店小宝/DSers 的发布接口是独立能力，不能用名称相近的 1688 分销接口冒充；见 [现行分销能力入口](../.agents/skills/1688-distribution/SKILL.md)。

## SKU 与下单确认

- 当前目录可发现 `get_order_skills_config`、`offer_sku_query_batch`、`query_address_list`、`order_view`、`query_order`、`buyer_query_order_list`。先读取当前 Schema，拿真实规格、价格、库存、数量限制、地址和预览，不由模型猜 SKU 索引、金额单位或地址对象。
- 原 `1688-order` 的 `fetch_and_confirm`、widget、`renderId` 回调、`agentSessionId` 和 Accio app/device 字段属于宿主集成。Codex 不天然提供这套协议，不伪造 `ACCIO_DESKTOP` 身份或参数；若接口必须依赖缺失的宿主字段，应明确该步骤未接通。可用独立工具完成的查询继续进行。
- 采购预览必须来自工具。返回 `orderFormUrl` 时保留完整原值，不拼接参数、不把旧链接冒充本次链接；用户在真实确认页完成下单与支付。生成预览或付款链接不能宣称已下单/已付款。
- 若已有受支持的原确认回流，须验证 `renderId` 的会话归属与消费状态；未知或重复回流不可重提。原确认组件对 SKU 组合超过 100 要求用户分批；此限制用于对应组件，不冒充所有 1688 API 的通用上限。
- 买家插件移植版默认 `mcp_backend=accio`，原采购包可能带 `aegis` 路径；本项目不为运行归档源码自动下载/安装旧后端、读取 Token 或直连业务服务。

## 售后、物流、发票与 DSers 履约

- 1688 与 Alibaba.com 的订单/退款路由分开。退款单、运单、订单 ID 的渠道来自本次工具或上下文；名称相似不混用接口。退款申请/修改/取消、投诉/取消、退货回填、催发催揽、开票及官方物流寄件分别按对应子 Skill 和最新 Schema 确定效果。
- 保存与发送只针对用户明确的订单、项目、数量、原因和内容。结果不明时先查当前状态，不重复申请退款、取消、发送或创建订单。
- DSers 中 Sales Order（销售渠道订单）、Supply Order（供应商采购单）、Seller Fulfillment（回写销售渠道履约）、Shipment（包裹物流）是不同对象。创建采购任务或付款链接不等于支付/发货/履约完成。
- DSers 的 1688 Dropshipping 付款链接待支付时可能临时隐藏订单；供应商下单后台处理中也可能暂时隐藏。沿用原任务或付款链接核对，不能把暂时不在列表中当成失败后重新下单。
- SKU Mapping 连接店铺变体与供应商变体，需核对 Ship-to-country、数量、BOGO/Bundle。全局 Mapping 可能影响未来订单，订单级供应商修改只影响指定订单；后来的 Mapping 不能追溯修改已经提交的采购单。
- 当前 205 项目录没有 DSers 专属工具。上述规则用于方案与后续适配；接入经过验证的 DSers 连接器之前，不能声称已完成其写操作。
