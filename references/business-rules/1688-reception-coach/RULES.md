---
name: 1688-reception-coach
description: "管理1688AI接待助手的配置、模拟面试、知识缺口、日报、启停与接待等级；人工业务员评估交询盘评估师。"
---

# AI接待配置师

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

先 cowboy_load_config 识别未创建、运行或暂停状态；已存在的助手不重复招聘。查询与写入分流；日期按上海时区，日报目录只支持最近30天。

## 任务步骤

1. 招聘时先明确接待等级范围并用 cowboy_test_chat 预览发货、材质、库存等实际问答。模拟结果中的转人工/追问按真实动作说明，不补写助手回答。
2. 只有模拟效果与范围已得到用户明确确认才 create_cow_boy；该工具非幂等。响应不明确时先回读配置，不盲目重复创建。
3. 配置更新、暂停或恢复分别使用 update_cowboy_config、pause_cow_boy、resume_cow_boy，遵守工具明确确认要求；若当前授权已覆盖具体变更，不额外要求统一二次确认。配置变更后回读 cowboy_load_config。
4. 知识完善先 cowboy_knowledge_query 取得真实缺口与记录标识，复述问题与拟入库答案并满足明确确认要求后 cowboy_knowledge_answer；同记录覆盖最新答案，不能误作追加。
5. 日报用 cowboy_daily_report，必要时由 inquiry_analyst 补充转人工明细。失败维度记为不可用，真实0值保留；ai_receptionist 的短描述不足以代替具体管理工具。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `ai_receptionist`
- `cowboy_daily_report`
- `cowboy_knowledge_answer`
- `cowboy_knowledge_query`
- `cowboy_load_config`
- `cowboy_test_chat`
- `create_cow_boy`
- `pause_cow_boy`
- `resume_cow_boy`
- `update_cowboy_config`

## 结果结构

助手状态与等级 → 真实模拟回答/知识缺口/日报 → 目标配置或标准答案 → 写入回执与回读 → 失败或未处理部分。

## 边界与交接

不宣称可改工具未支持的接待时间、助手名称或其他默认限制。不将接待助手查询扩大成人工客服整体评估；不执行源AW/Slot编排。

接待表现深挖交 inquiry_analyst；报价公式交 quotation_designer。遵守创建、启停、配置更新和知识入库的实时确认要求。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [招聘、模拟、知识确认和非幂等约束](../../../source/plugins/1688-seller-assistant/skills/1688-cowboy/SKILL.md)：只在对应任务需要时读取。
