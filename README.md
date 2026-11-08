# 1688 运营 Agents

浙江淞泰科技账号当前以**提升销售额、固定产品价格、优先新品推广及链接流量/转化**为阶段目标，暂不开展利润优化。首次业务运行、策略变化或约束不清时核对[本店当前阶段策略](references/account-strategies/songtai-sales-growth.md)，其余任务承接已确认版本。

2026-10-30起采用[销售增长运营流程](references/sales-growth-workflow.md)：**完整周/月比较 → 销售变化结论 → 逐链接优化或上新 → 直接执行/人工方案 → 生效后观察 → 到期评估**。公司重点产品另设长期跟踪，有投流时先做计划、按条件执行并每日检查。周报主对比前4周同星期完整周、辅比上周；月报比较前一完整自然月，并列总量和日均。新增月度复盘路由、[记录模板](references/templates/sales-growth-records.json)、[周期窗口计算](scripts/period_windows.py)和[月报输入模板](.agents/skills/1688-business-analysis/assets/monthly-input.json)。这些是执行流程及本地辅助能力，真实商品清单和经营台账需按具体任务建立，未开启定时任务或真实投放。

本项目将1688运营组织收敛为三个核心角色：**运营总控、商品运营、流量与投放运营**。总控的唯一入口是项目根目录 [AGENTS.md](AGENTS.md)，由根项目当前主 Agent 承担；商品和流量任务按需实际委派；复核及客户转化、ERP、采购等专项按需使用，不再为每项技能设置一个常驻岗位。

本次调整职责、入口和路由，完整保留从 Accio 迁移的业务规则原文及已有图片资产；用户已授权的限定规则修正按下文入口执行。每日/每周运营的状态衔接与变更检查已有文档协议，询盘转化另有本地问题状态和请求去重模块。**按用户要求暂不开定时任务**；该模块的 JSON 文件锁不等于全项目状态数据库、业务执行锁或统一执行网关。

合并清单的当前落实状态、31个旧角色逐项去向及实施后测试见[清单落实与测试结果](reports/2026-10-28-consolidation-completion/清单落实与测试结果.md)。原方案文件保留历史状态，当前执行仍以本项目路由和能力入口为准。后续补齐的目录清理及复测见[旧角色目录清理结果](reports/2026-10-28-legacy-entry-cleanup/旧角色目录清理结果.md)。

## 开始使用

在 Codex 中打开 `/Users/shileqi/1688运营agents`，或使用：

```sh
codex -C '/Users/shileqi/1688运营agents'
```

例如：“分析昨天经营情况，结合既有观察任务决定今天应做什么”“检查这批标题调整的效果，样本不足时先保持”“分析流量变化并给出投放策略”。根 [AGENTS.md](AGENTS.md) 规定执行入口；明确的小任务直接交对应领域，不强制做全店体检。

也可以单独打开 [商品运营项目](agents/product_operations/AGENTS.md) 或 [流量运营项目](agents/traffic_operations/AGENTS.md)，由当前领域会话直接执行。总控统一从项目根目录进入，原独立总控入口已[归档](archive/director-entry-20261029/README.md)。30个旧项目入口已移到[归档区](archive/legacy-agent-entries/README.md)，旧名仍通过注册表映射至新负责人和能力；`agents/` 只保留商品运营、流量运营两个领域目录和 `image-agent/` 图片模块，不在旧位置保留软链接。`skills/` 仍是 `.agents/skills/` 的快捷链接，不是第二套技能。

## 按需读取与运营状态

启动由短根入口和[真实状态摘要](references/operating-state.md)组成。总控选择任务，领域执行者才加载具体业务规则；[加载说明](references/context-loading.md)和路由的阶段清单区分方案、执行、监测、评估、人工回执。规则原文不变，选中模块完整读取，连接/数据/编辑字段等共用规则按原文章节取得。

```sh
python3 scripts/operating_state.py summary
python3 scripts/task_context.py --route title_optimization --phase plan --role director
python3 scripts/task_context.py --route title_optimization --phase plan --role executor --read
```

账本缺失时明确未初始化，并要求首次真实运营先核对历史；不会生成虚构商品、授权或销售结果。`due`扫描全部未结事项后分页，`object --id 对象ID`读取相关记录。询盘问题继续使用原转化状态，只保存引用。实际执行和到期结论由执行者按证据写入账本，摘要动态生成；这些本地工具不查询店铺、不自动派单、不开启投放或定时任务。

## 客户运营

[客户运营与转化 skill](.agents/skills/1688-customer-conversion/SKILL.md) 已接入 Accio 客户库、系统高成交意向/流失预警计划、自然语言筛选、画像、运营计划和按授权触达流程，沿用 `customer_conversion` 路由及原规则。可直接说：

- “查看客户运营总览，看看高意向和流失预警客户的情况。”
- “筛选近7天新增、采购意愿高、L2以上的客户。”
- “给流失预警计划准备一版跟进方案和话术。”
- “查看这个计划的触达、回复和成单情况。”

也可显式调用 `$1688-customer-conversion`。需要留档时可生成带店铺、观察时间和真实计划状态的静态总览页；页面本身不联网、不发送消息。业务查询依赖运行中的 Accio 与已连接的 `accio-1688` MCP；系统人群评分和画像服务继续来自云端。安装不会开启自动营销，短信、服务端定时调度和真实触达效果仍须按具体任务验证。原询盘、接待和报价功能保留在同一 skill 中，按需加载。

实现、验证和恢复范围见[客户运营安装记录](reports/2026-10-28-customer-operations-skill/安装与验证.md)。

每日运营现在包含[询盘与转化检查](.agents/skills/1688-customer-conversion/references/conversion-analysis.md)：总控先看概览和既有状态，有异常、重要新证据或复查到期才实际委派 `conversion_analysis` 临时专项。它复用客户技能，不增加核心岗位。缺少报价/寄样/跟进或线下成交记录记为未知；未成熟线索和观察中的措施继续等待既定条件，同一问题不会因为第二天仍存在就重复派单。默认只做读取和建议，不联系客户、不改客户数据、不发送每日销售催办；原显式客户运营功能继续保留。

[本地状态工具](references/conversion-state.md)保存问题、证据、观察与请求，区分待调度和真实已委派，提供幂等输入及该状态文件的事务锁。同一问题支持多项措施分别跟踪；每轮检查所有未结问题的到期条件，缺少新数据也会安排补证复查；未派发请求可取消或替代，领取前核对当前上下文。过程承诺超时与成交成熟度分别判断。它不读取实时店铺数据、不自动启动子 Agent、不执行客户或商品操作；本轮只完成模块及离线验证，首次真实运行还需核对历史报告和已有行动。

## 路由、能力与规则

| 内容 | 位置与作用 |
|---|---|
| 任务路由真源 | [task-routing.json](catalog/task-routing.json)：`routes[]` 指定每项任务的负责人、委派策略、能力、技能和规则 |
| 核心角色、能力及旧名映射 | [agent-registry.json](catalog/agent-registry.json)：`agents`、`skills`、`legacy_aliases` |
| 当前能力入口 | `.agents/skills/`，按任务加载，不把所有业务规则塞进三个大提示词 |
| 原业务规则 | `references/business-rules/<原技能名>/RULES.md`：逐份保留原31份技能业务文本及来源引用 |
| 实际委派 | [delegation.md](references/delegation.md)：主Agent/领域会话、真实启动ID、交接、失败接管和验收 |
| 持续运营 | [operating-cycle.md](references/operating-cycle.md)：策略、三类基线、问题/措施、观察期及每日/周度衔接 |
| 询盘转化状态 | [conversion-state.md](references/conversion-state.md)：本地问题合并、观察/复查、请求去重和实际委派登记 |
| 变更执行 | [execution-protocol.md](references/execution-protocol.md)：结构化变更单、前置检查、未知结果、回读和外部改动 |
| 共用约束 | [runtime.md](references/runtime.md)：连接、实时Schema、授权、图片、商品字段、数据口径等 |
| 来源差异登记 | [rule-questions.md](references/rule-questions.md)：具体原文、来源、场景、待核问题及用户已授权的限定裁决 |
| 广告规则修正 | [ad-decision-policy.md](references/ad-decision-policy.md)：商家止损选项、产出比零值和评估周期；列明范围内优先于原文 |
| 固定日报／周报／月报 | [报告模板用法](.agents/skills/1688-business-analysis/references/report-templates.md)：复用输入模板和本地HTML呈现，统计截止与取数时间分别记录 |
| 人工阅读索引 | [AGENT-INDEX.md](catalog/AGENT-INDEX.md)、[role-design.md](catalog/role-design.md) |

旧交接名称仅通过 `legacy_aliases` 改变组织去向。来源规则的步骤、参数、前置条件、适用范围、必要交互、提示和免责声明继续保留；不因没有本店实测删除来源公式或预估。预估与实际观测分开标记。有差异或宿主适配疑问的条款保留原文、来源和待核验项，不在合并时静默改写。2026-10-29用户已授权修正的广告条款按[广告经营决策修正规则](references/ad-decision-policy.md)执行，原文继续用于追溯；其他条款不受影响。历史报告、方案及源档案用于追溯，不是当前执行入口。

## 持续运营如何衔接

每轮先查询当前状态摘要和相关对象，核对有效策略版本、已执行措施、观察状态和上次运行结果，再获取必要的新数据。新聊天通过持久记录继续工作，不依赖完整聊天历史。优先使用任务指定记录位置；未指定时沿用 `reports/`，首次运行按周期协议建立状态记录并引用现有证据。

问题仍然存在，不等于今天要再次修改。执行中的措施保留固定基线、有效样本和数据成熟条件；数据没有更新或样本不足时记录原因与下一次评估条件，到期必须重新审视，不能无限等待或自动判失败。周检更新策略及优先级，但不清零仍在观察的措施。

每日报告分别说明实际动作、继续观察、效果结论和受阻项；保持现状也可以是合理决策。未来配置每日/周度独立定时任务时，应连接同一持久记录，并处理重叠运行和中断恢复。本次重构本身没有开启这些自动化。

## 执行能力与边界

店铺业务使用当前已连接的 Accio 1688 MCP 网关，使用期间保持 Accio 登录并运行，首次使用核对连接及店铺。模型和工具访问由当前宿主提供，角色说明不构成权限沙箱；读取技能或工具目录不等于实际启动专员，也不等于业务接口执行成功。

图片默认沿用 [image-agent](agents/image-agent/AGENTS.md)：Codex负责设计、提示词与验收，实际生成使用当前会话 `imagegen` 内置路径。用户明确选择其他服务时沿用选择，默认后端缺失或失败不自动切换。仅依据用户素材制作图片无需Accio连接；查询店铺、上传图片银行或应用商品再使用对应业务工具。既有图片设计、编辑、概念技能及模板保留。

已有商品基础属性与销售信息仍分开。当前SKU规格、颜色图片、SKU库存、阶梯数量和价格等销售信息没有对应编辑接口，需要在1688后台手动处理；基础尺寸写入不等于SKU规格已改变。后台回读不证明实际页面展示，展示效果优先由用户人工核查；代为使用展示核查工具须先按根规则取得具体范围的明确同意。

流量与投放角色保留策略判断，但尚未核实可用的广告写入接口前，不承诺自动建计划或调预算。客户转化、库存、成本和履约信号继续保留；CRM、接待、报价、触达分别遵循原规则，采购退款不能冒充卖家退款总盘。ERP入口可共享，聚水潭与吉客云的适配不能混用。跨平台源码不等于已接通对应服务。

## 来源档案与历史快照

以下为2026-10-25的提取和能力盘点成果，保留供业务核验；不是当前工具可用性或已完成业务动作的声明。

| 历史内容 | 位置与说明 |
|---|---|
| 官方卖家插件 | [原始源码](source/plugins/1688-seller-assistant/README.md)：技能、CRM子专家、CLI、工作流、测试与资源 |
| 官方采购与第三方插件 | `source/remote-plugins/`：1688采购、大泽、DSers、店小宝；下载提取不等于执行接入 |
| 本地相关插件和专家 | [LOCAL-SOURCES.md](source/LOCAL-SOURCES.md)：采购、选品、跨平台依赖和1688专家定义 |
| 桌面应用提取 | [EXTRACTION.md](source/desktop/EXTRACTION.md)：335份编译JS/资源，不等同于未编译TS/React源码 |
| 桌面独立资源 | `source/desktop-resources/`：MCP CLI、商家档案/身份workflow及知识库schema |
| 商品设计模板 | [模板入口](source/desktop/templates/README.md)：主图122、详情54、海报广告67、品牌12、参数图10，共265条及完整提示词、分页来源 |
| 官方找货技能 | `source/account-skills/1688-sourcing/`、`source/remote-skills/`，保留提取版本与校验 |
| 本地桥接器源码 | `source/bridge/`：本地适配器，单独标注，非Accio官方源码 |
| 205项工具原说明 | [2026-10-25-tool-catalog.md](catalog/2026-10-25-tool-catalog.md)、[tool-routing.json](catalog/tool-routing.json) |
| 工具Schema快照及来源映射 | [live-tool-schemas.json](catalog/live-tool-schemas.json)、[source-to-agent.json](catalog/source-to-agent.json)；执行前仍查实时定义 |
| 来源、版本、哈希和排除项 | `manifests/` |

历史盘点覆盖12个本地插件、11个专家及桌面ASAR的1606项；当时远端市场90项中明确含1688的5个插件均有对应文件。“全部”仅限本地安装、当时授权可见目录、可下载包和公开模板。云端服务端源码、模型权重及未下发私有提示词未取得，应用包没有source map；原专家提及的 `1688-shop-operate` 未找到，不列为已运行技能。

大泽、店小宝、DSers专属工具不在该205项历史目录中；实际执行前须核验当前连接和授权。模板的品牌、参数、价格是样例，改编时以真实商品事实替换。凭证、Cookie、Token、聊天记录、业务数据库、`.env`和私人记忆未纳入提取；一处上游内嵌API凭证在副本中脱敏并记录哈希，源文件未变。

## 验证与恢复

2026-10-30已落实阶段加载、短总控入口和轻量运营账本查询，13个技能及4个子Agent配置同步调整，199项测试和整包保留校验通过。范围、使用方法、六类场景审阅及恢复位置见[上下文精简实施与验证](reports/2026-10-30-context-loading/实施与验证.md)。

2026-10-29已修复广告判断与询盘状态的七项重要问题，具体变更、兼容迁移和119项测试结果见[重要问题修复与验证](reports/2026-10-29-operating-fixes/重要问题修复与验证.md)。

本次组织重构前的配置保存在 [configuration-before.tar.gz](outputs/routing-refactor-20261028/configuration-before.tar.gz)。业务回执和历史报告继续保留，原始 `source/` 与已有图片项目不因组织调整删除。

本轮完整变更、保留范围和后续能力边界见[路由与技能重构结果](reports/2026-10-28-routing-refactor/路由与技能重构结果.md)。

本地校验入口：

```sh
python3 '/Users/shileqi/1688运营agents/scripts/validate_package.py'
```

[VALIDATION.md](VALIDATION.md)记录验证范围和限制。目录、规则原文、文件链接与离线路由验证，不代表205项接口逐项业务实测；不能据此声称已经修改商品、调整投放、发送消息或开启自动运营。
