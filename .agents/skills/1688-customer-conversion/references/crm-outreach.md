# 计划、话术与实际触达

先读[原触达完整规则](../../../../references/business-rules/1688-outreach-operator/RULES.md)及其来源，沿用[执行协议](../../../../references/execution-protocol.md)。本适配用当前 MCP 与明确文本承接原卡片流程；不运行 AW、Slot、私有 CLI，不伪造组件执行锁或回调。这里只提供工作流和参数依据，没有开启计划或发送客户消息。

## 计划先行

1. 用 live `describe_tool` 核验 `newton_ai_crm_plan_operation`，查询真实 `planId`、客群、`actionConfig`、当前状态和权限；不要从名称猜 ID。查询可对子账号开放，创建和调整仅主账号。既有计划修改前必须按 ID 查询。
2. 新建先按[客户查询](crm-query.md)圈选、确认服务端总人数。单计划最多 100 人，准备批次也最多 100；超限时给出金额、活跃时间等允许条件的收窄方案，等用户选择，不静默截断、自行拆计划或改条件反复创建。既有明确选择继续沿用。
3. 创建参数包含计划名、已圈选目标与动作，创建授权不等于发送授权；创建返回 ID 后立即回读实际人数、被剔除人数和动作。已产生计划即使部分客户被剔除也不能重建、补建或重试。
4. 状态修改只使用 live 支持的 `open/pause/resume/finish`，同一计划串行。执行前确认状态已可执行。前端 `updateConfig`、自动模式或配置更新能力不能直接等同于 MCP `modify`；当前 Schema 未明确支持的变更不试写，交付待配置项。

以下是业务 `arguments` 示意，所有占位值须替换为本轮查询的真实对象；实际调用仍先 live describe。创建的 `actionConfig` 是 JSON **字符串**：

```json
{"operation":"create","planName":"已授权的计划名","target":{"mode":"ids","buyerLoginIds":["本次查询所得完整客户标识"]},"actionConfig":"{\"actions\":[{\"actionPoint\":\"wangwang_script\"}]}"}
```

状态变更示意：`{"operation":"modify","planId":"真实计划ID","planOperation":"pause"}`。`target.mode` 的 `filters/filter` 存在来源差异，见[来源登记](provenance.md)；按 live 定义核对，不靠创建请求试参，必要时采用已明确圈选的 `ids`。

## 准备与授权

完整用户话术原样使用，不查询画像或生成改写；仅有风格/目标时生成。统一模式用计划公共事实生成一次；个性化模式读取缓存画像，调用 `a2a_501498_newton_buyer_script_generator`，其输入形态为 `{"input":"已核验的买家事实、计划目标和商家要求"}`。画像缺失时用已知事实继续准备，不虚构需求；单客生成失败按原规则用安全短话术，禁止把推测写成购买事实。生成可能使用云端 AI 配额，不等于发送。

以可核对文本呈现目标范围/人数、渠道、最终话术模式、优惠金额和门槛、提醒接收者及执行时机。用户已经明确授权相同对象、内容和渠道时直接继续，不重复确认；只要求方案/草稿时先完成可审阅内容，再询问缺少的发送授权。旺旺、优惠券和小二提醒各自识别授权，不捆绑扩大范围。小二接收者必须从当前计划 `subAccountList` 的 ACTIVE 渠道候选明确选定，不能默认第一个、店主或 `ownerLoginId`；支持渠道以 live 契约为准。

`wangwang_coupon` 包含随券话术，不能再对同一批客户额外发送 `wangwang_script`；小二提醒作为独立动作，在前一动作收口后处理，取消或未获相应授权不继续。普通回复不展示客户画像原文、完整逐客名单、token 或原始回包；提供最多 20 条脱敏示例与可审阅的内容摘要。

## 实发契约和防重

调用前 describe `newton_ai_crm_customer_reach`。显式传真实 `planId`、授权客群、计划已有的 `actionPoint`、`requestId`、`triggerType=agent`；禁止省略买家范围让工具默认发送全量。`buyerLoginIds` 是逗号分隔字符串，旺旺按逐客调用，提醒将已授权范围合并为一次请求。`actionParams` 必须是以下对象序列化后的 JSON 字符串，不能传对象或计划配置结构：

| 行动点 | `actionParams` 内容 | 额外校验 |
|---|---|---|
| `wangwang_script` | `{"text":"最终完整话术"}` | text 非空，不携带券面字段 |
| `wangwang_coupon` | `{"text":"最终随券话术","couponAmount":10,"amountLimit":100}` | text 非空；满 > 减 > 0 且减 ≤ 满的 20%；示例金额不是默认授权 |
| `channel_remind` | `{"title":"客户跟进提醒","content":"已授权提醒正文","channel_type":"wechat_work"}` | 顶层同时传真实 `targetLoginId` 和 `channelType`，与所选激活候选一致 |

示意形态：

```json
{"planId":"真实计划ID","actionPoint":"wangwang_script","buyerLoginIds":"契约支持的真实业务客户标识","actionParams":"{\"text\":\"已授权的最终话术\"}","requestId":"本次行动已持久化的唯一轮次键","triggerType":"agent"}
```

`LOGINID_..._LOGINID` 原样保留于内部交接。上游组件曾在实发前解码，但本桥接尚未实测该标识契约；不能擅自解码、重新编码或输出明文。若 live 工具不能确认接受现有包装标识且没有合法可用标识，停止该实发步骤并报告前置缺口，继续交付已完成方案。

实发前按执行协议持久化行动 ID、店铺引用、计划 ID、授权依据、目标范围摘要、内容版本和稳定 `requestId`。同 `requestId + 同客户 + 同行动点` 为服务端声明的幂等键；恢复同一行动沿用原键，不生成新键重新发送。相同计划只安排一个执行者；记录协议不是自动锁，不能声称已有进程级防重。

超时、断线或回包不明时标记“未知”，先查询同计划及对应执行/跟进记录，核对本轮动作、客户与时间后再决定是否继续。汇总人数或模型生成的跟进摘要不能单独证明某条消息已送达；无法排除已发送时保留未知，禁止盲重试或新建计划重发。创建超时也先查同店已有计划，不换名重建。

当前目录尚未核验到可按 `requestId + 客户 + 行动点` 精确回查的独立执行记录工具。先使用已保存的原始逐项回执和实际可发现的只读接口；`get_followup_record_by_buyer` 的模型摘要只能作为辅助，不能替代逐项送达/发券证据。不猜造回查工具或参数；无法核定上一轮执行结果时，保留未知并完成可交付的状态说明，不能为“继续处理”重新生成轮次键。

按真实业务回执分别结算成功、失败、跳过、未知，区分执行次数和去重客户人数；准备完成、计划 running、HTTP 成功或请求受理均不等于送达。交付聚合结果、可核对回执摘要与待处理项。短信及服务端每日自动调度仅见于 UI/部分 Schema，当前未验证，不承诺短信成功、定时发送或后台持续运行。
