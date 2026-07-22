# Feishu Docx Block API — Patterns & Pitfalls

When creating a new Feishu docx document with structured content (code blocks, lists, headings) via the raw Docx API, the block schema is tricky. This reference documents what works and what doesn't.

## API Endpoints

| Action | Method | URL |
|--------|--------|-----|
| Create doc | POST | `/docx/v1/documents` |
| Write blocks | POST | `/docx/v1/documents/{doc_id}/blocks/{doc_id}/children` |
| Delete doc | DELETE | `/drive/v1/files/{doc_id}?type=docx` |

### Create Document in Specific Folder

```python
api("POST", "/docx/v1/documents", {
    "title": "Document Title",
    "folder_token": "<FOLDER_TOKEN>"  # skills folder or any folder
})
# Response: {"data": {"document": {"document_id": "xxx"}}}
```

### Write Blocks (Batch)

```python
api("POST", f"/docx/v1/documents/{doc_token}/blocks/{doc_token}/children", {
    "children": blocks,   # list of block objects
    "index": 0            # insertion position (optional)
})
```

## ⛔ CRITICAL: Max 50 Blocks Per Batch

API returns `99992402 "field validation failed"` with `field_violations: [{"field": "children", "description": "the max len is 50"}]` if you send more than 50 blocks. Split into batches.

## ⛔ CRITICAL: heading2/heading3 Blocks Fail

Block types 3 (heading2) and 4 (heading3) **consistently fail** with `1770001 "invalid param"` regardless of payload structure. Tested variants:
- `{"block_type": 3, "heading2": {"elements": [{"text_run": {"content": "..."}}]}}` → FAIL
- Adding `"style": {}` → FAIL
- Adding `"text_element_style": {}` inside text_run → FAIL

**Workaround**: Use bold text paragraphs with emoji prefixes:
```python
# H2 replacement
{"block_type": 2, "text": {"elements": [{"text_run": {
    "content": "📌 Heading Text",
    "text_element_style": {"bold": True}
}}]}}

# H3 replacement
{"block_type": 2, "text": {"elements": [{"text_run": {
    "content": "▸ Subheading Text",
    "text_element_style": {"bold": True}
}}]}}
```

## ⛔ CRITICAL: Image Blocks (block_type 27) Require Media Tokens

Image blocks require a **media token** from `drive/v1/medias/upload_all` — NOT `img_v3_xxx` from `im/v1/images` or file tokens from `drive/v1/files/upload_all`.

```python
# ✅ CORRECT (requires drive:drive scope)
{"block_type": 27, "image": {"token": "<MEDIA_TOKEN>", "width": 1080, "height": 1440}}

# ❌ FAIL: im/v1/images key → 1770001 invalid param
{"block_type": 27, "image": {"token": "img_v3_0213q_xxx", ...}}

# ❌ FAIL: drive/v1/files token → 1770001 invalid param
{"block_type": 27, "image": {"token": "KRngbSJQ3oZwkixM3QucU5kSndc", ...}}
```

Full details on the three upload APIs and their token types: see `references/feishu-docx-image-upload.md`.

## Working Block Types

### text (block_type: 2) — Paragraph
```python
{"block_type": 2, "text": {"elements": [{"text_run": {"content": "plain text"}}]}}
# With bold:
{"block_type": 2, "text": {"elements": [{"text_run": {
    "content": "bold text",
    "text_element_style": {"bold": True}
}}]}}
```

### code (block_type: 14) — Code Block
```python
{"block_type": 14, "code": {"elements": [{"text_run": {"content": "print('hello')"}}]}}
```
Multi-line code: join with `\n` into a single content string.

### bullet (block_type: 12) — Unordered List
```python
{"block_type": 12, "bullet": {"elements": [{"text_run": {"content": "list item"}}]}}
```

### ordered (block_type: 13) — Numbered List
```python
{"block_type": 13, "ordered": {"elements": [{"text_run": {"content": "numbered item"}}]}}
```

## Markdown → Blocks Parser Pattern

When converting a markdown file to Feishu blocks:

```python
blocks = []
lines = md_content.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith('## '):        # → bold text (📌 prefix)
        blocks.append(bold_paragraph("📌 " + line[3:].strip()))
    elif line.startswith('### '):     # → bold text (▸ prefix)
        blocks.append(bold_paragraph("▸ " + line[4:].strip()))
    elif line.startswith('```'):      # → code block
        i += 1; code = []
        while i < len(lines) and not lines[i].startswith('```'):
            code.append(lines[i]); i += 1
        blocks.append(code_block('\n'.join(code)))
        i += 1; continue
    elif line.startswith('- '):       # → bullet
        blocks.append(bullet(line[2:].strip()))
    elif line.strip():                # → text paragraph
        blocks.append(text_paragraph(line.strip()))
    i += 1
```

## Update Existing Block Text (PATCH)

### API Endpoint

| Action | Method | URL |
|--------|--------|-----|
| Update block text | PATCH | `/docx/v1/documents/{doc_id}/blocks/{block_id}` |

### Read Blocks First (GET)

```python
# List all blocks to find block_ids
api("GET", f"/docx/v1/documents/{doc_id}/blocks")
# Each block has: block_type, block_id, and content (text, bullet, etc.)
```

### Update Text Content

```python
update_payload = {
    "update_text_elements": {
        "elements": [
            {"text_run": {"content": "new text content"}}
        ]
    }
}
# PATCH /docx/v1/documents/{doc_id}/blocks/{block_id}
```

### ⛔ CRITICAL: Tenant Token → 403 Forbidden on Block Update

| Token Type | Read Blocks (GET) | Update Block (PATCH) |
|-----------|-------------------|---------------------|
| Tenant token | ✅ Works | ❌ 403 Forbidden |
| User OAuth token | ✅ Works | ✅ Works |

**Always use User OAuth token for block updates.** Read from `~/.lark/tokens.json`:
```python
with open("/home/ubuntu/.lark/tokens.json") as f:
    token = json.load(f)["access_token"]
```

## Complete Workflow

1. Get tenant_access_token via `/auth/v3/tenant_access_token/internal`
2. Create document: `POST /docx/v1/documents` with title + folder_token
3. Parse markdown into blocks (headings → bold text workaround)
4. Write blocks in batches of ≤50
5. Document URL: `https://open.feishu.cn/docx/{doc_token}`

## Python Helper Script

See `scripts/create_feishu_docx.py` for a reusable implementation.

## ⛔ CRITICAL: Folder Token Must Match Token Type

| Folder | Token Required | Folder Token |
|--------|---------------|--------------|
| App root folder | Tenant token ✅ | `""` (empty) or app-specific |
| User Skills folder | **User OAuth token** ✅ | `PdkOfBF0nlUKlkdVABZcYuKFneh` |
| User "My Folder" | **User OAuth token** ✅ | varies |

**Common failure**: Using tenant token to create docs in the Skills folder → `1770040 "no folder permission"` or doc lands in app root folder, invisible to user.

**Correct approach for Skills folder**: Use `lark doc create` (user OAuth) instead of raw curl:
```bash
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"
lark doc create --title "doc-name" --folder "PdkOfBF0nlUKlkdVABZcYuKFneh"
lark doc append <doc_id> --text "content..."
```

If you MUST use raw curl with blocks (e.g., for batch block creation), first get a user OAuth token from `~/.hermes/profiles/hr-assistant/home/.lark/tokens.json` and use it as the `Authorization: Bearer <USER_TOKEN>` header instead of tenant token.

### image (block_type: 27) — Image Block

⛔ **Creating image blocks directly with token in children payload ALWAYS fails** (1770001). Must use 3-step method:
1. Create empty block: `{"block_type": 27, "image": {"width": 1080, "height": 1440}}` (no `"index"` param)
2. Upload: `drive/v1/medias/upload_all` with `parent_type=docx_image`, `parent_node={block_id}`
3. PATCH: `/docx/v1/documents/{doc_id}/blocks/{block_id}` with `{"replace_image": {"token": "{file_token}"}}`

Full details: see `references/feishu-docx-image-embedding.md`.

## Known Limitations

- **Tenant token only creates in app-accessible folders**: User personal folders (Skills folder, "My Folder") require OAuth user token.
- **No inline formatting in code blocks**: `text_element_style` inside `code` blocks is ignored.
- **No language specification**: Code blocks don't support syntax highlighting language tags.
- **Append-only after creation**: To reorder content, delete and recreate the document.
- **Image blocks cannot be created with token directly**: Must use 3-step method (see image section above).
- **`batch_delete` endpoint requires DELETE method**: POST returns 404.
- **Do NOT include `"index"` when creating image blocks**: Causes 1770001 error. Omit to append at end.
