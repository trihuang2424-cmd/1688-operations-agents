# 轻量运营账本与恢复查询

[operating_state.py](../scripts/operating_state.py) 读取单店结构化账本，完整校验并扫描后生成短摘要、待处理清单和对象详情。它只使用 Python 标准库，不取业务数据、不连网关、不派发 Agent、不投放、不建调度，也不提供通用业务写入引擎。

默认真实账本位置为 reports/operating-state/current.json；多店或任务指定其他位置时显式传 --state。本次只建立工具和目录说明，没有填造店铺引用、历史行动、重点产品或广告计划。不存在账本表示**尚未初始化、需要历史核对**，不表示没有任务。

## 恢复和最小查询

从项目根目录执行；其他工作目录也可使用脚本绝对路径，默认状态路径仍相对项目根解析。

    python3 scripts/operating_state.py summary
    python3 scripts/operating_state.py due
    python3 scripts/operating_state.py object --id <行动ID、重点ID、诊断ID、计划引用或商品/草稿ID>
    python3 scripts/operating_state.py validate
    python3 scripts/operating_state.py check --id <行动ID> --require closure
    python3 scripts/operating_state.py check --id <行动ID> --require handoff

    python3 scripts/operating_state.py --state <单店账本.json> --at 2026-10-30T09:00:00+08:00 due --offset 10 --limit 10
    python3 scripts/operating_state.py summary --gap-offset 10 --gap-limit 10

全局参数 --state、--root、--at、--stale-after-hours 放在子命令之前，分页参数放在子命令之后。默认 --limit=10，允许1至1000。--offset 从0开始，返回 total 和 next_offset。缺口使用独立 gaps.total/items/next_offset 与 --gap-offset/--gap-limit；gap_counts 始终给出全部缺口按类型计数。不能因第一页没有目标就认定没有该任务。

| 命令 | 返回与用途 |
|---|---|
| summary | 本地策略版本和文件 SHA256 核对、数据截止、上次结论短摘、历史核对状态、人工待审核/待执行/待核验和未知结果计数、行动/长期重点/投流短卡、到期与缺口分页、相关证据路径分页 |
| due | 扫描全部行动、全部重点和每个行动内的广告计划；返回已到期、缺排期及结果未知的短卡。多个到期条件合并到同卡 reasons 数组，不漏任一条件 |
| object --id | 获取完整记录；展开同 issue_ref、双向 related_action_ids 关联行动，再带入诊断和长期重点。详情可能多页，不覆盖其他行动 |
| validate | 完整结构、关系、策略文件、证据路径、时间和状态校验，返回缺口及计数 |
| check --id | 校验单个行动的本地就绪条件；--require 可为 stage、handoff、delivery、execution、closure，默认 closure。返回结构是否有效、具体条件、引用检查和阻塞项，不派单或执行 |
| init --input | 显式创建待历史核对空壳；不导入历史、不覆盖已有文件，不声称真实业务已建档 |

所有查询先读一个 JSON 文件快照、验证全部记录、扫描全部到期条件，再过滤和分页。state_sha256 标识该次文件快照；跨页时保持同一 --at 并核对摘要不变，文件变化后从新快照重新分页。scan_complete=true 只说明这一文件全表扫描成功，不证明所有历史都已登记。摘要只在内存派生，不另存一份可写“当前状态”。

成功返回 JSON、退出0。状态缺失返回 status=uninitialized、counts=null、history_reconciliation_required=true、退出3，同时提供当前默认策略文件实测ID/版本/摘要；它只是本地来源信息。坏 JSON、重复字段、非有限数、不支持版本、缺必需字段、坏状态、跨店或断裂关系等返回 stderr JSON、退出2，不把失败伪装成空任务。可解释的数据缺口以 needs_attention 和 gaps 返回，保留仍可读的全部到期任务。

check 额外使用 check_passed 与 check_status 表达所选条件是否通过：通过退出0，未就绪退出4。structurally_valid=true 只代表结构可读，不代表行动或产物已经就绪。整体 status、ledger_status、gaps 和 gap_counts 仍保留账本警告；证据交付可在无关全局缺项存在时通过，但不能抹掉警告。check_scope=single_action_local_only，blocking_gaps 给出与该执行行动有关的额外前置缺口。策略来源未核对、行动策略版本不同、历史未核对、相关责任/人工交接/观察基线等执行缺口不能使 --require execution 或执行收尾通过。

恢复时先处理 requires_reconciliation=true 的未知结果，核对原执行者、真实任务、回执和后台状态，不因过期重试原写入。人工回执未确认时只跟进执行。随后检查所有到期和缺排期项，再依据真实新数据和现行授权确定任务。任何返回都不授予新业务授权，dispatch_permitted_by_this_tool 始终为 false。

## 初始化、历史核对和账本结构

首次真实运行先核对现有报告、执行回执、人工方案、在途任务和未知结果，确认真实网关 store_ref 与实际状态位置。不从策略名、公司名或目录名推断店铺引用。初始化输入仅包含：

    {
      "store_ref": "<当前网关确认的真实引用>",
      "strategy": {
        "strategy_id": "<策略原文ID>",
        "version": "<策略原文版本>",
        "reference": "references/account-strategies/songtai-sales-growth.md",
        "sha256": "<该文件原始字节的64位小写SHA256>"
      },
      "conversion_state_ref": null
    }

conversion_state_ref 已核对时填原转化状态文件路径，未核对用 null。以上只是说明，不是真实初始化输入。信息齐备后运行：

    python3 scripts/operating_state.py --state <单店账本.json> init --input <本轮真实初始化输入.json>

策略原文使用“策略ID：...；版本：...”明确标记；初始化只在文件、登记ID/版本和 SHA256 全匹配时创建。已有账本查询遇到策略文件变化仍返回到期任务，同时提醒重读原文、核对策略及待执行方案。旧行动保留原 strategy_version；未完成行动与当前策略不同会提示核对，不能重写固定基线。

账本根字段全部必需：

| 字段 | 契约 |
|---|---|
| schema_version / data_mode / timezone | 分别为 1、operating_ledger、Asia/Shanghai；模板不是账本 |
| store_ref / strategy | 单店真实引用及上述策略引用；子记录店铺必须相同 |
| history_reconciliation | status、reviewed_at、evidence_refs、outcome、unresolved |
| data_cutoff | 本账本最新经营判断实际所用数据截止，带时区；未登记用 null 并明确提示 |
| last_conclusion | null，或 recorded_at、summary、evidence_refs；摘要过长会标注截断，完整内容在对象详情、原账本和证据 |
| conversion_state_ref | 原转化文件路径或 null，仅引用 |
| reviews / actions / focus_products | 三个数组，复用[记录模板](templates/sales-growth-records.json)；每个字段须保留，未知按规定填 null/空数组并列缺口 |

init 创建 history_reconciliation.status=required。手工历史核对完成后，在同一账本登记真实 reviewed_at、证据路径及 outcome=imported 或 no_relevant_records。imported 至少有一条真实记录；确认无相关历史也必须有历史核对证据。未解决的历史问题逐项放 unresolved。no_relevant_records 只描述核对当时历史，不禁止之后新增真实行动。首次历史核对前不能据空表新增派单。

本模块不提供批量导入或状态更新命令，不迁移旧报告或模板。执行者依据原始证据维护同一真实账本：准备候选文件、完整校验、保存前序证据、核对原文件摘要未变化后同目录原子替换。具体业务授权、同对象串行和回读仍按[执行协议](execution-protocol.md)。只有 init 的本地写入由本工具负责验证、文件锁、临时文件 fsync 与原子独占发布；锁只覆盖初始化，不代表整个工作区、人工编辑或远端业务被锁住。不要删除 .lock 文件来“解锁”。

## 行动、人工回执、观察与关系

actions 采用模板全部字段，另必需 strategy_version。review_id/focus_id 可空，但非空时必须指向现存记录，并在对方 action_ids 有反向关联；每个行动只保存自己状态。related_action_ids 不得自引或指向缺失行动。issue_ref 可引用原问题证据或原转化问题稳定ID；不得复制问题状态。ID在三张表中不能冲突。

支持的行动状态：

    analysis_pending preparing_assets plan_ready awaiting_approval awaiting_manual_review
    awaiting_execution awaiting_manual_execution executing
    awaiting_verification awaiting_manual_verification observing evaluating
    blocked failed unknown insufficient_evidence completed cancelled

人工待执行/待核验使用明确状态和 manual_handoff.required=true；方案包括逐字段变更、步骤、素材、依赖、责任人、到期时间与所需完成证据。未知或未填字段报错或列缺口。非终态行动至少有可用的 next_review_at、人工 due_at 或观察评估/最晚重审日期；都没有时列待处理并标记 missing_followup_schedule，不会静默消失。未知结果不论排期是否在未来，都优先列入核对。

进入 observing/evaluating 必须有 execution.effective_at、真实 receipt_refs 和观察起点；人工执行还须 readback_refs，或在无法后台回读时于 execution 内提供：

    "effect_verification": {
      "status": "confirmed",
      "evidence_refs": ["<真实生效确认文件>"]
    }

计划交付、单纯“已提交”不构成生效证据。人工仍待审核/执行/核验时观察起点为空。display_verification_status 单独取 pending、unknown、verified_by_user、verified_with_authorization 或 not_applicable；后台回读不等于买家页面已核查。

completed 必须有真实生效时间、执行回执及 evaluation_history 验收结论；人工还须回读或上述生效确认。纯方案交付使用 plan_ready；决定不执行时用 cancelled 并提供 cancellation.recorded_at/reason/evidence_refs，不能伪造生效来关闭。普通事实纠错凭正确性验收可完成，不强迫设置经营观察。

observation.start/end 必须是带时区时间戳，使用 **[start, end)** 半开区间。10月21日至29日完整观察应登记 start=2026-10-21T00:00:00+08:00、end=2026-10-30T00:00:00+08:00。起点可以等于真实零点生效时间，不能早于生效；评估不能早于完整窗口的排他结束边界。evaluate_at/latest_reconsider_at 等排期允许日期，日期在 Asia/Shanghai 当天零点即到期，不表示该日数据完整。

fixed_baseline 只读原值，不随日常日期或滚动均值更新；日期基线结束日须早于生效日。缺历史/新品基线如实留缺口。可加 snapshot_sha256，值为该基线对象去掉 snapshot_sha256 后，以 Python json.dumps 的 ensure_ascii=False、sort_keys=True、separators=(',', ':')、allow_nan=False 编码 UTF-8 的 SHA256；不符报错。这能发现未同步摘要的修改，不能防止外部人员同时改基线与摘要；前版本和原始证据仍须保留。

evaluation_history 每条必需 evaluated_at、conclusion、decision、evidence_refs，按时间保留。效果评估记录 scheduled_evaluate_at 和明确 observation_end。延期再记 next_evaluate_at/extension_reason，保留原到期和原结论，不通过改日期抹掉到期历史。旧评估涉及不同窗口时必须填写其原 observation_end，避免与现窗口混淆。提前异常/干预另留证据，不冒充到期效果结论。

### 可选的决策与交付契约 workflow v1

新记录按模板填写 action.workflow.version=1，根 schema_version 仍为1。旧记录缺 workflow 仍按原规则读取，check 返回 contract=legacy_unknown、就绪条件不通过；不自动迁移、推定物料存在或伪造授权。小型只读任务不因此强制建完整账本。新版字段只在 workflow 存在时校验，不加入全体历史行动的必填字段。

| 字段 | 内容与约束 |
|---|---|
| deliverable_type | evidence、plan、asset 或 execution，按用户本轮要求选择；查证或方案请求不因能力可用扩展为发布 |
| delivered_at / delivery_receipt_refs | 非 execution 本轮实际交回后登记的带时区时间与真实交付回执引用；不能因文件生成或 check 通过就预填。execution 继续使用原有生效、回执和观察字段 |
| decision | choice、basis、evidence_refs、key_unknowns、investigation；明确选定动作及依据，未知原因本身不自动阻止低成本试验 |
| decision.investigation | status 为 not_required/in_progress/stopped/exhausted；blocking 明确未知是否阻断决策。in_progress 必须有 stop_conditions 和 stop_at 才可认定决策就绪；到期进入 due，不自动继续取证或执行 |
| preparation | required、required_types、due_at、deliverables；required_types 按用户目标列本次实际需要的产物类型。asset 交付必须明确，不能以copy/other替代要求的image。未完成物料的 due_at 进入到期扫描 |
| preparation.deliverables[] | type、artifact_refs、check_status、check_evidence_refs；type 为 evidence/plan/image/video/audio/copy/other，check_status 为 pending/passed/failed。passed 还须实际产物及检查证据存在，文件存在不等于内容通过检查 |
| approval | type、necessary_basis、basis_refs、review_objects、status、authorization_ref；记录必要确认的依据、具体对象及已有授权，不因能审核就制造用户待办 |
| approval.review_objects[] | type、artifact_refs；必须对应 preparation 中已登记通过检查的实际产物 |

approval.type 为 none、plan_review、asset_review、execution_authorization；status 为 not_required、pending、approved、rejected、covered。none 只能是 not_required；已有授权用 covered 并保存 authorization_ref，不再保留待审核行动状态。必要依据和引用未准备好时，不能形成有效用户审核待办，摘要以 unready_review_handoffs 单列，而不计入 manual_review。

plan_review 只要求可审核的完整方案及其检查证据，可以先审方案再生成图片。asset_review 必须有实际所需资产类型的产物，且本次必要物料完整并登记检查通过。execution_authorization 必须有具体方案和齐备的必要物料；只可用于 deliverable_type=execution。所有确认都复用现有授权边界；本地记录和 check 不证明授权内容真实，也不产生新授权。

本地 image 引用检查扩展名和文件头的基本类型一致性：PDF、设计brief或改名PNG的文本不能冒充图稿。它不检查图片质量、尺寸合规或商品真实性；这些需要真实的 check_evidence_refs。外部URL只返回 external_pending_verification，不因为链接存在或登记 passed 就自动通过。其余本地文件检查存在性和已登记检查证据，不声称自动验收内容。

准备物料使用 preparing_assets。交付和交接前实际运行，例如：

    python3 scripts/operating_state.py --state <指定账本.json> check --id <行动ID> --require handoff
    python3 scripts/operating_state.py --state <指定账本.json> check --id <行动ID> --require execution
    python3 scripts/operating_state.py --state <指定账本.json> check --id <行动ID> --require closure

readiness 各布尔值分别表达本阶段、交接、交付、执行准备和收尾条件，不能相互替代。handoff 通过可以表示方案已经可审，但不表示图稿或业务执行完成；execution 通过只表示本地执行前置齐备，不表示已经执行。执行收尾还须真实生效、执行回执及回读/生效确认；进入观察的行动还须有限观察条件与原有固定基线。unknown/blocked/failed 不因产物存在自动就绪。

非 execution 的 closure_ready 表示本次产物已具备交回条件，可以在最终交付前实际运行 check --require closure；它不表示用户已经收到。delivery_closed 独立要求 delivery_ready、显式 delivered_at 和实际存在的 delivery_receipt_refs。真实交回后或下次恢复时据回执维护；未交回不能仅为消除到期提示造回执。delivery_closed=true 时只跳过该行动本轮资料/物料阶段的准备和跟进到期，不再产生重复诊断或 missing_followup_schedule；摘要保留 delivery_closed 短卡和 delivered_stages 计数。行动内独立广告日检及长期重点照常扫描，unknown 仍需核对。未来不同 scope 另建关联行动，或依据新请求显式开启并记录新阶段，不能复用旧回执推定新产物已交付。

evidence/plan/asset 的本轮交付可用 plan_ready 和 delivery_ready/closure_ready 表达，不填写远端生效，不为交付报告而调用业务写入。completed 的原有真实生效语义保持不变；非 execution workflow 不进入执行、观察或 completed 状态。决定不执行时仍按既有 cancellation 证据规则登记。上述就绪检查只反映已登记的本地一致性，不能证明历史实际按顺序流转。

## 长期重点与广告日检

focus_products 使用模板全部字段。active 有公司依据、真实产品/草稿集合、目标、负责人及周/月复查；缺排期进入待处理。paused/exited 必须有 company_exit_decision_ref。单行动完成不退出重点身份，也不把所有行动永久留在观察中。未指定重点时不制造商品名单。

广告计划放 action.ad_plan，不另复制状态表。模板之外必需 status 和可为 null 的 next_daily_check_at。状态为 draft、awaiting_approval、awaiting_execution、awaiting_verification、active、paused、ended、unknown、cancelled。active 必须有真实 actual_plan_id 和 activation_evidence_refs；预算、授权、基线、成熟条件、责任人等缺口明确列出。计划引用唯一，重点 ad_plan_refs 指向实际嵌入计划。

daily_checks 每条保留 checked_at、data_cutoff、conclusion、evidence_refs，按检查时间排序；指标与归因详情可附加。实际日检后据真实条件更新 next_daily_check_at，查询不自动顺延。正在投流的计划独立扫描，即便关联行动已完成也继续日检；投流未知结果优先核对，不能按“已结束行动”隐藏。缺日检日期同样列待处理。重点 next_ad_daily_check_at 不代替每个计划自己的日检。

## 截止、证据与转化状态边界

时间戳含时区，比较统一转换到 Asia/Shanghai；--at 可固定测试或恢复时点。根数据截止默认超过48小时显示 stale，可用 --stale-after-hours 调整；它只提醒核对本轮数据需求，不是接口时效承诺、经营失败判断或强制重取全量的规则。未来截止、缺截止明确提示；每次诊断和投流日检另存各自实际截止。

证据路径相对 --root 解析，本地检查只证明文件存在，不证明内容正确；外部 URL 仅保留引用、标记未验证。本地缺文件作为缺口，原证据不为消除提示而改写。摘要保留证据路径分页，完整记录通过 object 读取。

[conversion_state.py](../scripts/conversion_state.py) 仍是询盘转化唯一状态模块。这里只显示 conversion_state_ref 及文件是否存在，不打开、复制、合并或迁移其问题/请求/回执。恢复时按[转化状态契约](conversion-state.md)另读原模块 summary；每日仍按原协议 ingest 扫描全部历史未结问题与措施，即使信号为空。运营摘要没有转化条目不表示转化无待办。

测试全部在临时目录构造离线数据：

    python3 -m unittest discover -s scripts -p 'test_operating_state.py'
