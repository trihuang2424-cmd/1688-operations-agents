# AI接待配置师：兼容能力入口

旧角色标识：`reception_coach`。当前负责人：`operations_director`；能力：`customer_conversion`。此入口保留旧项目路径，不再定义一个独立常驻岗位。

1. 先读[当前任务路由](/Users/shileqi/1688运营agents/catalog/task-routing.json)、[注册与旧名映射](/Users/shileqi/1688运营agents/catalog/agent-registry.json)及[执行约定](/Users/shileqi/1688运营agents/references/runtime.md)。
2. 按当前[能力技能](/Users/shileqi/1688运营agents/.agents/skills/1688-customer-conversion/SKILL.md)处理任务，并完整读取[本入口保留的业务规则](/Users/shileqi/1688运营agents/references/business-rules/1688-reception-coach/RULES.md)及其中按条件引用的源业务规则。规则中的旧角色名按legacy_aliases解释；业务步骤、数值、前置和免责声明不因岗位合并而改变。
3. 在总控中使用该能力时按[交接协议](/Users/shileqi/1688运营agents/references/delegation.md)委派；用户已单独打开本目录或当前已被委派执行该能力时，直接完成本任务，不递归启动同一角色或额外总控。
4. 多对象修改与观察状态按[共用执行协议](/Users/shileqi/1688运营agents/references/execution-protocol.md)处理。读取技能不等于启动子Agent；只报告真实委派及真实执行。

仅此组织入口更新。原业务规则已逐字保留，见[完整性清单](/Users/shileqi/1688运营agents/manifests/routing-refactor-20261028-preservation.json)。
