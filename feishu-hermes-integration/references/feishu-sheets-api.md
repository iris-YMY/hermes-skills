# Feishu Sheets API Patterns (Verified)

## Creating a Spreadsheet

```bash
POST /open-apis/sheets/v3/spreadsheets
{"folder_token": "", "title": "Spreadsheet Title"}
```
- Returns `data.spreadsheet.spreadsheet_token` and `url`
- Works with tenant access token
- ❌ `POST /drive/v1/files` with `type: "bitable"` returns 404 — use sheets endpoint instead
- ❌ Bitable requires `bitable:app` or `base:app:create` scope — not available in standard hr-assistant app

## Getting Sheet ID

The spreadsheet token is NOT the same as the sheet_id (grid ID). You must query:

```bash
GET /open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query
```
Returns `data.sheets[].sheet_id` (e.g., `"8b6dde"`) — this is required for writing data.

## Writing Data

```bash
PUT /open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values
{"valueRange": {"range": "{sheet_id}!A1:J8", "values": [[...]]}}
```
- ⚠️ Must use `valueRange` (camelCase), not `value_range` — error 9499 otherwise
- ⚠️ `range` must use `sheet_id` (from query), NOT `spreadsheet_token` — error 90215 "sheetId not found"
- ⚠️ Must use `--data-raw` in curl for JSON with Chinese characters
- First row = headers, subsequent rows = data

## Example: Project Schedule Sheet

```python
headers = ["日期", "星期", "影片名称", "开始时间", "结束时间", "影院", "影厅", "地址", "类型/单元", "备注"]
data = [
    ["6月13日", "周六", "剧院魅影：25周年纪念演出", "12:00", "14:40", "上海大光明电影院", ...],
    ...
]
```

## Batch Writing Large Datasets (1000+ rows)

The Feishu Sheets API has a practical limit per request. For large datasets (e.g., 4,221 financial records), batch in chunks of ~500 rows:

```python
import json, subprocess, time

SPREADSHEET = '<spreadsheet_token>'
SHEET_ID = '<sheet_id>'
BATCH_SIZE = 500  # rows per API call

headers = ['交易时间', '分类', '收支类型', '金额', '备注', '账户', '来源', '平台']
all_rows = [headers] + data_rows  # data_rows = list of lists

for batch_idx in range(0, len(all_rows), BATCH_SIZE):
    batch = all_rows[batch_idx:batch_idx + BATCH_SIZE]
    start_row = batch_idx + 1
    end_row = start_row + len(batch) - 1
    range_str = f'{SHEET_ID}!A{start_row}:H{end_row}'
    
    payload = json.dumps({
        "valueRange": {"range": range_str, "values": batch}
    }, ensure_ascii=False)
    
    # Write payload to temp file to avoid shell escaping issues with Chinese text
    with open(f'/tmp/batch_payload_{batch_idx}.json', 'w', encoding='utf-8') as f:
        f.write(payload)
    
    cmd = f'curl -s -X PUT "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SPREADSHEET}/values" ' \
          f'-H "Authorization: Bearer {TOKEN}" ' \
          f'-H "Content-Type: application/json; charset=utf-8" ' \
          f'-d @/tmp/batch_payload_{batch_idx}.json'
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    resp = json.loads(result.stdout)
    if resp.get('code') != 0:
        print(f"Batch {batch_idx}: ERROR - {resp}")
    time.sleep(0.5)  # rate limiting
```

**Key pitfalls for batch writes:**
- Use `-d @file.json` instead of `-d 'json_string'` — Chinese characters get mangled by shell escaping
- Batch size 500 is safe; 1000 may hit request size limits
- Add `time.sleep(0.5)` between batches to avoid rate limiting
- First batch includes header row (row 1), subsequent batches start from their calculated row number

## Styling Cells

Use `PUT /sheets/v2/spreadsheets/{token}/style` with `appendStyle` key:

```bash
curl -s -X PUT "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{token}/style" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"appendStyle":{"range":"{sheet_id}!A1:G1","style":{"bold":true,"backColor":"#4472C4","foreColor":"#FFFFFF"}}}'
```

- ⚠️ Must use `appendStyle`, NOT `updateStyle` — `updateStyle` returns 9499 error
- Style keys: `bold` (bool), `backColor` (hex), `foreColor` (hex), `fontSize` (int), `wrapText` (bool)
- Colors: `"#4472C4"` (blue), `"#FFFFFF"` (white), `"#FFF2CC"` (light yellow)

## Permission Sharing

```bash
PUT /open-apis/drive/v1/permissions/{spreadsheet_token}/public?type=sheets
{"link_entity_permission_type": "view", "external_access_entity_permission_type": "close"}
```
⚠️ This endpoint may return 404 with tenant token if the app lacks the required scopes. For user-owned docs, use user_access_token via lark-cli instead.

## Scope Requirements

| Operation | Required Scope |
|-----------|---------------|
| Create spreadsheet | `sheets:spreadsheet` |
| Write cells | `sheets:spreadsheet` |
| Read cells | `sheets:spreadsheet:readonly` |
| Set permissions | `drive:drive` |

## Visibility Note

Documents created with tenant_access_token are app-owned and won't appear in the user's "我的文档" or personal drive. To make them visible to the user, either:
1. Use user_access_token (via `lark auth login`) to create the sheet
2. Share the link directly with the user in a message
3. Manually move/copy the file in the Feishu UI
