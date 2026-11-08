# 1688 图片 Agent

面向 Codex 的项目式图片 Agent。由 Codex 负责商品理解、方案设计、提示词扩写、工具调用和结果检查；生图使用当前可用且用户选定的模型服务。

## 使用

在 Codex 中将 `/Users/shileqi/1688运营agents/agents/image-agent` 打开为项目并开始新对话。入口是 `AGENTS.md`，技能位于 `.agents/skills/`；可见的 `skills/` 是指向同一目录的相对符号链接。

也可在终端启动：

```sh
codex -C '/Users/shileqi/1688运营agents/agents/image-agent'
```

在其他会话中使用，可直接要求：“读取 /Users/shileqi/1688运营agents/agents/image-agent/AGENTS.md，并按其中的图片 Agent 处理本次需求。”

没有修改全局 Codex 配置，也没有创建新聊天、独立常驻服务或全局技能。其他项目不会因为这个目录存在而自动切换角色。

## 三个技能

| 名称 | 用途 |
|---|---|
| `1688-image-design` | 主副图、卖点图、详情页、营销图、套图风格、提示词设计与审查 |
| `1688-image-edit` | 白底、换背景、SKU换色、模特、Logo、文字、翻译、特写、清晰度、诊断优化 |
| `1688-product-visual-concepts` | 新产品外观概念、差异化方案与视觉交接 |

例如：“使用 $1688-image-design，为这个商品设计四张主副图，先只给提示词。”也可按自然语言选择技能。

## 迁移与边界

迁移本机通用图片指南及37份参考文档；整合国际站图片生成、AI图片工作室、商品套图模板和产品概念设计方法；重写工具、素材、任务状态和交付流程。详情见 [MIGRATION.md](MIGRATION.md)。

这是本地规则适配版，不是1688云端 ImageAgent 的完整克隆。私有诊断逻辑、云端内部系统提示词和模型权重并未取得。新增1688采购场景指导也不是平台官方政策。

生成依赖当前会话实际提供的 `imagegen` 技能和图片工具；安装技能不保证每个会话有可用生图工具。工具缺失时完成完整提示词，说明替代路径，不自动切换API或Accio云端。API路径需要自己的凭据和计费条件。

## 原文与验证

`sources/manifest.json` 记录65份本地原文的路径、字节数和SHA-256；`sources/accio/` 中是 `.txt` 档案，不参与技能选择。没有复制授权令牌、账户配置、日志、聊天记录或可执行程序。

结构、引用、原文校验和及Codex实际发现检查记录在 [VALIDATION.md](VALIDATION.md)。安装验证不执行付费生图、视频生成或线上商品变更。
