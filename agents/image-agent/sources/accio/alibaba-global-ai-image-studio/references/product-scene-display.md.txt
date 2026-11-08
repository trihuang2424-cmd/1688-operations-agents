---
name: product-scene-display
description: 将商品图片合成到指定场景中展示，结果路径保存在json中。通过 mcp_call 工具调用商品场景展示服务处理图片，输入一张商品图片和场景描述prompt，输出场景展示后的图片路径。当用户需要在特定场景中展示商品、生成商品场景图、制作产品展示效果图时使用。
---

# 商品场景展示

## 功能说明

本 Skill 用于将商品图片合成到用户指定的场景中，生成商品场景展示图，适用于电商产品展示、营销素材制作、产品效果图生成等场景。

## 使用流程

### 1. 准备输入

- **图片输入**：一张商品图片（支持常见格式：JPG、PNG、WEBP 等）
- **场景描述**：用户提供的场景 prompt，描述希望商品展示的场景

**场景描述示例：**
- "在现代化的客厅沙发上"
- "放在木质餐桌上，周围有鲜花装饰"
- "在阳光明媚的户外草坪上"
- "放在简约风格的办公桌上"

### 2. 调用 MCP 服务（两步调用）

商品场景展示需要调用两个 MCP 工具，按顺序执行：

#### 步骤 2.1：调用场景展示工具

使用 `mcp_call` 调用 `ggs_product_ai_image_generate` 工具：

```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_generate",
  "arguments": {
    "abilityCode": "ggsImageGenerate"
    "imageUrl": "<图片URL>",
    "prompt": "<用户场景描述>"
  }
}
```

**参数说明：**
- `abilityCode`：固定值 `ggsImageGenerate`（商品场景展示能力代码）
- `imageUrl`：输入商品图片的URL地址
- `prompt`：用户提供的场景描述，应尽量具体清晰

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

处理后的场景展示图 URL 为 `data.imageUrlList[0]`。

## 注意事项

1. **两步调用**：必须先调用 `ggs_product_ai_image_generate` 获取 requestKey，再调用 `ggs_product_ai_image_generate_result` 获取结果
2. **轮询机制**：第二步需要轮询获取结果，每 10 秒尝试一次，最多 10 次
3. **场景描述**：prompt 应尽量具体清晰，描述场景的环境、光线、风格等细节
4. **错误处理**：处理失败时检查 `success` 字段和 `errorMsg` 信息
5. **工具发现**：如不确定工具名称，可先使用 `mcp_call` 的 `action=search` 搜索：
   ```
   mcp_call {
     "action": "search",
     "keyword": "product_ai_image"
   }
   ```
6. **状态检查**：结果中的 `status` 字段表示处理状态，`status: 1` 表示成功
7. **超时处理**：如果 10 次轮询后仍未成功，应向用户报告超时错误

## 使用示例

**场景1：客厅展示**

用户："帮我把这个抱枕放到现代风格的客厅沙发上展示"

执行步骤：
1. 获取用户提供的商品图片路径
2. 获取用户场景描述：现代风格的客厅沙发上
3. 调用 `ggs_product_ai_image_generate` 工具获取 requestKey
4. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果（每10秒一次，最多10次）
5. 返回最终结果

**示例调用：**

第一步 - 调用场景展示：
```
mcp_call {
  "action": "mcp",
  "name": "ggs_product_ai_image_generate",
  "arguments": {
    "abilityCode": "ggsImageGenerate"
    "imageUrl": "https://sc01.alicdn.com/kf/H5b56916614944dafaa06ea9f03aff8979.jpg",
    "prompt": "现代风格的客厅沙发上"
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

**场景2：办公场景**

用户："我想看看这个笔记本放在办公桌上是什么效果"

执行步骤：
1. 获取用户提供的商品图片路径
2. 获取用户场景描述：放在办公桌上
3. 调用 `ggs_product_ai_image_generate` 工具获取 requestKey
4. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果
5. 返回最终结果

**场景3：户外场景**

用户："帮我生成这张户外背包在山间小路上的场景图"

执行步骤：
1. 获取用户提供的商品图片路径
2. 获取用户场景描述：在山间小路上
3. 调用 `ggs_product_ai_image_generate` 工具获取 requestKey
4. 轮询调用 `ggs_product_ai_image_generate_result` 工具获取处理结果
5. 返回最终结果

**成功后输出示例：**

已经帮你生成图片

![](https://sc04.alicdn.com/kf/H696151c21a7342229edefd0b3769a579S/200042360/H696151c21a7342229edefd0b3769a579S.png)

基于该图唤起[创意工坊](https://aistudio.alibaba.com/ggs-ai-studio#/creative-workshop/imageExtraction)进行自由创作
