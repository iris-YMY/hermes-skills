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

## View Creation
```
POST /bitable/v1/apps/{app_token}/tables/{table_id}/views
```
Supported types: `grid`, `kanban`, `gallery`, `gantt`, `form`
⚠️ `chart` is NOT supported → returns 99992402

## Dashboard/Charts
Bitable dashboards and charts **cannot be created via API**. Must be created manually by user in the Bitable UI. Provide a configuration guide card with exact chart specs.

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
