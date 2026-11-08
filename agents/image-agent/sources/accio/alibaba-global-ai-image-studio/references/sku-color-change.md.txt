---
name: sku-color-change
description: 将商品图片中的指定区域更换为指定颜色，结果路径保存在json中。通过 mcp_call 工具调用 SKU 换色服务处理图片，输入原图、换色区域prompt和目标颜色hex值，输出生成的换色后图片路径。当用户需要将商品换色、改变商品颜色、调整商品颜色时使用。
---

# SKU 换色功能

## 功能说明

本 Skill 用于将商品图片中的指定区域更换为指定颜色，适用于商品多颜色展示、SKU颜色变体生成等场景。

## 使用流程

### 1. 准备输入

- **原图**：需要换色的商品图片 URL
- **prompt**：描述换色区域（如：衣服的主体、包包的皮革部分、鞋子的鞋面等）
- **hexColor**：目标颜色的十六进制色值（如：#FF0000 表示红色，#0000FF 表示蓝色）
  - 如果用户输入的是颜色名称（如"红色"、"蓝色"），需要将其转换为对应的 hex 色值

### 2. 调用 MCP 服务（两步调用）

SKU 换色需要调用两个 MCP 工具，按顺序执行：

#### 步骤 2.1：调用 SKU 换色工具

使用 `mcp_call` 调用 `ggs_product_ai_image_color_change` 工具：

```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_color_change",
  "arguments": {
    "imageUrl": "<图片URL>",
    "prompt": "<换色区域描述>",
    "hexColor": "<目标颜色hex值>"
  }
}
```

**参数说明：**
- `imageUrl`：输入图片的 URL 地址
- `prompt`：描述换色区域，如"商品主体"、"衣服的主体"、"包包的皮革部分"
- `hexColor`：目标颜色的十六进制色值，如"#FF0000"

**返回示例：**
```json
{
  "success": true,
  "data": "c3282371-45d5-493e-a90e-00948eecb342"
}
```

从返回结果中获取 `data` 字段作为 `requestKey`，用于下一步查询结果。

#### 步骤 2.2：获取处理结果（轮询机制）

由于图片处理需要时间，第二步需要采用**轮询机制**获取结果：

- **轮询间隔**：每 10 秒尝试一次
- **最大尝试次数**：10 次（最长等待 100 秒）

使用上一步返回的 `requestKey` 调用 `ggs_product_ai_image_generate_result` 工具：

```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_generate_result",
  "arguments": {
    "requestKey": "<步骤2.1返回的data值>"
  }
}
```

**参数说明：**
- `requestKey`：步骤 2.1 返回的 `data` 字段值

**轮询逻辑：**

1. 首次调用后检查 `data.status` 字段
2. 如果 `status: 1` 且 `success: true`，返回结果
3. 如果仍在处理中，等待 5 秒后再次调用
4. 重复步骤 2-3，最多尝试 10 次
5. 如果 10 次后仍未成功，返回超时错误

**返回示例：**
```json
{
  "data": {
    "imageUrlList": [
      "https://sc04.alicdn.com/kf/H696151c21a7342229edefd0b3769a579S/200042360/H696151c21a7342229edefd0b3769a579S.png"
    ],
    "status": 1
  },
  "errorCode": null,
  "errorMsg": null,
  "success": true
}
```

处理后的图片 URL 在 `data.imageUrlList[0]` 中。

### 3. 输出结果

**重要：直接原样返回第二个 MCP 工具的 JSON 响应结果，不要做任何额外操作。**

- ✅ 正确：返回 `ggs_product_ai_image_generate_result` 的完整 JSON 响应
- ❌ 错误：下载处理后的图片、保存文件、尝试查看图片等

最终返回示例：
```json
{
  "data": {
    "imageUrlList": [
      "https://sc04.alicdn.com/kf/H696151c21a7342229edefd0b3769a579S/200042360/H696151c21a7342229edefd0b3769a579S.png"
    ],
    "status": 1
  },
  "errorCode": null,
  "errorMsg": null,
  "success": true
}
```

处理后的换色图 URL 为 `data.imageUrlList[0]`。

## 颜色名称转 Hex 色值对照表

当用户输入颜色名称时，使用以下对照表转换为 hex 色值：

| 颜色名称 | Hex 色值 |
|---------|---------|
| 红色 | #FF0000 |
| 绿色 | #00FF00 |
| 蓝色 | #0000FF |
| 黄色 | #FFFF00 |
| 黑色 | #000000 |
| 白色 | #FFFFFF |
| 紫色 | #800080 |
| 橙色 | #FFA500 |
| 粉色 | #FFC0CB |
| 灰色 | #808080 |
| 棕色 | #A52A2A |
| 青色 | #00FFFF |
| 深蓝色 | #00008B |
| 浅蓝色 | #ADD8E6 |
| 米色/米白色 | #F5F5DC |
| 酒红色 | #722F37 |
| 藏青色 | #000080 |
| 墨绿色 | #006400 |

## 注意事项

1. **两步调用**：必须先调用 `ggs_product_ai_image_color_change` 获取 requestKey，再调用 `ggs_product_ai_image_generate_result` 获取结果
2. **轮询机制**：第二步需要轮询获取结果，每 10 秒尝试一次，最多 10 次
3. **prompt 规范**：
   - 必须明确指定要换色的区域，如"商品主体"、"衣服的主体"、"包包的皮革部分"、"鞋子的鞋面"等
   - 如果用户没有指定换色区域，默认使用"商品主体"
4. **hexColor 规范**：
   - 必须是有效的十六进制色值格式，如"#FF0000"
   - 如果用户输入颜色名称，需先转换为对应的 hex 色值
   - 支持 3位简写（如"#F00"）和 6位完整格式（如"#FF0000"）
5. **错误处理**：处理失败时检查 `success` 字段和 `errorMsg` 信息
6. **状态检查**：结果中的 `status` 字段表示处理状态，`status: 1` 表示成功
7. **超时处理**：如果 10 次轮询后仍未成功，应向用户报告超时错误

## 使用示例

**场景：将红色衣服换成蓝色**

用户："帮我把这件红色衣服换成蓝色"

执行步骤：
1. 获取用户提供的原图 URL
2. 识别换色区域："衣服的主体"
3. 将颜色名称"蓝色"转换为 hex 色值："#0000FF"
4. 调用 `ggs_product_ai_image_color_change` 工具获取 requestKey
5. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果（每10秒一次，最多10次）
6. 返回最终结果

**示例调用：**

第一步 - 调用 SKU 换色：
```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_color_change",
  "arguments": {
    "imageUrl": "https://sc01.alicdn.com/kf/H5b56916614944dafaa06ea9f03aff8979.jpg",
    "prompt": "衣服的主体",
    "hexColor": "#0000FF"
  }
}
```

第二步 - 轮询获取结果（使用第一步返回的 data 值）：
```
# 最多尝试 10 次，每次间隔 10 秒
for attempt in range(1, 11):
  mcp_call {
    "action": "mcp",
    "name": "ggs_product_ai_image_generate_result",
    "arguments": {
      "requestKey": "c3282371-45d5-493e-a90e-00948eecb342"
    }
  }
  
  # 检查结果
  if success == true and status == 1:
    # 成功，返回 imageUrlList[0]
    break
  else:
    # 等待 5 秒后重试
    wait(10 seconds)
```

**成功后输出示例：**

已经帮你生成图片

![](https://sc04.alicdn.com/kf/H696151c21a7342229edefd0b3769a579S/200042360/H696151c21a7342229edefd0b3769a579S.png)

基于该图唤起[创意工坊](https://aistudio.alibaba.com/ggs-ai-studio#/creative-workshop/imageExtraction)进行自由创作
