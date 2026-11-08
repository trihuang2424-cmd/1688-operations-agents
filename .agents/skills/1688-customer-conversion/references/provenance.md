# 来源、迁移差异与验证边界

适配日期：2026-10-28，Asia/Shanghai。原业务规则、上游文件和历史报告保持原样；本目录为当前宿主补充执行适配，不是服务端算法源码或 Accio 页面副本。仅使用现有 MCP 桥接，不复制前端 bundle、客户库、Cookie、Token、签名或授权凭证。

## 可追溯依据

| 依据 | 本次用途 |
|---|---|
| [客户管理规则](../../../../references/business-rules/1688-crm-manager/RULES.md)、[触达规则](../../../../references/business-rules/1688-outreach-operator/RULES.md) | 原有业务前置、权限、脱敏与交付规则 |
| [上游客户筛选](../../../../source/plugins/1688-seller-assistant/skills/1688-shop-crm-customer-filter/SKILL.md) | 金额与时间口径、字段映射、查询预算、地区与手机号限制；只读研究，不执行其 CLI 指令 |
| [上游触达流程](../../../../source/plugins/1688-seller-assistant/skills/1688-shop-aicrm-segment-reach-strategy/SKILL.md)、[运行合同](../../../../source/plugins/1688-seller-assistant/skills/1688-shop-aicrm-segment-reach-strategy/references/active-contracts.md) | 三类动作、话术模式、券面校验、独立渠道选择、真实回执及重复执行保护；不移植 Slot/AW/私有 CLI |
| [上游 crm-cli.js](../../../../source/plugins/1688-seller-assistant/scripts/crm-cli.js) | 100 人约束、先圈选、互斥动作、部分建成和未知结果处理；源码存在不代表该命令可在本宿主执行 |
| [调查报告](/Users/shileqi/Documents/ChatGPT/jacky/outputs/accio-customer-ops-2026-10-28/调查报告.md)、[接口证据](/Users/shileqi/Documents/ChatGPT/jacky/outputs/accio-customer-ops-2026-10-28/api-evidence.json)、[计划证据](/Users/shileqi/Documents/ChatGPT/jacky/outputs/accio-customer-ops-2026-10-28/plan-evidence.json) | 2026-10-28 的只读统计、字段、筛选与计划结果及工具 Schema；历史证据不作为当前业务状态 |
| [前端证据](/Users/shileqi/Documents/ChatGPT/jacky/outputs/accio-customer-ops-2026-10-28/frontend-evidence.md)、[历史工具快照](../../../../catalog/live-tool-schemas.json) | 区分页面、宿主与工具能力；参数示例依据，执行时仍须 live describe |

## 已登记的适配差异

| 差异 | 当前处理及未验证部分 |
|---|---|
| 原流程要求 CLI、Slot、组件存储及独立确认 | 当前宿主用结构化文本、已有授权与执行记录承接；不声称有原 900 秒组件计时、不可重复点击锁或自动历史恢复。缺少具体发送授权时完成可审阅方案后再询问 |
| 来源筛选 CLI 内置手机号与地区保护，桥接直接暴露业务工具 | 在查询选择、用户输出、文件和交接处保留同等限制；不把直调当作绕过来源规则的许可 |
| 创建计划的 Schema 写 `target.mode=filters`，上游 crm-cli 转为 `filter` | 两者并列保留，执行前核对 live 契约，不通过写请求试探；示例选已验证字段结构的 ids 模式 |
| 上游超 100 人的建议包含“地区” | 仍保留原文；本 CRM 查询规则明确禁止地区筛选，不采用该项建议，改列金额、活跃等合法条件供用户选择，不自行分拆 |
| 触达 Schema 的行动点中文说明把 script/coupon 反写 | 以 `actionParams` 明确契约和上游组件共同证据区分：script 仅 text，coupon 为 text 加满减；执行前 live 核验，不按错写说明互换 |
| 上游组件解码 LOGINID 后实发，本项目要求包装原样传递 | 不自动移植解码；执行前核验 live 标识契约，只有包装值且兼容性未明确时报告缺口，不向真实客户试发 |
| 前端有 updateConfig、短信、自动模式，聊天工具有独立 Schema | 不能把前端参数直接传给 MCP；当前未验证的配置更新、短信资质、调度时刻与恢复机制分别记录，不承诺已支持 |
| 属性新增工具描述提到 attrKey/指定买家，快照仅暴露 attrLabel/attrType/value | 以 live 暴露参数为准，不虚构参数；成功后回读真实键及作用范围 |

调查已验证只读统计、字段、示例筛选和现有计划查询。本次安装再次只读核验统计和计划查询，记录在[安装期联通证据](../../../../reports/2026-10-28-customer-operations-skill/live-verification.json)；计划创建/变更、画像刷新、话术生成、导入、打标、属性新增与实际触达没有因此完成或通过端到端验证。工具目录可见与 Schema 校验只证明可发现、可按契约准备。

尚未获得平台高意愿/流失评分公式、系统计划完整圈选算法、跨来源匹配去重实现、内部模型与计费细则、自动调度服务端源码。本 skill 复用云端业务能力与本地编排，不宣称离线复制这些服务，也不包含截图中可嵌入的完整 MCP App 界面。
