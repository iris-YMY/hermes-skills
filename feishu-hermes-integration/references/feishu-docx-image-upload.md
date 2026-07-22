# Feishu Docx Image Upload & Embedding — API Patterns (2026-07-21)

## Three Image Upload APIs — Which One to Use

| API | Endpoint | Returns | Use In Docx? | Scope Needed |
|-----|----------|---------|--------------|--------------|
| IM Image | `POST /im/v1/images` | `img_v3_xxx` | ❌ Cannot embed in docx | `im:resource` (app scope) |
| Drive Media | `POST /drive/v1/medias/upload_all` | `file_token` (media type) | ✅ Designed for docx embedding | `drive:drive` (app scope) — often forbidden |
| Drive File | `POST /drive/v1/files/upload_all` | `file_token` (file type) | ❌ Wrong token type for docx blocks | `drive:drive` (user OAuth OK) |

## ⛔ CRITICAL: `im/v1/images` Keys CANNOT Be Embedded in Docx

`POST /im/v1/images` successfully uploads and returns `img_v3_0213q_xxx` keys. However:
- These keys are for **IM message images only** (chat cards, rich text messages)
- Using them in docx block_type 27 image blocks → `1770001 "invalid param"` regardless of payload structure
- Confirmed with: `{token: "img_v3_xxx", width: 700, height: 933}` → FAIL
- Confirmed with: `{token: "img_v3_xxx"}` (no dims) → FAIL
- Confirmed with: `{token: "img_v3_xxx", width: 1080, height: 1440, align: 1}` → FAIL

## ⛔ CRITICAL: `drive/v1/files/upload_all` Tokens Are File Type, Not Media Type

`POST /drive/v1/files/upload_all` (user OAuth token works) returns a file token like `KRngbSJQ3oZwkixM3QucU5kSndc`. But:
- This is a **file** token, not a **media** token
- Using in docx image block → `1770001 "invalid param"`
- The docx API distinguishes between file tokens and media tokens

## ✅ Correct Path: `drive/v1/medias/upload_all`

This is the ONLY API that produces media tokens usable in docx image blocks.

```bash
curl -s -X POST "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -F "file_name=image.jpg" \
  -F "parent_type=ccm_import_open" \
  -F "parent_node=doc_image" \
  -F "size=<FILESIZE_BYTES>" \
  -F "file=@/path/to/image.jpg"
```

**Required scope**: `drive:drive` (application-level permission)
**Common error**: `1061004 "forbidden"` — app lacks `drive:drive` scope
**Fix**: Go to Feishu Open Platform → App Settings → Permissions → Enable `drive:drive` → Publish new version

### parent_type / parent_node Combinations

| parent_type | parent_node | Works? |
|-------------|-------------|--------|
| `ccm_import_open` | `doc_image` | ✅ Standard for doc images |
| `ccm_import_open` | `""` (empty) | ❌ forbidden |
| `doc_image` | doc_id | ❌ parent node not exist (doc_id is not a folder) |
| `bitable_file` | `""` | ❌ parent node not exist |

## Block Type 27 (Image) — Payload Format

### What Works (when you have a valid media token)
```json
{
  "block_type": 27,
  "image": {
    "token": "<MEDIA_TOKEN_FROM_DRIVE_MEDIAS>",
    "width": 1080,
    "height": 1440
  }
}
```

### What Creates Empty Blocks (no image rendered)
```json
// Elements wrapper — creates block but token is empty
{
  "block_type": 27,
  "image": {
    "elements": [{"text_run": {"content": "<IMG_KEY>"}}]
  }
}

// image_token field — accepted but image not rendered
{
  "block_type": 27,
  "image": {
    "image_token": "<IMG_KEY>",
    "width": 1080,
    "height": 1440
  }
}

// file_token field — accepted but image not rendered
{
  "block_type": 27,
  "image": {
    "file_token": "<FILE_TOKEN>",
    "width": 1080,
    "height": 1440
  }
}
```

### What Fails with `1770001 invalid param`
- `{token: "img_v3_xxx", ...}` — IM image keys
- `{token: "KRngbS...", ...}` — drive file tokens
- Any token field without valid media token

## Xiaohongshu Image Extraction Notes

When extracting image URLs from XHS SSR HTML:
1. URLs in JSON data contain `\\u002F` (double-escaped slashes) — must decode: `.replace('\\u002F', '/')`
2. CDN URLs are time-limited (~30min). Extract fresh URLs before downloading.
3. Use `urllib.request.urlretrieve` with `ThreadPoolExecutor(max_workers=5)` for parallel downloads — faster than sequential curl.
4. Pattern for H5_DTL scene URLs: `re.findall(r'"imageScene":"H5_DTL","url":"(http[^"]+)"', html)`
5. Fallback: `re.findall(r'src="(http://sns-webpic[^"]+!h5_1080jpg)"', html)`

## Recommended Workflow for XHS → Feishu Doc with Images

1. Fetch XHS HTML with mobile UA, extract image URLs (decode `\\u002F`)
2. Download images with ThreadPoolExecutor (fast parallel)
3. Upload to Feishu via `drive/v1/medias/upload_all` (needs `drive:drive` scope)
4. Create docx via `POST /docx/v1/documents`
5. Build blocks: text blocks + image blocks (block_type 27 with media token)
6. Write blocks in batches of ≤50
