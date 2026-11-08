# 安装验证

验证日期：2026-10-25。

目录整理：本项目已移至 `agents/image-agent/`。下方命令与 `validation-discovery.json` 保留迁移前实际检查的原始路径；当前打开路径见 [README.md](README.md)。

## 结果

| 项目 | 结果 |
|---|---|
| Codex项目入口 | 本机 `codex debug prompt-input` 返回的模型上下文包含本项目AGENTS.md |
| 项目技能发现 | 实际技能目录列出1688-image-design、1688-image-edit、1688-product-visual-concepts，根路径为本项目 `.agents/skills` |
| 技能结构 | 三个技能均通过系统skill-creator的quick_validate.py验证函数 |
| UI元数据 | 三份openai.yaml可解析，默认提示词包含技能名，自动选择已开启，短描述长度符合要求 |
| 活跃参考 | 42份参考文档；技能及项目文档的相对链接检查通过 |
| 原文档案 | 65份文件的SHA-256与复制前记录一致，当前Accio原文件也未改变 |
| 可见目录 | `skills/`相对链接正确指向 `.agents/skills/` |

上下文检查使用本机Codex的本地渲染命令，未请求模型推理：

```sh
codex --no-daemon -C '/Users/shileqi/1688运营agents/image-agent' debug prompt-input
```

机读结果见 [validation-discovery.json](validation-discovery.json) 和 [validation-structure.json](validation-structure.json)。检查输出只保留必要的结构与布尔结果，未保存全局模型上下文或凭据。

默认Python与桌面依赖Python缺少PyYAML，因此验证器使用本机现有缓存中的PyYAML运行，没有安装依赖或修改系统环境。该包本身不需要Python依赖即可被Codex读取。

## 内容审查与未验证范围

已检查适配后的技能不存在必须使用Accio专用生图参数、强制英文成图、自动写用户记忆或静默切换原云端的执行要求。原协议只保留为明确选择该服务时的兼容说明和审计原文。

官方在线文档请求返回403，本次加载兼容性结论依据本机Codex实际输出及已安装系统技能说明，而非未打开的网页。

未进行生图、视频或线上商品变更，也未做独立模型行为评测。没有验证每个Codex会话的图片工具可用性、不同生图后端的质量、原Accio云端Agent等价性与计费。当前结果证明项目可读取、技能可发现及文件结构完整，不证明生成效果已与原服务一致。
