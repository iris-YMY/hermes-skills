# Feishu Sheets Styling API Patterns (Verified 2026-06-18)

## Styling Cells (Header Formatting, Bold, Colors, Wrap Text)

Use the `/sheets/v2/spreadsheets/{token}/style` endpoint with **`appendStyle`** (NOT `updateStyle`):

```bash
PUT /open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/style
{
  "appendStyle": {
    "range": "{sheet_id}!A1:G1",
    "style": {
      "bold": true,
      "backColor": "#4472C4",
      "foreColor": "#FFFFFF"
    }
  }
}
```

### Style Properties
- `bold`: true/false
- `backColor`: hex color string (e.g., "#4472C4" for blue, "#FFF2CC" for yellow)
- `foreColor`: hex color string for text
- `wrapText`: true/false (enables text wrapping in cells)
- `fontSize`: number (not verified, may not work)

### Common Use Cases

**Header row styling (blue background, white text, bold):**
```json
{
  "appendStyle": {
    "range": "{sheet_id}!A1:G1",
    "style": {
      "bold": true,
      "backColor": "#4472C4",
      "foreColor": "#FFFFFF"
    }
  }
}
```

**Section header styling (yellow background, bold):**
```json
{
  "appendStyle": {
    "range": "{sheet_id}!A14:G14",
    "style": {
      "bold": true,
      "backColor": "#FFF2CC"
    }
  }
}
```

**Enable text wrapping for long content columns:**
```json
{
  "appendStyle": {
    "range": "{sheet_id}!G1:G18",
    "style": {
      "wrapText": true
    }
  }
}
```

## Pitfalls

### 🔴 Use `appendStyle`, NOT `updateStyle`
The API requires the key to be `appendStyle` (not `updateStyle`). Using `updateStyle` returns:
```
code: 9499
msg: "Missing required parameter: AppendStyle"
```

### 🔴 Column Width Adjustment Does NOT Work
The `/sheets/v3/spreadsheets/{token}/dimension_range` endpoint returns **404 page not found**:
```bash
PUT /open-apis/sheets/v3/spreadsheets/{token}/dimension_range
# Returns: 404 page not found
```
**Workaround**: Column widths cannot be set via API. Users must adjust manually in the Feishu UI, or accept default widths.

## Complete Workflow Example

```bash
# 1. Create spreadsheet
POST /sheets/v3/spreadsheets
{"folder_token": "...", "title": "..."}

# 2. Get sheet_id
GET /sheets/v3/spreadsheets/{token}/sheets/query

# 3. Write data
PUT /sheets/v2/spreadsheets/{token}/values
{"valueRange": {"range": "{sheet_id}!A1:G18", "values": [[...]]}}

# 4. Style header row (bold + blue background + white text)
PUT /sheets/v2/spreadsheets/{token}/style
{"appendStyle": {"range": "{sheet_id}!A1:G1", "style": {"bold": true, "backColor": "#4472C4", "foreColor": "#FFFFFF"}}}

# 5. Enable text wrapping for long content columns
PUT /sheets/v2/spreadsheets/{token}/style
{"appendStyle": {"range": "{sheet_id}!G1:G18", "style": {"wrapText": true}}}
```
