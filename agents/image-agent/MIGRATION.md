# 迁移记录

基于2026-10-25本机文件制作；只表明本地存在这些资料，不保证与供应商最新云端版本或原始发行版一致。

| 原资料 | 运行中的适配位置 |
|---|---|
| `image-prompt-guide`，1个入口与37个参考 | `1688-image-design`；保留设计/编辑/翻译/版式方法，重写入口、执行合同和工作流 |
| `alibaba-image-generation`，11份文件 | `1688-image-edit` 的操作表与句式，结合主技能编辑参考 |
| `alibaba-global-ai-image-studio`，6份文件 | 合并重复操作；“一键优化”改为显式诊断，未复制专有优化算法 |
| 商品定招 `image-prompts`，6份文件 | 主技能的 `listing-recipes.md`；保留场景、细节、卖点、模特、工序表达 |
| `ai-product-designer` | `1688-product-visual-concepts`；保留概念比较，移除强制数量与供应商调用 |
| `Design Expert` 提示词 | 根 `AGENTS.md` 的任务路由和结果检查；移除原宿主界面、静默输出和自动记忆写入要求 |
| 1688插件路由与ImageAgent执行规约 | 可选 `accio-cloud-contract.md`；原文仅审计留档，不作为新Agent默认路由 |

## 必要变更

- `.agents/skills/` 提供项目技能结构，`AGENTS.md` 提供明确读取入口；`agents/openai.yaml` 提供技能UI元数据，不冒充独立Agent进程配置。
- 生成使用当前 `imagegen` 与实时工具schema，不携带原平台 `task_type`、固定轮询、i豆跳转链接或Host凭据机制。
- 图内中文按用户要求保留；不继承国际站强制英文、固定画面占比和默认省略prompt的云端策略。
- 2K是可选交付目标，不承诺后端固有尺寸。引用图的输入方式、透明处理和保存行为由当前生图路径决定。
- 未提及的标记默认保留，只在实质冲突时补问；用户已授权的步骤不再次设置确认门槛。
- 设计与商品事实分开。新增 `merchant-context.md` 支持批发采购语境，但不声称为官方平台政策。
- 不在每次任务自动写用户画像，不启动子Agent或后台任务，不修改现有桥与原Accio安装。

## 原文档案

完整65份来源按原字节保存在 `sources/accio/` 的 `.txt` 文件中，SHA-256见 `sources/manifest.json`。运行技能只链接适配后的内容，原文不进入技能自动发现路径。

原服务的认证、云端内部提示词、模型路由和计费均未复刻。`image_agent` 与 `image_agent_run` 的后端等价性未验证，真实生成质量需在用户选择后端和任务后实测。
