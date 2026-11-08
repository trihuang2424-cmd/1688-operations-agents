---
name: 1688-image-edit
description: 修改已有1688商品图片，包括白底、换背景、SKU换色、Logo贴图、模特展示、局部细节、文字替换、图片翻译、清晰度及诊断优化。保持商品身份和未要求修改的内容；新套图规划使用1688-image-design。
---

# 商品图片编辑

整合本机图片生成、AI图片工作室和通用图片指南中的可迁移编辑方法。不是原工作室私有后端的复刻。

## 执行

1. 检查实际输入图，区分商品、编辑底图、人物、Logo、属性来源与风格参考。没有必要原图时先补齐，不能用文字重画冒充对原图的编辑。
2. 根据用户要求确定 **修改目标、目标状态、保留属性、必要连带变化**。读 [operations.md](references/operations.md) 的对应操作，再按需读取 [编辑工作流](../1688-image-design/references/image-edits.md) 与 [编辑句式](../1688-image-design/references/edit-patterns.md)。
3. 写完整提示词和引用角色。用户要“换颜色”不等于重做材质，要求“换视角”则不能同时禁止必要的投影和阴影变化。
4. 只要方案/提示词时不提交。实际执行读取 [Codex工具适配](../1688-image-design/references/generation-runtime.md) 和当前 `imagegen` 技能。
5. 检查改动是否实现、商品是否漂移、文字/标记是否准确、无关内容是否改变。无法确认原样保持时不能声称像素级一致；修复围绕观察到的问题进行。

## 特殊操作

- 图片翻译读 [翻译指导](../1688-image-design/references/image-translation.md)，建立区域与目标文案映射。产品固有标签与后加文案区分处理。
- Logo应用读 [品牌资产](../1688-image-design/references/brand-assets.md)，区分贴在物体表面与画布平面，不把角标压到商品上。
- 模特与试穿读 [类目关系](../1688-image-design/references/commerce-recipes.md)，正确处理接触、受力、遮挡、比例与原商品结构。
- “一键优化”先做 [可解释诊断](references/diagnose-optimize.md)，按实际缺陷调整，不声称复现云端专有打分。
- 多图按 [多输出规则](../1688-image-design/references/parallel-generation.md) 关联输入/输出；不复制原平台固定2秒提交间隔、固定轮询次数或数量上限。

用户已明确标记保留/移除范围时直接沿用；不因每个可见Logo都重复提问。未提及的标记默认保留；只有请求与标记处置存在实质冲突时补问。

保留源图和接受过的结果，交付实际图片与必要差异说明。生成编辑不默认上传图片银行或替换线上商品。
