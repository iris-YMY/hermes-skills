# Feishu Docx Image Embedding — Complete Reference

## The Problem

Feishu docx image blocks (block_type 27) require a **media token** — but getting the right type of token is non-trivial. There are 3 upload APIs, and only one combination works for docx image embedding.

## ⛔ Three Upload APIs and Their Token Types

| API | Token Format | Works in docx image block? | Required Scope |
|-----|-------------|---------------------------|---------------|
| `POST /im/v1/images` | `img_v3_0213q_xxx` | ❌ 1770001 invalid param | `im:resource` |
| `POST /drive/v1/files/upload_all` | `KRngbSJQ3oZwkix...` (file token) | ❌ 1770001 invalid param | `drive:drive` |
| `POST /drive/v1/medias/upload_all` | `CYgtbXBoHo2M...` (media token) | ✅ Works (with correct parent) | `drive:drive` |

## ⛔ CRITICAL: parent_type=docx_image + parent_node={block_id}

The `drive/v1/medias/upload_all` API has multiple `parent_type` values. **Only `docx_image` works for docx embedding**, and `parent_node` MUST be the **block_id** (not the doc_token).

| parent_type | parent_node | Result |
|------------|-------------|--------|
| `ccm_import_open` | `doc_image` | ❌ 1061004 forbidden |
| `ccm_import_open` | (empty) | ❌ 1061004 forbidden |
| `explorer` | (empty) | ✅ Uploads but token NOT usable in docx blocks |
| `doc_image` | {doc_token} | ❌ 1061044 parent node not exist |
| `doc_image` | {root_folder} | ❌ 1061044 parent node not exist |
| `docx_image` | {doc_token} | ✅ Uploads but token NOT linked to block |
| **`docx_image`** | **{block_id}** | ✅ **CORRECT — token accepted by replace_image** |

## The 3-Step Method (CONFIRMED WORKING 2026-07-21)

### Step 1: Create Empty Image Block

```python
POST /docx/v1/documents/{doc_id}/blocks/{doc_id}/children
{
    "children": [
        {"block_type": 27, "image": {"width": 1080, "height": 1440}}
    ]
}
```
- ⛔ **Do NOT include `"index"` parameter** — causes 1770001 error
- Returns `data.children[0].block_id` → use in Step 2

### Step 2: Upload Image for Block

```bash
curl -X POST "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -F "file_name=image.jpg" \
  -F "parent_type=docx_image" \
  -F "parent_node={BLOCK_ID}" \
  -F "size={FILE_SIZE}" \
  -F "file=@/path/to/image.jpg"
```
- Returns `data.file_token` → use in Step 3

### Step 3: PATCH Block with Image Token

```python
PATCH /docx/v1/documents/{doc_id}/blocks/{block_id}
{
    "replace_image": {
        "token": "{file_token}"
    }
}
```
- ✅ Returns `data.block.image.token` populated with the media token
- Works with tenant token (no need for user OAuth)

## Batch Processing Pattern

```python
for i, image_path in enumerate(images):
    # Step 1
    r = create_empty_image_block(doc_id, token)
    block_id = r["data"]["children"][0]["block_id"]
    
    # Step 2
    media_token = upload_for_block(image_path, doc_id, block_id, token)
    
    # Step 3
    patch_image_block(doc_id, block_id, media_token, token)
    
    time.sleep(0.3)  # Rate limit
```

## Deleting Broken Image Blocks

Empty image blocks (token="") show as "upload failed" in the Feishu UI.

```bash
# DELETE method (NOT POST — POST returns 404)
DELETE /docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete
{"start_index": N, "end_index": M}
```
- `start_index` is 0-based position in block list (0 = page block)
- `end_index` is exclusive
- Use GET blocks first to find positions of broken blocks

## Permission Requirements

- `drive:drive` scope needed for `drive/v1/medias/upload_all`
- `im:resource` scope needed for `im/v1/images` (not useful for docx anyway)
- hr-assistant app (`cli_aa9ebcbfc6e35cba`) confirmed working as of 2026-07-21

## Script

See `scripts/embed_docx_images.py` for a reusable batch implementation.
