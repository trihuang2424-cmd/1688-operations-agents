---
name: 1688-product-operations
description: "负责1688商品诊断、标题关键词、属性优化与图片任务；经营优化制作真实成品供审核，获批后按范围应用、回读和评估。明确只查证或只方案时按该范围交付。"
---

# 1688 商品运营

路由：`product_diagnosis`、`title_optimization`、`product_change`、`product_images`；新品和市场任务用下表对应入口。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

`product_operations` 直接处理交接或独立会话中的具体商品任务，不再启动本角色或总控。输入为目标、真实店铺引用、商品范围、策略版本、既有措施、授权及交付要求；用[对象状态](../../../references/operating-state.md)恢复相关记录，不要求读取全店历史。

| 本次需求 | 完整读取 |
|---|---|
| 商品定位、诊断、筛查、库存预警 | [原商品诊断规则](../../../references/business-rules/1688-merchandising-analyst/RULES.md) |
| 标题与关键词方案 | [原标题规则](../../../references/business-rules/1688-title-optimizer/RULES.md)；应用时进入 `product_change` 并读原商品编辑规则 |
| 已有商品属性、标题、图片或状态修改 | [原商品编辑规则](../../../references/business-rules/1688-product-editor/RULES.md)；执行阶段加载[执行协议](../../../references/execution-protocol.md) |
| 图片方案、生成、编辑、上传或应用 | [原视觉制作规则](../../../references/business-rules/1688-creative-studio/RULES.md)及[现有 image-agent 入口](../../../agents/image-agent/AGENTS.md) |
| 竞品与市场研究 | [竞争与市场研究](../1688-market-research/SKILL.md) |
| 新商品素材、草稿或发布任务 | [新商品准备与发布](../1688-listing-publisher/SKILL.md) |

销售增长任务承接总控的经营结论或公司重点产品立项；明确小任务按指定范围直接执行。计划与执行阶段读取[逐链接执行与人工交接](../../../references/sales-growth-workflow.md#逐链接执行与人工交接)，交付具体改动、依据、可执行部分和人工待办，不能停在泛泛建议。价格固定；已有商品的销售信息/SKU 仍须手动编辑，基础信息尺寸不能代替 SKU 尺寸，详见[商品编辑字段边界](../../../references/runtime.md#商品编辑字段边界)。

图片默认采用现有 image-agent 的当前会话 `imagegen` 路径；沿用用户明确选择的服务，失败不自动换后端。实际页面核查按根规则先取得明确授权，后台回读不证明买家展示正常。

按[决策与阶段交付](../../../references/sales-growth-workflow.md#决策与阶段交付)核对任务交付类型；支持的路由传 `--deliverable`。本店正常经营或投放优化中，有较明确信号支持标题、主图或详情改动时，按[成品审核与应用](../../../references/sales-growth-workflow.md#成品审核与应用)交实际标题/详情文稿及所需图片，简述原因和预期改善；用户批准具体版本后直接完成已核实接口支持的应用、必要上传、回读与观察，不增加同版本的执行审批。纯取数、本地规则维护及用户明确只查证/只方案/不生成/不应用时按该范围完成。

拟做图片试验先检查可取得的现图、真实商品和随货配置，记录已看过的素材及未核实项；网页展示核查沿用既有授权要求。成品交真实文件、版本与检查证据，设计说明不算图片；缺素材或生成能力时说明已尝试来源、精确缺项及可继续部分，交回总控协调，不把制作工作转交用户。详情先交完整成品，再按实时定义核实写入能力；不支持的部分交具体人工材料与回执要求。涉及投放或拉新效果时复用交接中的全店成交及新/老/未知拆分，按[拉新分析](../../../references/acquisition-analysis.md)保留关联缺口。新版行动交回前运行 `operating_state.py check --id <行动ID> --require handoff`，业务执行前核对 `--require execution`。

监测、评估或接收生效回执时加载[两类观察](../../../references/sales-growth-workflow.md#两类观察)：保留单次行动 `action_id`、固定基线与长期重点 `focus_id`，实际生效回读或人工确认后才启动有限观察。同一证据不重复修改；行动完成不取消重点身份。向总控返回方案、人工事项、执行/确认回执、证据与观察状态，跨领域依赖交回协调；同对象写入由明确执行者串行完成。
