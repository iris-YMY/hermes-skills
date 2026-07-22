# Feishu Sheets Batch Write Pattern

## Create Spreadsheet
```python
import json, subprocess

USER_TOKEN = "<from tokens.json access_token>"
SPREADSHEET_TOKEN = "<from creation response>"

# Create in user's My Folder (user OAuth token required)
result = subprocess.run(
    f'curl -s -X POST "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets" '
    f'-H "Authorization: Bearer {USER_TOKEN}" -H "Content-Type: application/json" '
    f'-d \'{{"title":"<TITLE>"}}\'',
    shell=True, capture_output=True, text=True
)
resp = json.loads(result.stdout)
spreadsheet_token = resp['data']['spreadsheet']['spreadsheet_token']
```

## Query Sheet ID
```python
result = subprocess.run(
    f'curl -s "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query" '
    f'-H "Authorization: Bearer {USER_TOKEN}"',
    shell=True, capture_output=True, text=True
)
sheet_id = json.loads(result.stdout)['data']['sheets'][0]['sheet_id']
```

## Batch Write (500 rows per batch)
```python
import json, subprocess, time

BATCH_SIZE = 500
headers = ['交易时间', '分类', '收支类型', '金额', '备注', '账户', '来源', '平台']
all_rows = [headers] + data_rows  # data_rows = list of lists

for batch_idx in range(0, len(all_rows), BATCH_SIZE):
    batch = all_rows[batch_idx:batch_idx + BATCH_SIZE]
    start_row = batch_idx + 1
    end_row = start_row + len(batch) - 1
    col_count = len(headers)
    last_col = chr(ord('A') + col_count - 1)  # H for 8 columns
    
    range_str = f'{sheet_id}!A{start_row}:{last_col}{end_row}'
    payload = json.dumps({
        "valueRange": {"range": range_str, "values": batch}
    }, ensure_ascii=False)
    
    # Write to temp file — avoids shell escaping issues with Chinese text
    tmp_file = f'/tmp/batch_payload_{batch_idx}.json'
    with open(tmp_file, 'w', encoding='utf-8') as f:
        f.write(payload)
    
    result = subprocess.run(
        f'curl -s -X PUT '
        f'"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values" '
        f'-H "Authorization: Bearer {USER_TOKEN}" '
        f'-H "Content-Type: application/json; charset=utf-8" '
        f'-d @{tmp_file}',
        shell=True, capture_output=True, text=True, timeout=30
    )
    resp = json.loads(result.stdout)
    if resp.get('code') != 0:
        print(f"Batch {batch_idx}: ERROR - {resp}")
    time.sleep(0.5)  # Rate limit
```

## Key Notes
- Max 500 rows per API call
- Use `-d @file` not `-d '{json}'` to avoid shell escaping with CJK characters
- `sheet_id` (not `spreadsheet_token`) is used in the range string
- Column letters: A=1, B=2, ..., H=8 columns
- Sort data by date descending before writing (newest first)
