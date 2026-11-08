---
name: remove-watermark
description: 从图片中移除水印、网站信息、联系方式或二维码，生成干净的图片。通过 mcp_call 工具调用水印移除服务处理图片，输入一张图片，服务自动检测并移除水印，输出处理后的图片路径。当用户需要去除图片水印、清除网站标识、移除联系方式或二维码时使用。
---

# 图片水印移除

## 功能说明

本 Skill 用于从图片中移除水印、网站信息、联系方式或二维码等不需要的元素，生成干净的图片，适用于电商产品图处理、图片素材净化等场景。

## 支持的移除类型

1. **水印** - 文字水印、图片水印、半透明水印等
2. **网站信息** - 网站URL、网站Logo、来源标识等
3. **联系方式** - 电话号码、微信号、QQ号等
4. **二维码** - 各类二维码图片

## 使用流程

### 1. 准备输入

- 输入：一张待处理的图片（支持常见格式：JPG、PNG、WEBP 等）
- 图片路径：用户提供的图片文件路径
- 服务将自动检测图片中的水印、文字、二维码等元素并移除

### 2. 调用 MCP 服务（两步调用）

水印移除需要调用两个 MCP 工具，按顺序执行：

#### 步骤 2.1：调用水印移除工具

使用 `mcp_call` 调用 `ggs_product_ai_image_generate` 工具：

```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_generate",
  "arguments": {
    "abilityCode": "ggsImageOptimize"
    "imageUrl": "<图片URL>",
    "prompt": ""
  }
}
```

**参数说明：**
- `abilityCode`：固定值 `ggsImageOptimize`（水印移除能力代码）
- `imageUrl`：输入图片的URL地址
- `prompt`：固定为空字符串

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

处理后的无水印图片 URL 为 `data.imageUrlList[0]`。

## 注意事项

1. **两步调用**：必须先调用 `ggs_product_ai_image_generate` 获取 requestKey，再调用 `ggs_product_ai_image_generate_result` 获取结果
2. **轮询机制**：第二步需要轮询获取结果，每 10 秒尝试一次，最多 10 次
3. **错误处理**：处理失败时检查 `success` 字段和 `errorMsg` 信息
4. **工具发现**：如不确定工具名称，可先使用 `mcp_call` 的 `action=search` 搜索：
   ```
   mcp_call {
     "action": "search",
     "keyword": "product_ai_image"
   }
   ```
5. **状态检查**：结果中的 `status` 字段表示处理状态，`status: 1` 表示成功
6. **超时处理**：如果 10 次轮询后仍未成功，应向用户报告超时错误
7. **版权注意**：请确保有权处理该图片，移除水印可能涉及版权问题

## 使用示例

**场景1：移除图片水印**

用户："帮我把这张图片上的水印去掉"

执行步骤：
1. 获取用户提供的图片路径
2. 调用 `ggs_product_ai_image_generate` 工具获取 requestKey
3. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果（每10秒一次，最多10次）
4. 返回最终结果

**示例调用：**

第一步 - 调用水印移除：
```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_generate",
  "arguments": {
    "abilityCode": "ggsImageOptimize"
    "imageUrl": "https://sc01.alicdn.com/kf/H5b56916614944dafaa06ea9f03aff8979.jpg",
    "prompt": ""
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

**场景2：移除网站标识**

用户："这张图片右下角有个网站地址，帮我删掉"

执行步骤：
1. 获取用户提供的图片路径
2. 调用 `ggs_product_ai_image_generate` 工具（`abilityCode: ggsImageOptimize`）获取 requestKey
3. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果
4. 返回最终结果

**场景3：移除二维码**

用户："帮我清除图片上的二维码"

执行步骤：
1. 获取用户提供的图片路径
2. 调用 `ggs_product_ai_image_generate` 工具（`abilityCode: ggsImageOptimize`）获取 requestKey
3. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果
4. 返回最终结果
