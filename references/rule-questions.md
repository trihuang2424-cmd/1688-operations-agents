# 来源规则差异与待核验事项

登记日期：2026-10-28（Asia/Shanghai）。本登记表落实角色与技能合并清单中的差异留存要求，供当前能力入口定位原文与待核问题；不替代业务规则，也不修改其生效条件。

本次仅核对本地文件，未调用业务接口、取得新的实时工具定义或验证店铺能力。下列条款保持原文；“未裁决”表示尚未完成适用范围核验，不表示任一条款已被删除、改写、停用或扩大适用范围。实际任务仍按[共用执行约定](runtime.md)、当前技能、完整来源规则及用户已有授权执行。

## RQ-001：same_img_offer_search 的场景表述

状态：**待核验，未裁决**。涉及能力：采购研究、竞争与市场研究、分销。由运营总控协调相关任务负责人核验，并保存后续证据；本次角色合并不决定工具的适用场景。

| 来源及准确位置 | 现有原文 | 业务场景 | 待核问题 | 状态 |
|---|---|---|---|---|
| [采购迁移说明，第9行](purchasing-migration.md:9) | “普通图片找同款走 `find_product`；用户明确要求分销图搜才进入 `same_img_offer_search`。链接搜索用真实商品 ID 或官方详情返回的图，不臆造图片 URL。” | 普通图片找同款、明确分销图搜与链接搜索的迁移适配 | 此处分流条件与下列采购研究、市场研究中的候选工具说明应如何结合适用？需核对对应原始技能、既有用户要求及当前工具定义；不能仅凭候选清单推导条件已放宽。 | 待核验，未裁决 |
| [原采购研究规则，第16行](business-rules/1688-sourcing-advisor/RULES.md:16) | “1. 按线索用 find_product / same_img_offer_search 搜商品，或用 1688_source_suppliers / 1688_source_suppliers_infos 找供应商。不把图片相似当作材质、型号或资质完全相同。” | 买家找货、图搜与供应商研究；同一文件另要求执行前核对采购迁移补充 | 此处并列工具是否只概括候选，具体图搜条件是否由其引用的迁移说明和源技能限定？两处原文均保留，不能单独抽出这一行作为不限场景的调用依据。 | 待核验，未裁决 |
| [原市场机会规则，第20行](business-rules/1688-market-opportunity/RULES.md:20) | “候选工具：`opp_market_search_data_query`, `find_product`, `same_img_offer_search`。” | 卖家品类、关键词及市场机会研究 | 卖家研究中该候选工具对应哪种具体图搜场景，是否承接采购或分销子流程？该行仅列候选，未在本行给出适用条件；须结合完整规则及来源核验，不能把目录存在当作已支持全部研究场景。 | 待核验，未裁决 |
| [原分销规则，第16行](business-rules/1688-distribution-operator/RULES.md:16) | “1. 关键词分销选品用 distribution_select_offer；只有用户明确分销图搜时协同 sourcing_advisor 用 same_img_offer_search。候选商品用 distribution_offer_info 核对价格、履约及分销条件。” | 明确的分销选品、分销图搜及候选核验 | 此处与采购迁移说明中的分销条件一致；需要核验的是它与较宽泛候选表述之间的适用关系，并非已发现两条分销条件互相冲突。旧交接名仍按注册表映射，不恢复旧岗位。 | 原文一致部分已记录；整体适用关系未裁决 |

核验时应保留完整上下文，并继续读取所选流程引用的来源：

- [1688 图文找货与同款比较源技能](../source/remote-plugins/1688-purchasing-assistant/1688-purchasing-assistant/skills/1688-product-find/SKILL.md)。
- [市场与关键词研究源技能](../source/plugins/1688-seller-assistant/skills/1688-product-keyword-research/SKILL.md)。
- [分销源技能](../source/remote-plugins/1688-purchasing-assistant/1688-purchasing-assistant/skills/1688-distribution/SKILL.md)。

后续记录应包含核验日期、具体业务场景、使用的原文与来源、实时工具证据（如实际取得）、用户要求依据、结论及仍未解决的问题。若核验结果提出删除、改写或停用来源业务规则的建议，仍须按既有规则向用户说明并取得明确同意；本登记表本身不作该决定。

## RQ-002：标题方案在未升级客户端中的选择与回退

状态：**待核验，未裁决**。涉及能力：商品优化中的标题方案选择。由商品运营核验具体客户端行为、来源版本及用户回传，再交运营总控协调；本次仅登记发现，不改动或停用来源规则。

同一份 [interaction-specs.md](../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/references/interaction-specs.md) 对未升级客户端给出两套不同处理：前段 Step 3a/4a 要求重新选择，后段“未升级客户端兜底处理”允许启发式选方案或使用默认标题。两段均明确涉及未升级客户端，不能直接解释为互不相干的场景。

| 来源及准确位置 | 现有原文（摘录） | 业务场景 | 待核问题 |
|---|---|---|---|
| [Step 3a，第446行](../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/references/interaction-specs.md:446) | **严禁**用"取行数最多的方案"等启发式猜测算法 | 未升级客户端跨方案混勾；该段要求重新弹窗 | 与第523行针对同类输入的处理相反，应核验来源版本和实际客户端协议，不能凭段落先后推断哪段失效。 |
| [Step 6，第483行](../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/references/interaction-specs.md:483) | **禁止**回退读 CLI 原始返回里的 `new_title`（用户编辑会被覆盖丢失） | 前置完整性校验后读取最终标题；Step 4a对缺字段要求重新选择 | 与第524行缺少“新标题”行时的默认值回退存在差异；需核验如何保留用户实际选择与编辑。 |
| [旧客户端兜底第4步，第523行](../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/references/interaction-specs.md:523) | **取行数最多的方案**作为用户意图；行数相同时优先取方案 A | 未升级客户端跨方案混勾 | 与第446行冲突；提示用户已选择的结果不等于用户确认了该选择。记录原文，暂不作适用性裁决。 |
| [旧客户端兜底第5步，第524行](../source/plugins/1688-seller-assistant/skills/1688-item-title-optimizer/references/interaction-specs.md:524) | 若该 `field` 未被用户勾选 → **回退到原始优化结果中该方案的 `new_title`** | 所选集合缺少“新标题”行 | 与前段缺字段重新选择及禁止回退的流程不同；需核验真实回传与来源适配，不能由角色合并决定替代值。 |

发现证据：[商品模拟任务记录](../reports/2026-10-28-consolidation-completion/simulation/product-task-record.json)。本轮仅生成模拟草稿，没有卡片回传、方案应用或业务写入，因此未触发上述分支，也未将任一条款视为已失效。后续如任务实际进入这些交互分支，应先核验具体适用流程，不把本轮草稿演练通过视为交互冲突已解决。

## 记录边界

本次未将“来源规则的曝光预估与本店实测不同”登记为规则冲突。标题曝光预估的原有条件、数值及免责声明继续保留；执行与报告中区分预估和实际观测，不因缺少本店实测而停用来源规则。其他差异仅在发现具体原文与适用性问题后新增，不能为补齐清单虚构争议。

## 2026-10-29 已裁决补充

以下三项依据2026-10-29本轮用户修复重要规则与状态问题的指令完成项目运行规则修正。前文登记日期、未裁决状态及记录边界对应2026-10-28的既有条目；RQ-001、RQ-002继续保持原状态。来源原文与`references/business-rules/`均未修改。以下只在明确列出的冲突范围采用[广告经营判断补充规则](ad-decision-policy.md)，其他原业务规则继续有效；本轮未调用广告业务接口或执行任何投放调整。

### RQ-003：商家止损建议与平台续投约束

状态：**已裁决，2026-10-29生效**。适用：广告解读、投放建议与效果复盘，包括总控经营分析和流量专员。

| 来源及条款 | 原规则摘录/范围 | 裁决 |
|---|---|---|
| [广告分析规范第1节](../source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/references/ad-analysis-rules.md:7)，及第6/12/16节对应引用、第17.1节优先级 | 禁止建议暂停/关停，改为预算再分配；即使产品手册提及停投仍遵循不建议暂停 | 采用补充规则AD-001，允许按商家目标与证据提出继续、增投、降预算、重分配、暂停或终止等方案；真实合同限制和产品能力单独核实 |
| [广告分析规范第18节](../source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/references/ad-analysis-rules.md:315)，[自由取数技能Step 8.1及核心规则18](../source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/SKILL.md:578) | SKA服务中禁止暂停/退款/降低预算建议，预算收缩转交小二；查询异常或查无档案按非SKA处理 | SKA状态未知保持未知；服务身份和小二建议不能代替真实合同限制或企业决策。可提出有依据的止损或依约退款选项，核实合同/年度方案影响；实际写入权限不因建议产生 |

执行依据：[ad-decision-policy.md](ad-decision-policy.md) AD-001。继续遵守已有授权和工具前置，不为范围内已授权动作重复确认。本裁决不承诺当前已经具备广告写入能力。

### RQ-004：广告产出比的零值与利润含义

状态：**已裁决，2026-10-29生效**。适用：广告指标计算、排序、预警和解释。

| 来源及条款 | 原规则摘录/范围 | 裁决 |
|---|---|---|
| [广告分析规范第4节](../source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/references/ad-analysis-rules.md:29) | ROI＝转化金额÷花费金额 | 保留平台字段名并说明是广告产出比，不视为利润ROI；利润另核成本和计算口径 |
| [广告分析规范第8节](../source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/references/ad-analysis-rules.md:98) | 零支付有消耗称“全额沉没”；花费>0但成交额=0时ROI记N/A，以避免除零 | 已确认花费>0且真实成交额=0时产出比为0；字段缺失与分母为0分别标记。平台零成交不能单独证明整体经营无价值，也不能凭缺失断言已有线下收益 |

同一口径修正同时覆盖原规范第7节的部分成本“净利率/真实盈利水平”命名，以及第8节仅凭线索成本健康强制认定“线上ROI低估、承接正常”的表述：按实际成本覆盖注明贡献额/率，归因遗漏与承接质量须有独立证据。

执行依据：[ad-decision-policy.md](ad-decision-policy.md) AD-002。保留原始回执，覆盖不足以确认真实零时留空并说明原因；成熟度和回补状态另存，不混淆数值与经营结论。

### RQ-005：统一广告检查节点与转化成熟条件

状态：**已裁决，2026-10-29生效**。适用：投放措施的观察、复查和效果评估。

| 来源及条款 | 原规则摘录/范围 | 裁决 |
|---|---|---|
| [广告分析规范第15节](../source/plugins/1688-seller-assistant/skills/1688-shop-freedom-query-data/references/ad-analysis-rules.md:245) | 24小时监测、3天验证、7天完整评估并决定放量 | 采用补充规则AD-003，这些是可选过程检查节点；最终评估按采购周期、样本、归因/退款回补与既定指标成熟条件确定 |
| [运营周期约定的效果评估条件](operating-cycle.md#何时观察何时评估) | 不给所有商品机械套用固定天数；新事实或既定干预条件可提前处理 | 保留该约定。成交尚未成熟不阻止对已证实消耗、预算、设置和承接异常形成建议并在原授权内处置；单纯表现仍差不触发重复修改 |

执行依据：[ad-decision-policy.md](ad-decision-policy.md) AD-003。最早评估、样本依据、最晚复审及提前干预条件继续按具体措施保存；本裁决不创建每日或每周定时任务。
