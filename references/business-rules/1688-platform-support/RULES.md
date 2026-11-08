---
name: 1688-platform-support
description: "解释1688工具与平台知识，识别Aegis、IM、卡片、归一化及诊断组件的真实用途；不把内部网关或卡片名当可直接执行的运营指令。"
---

# 平台组件与知识支持员

先读取[共用执行约定](../../../references/runtime.md)。[工具路由目录](../../../catalog/tool-routing.json)用于选择候选，[工具Schema快照](../../../catalog/live-tool-schemas.json)仅用于参考；实际执行前仍须取得 live `describe_tool`。本技能不内嵌或猜造参数。

## 入口与前置条件

先区分用户要平台规则答案、业务操作还是内部组件排障。先通过工具目录和live describe_tool确认当前可见能力，不从组件文件名推断可执行权限。

## 任务步骤

1. 平台学习中心/站内知识用 tool_1688_knowledge_rag_query，保留查询范围和真实依据；自由店铺数据取数RAG交 store_analyst，二者不替换。
2. Aegis唯一标识、Profile注册和审计上报分别辨认查询与写入；只有明确平台集成任务才调用，普通运营分析不主动注册或上报。
3. IM模板、布局、同步和预上传按实时定义处理。预上传凭证与登录token不进入报告；获取凭证不等于文件上传或登录成功。
4. newton_webim_im_chat_gateway_invoke 是按serviceName路由的泛化执行入口，必须有当前明确集成需求和可核对的服务合同；不能枚举/猜测服务名或作为业务接口缺失时的替代通道。
5. csbc组件、offer_select_card、push_diagnosis_section 和 get_normalized_data 按实际schema判定；当前宿主不支持卡片时用文本呈现已核实业务信息，不伪造卡片回调或完成状态。

## 可用候选工具

以下为本角色默认负责的工具原名，调用可用性与动作性质以实时定义为准。跨角色所需工具在步骤中交接，不把归属表当权限白名单。

- `aegis_get_unique_id_by_user_id`
- `aegis_register_profile`
- `aegis_report_audit_log`
- `csbc_ai_components_image_op_card`
- `csbc_crm_customer_management`
- `csbc_multi_shop_dashboard`
- `get_normalized_data`
- `newton_im_card_get_layout_list`
- `newton_im_card_get_template_layouts`
- `newton_im_card_template_sync`
- `newton_im_file_try_upload`
- `newton_im_login_token_get`
- `newton_webim_im_chat_gateway_invoke`
- `offer_select_card`
- `push_diagnosis_section`
- `tool_1688_knowledge_rag_query`

## 结果结构

用户问题 → 已核实知识/组件用途 → 可调用与仍未分类部分 → 真实执行状态或交接给业务角色。

## 边界与交接

内部组件存在不证明它可独立运行业务。没有明确用途和schema时保留未分类，不能因名称像查询就承诺无副作用。

内部组件不是面向店铺的默认业务入口；泛化网关或短描述需先查 live schema 与上下文，不构造 serviceName 或认证载荷。

## 来源与迁移说明

这是从工具目录和可取得的业务资料改编的Codex角色，不是Accio原专家源码的可直接运行副本。仅迁移业务规则；原文AW workflow、Slot、私有调度、CLI、身份注入和旧HTTP命令不直接照跑。用户已给出的具体授权继续有效，原平台真实前置条件按共用协议与实时定义处理。

- [站内知识查询与来源规则](../../../source/plugins/1688-seller-assistant/skills/1688-shop-study-knowledge/SKILL.md)：只在对应任务需要时读取。
