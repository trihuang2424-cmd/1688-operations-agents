# 按任务阶段加载上下文

`catalog/task-routing.json` 的 `routes[].phase_loading` 是唯一阶段依赖来源；注册表保留角色、能力、旧名和完整规则索引，不复制阶段矩阵。版本 2.4.0 保留 24 条路由、15 项能力、3 个核心角色和原业务规则。只缩小本轮需要读取的范围；选中的 `RULES.md` 和来源业务文件仍完整读取，不能用短摘要替代其中步骤、参数、前置、必要交互、提示或免责声明。

用户已授权本次读取组织调整。旧 `RULES.md` 或来源中通用启动、组织交接以及“先读整份共用文件”的加载路径，由当前阶段清单替代，不再据此反向全读 `runtime.md`、全部岗位或全部来源。此适配只改变组织与读取范围，不覆盖业务步骤、数值参数、前置、必要交互等实质规则；阶段清单未覆盖、但实际业务需要的来源仍必须补读。原文件及其校验基准保持不变。

## 启动与选择

总控启动只读根 [AGENTS.md](../AGENTS.md) 和真实状态摘要。已有任务指定账本时沿用该账本；默认摘要命令为：

```sh
python3 scripts/operating_state.py summary
python3 scripts/task_context.py list
```

`list` 只列路由 ID、负责人、意图和支持阶段，避免为了选路由先输出整份目录。摘要中的未初始化、缺失、结果未知和待对账不是“无问题”；按对象深入时再读具体记录及原始证据。没有额外运行记录或接口回执时，加载工具不会声称已执行、已委派、已生效或已产生经营效果。

选择明确的路由和阶段后生成读取清单：

```sh
python3 scripts/task_context.py --route title_optimization --phase plan --role director
python3 scripts/task_context.py --route title_optimization --phase plan --role executor
python3 scripts/task_context.py --route title_optimization --phase execute --role executor --details
```

`director` 是路由、交接和状态协调视图，不预读领域技能、业务规则或来源文本。`executor` 是本阶段真正进行业务分析、制定方案、核验或执行的人；总控自己完成经营分析时也用 `executor`，不能凭主 Agent 身份省略完整适用规则。领域任务的真实委派仍遵循[委派约定](delegation.md)，读取清单不算真实启动。

同一上下文已完整读过、内容未变的文件不重复读取。`--details` 提供选中文本和原文件的 SHA-256、字节数，以及各条件会追加的确切路径；这些字段支持核对版本，不是自动缓存或权限隔离。默认输出保留确切 `read` 清单、条件名和触发说明，不把完整目录带进每个任务。

## 阶段与真实任务范围

| 阶段 | 本轮工作 | 关键加载差异 |
|---|---|---|
| `plan` | 分析事实、形成可审阅的具体方案或交接 | 标题方案完整读取标题规则及必要来源；未进入应用阶段不加载编辑规则或执行协议 |
| `execute` | 按已有授权和实时能力实施该任务，也可为取数分析 | 涉及写入时加载完整业务规则、共用执行协议和实时工具前置；标题应用追加编辑规则 |
| `monitor` | 既有行动、真实截止、必要概览及到期检查 | 每日本地协调不加载旧总控全文；只查本地转化状态时不加载询盘/CRM规则；实际取数选择相应条件 |
| `evaluate` | 对固定基线、完整观察区间和成熟条件形成到期结论 | 加载比较基线、两类观察及本次实际分析模块；证据不足也要留下结论和下次可判断条件 |
| `receipt` | 接收人工完成事实、核对证据和实际生效，再决定观察起点 | 纯本地回执不加载发品/编辑业务；实际后台核验时通过 `data_query` 追加该路由完整规则及来源 |

各路由只开放有意义的阶段；例如 `platform_rules` 不支持 `receipt`。未知路由、缺失阶段、未支持阶段或无效条件都返回错误，不自动改成另一个阶段。任务从方案转为执行、从本地回执转为后台核验时，重新生成对应清单。周期协调路由中的经营取数或专业诊断另选 `daily_metrics`、`period_analysis` 或实际领域路由，不能把协调摘要当成完整业务规则。

人工完成回执统一可从 `daily_operations / receipt` 接入，保留原 `action_id`、原领域路由、真实完成事实和证据。需要后台回读时进入原路由的 `receipt / executor` 并加 `data_query`；支持的基础字段和人工销售字段分别核验，买家页面核查仍须遵循既有授权边界。不能把“方案已交付”写成“商品已修改”。

到期评估统一可从 `daily_operations / evaluate` 接入，再按原行动路由的 `evaluate / executor` 做具体评估。询盘转化到期需深析时用 `conversion_analysis`，先核对已有问题、请求、全部关联措施和真实任务状态，避免重复派单。详细周期和观察要求直接读取[工作流原章节](sales-growth-workflow.md#两类观察)。

## 交付类型与条件交接

阶段表示当前做哪类工作，交付类型表示本轮必须拿出什么结果。`traffic_and_ads`、`product_diagnosis`、`product_images` 的 `plan/execute` 阶段声明了 `completion_contract`；沿用五个阶段，不把每次分析强制扩为制作或发布。按用户本轮目标显式选择 `--deliverable evidence|plan|asset|execution`：证据、具体方案、真实成稿、执行及生效证据。图片设计说明不算成稿，成稿不算已经应用。

```sh
# 只查证据：候选交接不激活，不生成图片或修改商品
python3 scripts/task_context.py --route traffic_and_ads --phase execute --role executor --deliverable evidence

# 用户已有范围包含图稿制作时，另选成稿交付；不等于上传或应用授权
python3 scripts/task_context.py --route product_images --phase execute --role executor --deliverable asset

# 已有应用授权且进入真实应用任务时，还需选对应边界条件
python3 scripts/task_context.py --route product_images --phase execute --role executor --deliverable execution --condition apply_images
```

不传交付类型时保留目录中的兼容默认值；返回的 `scope_origin=default` 或 `explicit` 仅说明该选择来源，均不证明用户授权。未声明完成契约的旧路由只接受其阶段默认类型，返回 `completion_contract.declared=false`，不能声称本地加载器已经定义或验收其具体交付物。

`conditional_handoffs` 给出有条件的下一路由、阶段、责任角色、交付类型及所需既有范围。证据交付一律为 `candidate_only`；其余匹配项为 `pending_scope_check`，仍未激活或下派。总控依据用户目标、真实证据和既有授权决定是否承接，缺范围时交具体下一步，缺事实时先完成不依赖它的部分。`authorization=inherit_only` 与 `automatic_execution=false` 固定保留；目录、命令参数和候选交接都不能授权生图、上传、应用或投放写入。

脚本返回完成要求和候选交接，校验目标与边界的结构一致性；它不判断用户实际授权，不启动子任务，不查询业务，不核实成稿存在或远端生效。具体阶段验收按[决策与阶段交付](sales-growth-workflow.md#决策与阶段交付)和真实交付证据完成。

## 条件依赖与任务包

条件来自真实任务范围，不是可随意关闭的优化开关。任务事实已触发某条件时必须选择；模块、服务或能力还不能确定时，先说明缺少哪项决定，停止依赖该决定的动作，同时完成其他明确部分。直接广告路由默认加载广告修正规则；直接图片业务默认加载图片约定；商品修改/上新及标题应用默认加载字段边界，不能通过不传条件绕过。

```sh
# 纯本地状态与到期检查：不读取询盘/CRM业务原文
python3 scripts/task_context.py --route conversion_monitoring --phase monitor --role executor

# 这次只读取询盘，不无条件同时加载CRM
python3 scripts/task_context.py --route conversion_monitoring --phase monitor --role executor --condition inquiry

# CRM专项深析：完整CRM规则和来源，不加无关的询盘规则
python3 scripts/task_context.py --route conversion_analysis --phase evaluate --role executor --condition crm

# 人工发品回执需要后台核验：追加完整发品规则和实时工具约定
python3 scripts/task_context.py --route new_listing --phase receipt --role executor --condition data_query
```

主要条件：

| 条件 | 何时需要 |
|---|---|
| `strategy_refresh` | 首次真实业务、策略版本变化或约束不清时读完整本店策略；子任务已收到确认版本和适用约束可复用 |
| `data_query` | 读取真实业务数据，追加连接工具和数据交接原章节；源接口条件及实时 Schema 仍须核实 |
| `free_query` | 自由取数/RAG接口发现，另读完整自由取数来源；不以旧 API 文档替代实时发现 |
| `ads` | 任何广告分析、建议、执行或复核，追加已授权广告决策修正规则 |
| `images` / `apply_images` | 图片方案/生成/编辑，或上传并应用到商品；按实际动作分别保留图片后端及商品写入边界 |
| `sales_fields` / `stock_warning` | 销售SKU/尺寸/价格等字段，或库存预警核实；价格授权、字段限制和实时库存口径继续有效 |
| `inquiry` / `crm` | 实际询盘或CRM取数及解释；两者都需要才双载，不能以轻量检查名义省略适用规则 |
| `transfer_inquiry` / `crm_plan_query` | 转人工边界，或只读已有系统计划状态；分别要求先选择 `inquiry` / `crm` |

`conversion_analysis` 必须明确 `inquiry` 或 `crm`，不能以空范围启动深析。`conversion_monitoring` 无条件时只做本地状态工作；选择实际取数但未选业务范围会报错。只读系统计划确需原触达规则时加载完整原文，但操作范围仍限查询，不因此获得创建、开启或发送授权。

其他复合路由也必须选择实际模块：客户运营选 `crm`、`crm_maintenance`、`inquiry`、`reception`、`quotation`、`outreach`；ERP选 `jushuitan` 或 `jackyun`；连接/组件选 `connection` 或 `platform_components`；采购研究选 `sourcing` 或 `company`；买家事务选 `order`、`procurement_inquiry`、`fulfillment`、`aftersales`、`invoice`；分销选 `distribution_1688` 或 `cross_platform`。同时涉及多个模块时重复传 `--condition`，保留各自完整前置。具体可选条件和来源追加以脚本 `--details` 为准。

任务包另附目标、真实店铺引用和对象、实际周期/数据截止、有限证据路径、适用策略版本与约束、既有行动及授权。仅凭路径清单不能推定子 Agent 知道真实上下文，详见[最小任务包](delegation.md#最小任务包)。源码中的宿主命令、原角色名和权限声明不因读取而成为当前可执行工具。

## 原文章节读取

```sh
python3 scripts/task_context.py read 'references/runtime.md#连接和工具'
python3 scripts/task_context.py read 'references/runtime.md#商品编辑字段边界'
python3 scripts/task_context.py read 'references/sales-growth-workflow.md#两类观察'
python3 scripts/task_context.py --route title_optimization --phase plan --role executor --read
```

`read` 校验项目内相对路径和锚点，返回原文件完整章节，包含子章节，直到下一个同级或更高层标题。支持精确中文标题或普通 Markdown slug；不会将代码块中的 `##` 当作章节。缺失/重复锚点、绝对路径、目录、越界路径或越界符号链接都报错。正文保留原换行，不用模型重写。`--read` 仅打印简短任务头和选中的原文，避免先复制完整依赖详情。

`RULES.md` 和 `source/` 业务来源拒绝按锚点截断；选中后完整读取。来源加载索引提供必读来源入口、条件追加和 `source_followups`，来源内部更细的实际子流程要求仍须继续完整读取。索引不宣称已穷尽所有传递依赖。例如原标题来源要求首次执行不同能力前完整读对应 capability 文件，阶段清单已列主要能力前置；关键词能力通过 `title_keywords` 加载。图片模板按原文的具体分类选用，不把全部模板作为每日默认上下文。

## 离线校验

```sh
python3 scripts/task_context.py validate
python3 scripts/test_task_context.py
```

`validate_loading_contract(root, catalog)` 是供整包校验调用的纯读取函数，检查全部阶段、规则、条件、源文件、锚点和关键强制依赖。现有来源、完整业务规则与归档入口 SHA 校验继续由整包校验保留；新增加载元数据不改变来源校验基准。这些工具只读取本地文件，不访问网关、不执行业务、不触发调度，也不代表已经建立自动缓存或硬权限隔离。
