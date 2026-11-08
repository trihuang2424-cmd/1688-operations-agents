---
name: 1688-platform-knowledge
description: "检索与解释1688平台规则及经营知识，保留来源和适用条件；不是店铺经营数据查询入口。"
---

# 1688 平台规则检索

路由：`platform_rules`。按[阶段加载约定](../../../references/context-loading.md)在项目根运行 `python3 scripts/task_context.py --route <ID> --phase <阶段> --role executor`（仅协调用 `director`；条件用 `--condition`），读取本阶段依赖。实际分析、制定业务方案或执行前须完整读取适用 `RULES.md` 及必需来源，摘要不能替代；纯本地恢复、状态检查或回执只读本阶段清单。去重、父子上下文和旧名处理遵循统一约定。

这是当前任务负责人可调用的共享能力，不单设知识岗位。开展平台检索与解释时完整读取[原平台知识规则](../../../references/business-rules/1688-platform-knowledge/RULES.md)及其引用的来源业务规则；若任务来自原 `platform_support` 的知识场景，同时读取[原平台组件与知识规则](../../../references/business-rules/1688-platform-support/RULES.md)以保留该场景的条件。

交付与当前问题对应的规则依据、适用范围和未解决项；涉及数据接口发现或连接维护时按任务路由进入相应能力，不能以共享入口混同流程。

