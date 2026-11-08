# 客户运营静态总览

用户需要截图式概览、可保存页面或跨会话复盘时使用；普通统计问题直接回复即可。生成器只整理输入，绝不取数或执行计划。默认调用路径是当前宿主的 MCP 桥接，不直接访问 1688 私有 HTTP、取 Cookie 或搬运 Accio 前端包。

## 取数与输入

按 [查询流程](crm-query.md) 读取 `customer_stats` 和 `newton_ai_crm_plan_operation` 的 `operation=query`。保留当前店铺归属、真实取数时间以及返回错误；只读查询并不要求用户额外开启执行权限。

在本轮 `reports/` 中准备一个 JSON 对象：

```json
{
  "storeAttribution": "接口核实的店铺名称",
  "visibilityScope": "unknown",
  "observedAt": "2026-10-28T14:30:00+08:00",
  "stats": {"totalCount": 867, "site1688CustomerCount": 867, "recent7dNewCount": 59},
  "plans": [{"planId": "真实计划ID", "planName": "计划名称", "planType": "system", "strategyCode": "inquiry_convert", "status": "not_started", "customerCnt": 100}]
}
```

以上只是结构示例，不能当作当前数据；每次用真实返回替换。`stats/plans` 也接受工具的 `content[].text`、JSON 文本及 `data/result` 包装。输入中的计划标识必须来自真实查询；计划数组需要明确为计划记录，不从 `buyerInfoList/currentGroupList` 推算总人数。

`visibilityScope` 仅接受 `all_store`（已核实主账号全店）、`assigned`（已核实子账号名下）和 `unknown`（默认）。没有主/子账号范围证据就保留 `unknown`；店铺连接名称不能证明全店权限。报告使用“当前授权可见客户”，不能把接口 `totalCount` 自动描述为全店全部客户。

优先在工具结果的内存处理中提取白名单，再保存投影；文件命名和说明标明“派生摘要”，不能把重新包装后的投影称为完整原始回执。不要为了制表把整个计划响应内嵌的客户ID、联系方式、选中客户列表或其他私密内容落盘。脚本输出会再次白名单过滤，但不能撤销此前已保存原始客户明细的行为。不能以本脚本为客户全量导出通道。

保留输入缺失值和业务失败，不用零或旧成功结果补位。`observedAt` 是取数观察时间；计划分组的 `ds` 是该组数据日期，两者不互相替代。历史快照不得描述为实时页面。

## 执行

在项目根目录运行（路径可替换为本轮记录位置）：

```sh
python3 .agents/skills/1688-customer-conversion/scripts/crm_snapshot.py \
  --input reports/本轮/customer-overview-input.json \
  --json-out reports/本轮/customer-overview.json \
  --html-out reports/本轮/customer-overview.html
```

也可用 `--input -` 从标准输入接收 JSON。`--overwrite` 只用于已决定更新的本地输出；输入文件不得被覆盖。需要保留历史时使用不同文件名。脚本仅依赖 Python 标准库；离线测试：

```sh
python3 -m unittest discover \
  -s .agents/skills/1688-customer-conversion/scripts \
  -p 'test_crm_snapshot.py' -v
```

## 验收与交付

核对输出中的 `warnings`、来源状态、客户总数与计划覆盖人数，不能把服务端查询失败解释为 0 客户/0 计划。同计划去重只消除重复记录，冲突应保留告警。策略之间的客群可能重叠，不能相加冒充全店独立客户数；回复、成单和执行次数按各自口径展示。

页面提供统计卡、计划卡和状态汇总，不包含真实客户操作按钮、发送功能、自动刷新或第三方脚本。交付链接时说明店铺、取数时间及是否有缺失/失败。它是本地静态报告，不是完整 Accio MCP App 或服务端自动运营系统。
