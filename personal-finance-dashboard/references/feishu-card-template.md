# Feishu Interactive Card Template for Finance Dashboard

## Card Structure
Send via `POST /im/v1/messages` with `msg_type: "interactive"`. Content is JSON string of the card object.

## Key Elements

### column_set (side-by-side layout)
```json
{
  "tag": "column_set",
  "flex_mode": "bisect",
  "background_style": "grey",
  "columns": [
    {"tag": "column", "width": "weighted", "weight": 1, "elements": [
      {"tag": "div", "text": {"tag": "lark_md", "content": "**Label**\nValue"}}
    ]},
    {"tag": "column", "width": "weighted", "weight": 1, "elements": [
      {"tag": "div", "text": {"tag": "lark_md", "content": "**Label**\nValue"}}
    ]}
  ]
}
```

### Unicode Bar Charts (for trends and distributions)
Use `lark_md` with Unicode block characters:
- `████████░░` — filled vs empty blocks for proportional visualization
- `▓▓▓▓▓▓░░░░` — alternative style for secondary charts

Example monthly trend:
```
**2025-06** ¥31,756 ████████░░
**2025-07** ¥29,166 ███████░░░
**2026-01** ¥76,346 ████████████████████
```

Scale: max value = 20 blocks (████████████████████). Other values proportional.

### Button (link to spreadsheet)
```json
{
  "tag": "action",
  "actions": [{
    "tag": "button",
    "text": {"tag": "plain_text", "content": "📊 查看完整数据源"},
    "url": "https://xxx.feishu.cn/sheets/SPREADSHEET_TOKEN",
    "type": "primary"
  }]
}
```

### Note (footer)
```json
{
  "tag": "note",
  "elements": [{"tag": "plain_text", "content": "📎 元数据 | 生成时间：YYYY-MM-DD"}]
}
```

## Full Card Template
```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "💰 Title"},
    "template": "blue"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "**数据范围**：...\n**数据来源**：..."}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "## 📊 年度财务总览"}},
    {"tag": "column_set", "flex_mode": "bisect", "background_style": "grey", "columns": [...]},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "## 📱 平台对比"}},
    {"tag": "column_set", "flex_mode": "bisect", "columns": [...]},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "## 📅 月度支出趋势"}},
    {"tag": "div", "text": {"tag": "lark_md", "content": "Unicode bars here..."}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "## 🏷️ 消费分类 Top 8"}},
    {"tag": "div", "text": {"tag": "lark_md", "content": "Unicode bars here..."}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "## 🔥 年度大额支出 Top 5"}},
    {"tag": "div", "text": {"tag": "lark_md", "content": "Numbered list..."}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "## 📌 数据洞察"}},
    {"tag": "div", "text": {"tag": "lark_md", "content": "Bullet points..."}},
    {"tag": "hr"},
    {"tag": "note", "elements": [{"tag": "plain_text", "content": "Footer..."}]},
    {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": "📊 查看完整数据源"}, "url": "...", "type": "primary"}]}
  ]
}
```

## Sending the Card
⚠️ Use **tenant_access_token** (not user OAuth token) for message sending:
```python
payload = json.dumps({
    "receive_id": chat_id,
    "msg_type": "interactive",
    "content": json.dumps(card_object, ensure_ascii=False)
}, ensure_ascii=False)

# Write to temp file, then curl -d @file
```

## Gotchas
- `lark_md` supports: **bold**, `code`, line breaks with `\n`
- `lark_md` does NOT support: tables, images, links
- `column_set` max 4 columns, use `flex_mode: "bisect"` for 2-col layout
- `background_style: "grey"` only works on first column_set in a group
- Keep total card size reasonable — Feishu has rendering limits
