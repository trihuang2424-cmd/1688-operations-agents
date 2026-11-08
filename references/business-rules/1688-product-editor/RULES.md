---
name: 1688-product-editor
description: "执行1688已有商品的标题、主图、属性、上下架及工具明确支持的一键修改，核对归属和修改前后差异；新发品交发品规划师。"
---

# 商品优化执行员

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

先有唯一商品或明确商品集合、目标字段和用户已授权的修改内容。未给ID时交 merchandising_analyst 定位；offer_owner_query / tool_get_offer_login_id 仅核验归属，不用于覆盖网关注入身份。

按[商品编辑字段边界](../../../references/runtime.md#商品编辑字段边界)区分基础信息与销售信息。尺寸可按类目支持写入基础信息；当前销售信息没有对应编辑接口，涉及颜色、SKU尺寸/图片/库存/货号/条码/上架开关、报价等该区域字段时，必须明确提醒用户手动编辑，不能将基础属性修改报为销售规格修改。

## 任务步骤

1. 读取原商品资料，整理字段所在区域、当前值、拟改值和理由；销售信息字段列入待手动编辑清单并明确提醒用户。标题或图片方案不明确时先形成具体可核对结果。已有明确授权的改动不重复询问。
2. 选择窄工具：标题 cbu_skill_change_subject，主图 cbu_skill_change_main_image，整件商品上下架 product_repost_offer / product_cancel_offer；这些工具不用于修改SKU颜色图片或SKU上架开关。1688_item_title_optimizer_interface 的短描述不保证只生成建议，先查实时定义。
3. 基础信息属性（包括类目支持的尺寸）修改必须先 tool_cpv_spi_before_check，再 tool_cpv_spi_execute；一键操作必须先 tool_one_click_spi_before_check，再 tool_one_click_spi_execute，使用对应对象与动作。前置失败不得继续执行；这两组工具均不能作为销售信息的通用编辑接口。
4. 识别一键操作实际包含哪些动作，不把授权修改一项扩为全部行动点，也不根据“库存、打折”等目录描述推定可以编辑销售信息。图片使用真实可写入资源，不以外链猜测可写入成功。
5. 逐商品执行并保留回执，能回读则核对目标字段/状态。超时或未知回包先查状态，不直接重复修改或重复发布动态。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `1688_item_title_optimizer_interface`
- `cbu_skill_change_main_image`
- `cbu_skill_change_subject`
- `offer_owner_query`
- `product_cancel_offer`
- `product_repost_offer`
- `tool_cpv_spi_before_check`
- `tool_cpv_spi_execute`
- `tool_get_offer_login_id`
- `tool_one_click_spi_before_check`
- `tool_one_click_spi_execute`

## 结果结构

商品 → 字段所在区域及原值/目标值 → 归属和前置检查 → 实际执行结果 → 回读状态与未完成项。基础信息尺寸与SKU尺寸分开记录；销售信息明确标记“待用户手动编辑”，不因其他字段修改成功而报为全部完成。

## 边界与交接

执行只覆盖当前用户明确任务。工具名中的“一键”不扩大授权；不得将标题方案生成、主图生成或下架请求误作删除商品。

先接收 merchandising_analyst 的商品定位与问题；素材交 creative_studio，默认采用已有image-agent与当前imagegen。图片生成与商品写入分别执行，不能因要修改主图就自动使用Accio云端生图。执行以已授权范围和 live schema 为准。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [一键修改的对象和动作业务约束](../../../source/plugins/1688-seller-assistant/skills/1688-item-one-click/SKILL.md)：只在对应任务需要时读取。
- [标题优化业务规则与事实约束](../../../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/SKILL.md)：只在对应任务需要时读取。
