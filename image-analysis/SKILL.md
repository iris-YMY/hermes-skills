---
name: image-analysis
description: "图片分析：调用 qwen-vl-max 视觉模型，通过 vision_analyze 或 browser_vision 工具识别图片内容。"
---

# Image Analysis

## 前置条件

`config.yaml` 须包含：
```yaml
auxiliary:
  vision:
    provider: qwen
    model: qwen-vl-max
  compression:
    provider: qwen
    model: qwen-turbo
```

## 快速决策

| 条件 | 推荐方式 |
|------|---------|
| `auxiliary.vision` 已配置 | 方式1（vision_analyze） |
| `auxiliary.vision` 未配置 / 不确定 | **直接跳方式3**（方式1、2都会失败） |
| 方式1/2报 `model_not_found` | 方式3 |
| 方式3也失败 | 检查 API Key 是否有效 |

## 使用方式

### 方式1：vision_analyze 工具
```
vision_analyze(image_url="/path/to/image.jpg", question="描述/提取内容")
```
- `image_url`：本地路径或 http(s) URL
- 支持 JPG/PNG/WebP

### 方式2：browser_vision 工具
```
browser_navigate(url="http://localhost:8899/image.jpg")  # 先加载图片
browser_vision(question="描述/提取内容")                   # 再分析
```
适用于 `vision_analyze` 失败时的备选。

### 方式3：直接调 API（当工具不可用时）
```python
import base64, json, urllib.request
with open("image.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()
payload = {
    "model": "qwen-vl-max",
    "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
        {"type": "text", "text": "你的问题"}
    ]}],
    "max_tokens": 2000
}
req = urllib.request.Request("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    data=json.dumps(payload).encode(), method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", "Bearer <API_KEY from config.yaml>")
result = json.loads(urllib.request.urlopen(req, timeout=30).read())
print(result["choices"][0]["message"]["content"])
```

## 故障排查

| 错误 | 原因 | 修复 |
|------|------|------|
| `model 'gpt-4o-mini' does not exist` | auxiliary 未配置 | 添加 `auxiliary.vision` 到 config.yaml |
| `401 Unauthorized` | API Key 无效 | 检查 config.yaml `providers.qwen.api_key` |
| 中文 OCR 模糊 | qwen-vl-max 偶有遗漏 | 用方式3重试，或调大 max_tokens |
