---
name: 1688-listing-publisher
description: "将图片或Excel资料准备为1688商品素材包、草稿或实际接口支持的发布任务，保留发品流程、预测核对和异步状态。"
---

# 1688 新商品准备与发布

路由：`new_listing`。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

本能力由商品运营直接执行；先确定资料、商品范围、期望状态及授权。开展资料准备、预测或发布业务前完整读取[原发品规则](../../../references/business-rules/1688-listing-publisher/RULES.md)及必需来源。新商品准备、草稿、发布和已有商品修改分别确认接口与状态。

| 本轮阶段 | 按需加载与交付 |
|---|---|
| 计划/执行 | [逐链接执行与人工交接](../../../references/sales-growth-workflow.md#逐链接执行与人工交接)：素材、预测待核字段、可执行步骤与人工事项；写入/异步提交加载[执行协议](../../../references/execution-protocol.md) |
| 图片制作 | [原视觉制作规则](../../../references/business-rules/1688-creative-studio/RULES.md)和[现有 image-agent 入口](../../../agents/image-agent/AGENTS.md)的相关技能；默认当前会话 `imagegen`，不自动替换用户服务 |
| 生效回执/监测/评估 | [两类观察](../../../references/sales-growth-workflow.md#两类观察)，恢复相关[对象状态](../../../references/operating-state.md) |

销售增长上新承接经营结论或公司重点立项；重点产品不必等待全店下滑，新品缺少历史成交不阻塞资料准备。沿用公司确定的价格，资料不足先完成可做部分。人工事项须给字段现值/目标值、步骤、素材、负责人或待认领状态及完成回执要求；新字段没有现值时如实标明。

逐商品交付真实素材、草稿、任务或发布状态及失败项。草稿和待人工发布不算上线，发布前置、已有商品的销售信息编辑边界及实际页面核查授权继续有效。实际生效并回读或人工确认后，才启动 `action_id` 的有限观察；新品可用有证据的真实零基线。长期 `focus_id` 与单次上新分开，保留供货事实与观察条件交总控衔接推广，不凭同一证据重复动作。
