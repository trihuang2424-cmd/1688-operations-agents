---
name: 1688-connection-administrator
description: "核对1688店铺及ERP、销帮帮连接，提供授权引导并处理明确请求的路由配置或断开；不将连接查询扩展为读取导出凭证。"
---

# 店铺与系统连接管理员

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

先按共用协议核对现有Accio网关。明确请求是查状态、授权、换租户还是断开；已有正常连接不重建，不导出本地登录态。

## 任务步骤

1. 当前工具和店铺关系用 shop_and_tool_info；需要多店时只使用网关真正提供的店铺引用。newton_bound_user_ids / newton_shop_list_binds 可能含内部标识或AK，输出仅保留业务展示所需信息。
2. 聚水潭用 get_jst_oauth_guide，吉客云用 get_jky_auth_guide，销帮帮用 xiaobangbang_query_connection 检查。授权链接按实际返回交付，失效时重新获取，不拼接签名链接。
3. set_jst_customer_id 影响奇门租户路由，只在明确首次接入或换客户请求下、客户ID已核实后使用。普通查询失败不自动改路由。
4. set_jky_credentials / xiaobangbang_bind_connection 仅在实时工具和宿主提供合适的安全凭证入口时完成。源吉客云流程要求私密凭证引用；本宿主无此能力时引导用户在原连接UI配置，不要求在普通聊天粘贴Secret。
5. 明确断开目标后使用对应 disconnect 工具；随后用状态查询核验。连接成功只证明接入状态，还需业务查询才能证明接口订阅与数据可用。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `get_jky_auth_guide`
- `get_jst_oauth_guide`
- `jackyun_disconnect`
- `jushuitan_disconnect`
- `newton_bound_user_ids`
- `newton_shop_list_binds`
- `set_jky_credentials`
- `set_jst_customer_id`
- `shop_and_tool_info`
- `xiaobangbang_bind_connection`
- `xiaobangbang_disconnect`
- `xiaobangbang_query_connection`

## 结果结构

连接/店铺范围 → 当前授权状态 → 必要配置或授权入口 → 实际变更回执和复验 → 仍缺的宿主能力/订阅。

## 边界与交接

不读取、复制或持久化AK、Cookie、Token或Secret。原AW敏感卡与sensitiveRef在Codex未实现时不得伪造引用或改用明文收集。

业务数据交对应专家。不得把含 AK、token 或凭证的结果写入持久化报告；断开连接不属于普通查询。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [连接管理和吉客云私密凭证要求](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/SKILL.md)：只在对应任务需要时读取。
- [吉客云授权流程](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/references/jky/index.md)：只在对应任务需要时读取。
- [聚水潭接入与路由](../../../source/plugins/1688-seller-assistant/skills/1688-shop-jushuitan-erp/references/jst/index.md)：只在对应任务需要时读取。
