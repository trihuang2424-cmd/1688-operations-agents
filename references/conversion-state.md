# 询盘转化问题的本地状态契约

[conversion_state.py](../scripts/conversion_state.py) 保存单店问题、分析请求、真实派发回执和明确评估结果。它不取业务数据、不调用模型、不启动 Agent、不修改客户/商品/投放、不发送消息，也不创建定时任务。经营判断仍由[询盘转化分析流程](../.agents/skills/1688-customer-conversion/references/conversion-analysis.md)负责；主 Agent 只将有据的规范化信号交给本模块。

## 文件和命令

每店独立状态文件，建议在实际采用的运营状态目录内使用 `conversion/<店铺本地别名>.json`。`store_ref` 必须来自当前网关，不能从文件名推断授权。首次真实运行才创建状态；不能将示例、测试店、模拟问题写入真实运营目录。

```text
python3 scripts/conversion_state.py --state <状态.json> <命令> --input <命令输入.json>
```

所有命令输入均含 `store_ref`；新输入使用 `schema_version: 2`，`ingest` 强制声明版本；兼容旧版输入 `1`。成功输出 JSON 并返回 0，失败返回 2；失败不提交该轮部分变更，包括迁移。每次输入与输出都应保存在本次运行证据目录。原始回执与分析正文存文件，通过引用关联；不复制完整客户库、聊天全文、凭证或地区画像。

| 命令 | 除 store_ref 外的主要输入 | 结果/边界 |
|---|---|---|
| `init` | 无 | 空状态，`history_reconciliation.status=required`；不是“店铺无问题” |
| `reconcile-history` | `reviewed_at,evidence_refs,outcome,issues` | 先读取既有报告、行动、未完成任务，`outcome=no_relevant_actions` 时 issues 为空；`imported` 时至少导入一条 signal 结构的历史问题。未完成/未知行动须带关联记录和复查时间 |
| `ingest` | `schema_version,run_id,observed_at,signals[]` | 更新本轮信号并扫描全部未结问题及各行动的到期条件；空数组也扫描，输出 `outcomes` 和 `due_reviews`；不代表已经委派 |
| `summary` | 无 | 未结问题卡、各项 `related_actions`、当前 `context_digest`、计数和待认领/对账请求；旧状态首次成功读取会事务迁移 |
| `migrate` | 无 | 可显式执行版本升级；已为2时不重复迁移；返回摘要和迁移概要 |
| `claim` | `request_id,claimant,claimed_at` | 只有 pending、无未知行动且请求上下文仍有效时可领取；成功返回 claim.token 后才可真实 spawn |
| `revalidate-request` | `request_id,reviewed_at,reason,evidence_refs,context_digest` | pending 请求的证据/行动变化后，读取最新摘要并明确核对后登记；摘要散列已变化则拒绝，不绕过未知行动对账 |
| `cancel-pending` | `request_id,recorded_at,outcome,reason,evidence_refs,next_review_at` | 仅未认领的 pending 可取消；outcome 为 `cancelled/superseded`，后者还须 `replacement_ref` 指向替代策略/计划；不关闭业务问题、不自动创建替代任务 |
| `record-dispatch` | `request_id,claim_token,agent_id,task_id,receipt_ref,dispatched_at` | 真实 spawn 回执后登记；名称/读技能不算派发 |
| `mark-unknown` | `request_id,recorded_at,reason,evidence_refs` | 认领或派发中断，保留任务，不自动重试 |
| `reconcile-request` | `request_id,reviewed_at,reason,evidence_refs,outcome` | `not_dispatched` 只有已核实根本未派发才回 pending；`dispatched` 补齐或核对 agent_id/task_id/receipt_ref/dispatched_at；仍未知就保留状态 |
| `record-result` | `request_id,completed_at,outcome,conclusion,decision_source,evidence_refs,evaluation,next_review_at` | 有真实派发或有据透明代行记录才能验收；evaluation 是同 scope 的完整 signal 结构。未结案均须未来复查时间 |
| `record-action` | `issue_id,recorded_at,reason,evidence_refs,related_actions[]` | 按 action_id 更新指定行动，各未完成行动有独立 `next_review_at`；不覆盖其他行动；可显式提供顶层 next_review_at 更新问题复查时间；兼容旧单项 related_action |
| `record-task-end` | `request_id,ended_at,termination,task_stopped,reason,evidence_refs,next_review_at` | `termination=failed/cancelled`，且 `task_stopped=true` 有证据；结束失败/取消的原任务，不冒充分析完成。下次复查再考虑新请求 |
| `record-direct-start` | `request_id,claim_token,executor_ref,capability_check_ref,started_at,reason` | 仅 `reason=no_subagent_tools` 且工具确实缺失时记录总控透明代行，随后可 record-result；没有 agent_id，也不算真实委派 |

时间使用带时区 ISO 8601，例如 `2026-10-29T09:00:00+08:00`。同店 `observed_at` 不可倒退；同一问题的新监测不能覆盖之后形成的评估。复查时间依据既定策略、数据成熟时间或明确业务条件设置，不在模块内硬编码“几天必须修改”。

### 旧状态迁移

持久状态版本为2。已有版本1文件在第一次**成功命令**中自动迁移，也可先调用 `migrate`；使用同一文件锁和原子提交，错误时原文件保持不变。原 issue/request/run 标识、claim token、派发回执、结果和 run 重放响应均保留。`migrations` 只记录一次版本与来源散列，并保存一次完整 `source_snapshot`，摘要不返回该全文。

旧单行动及其复查日期转入 `issue.actions[action_id]`。旧决定/结果中曾被单字段覆盖的其他行动也按ID恢复；无法据当前记录确认结束的历史行动保留为 `unknown` 并标记 `migration_review_required`，先对账，不能推定已完成。原历史不删除。旧 pending 请求缺少创建时的完整行动快照，须 `revalidate-request` 后领取；已领取/派发/未知任务沿用原恢复路径，不因升级重派。迁移不改变旧成交指标的成熟度语义，也不会重新运行旧 `run_id` 的到期扫描。

## 监测输入

以下仅说明结构，示例中的店铺与证据值必须替换为真实来源，不能直接运行到实店状态。`content_fingerprint` 填规范化业务内容的 SHA256；不把抓取时间、文件路径等非业务变化混进散列。

```json
{
  "schema_version": 2,
  "store_ref": "<当前网关返回的店铺引用>",
  "run_id": "<唯一运行标识>",
  "observed_at": "2026-10-29T09:00:00+08:00",
  "signals": [{
    "scope": {
      "object_type": "product",
      "object_id": "<商品ID>",
      "problem_type": "conversion",
      "cohort_id": "<稳定的可比较客群定义>",
      "metric_id": "<询盘成单指标定义标识>"
    },
    "signal": "anomaly",
    "evidence": {
      "source": "<实际接口/证据来源>",
      "period_start": "2026-10-21",
      "period_end": "2026-10-27",
      "cutoff": "2026-10-28T00:00:00+08:00",
      "definition": "<分子、分母、范围、已知覆盖限制>",
      "version": "<数据/口径版本>",
      "content_fingerprint": "<64位小写SHA256>",
      "refs": ["<证据文件或回执引用>"]
    },
    "quality": {
      "coverage": "complete",
      "comparability": "comparable",
      "sample": "sufficient",
      "maturity": "mature"
    },
    "criteria": {
      "source": "<策略版本/来源规则/固定基线>",
      "condition": "<有依据的判断条件及适用范围>"
    },
    "next_review_at": "2026-11-03T09:00:00+08:00"
  }]
}
```

`scope` 严格接受上例五个字段。`object_type` 为 `shop/product/channel/cohort`，不接受买家级身份作为持久对象；`cohort_id`、`metric_id` 不能每天以新的抓取日期替换，否则会人为产生新问题。真正不同获客批次需要分别评估时可用不同 cohort，但须保持定义一致。

`problem_type` 为 `conversion/followup/order/repurchase/response/handoff/demand_mismatch/inquiry_volume/inquiry_quality/data_gap/process_commitment`。前四类仍表示需要成熟队列的结果判断，例如跟进后的成单率、样单转大货率；不能用 `maturity=not_applicable` 绕过。明确接待事实、交接事实可使用 `not_applicable`。

已确认报价、寄样、回访或履约承诺是否按时执行，单列 `problem_type=process_commitment`，使用 `maturity=not_applicable`，无需等采购成交周期。该信号必须附以下事实：

```json
{"process_commitment":{"stage":"quotation","commitment_ref":"<已确认承诺来源>","due_at":"2026-10-29T12:00:00+08:00","checked_at":"2026-10-29T14:00:00+08:00","expected_event":"<承诺的具体动作>","observed_status":"missed"}}
```

`stage` 为 `followup/quotation/sample/fulfillment`；事实状态为 `fulfilled/missed/unknown/not_due`。`checked_at` 表示证据覆盖的实际核验时点，不能晚于本轮时间；已知事实也不能晚于证据 cutoff。`missed` 必须已到期且有覆盖充分的未履行事实；缺少跟进记录、站外不可见或只有抽样均不能据此判漏做，使用 unknown/有限覆盖。正常信号须为 fulfilled 或 not_due；异常须为 missed，仍受样本和覆盖校验。这里只生成分析/建议，不自动联系客户或发送催办。

scope 的 cohort/metric 绑定稳定的承诺事件或明确的可比聚合定义，不以每日抓取时间创建新问题。改变同一承诺的阶段、内容或期限须提供 `commitment_change={reason,evidence_refs}`，原观察保存旧承诺和超时事实。补救完成可依据 fulfilled 结案，但不表示原承诺准时兑现；新采购承诺须按真实事件定义区分。

字段枚举：

- `signal`: `normal/anomaly/unknown`。
- `quality.coverage`: `complete/partial/missing`；完整指本次结论范围完整，不等于全店全部系统都已覆盖。
- `quality.comparability`: `comparable/mixed/unknown`。
- `quality.sample`: `sufficient/insufficient/unknown`。
- `quality.maturity`: `mature/immature/unknown/not_applicable`。

缺失、不可比、样本不足不会变成 0 或经营失败；转化类未成熟单独标记观察。此类问题及未完成行动必须带 `next_review_at`，避免无限期挂起。原始工具不支持的周期不能通过这里的日期字段伪造支持；每项信号保留其真实报表区间、截止日期与口径。证据 refs 和可选的 `retrieved_at` 可以变化，但不参与证据标识；证据标识包含来源、周期、cutoff、口径版本及内容指纹。

关联行动在 `signal` 或 `record-action/record-result` 中使用 `related_actions` 数组：

```json
{"related_actions":[{"action_id":"<商品措施>","status":"observing","next_review_at":"2026-11-03T09:00:00+08:00","evidence_refs":["<商品变更回执与固定基线>"]},{"action_id":"<接待措施>","status":"unknown","next_review_at":"2026-10-30T09:00:00+08:00","evidence_refs":["<接待执行回执>"]}]}
```

持久状态使用 `issue.actions` 字典，按 `action_id` 保存。status 为 `observing/active/completed/unknown`；每项未完成行动都有自己的 `next_review_at`，问题总复查日另存。completed 表示该项行动无需继续独立复查，不因残留旧日期再派任务；若经营效果仍需观察，保持 observing。更新一个ID不删除或完成其他ID；数组为空也不表示清空。日常信号只能重复携带相同行动或加入新的有据行动，不能覆盖已有状态和日期；状态变化通过 record-action/record-result 留证登记。两种行动输入不能同时出现。

兼容旧单项 `related_action`，其缺少内部复查日期时沿用旧顶层 `next_review_at`。新输入把日期写在每个行动内部；顶层日期只用于问题整体。任一行动未知都先对账；任一行动仍 active/observing 时，不因另一行动 completed 而把同一低指标当新异常重复派单。到期分析验收须逐项更新已到期的未完成行动，不能只延后问题总日期。

首次历史导入若有进行中的分析任务，应将相关行动标为 unknown 并引用真实任务记录，先核对任务/回执，再决定是否建立新的分析请求；空索引不证明没有历史任务。

摘要的 `owner=operations_director` 表示总控仍负责问题协调。结果可提供 `recommended_owner`（`operations_director/product_operations/traffic_operations/sales_owner/company_owner/unknown`）表达建议去向；它不改变实际负责人，也不代表已交接或派发。摘要同时返回 quality、criteria、最近监测与决定，供总控理解缺口；已结案详情保留在完整状态文件，默认不向总控重复加载历史。

## 请求去重与结果

稳定 issue_id 由店铺和五个 scope 字段生成，不含每天窗口。相同 run_id 和相同输入重放返回原结果；不同输入占用相同 run_id 会拒绝。空 signals、某项没出现、一次正常信号或证据缺失均不会自动关闭旧问题。

新抓取若带来早于当前证据 cutoff 的缓存数据，只记录 `stale_evidence` 及补证状态，保留较新评估；不能用旧异常缓存重新打开已结案问题。已经安排的复查仍可到期请求一次重新检查。

首个有完整、可比、足够样本且必要时已成熟的异常可排分析请求；但历史未对账、未知行动、正在等待的请求会先阻止新派发。已有措施观察中时，仍低于目标或滚动指标变化只更新问题记录。允许重析的依据为：

1. 到达问题或任一行动的 next_review_at；每次 ingest 在更新本轮信号后扫描所有未结问题，哪怕 signals 为空或该商品缺席，也在 `due_reviews` 返回一次复查或对账项。缺席不新增 observation、不更改旧证据及截止时间；请求明确用于补证/继续观察，不据此判失败。同问题同轮多个到期条件合入一个请求；已有在途请求或未知行动仍阻止新派发。
2. 独立标记的重要新事实 `new_fact={id,reason,evidence_refs}`，同时证据标识确实改变。
3. 达到有来源的提前干预条件 `intervention={id,reason,evidence_refs,criteria_source}`，同时证据改变。
4. 已凭完整正常证据明确结案，之后出现新证据支持的成熟异常，重开同一问题。

第 2/3 项必须由分析者解释新事实为何重要。新文件名、抓取时间变化、窗口移动、同一句“指标仍低”都不构成重要新事实。模块校验结构与去重，不能代替这项业务判断。

pending、claimed、dispatched、unknown 中的任何请求都阻止同问题再次排请求。claim 在本地锁内核对当前证据、质量/标准、各行动及复查状态的散列；有变化就拒绝领取，并在摘要标记 `needs_revalidation`。总控读取最新摘要和必要证据，核实任务仍有价值及外部策略仍有效，再用 `revalidate-request` 留下原因、证据与精确 context_digest。散列在复核与领取之间再次变化会继续拒绝；仅文件路径/抓取时间改变而业务内容未变不构成新业务证据。本地脚本不知道未录入的公司策略变化，总控必须核对真实策略和授权。

策略改向、商品退出或任务已无必要时，用 `cancel-pending` 取消或标记被替代；替代关系通过 `replacement_ref` 留证，后续是否创建新任务由总控决定。取消请求不等于问题恢复正常，也不取消其他行动或承诺，仍给出问题未来复查时间。已claimed/dispatched/unknown不能走此命令。claim 成功后拿到 token 才真实 spawn；中断不能自动过期重领。必须先核对宿主任务和回执：明确未派发才恢复 pending，若上下文变化还须复核；已派发则登记原任务；失败/取消先证实原任务停止并 record-task-end；仍未知保留，不凭超时重派。

`record-result.outcome` 为 `observe/resolved/needs_evidence/open`。所有非 resolved 结果须安排未来复查；observe 不等于已执行修改，只登记真实行动。resolved 必须有完整、可比、样本充分且必要时已成熟的 normal 评估及明确说明，且所有关联行动都已完成，不能结案隐藏未知或观察中措施。旧截止时间或早于最新监测的结论不能结案。非结案验收也须逐项处理已到期的未完成行动，给出结论或未来复查时间。结果保留证据和决定，同一请求不能被另一个结果覆盖。

## 本地可靠性和范围

状态写入采用 `fcntl.flock` 和同目录临时文件、fsync、原子 replace；同状态文件并发修改不会丢写。`.lock` 文件只是锁的载体，存在不代表正在运行，不能删锁文件来“解锁”。这只保护本脚本的本地读改写和认领，不能锁住网关、其他脚本、人工修改或真实 spawn；更不能称作客户只读权限隔离。宿主仍须遵循领域授权、按需委派和外部业务操作协议。

本模块不自行决定阈值、归因或最终业务动作，不自动构造 CRM 查询，不保证输入引用真实存在，也无法从一个 ID 证明真实 spawn。调用者须保存并核对来源和真实回执。测试使用临时目录中的虚构店铺，不接触真实业务；运行 `python3 -m unittest discover -s scripts -p 'test_conversion_state.py'` 验证去重、缺失值、成熟度、复查、派发恢复和并发认领。
