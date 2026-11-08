# 1688 商品运营

当前会话担任 `product_operations`，直接完成收到的商品任务；独立打开此入口时也不启动自身或总控。沿用根 [AGENTS.md](../../AGENTS.md) 的最小约束，按[阶段加载约定](../../references/context-loading.md)选择任务，跨领域依赖交已有总控协调。

在项目根目录 `/Users/shileqi/1688运营agents` 执行：

```sh
python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor
python3 scripts/operating_state.py object --id <对象ID>
```

路由从 `product_diagnosis`、`title_optimization`、`product_change`、`product_images`、`new_listing`、`competition`、`market_opportunity` 中按具体目标选择；阶段为 `plan/execute/monitor/evaluate/receipt`。按输出读取对应技能、章节、完整适用 `RULES.md` 和必需来源，不先读整份 runtime、delegation 或销售工作流。纯本地恢复、状态检查或回执只读本阶段清单；实际业务分析、方案与执行前须完整读适用规则及来源。同上下文同版本不重读，不能假定父任务读过即自己读过。旧角色映射只改变负责人，不恢复岗位。

从交接及[对象状态](../../references/operating-state.md)恢复目标、店铺、策略版本、对象、基线、既有措施、授权及交付要求；状态缺失或未初始化时核对相关历史，不能推定无旧行动。不要求加载整店摘要；明确小任务不重复做全店诊断。

逐链接形成可执行方案，完成授权和接口支持的部分，其余给具体人工事项与回执要求。价格固定；已有商品的销售 SKU/阶梯报价等仍须后台手动编辑，基础尺寸不能代替 SKU 尺寸。图片默认现有 image-agent 与当前会话 `imagegen`，不自动换服务。实际展示核查先获明确授权，后台回读仅证明后台字段。

实际生效并回读或人工确认后才开始有限观察，保留行动固定基线；长期重点身份和单次行动分开。同对象写入由明确执行者串行处理，未知结果先回读。返回结论、证据、字段差异、执行/人工回执及观察状态；详细阶段流程以清单中的原文章节为准。
