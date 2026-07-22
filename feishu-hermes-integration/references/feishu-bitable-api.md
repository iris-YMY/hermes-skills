# Feishu Bitable API Patterns

## Creating a Bitable App
```
POST /bitable/v1/apps
Body: {"name": "...", "folder_token": ""}
→ Returns: app_token, default_table_id, url
```
Requires: `bitable:app` scope (NOT just `bitable:app:readonly`)
`folder_token: ""` creates in user's root (My Folder) when using user OAuth token.

## Field Creation (one-by-one only)
```
POST /bitable/v1/apps/{app_token}/tables/{table_id}/fields
```
⚠️ `fields/batch_create` returns 404 — must create fields individually.

### Field Types
| Type | Name | Notes |
|------|------|-------|
| 1 | Text | Default, also used for primary field |
| 2 | Number | Use `"formatter": "0.00"` for currency |
| 3 | SingleSelect | Options with color codes (0-7) |
| 5 | DateTime | Value = millisecond timestamp |
| 7 | Checkbox | Boolean, set `true`/`false` to mark/flag records |
| 20 | Formula | Use `DATETIME_FORMAT()` for date extraction |

### DateTime Field Value
```python
from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=8))
dt = datetime(2026, 6, 1, 15, 30, tzinfo=CST)
timestamp_ms = int(dt.timestamp() * 1000)  # 1780317000000
```

### Formula Field for Month Extraction
```json
{
  "field_name": "月份",
  "type": 20,
  "property": {
    "formula_expression": "DATETIME_FORMAT(CurrentValue.[交易时间], \"yyyy-MM\")"
  }
}
```

### SingleSelect Field with Options
```json
{
  "field_name": "收支类型",
  "type": 3,
  "property": {
    "options": [
      {"name": "支出", "color": 0},
      {"name": "收入", "color": 1},
      {"name": "不计收支", "color": 2}
    ]
  }
}
```

## Batch Record Insertion
```
POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create
```
⚠️ Payload MUST be wrapped: `{"records": [{"fields": {...}}, ...]}`
Bare array → code 9499 "Bad Request"

Max 500 records per batch. Write payload to temp file, use `curl -d @file`.

## Batch Record Update
```
POST /bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update
```
Payload: `{"records": [{"record_id": "recXXX", "fields": {"字段名": value}}, ...]}`
Max 500 records per batch. Use to mark/flag records (e.g., set Checkbox field to `true`).
Same wrapping requirement as batch_create.

## View Management

### List Views
```bash
curl -s "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views" \
  -H "Authorization: Bearer $TOKEN"
# → Returns view_id, view_name, view_type for each view
```

### Create View
```
POST /bitable/v1/apps/{app_token}/tables/{table_id}/views
```
Supported types: `grid`, `kanban`, `gallery`, `gantt`, `form`
⚠️ `chart` is NOT supported → returns 99992402

### Delete View
```
DELETE /bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}
```

### Get View Details
```
GET /bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}
```

### ⛔ View Filters/Sorts CANNOT Be Set via API (FOUND 2026-06-22)
Both PATCH and POST with `property.filter_info` **silently fail** — API returns `code: 0` but the view's `property` is always `null`. Filters, sorts, and groupings must be configured manually in the Feishu Bitable UI.

**Workaround**: When creating views that need filters, create the view via API, then instruct the user to manually add filter conditions in the UI. Provide exact filter specs (field name, operator, value).

**Failed formats tried** (all return null property):
- PATCH with `{"property": {"filter_info": {"conjunction": "and", "conditions": [...]}}}` → code 0, property null
- PATCH with `{"filter_info": {"conjunction": "and", "conditions": [...]}}` at top level → code 0, property null  
- POST with filter_info in property during creation → code 0, property null
- PUT endpoint → 404 (does not exist)

## Dashboard/Charts
Bitable dashboards and charts **cannot be created via API**. Must be created manually by user in the Bitable UI. Provide a configuration guide card with exact chart specs.

**User Preference**: When user asks for "BI看板" or "数据看板", they want a **Bitable (多维表格) with built-in dashboard** — NOT static HTML files, NOT message cards, NOT spreadsheets. The user will configure charts in the Bitable UI themselves. Our job is to:
1. Create the Bitable with correct data structure and fields
2. Write all records via batch_create
3. Provide chart configuration recommendations (chart type, axis, filters)
4. Guide the user to create the dashboard in Bitable UI

## Additional Tables
```
POST /bitable/v1/apps/{app_token}/tables
Body: {"table": {"name": "月度汇总", "default_view_name": "...", "fields": [...]}}
```
Can include field definitions in creation payload (unlike the default table).

## Deleting Default Fields
New Bitable creates a default table with dummy fields (文本, 单选, 日期, 附件).
Delete them via `DELETE /bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}`.
Cannot delete the primary field — rename it instead.

## Cleanup: Delete Default Table
After creating custom tables, delete the default empty table:
```
DELETE /bitable/v1/apps/{app_token}/tables/{default_table_id}
```

## Fetching All Records (Pagination)
Bitable `GET /records` returns max 500 per page. Must paginate with `page_token`:
```python
all_records = []
page_token = None
while True:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=500"
    if page_token:
        url += f"&page_token={page_token}"
    resp = api_call('GET', url, token)
    items = resp.get('data', {}).get('items', [])
    all_records.extend(items)
    if not resp.get('data', {}).get('has_more'):
        break
    page_token = resp['data'].get('page_token')
    time.sleep(0.2)  # rate limiting
```
⚠️ Each item has `record_id` (for updates) and `fields` dict. Field values may be strings even for Number fields — always cast with `float(str(val).replace(',',''))`.

## ⛔ Tenant Token Gets 91403 Forbidden on Record Writes (FOUND 2026-06-15)
Writing records to a **user-owned** bitable with tenant access token returns `code: 91403, msg: "Forbidden"`.
- **Root cause**: The app (tenant identity) is not a collaborator on user-owned bitables.
- **Fix**: Use **user access token** (from `$LARK_CONFIG_DIR/tokens.json`):
  ```bash
  USER_TOKEN=$(python3 -c "import json; f=open('$LARK_CONFIG_DIR/tokens.json'); d=json.load(f); print(d['access_token'])")
  curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"fields": {"Field1": "value", "Field2": 698}}'
  ```
- Tenant token **CAN** read bitable metadata (list tables, list fields) on accessible bitables.

## Listing Tables and Fields in a Bitable
```bash
# List all tables in a bitable app
curl -s "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables" \
  -H "Authorization: Bearer $TOKEN"
# → Returns table_id (e.g., tblUhdkG3neKgv5E), name, revision

# List fields of a specific table
curl -s "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields" \
  -H "Authorization: Bearer $TOKEN"
# → Returns field_id, field_name, type, property (formatter for numbers, etc.)
```
- `lark doc search <keyword>` also returns bitables (type: "bitable") — useful for finding bitables by keyword.

## ⚠️ Large Dataset Pagination — curl stdout Truncation (FOUND 2026-06-22)
When paginating large tables (4000+ records), **do NOT pipe curl to stdout** for `json.loads()` — control characters in record content cause `JSONDecodeError`.

**Correct**: write to file with `curl -o`, read with `json.load(f, strict=False)`:
```python
cmd = f'curl -s "{url}" -H "Authorization: Bearer {token}" -o /tmp/page_{n}.json'
terminal(cmd, timeout=30)
with open(f'/tmp/page_{n}.json') as f:
    data = json.load(f, strict=False)
```
`json_parse()` also fails on truncated stdout. Always use file-based I/O for multi-page fetches.

## Filtering Records Client-Side
Bitable API has limited server-side filtering. For complex filters (e.g., platform=微信 AND category=日常消费), fetch all then filter in Python:
```python
filtered = [r for r in all_records 
            if str(r['fields'].get('平台','')) == '微信' 
            and str(r['fields'].get('分类','')) == '日常消费']
```
