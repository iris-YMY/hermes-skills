# Feishu API Patterns (Verified)

## Token Types & Ownership

| Token Type | How to Get | Doc Ownership | Visible in User's "我的文档"? |
|-----------|-----------|---------------|-------------------------------|
| `tenant_access_token` | `POST /auth/v3/tenant_access_token/internal` | App-owned | ❌ No |
| `user_access_token` | OAuth flow (`lark auth login`) → `~/.lark/tokens.json` | User-owned | ✅ Yes |

## Folder Creation

```bash
# Works with BOTH tenant and user tokens
POST /open-apis/drive/v1/files/create_folder
{"folder_token": "", "name": "Folder Name"}
```
- `folder_token: ""` creates in root drive
- Returns `data.token` (the folder token for subsequent operations)

## Document Creation

```bash
# Works with BOTH tenant and user tokens
POST /open-apis/docx/v1/documents
{"folder_token": "<token>", "title": "Doc Title"}
```
- Returns `data.document.document_id`
- ⚠️ `POST /open-apis/drive/v1/files/create_file` returns 404 — does not exist

## Writing Content

### Via lark-cli (RECOMMENDED for user docs)
```bash
lark doc append <doc_id> --text "Line1\nLine2\n### Heading"
```

### Via direct API
```bash
POST /open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children
{"children": [
  {"block_type": 2, "text": {"elements": [{"text_run": {"content": "Hello", "text_element_style": {"bold": true}}}]}}
]}
```
- `block_type 2` = paragraph (the only reliable type for direct API writes)
- Use `text_element_style.bold: true` for heading-like emphasis
- ⚠️ **Block types 3 (heading2), 4 (heading3), 5 (heading4) and 31 (divider) FAIL with error 1770001** — use paragraph + bold styling instead
- ⚠️ Must use `"content"` NOT `"text"` in `text_run` — error 99992402 otherwise
- ⚠️ Use `--data-raw` instead of `-d` in curl for JSON with non-ASCII characters (Chinese), prevents encoding corruption
- 💡 Send in batches of ≤20 children per API call to avoid payload limits

## Block Deletion

```bash
DELETE /open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}
```
⚠️ **Returns 404** — this endpoint does not work reliably. Use `lark doc update-block` to overwrite content, or create a new document.

## Scope Requirements

| Operation | Required Scope | Token Type |
|-----------|---------------|------------|
| Create folder | `drive:drive` or `space:folder:create` | Tenant or User |
| Create doc in folder | `docx:document:create` | Tenant or User |
| Append content | `docx:document` | Tenant or User |
| Read doc content | `docx:document:readonly` or `docs:document.content:read` | Tenant or User |
| List drive items | `drive:drive:readonly` | Tenant or User |

## Bitable (多维表格) API

### Scope Requirement
- Need BOTH `bitable:app` AND `bitable:app:readonly` for full read-write access
- lark-cli default only includes `bitable:app:readonly` — must patch `internal/scopes/scopes.go`:
```go
"bitable": {
    Scopes: []string{"bitable:app", "bitable:app:readonly"},
}
```
Then rebuild + re-authorize.

### Core Endpoints (User Access Token)
```bash
# Create app
POST /bitable/v1/apps  {"name":"...","folder_token":""}

# Create table in app
POST /bitable/v1/apps/{app_token}/tables  {"table":{"name":"...","fields":[...]}}

# Create field (one-by-one, NOT batch — batch returns 404)
POST /bitable/v1/apps/{app_token}/tables/{table_id}/fields  {"field_name":"...","type":N}

# Batch create records (500/batch recommended)
POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create  {"records":[...]}

# Batch delete records
POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete  {"records":["rec_id1","rec_id2"]}

# Create view (grid/kanban/gallery/gantt/form ONLY)
POST /bitable/v1/apps/{app_token}/tables/{table_id}/views  {"view_name":"...","view_type":"grid"}
```

### Field Types
| Type | Name | Notes |
|------|------|-------|
| 1 | Text | Plain text |
| 2 | Number | Use `property.formatter: "0.00"` |
| 3 | SingleSelect | Options in `property.options` |
| 5 | DateTime | Value = millisecond Unix timestamp |
| 17 | Attachment | |
| 20 | Formula | `property.formula_expression` |

### ⚠️ Critical Limitations
- **Dashboard/chart views CANNOT be created via API** — `view_type` only accepts grid/kanban/gallery/gantt/form. Dashboards must be manually configured in the Feishu web UI. Once created, they auto-refresh when underlying data updates.
- **Field batch_create returns 404** — must create fields one-by-one
- **DateTime values**: Must be millisecond-precision Unix timestamps (e.g., `1780317947000`), NOT seconds

## lark-cli Scope Patch

If `drive:drive` is missing from user auth, add to `~/lark-cli/internal/scopes/scopes.go`:
```go
"documents": {
    Scopes: []string{..., "drive:drive", "drive:drive:readonly", ..., "space:folder:create"},
}
```
Then rebuild and re-authorize.
