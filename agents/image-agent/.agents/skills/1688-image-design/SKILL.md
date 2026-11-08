---
name: 1688-image-design
description: 为1688商品规划和制作主图、副图、卖点图、详情页、场景图及营销套图，将简单需求转成有商品证据、准确文案和一致风格的提示词，并检查成图。也用于只看方案或提示词的请求；已有图片单项修改优先使用1688-image-edit。
---

# 1688 商品图片设计

将需求转为可交付图片，先区分提示词/方案交付与实际生图，遵循数量、尺寸、素材、风格和已确认选择。设计方法与执行后端分离，工具协议以当前schema为准。

## 工作流程

1. 读取真实素材，分配商品身份、编辑画布、样式、姿态、属性来源或品牌原件等角色。实际商品的参考图不能用文字猜测替代。
2. 为每张图确定六项：**买家问题、商品证据、画面关系、布局、准确文案、共享风格**。简短需求可补充合理视觉表达，不创造商品参数。1688任务按需读 [merchant-context.md](references/merchant-context.md)。
3. 读取下表对应参考，写出每张图完整提示词。保留精确文字和关键约束，不将已解决的构图关系压缩回“高级、专业”。
4. 检查需求覆盖、保留项与修改目标是否矛盾、参考图顺序与事实来源。只要方案或提示词时使用 [prompt-review.md](references/prompt-review.md)，到交付边界即停止。
5. 用户要求生图时读取 [generation-runtime.md](references/generation-runtime.md) 并执行。多图按 [parallel-generation.md](references/parallel-generation.md) 记录每项提示词、输入、依赖、实际结果和状态。
6. 检查实际商品结构、文案、物理关系、风格一致性及文件尺寸。范围内可针对明确错误修正一次；未完成和无法验证之处如实说明，不重复提交未知状态任务。

## 提示词结构

只填当前任务有用的项目；这是文字组织方式，不是API字段：

```text
Asset type: 图片用途。
Input images: 每张真实输入图的编号与角色。
Primary request: 用有依据的视觉内容回答本图的买家问题。
Canvas and composition: 布局、主体关系、必要留白、目标比例。
Materials, color and style: 已确认商品属性与共享视觉表达。
Typography: 逐字文案、位置、层级和语言。
Product invariants: 不可改变的真实身份与属性。
Avoid: 与任务有关的错误、虚构内容和不希望发生的变化。
```

按后端能力选择清晰的提示词语言。采用英文指令时，中文图内文字仍原样引用。用户已有详细提示词时只整理必要结构，不擅自扩写创意。

## 尺寸与交付

用户尺寸或已核实平台要求优先。没有指定时可将2K长边作为商业成图目标，不能当作所有后端支持的固定参数或承诺。生成尺寸、后处理尺寸和交付尺寸分别核实，不拉伸商品。

多张独立图片交付独立文件，联系表只是补充。详情页按需求交付各屏与拼接图，不增加用户未要求的整套。项目素材保存到工作目录，使用绝对路径预览。

## 按需参考

| 当前需要 | 读取 |
|---|---|
| 生图后端、输入、参数、交付 | [generation-runtime.md](references/generation-runtime.md) |
| 工作流接手、续接、部分成功 | [codex-orchestration.md](references/codex-orchestration.md) |
| 1688采购问题、商品事实、店铺数据 | [merchant-context.md](references/merchant-context.md) |
| 主图、材质、规格、使用、配件、对比 | [product-images.md](references/product-images.md) |
| 套图中的场景、模特、细节、卖点、工序 | [listing-recipes.md](references/listing-recipes.md) |
| 类目接触、穿戴、安装、结构 | [commerce-recipes.md](references/commerce-recipes.md) |
| 套图配色、字体、视觉关系 | [design-patterns.md](references/design-patterns.md) |
| 详情页拆屏、排版、长图 | [detail-pages.md](references/detail-pages.md) |
| 海报、促销、社交图片 | [marketing-images.md](references/marketing-images.md) |
| 字体、材质效果、视觉表达 | [visual-recipes.md](references/visual-recipes.md) |
| Logo、包装、品牌资产 | [brand-assets.md](references/brand-assets.md) |
| 工艺说明、规格示意、技术图 | [technical-visuals.md](references/technical-visuals.md) |
| 图片翻译 | [image-translation.md](references/image-translation.md) |
| 编辑与修复 | [image-edits.md](references/image-edits.md)、[edit-patterns.md](references/edit-patterns.md) |
| 生成前看提示词 | [prompt-review.md](references/prompt-review.md) |
| 多输出、依赖与状态 | [parallel-generation.md](references/parallel-generation.md) |
| 用户明确选择原云端Agent | [accio-cloud-contract.md](references/accio-cloud-contract.md) |

例子提供表达方法，不代表当前商品事实或1688现行官方规则。
