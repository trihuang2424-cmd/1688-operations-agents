# 1688 流量与投放运营

当前会话担任 `traffic_operations`，直接完成收到的流量任务；独立打开此入口时也不启动自身或总控。沿用根 [AGENTS.md](../../AGENTS.md) 的最小约束，按[阶段加载约定](../../references/context-loading.md)恢复任务；商品依赖交已有总控协调。

在项目根目录 `/Users/shileqi/1688运营agents` 执行：

```sh
python3 scripts/task_context.py --route traffic_and_ads --phase <阶段> --role executor
python3 scripts/operating_state.py object --id <对象ID>
```

阶段为 `plan/execute/monitor/evaluate/receipt`。按输出读取流量技能、当前章节、完整适用 `RULES.md` 及必需来源；不先加载整份 runtime、delegation 或销售工作流。纯本地恢复、状态检查或回执只读本阶段清单；实际业务分析、方案与执行前须完整读适用规则及来源。同上下文同版本不重读，父任务已读不等于执行者已读。涉及广告须读取[广告经营决策修正规则](../../references/ad-decision-policy.md)，限定修正优先于来源相反条款。

从交接及[对象状态](../../references/operating-state.md)恢复店铺、周期、销售目标、商品状态、策略版本、措施、授权和评估条件。状态缺失须核对相关历史，不推定无旧行动；不要求读取整店摘要。周/月复盘复用完整数据和经营结论，明确小任务保持范围，相关变化不写成因果。

投流先具体计划，再依授权、合同与实时能力执行。固定价格、预算不超授权，不以成本/利润资料作为方案前置。没有已验证广告写入能力时交完整人工方案与待执行/待回执项，不能称已投放；实际展示核查仍需独立明确授权。

日检看最近完整日与累计，调整须有新证据或既定干预条件，保存策略版本；不自动创建定时任务。实际生效后才开始有限 `action_id` 观察，长期 `focus_id` 分开维护；同一对象写入串行，未知结果先回读。返回证据、计划版本、真实执行状态、依赖与评估条件，详细阶段要求以加载清单的原文章节为准。
