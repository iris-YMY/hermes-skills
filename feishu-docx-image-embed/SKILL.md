---
name: feishu-docx-image-embed
category: devops
description: 飞书docx文档嵌入图片（三步法）
---

# 飞书文档嵌入图片

## 三步法

### Step 1: 创建空图片block
```
POST /docx/v1/documents/{doc_id}/blocks/{doc_id}/children
body: {"children":[{"block_type":27,"image":{"width":1080,"height":1440}}]}
→ 返回 block_id
```
⚠️ **不要传 index 参数**（传了返回 invalid param）

### Step 2: 上传图片
```
POST /drive/v1/medias/upload_all (multipart form)
  -F parent_type=docx_image
  -F parent_node={block_id}    ← 必须是 Step1 的 block_id
  -F file=@image.jpg
→ 返回 file_token
```
⚠️ parent_type 必须是 `docx_image`（非 doc_image/ccm_import_open/explorer）
⚠️ parent_node 必须是 `block_id`（非 doc_id）

### Step 3: PATCH替换
```
PATCH /docx/v1/documents/{doc_id}/blocks/{block_id}
body: {"replace_image":{"token":"{file_token}"}}
```
⚠️ 操作名是 `replace_image`

## 权限
| 操作 | Token |
|------|-------|
| 创建block + PATCH | tenant_token |
| media上传 | tenant_token（需 im:resource:upload + drive 权限） |

## 删除blocks
```
DELETE /docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete
body: {"start_index":N,"end_index":M}
```
⚠️ 用 DELETE 方法（非 POST）
