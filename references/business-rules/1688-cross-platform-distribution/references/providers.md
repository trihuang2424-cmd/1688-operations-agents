# 服务差异与原始依据

原始文件是业务依据，执行能力仍由实时宿主决定。不要把原协议里宣称“已连接”的文字当成当前会话证据。

## 大泽

原 Skill：[daze-cli-batch-publishing](../../../../source/remote-plugins/daze-store-manager-cli/skills/daze-cli-batch-publishing/SKILL.md)。

- 原 `dzgj` 仅支持首版验证过的国际站目标；每批 1～20 条商品 URL。不能列出后端授权店铺，也不能独立查询模板；本地默认店名不是授权证明。
- 原 CLI 默认线上发布，因此必须明确选择“上架”或“保存草稿”，执行时显式 `publishType` 对应 1 或 2，不能让默认值替用户决定。
- 本次预览绑定店铺、逐条货源链接及发布方式；复用已明确的用户授权，不把独立默认店铺确认重复加在总确认前。
- 已返回任务继续查同一 `taskId`。网络不确定时先核对同一幂等键/任务，不重新发一批。没有稳定会员状态查询接口，不把未知业务错误推断成会员问题。

## 店小宝

原 Skill：[dxb](../../../../source/remote-plugins/dxb/dxb/skills/dxb/SKILL.md)；独立图片操作：[dxb-image](../../../../source/remote-plugins/dxb/dxb/skills/dxb-image/SKILL.md)。

- 支持目标平台以实际店铺返回为准。按当前账号列店铺；只有一家可按用户范围使用，多家须确定目标，不能发到所有店铺或偷用旧默认店铺。平台身份来自 `ptName` / `ptNameZn`，不从店名推测。
- 1688是货源平台，不等于国际站目标。Amazon需真实站点和UPC豁免/GTIN信息；国际站特定发货地按原规则收集。用户纠正时保留既有链接，只修正受影响字段。
- 原工具会由服务端判断货源 URL 支持情况，不凭自制域名名单拒绝用户提供的有效来源，也不因未知来源而假称可发布。
- 记录提交响应实际 `storeName` 与任务ID，后续查同一目标。认证在对应连接器完成，本项目不复制用户密文。

## DSers

原 Skill 目录：[DSers skills](../../../../source/remote-plugins/dsers-dropshipping-pro/dsers-dropshipping-pro/skills)。按任务读取 `product-research-skill`、`product-management-skill`、`product-listing-optimization`、`product-pricing-skill`、`product-publishing-skill`、`supplier-mapping-skill`、订单或物流对应 Skill。

- 发布仅针对已选的 Pre-published Products，单次上限100，目标需实际连接且支持发布；CSV店铺不是发布目标。预览按“商品×店铺”，使用真实默认设置，Shipping Profile只能读取/选择已有配置。
- `active`和销售渠道分别验证。定价规则、商品内容、发布、供应商映射是不同变更，不能一次授权混写。保存定价或映射前显示实际差异。
- Mapping 对应店铺SKU→供应商SKU，核对国家、数量、BOGO/Bundle；AI建议生成不等于已经保存。保存后回读，不因结果不明重复保存。
- 分清 Sales Order / Supply Order / Seller Fulfillment / Shipment。付款链接、任务受理、物流号同步的回执各有不同含义；临时隐藏订单沿原任务查验，不重下单。
- 原 MCP地址是 `https://ai.dsers.com/mcp`，这只是包内声明；不能由URL存在推断账号已授权或工具已经可调用。
