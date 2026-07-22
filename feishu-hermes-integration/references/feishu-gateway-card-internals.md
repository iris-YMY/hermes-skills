# Feishu Gateway: Outbound Message Types & Card Limitations

## Gateway `_build_outbound_payload` (feishu.py:3831)

The gateway's normal `send()` flow only supports two message types:

```python
def _build_outbound_payload(self, content: str) -> tuple[str, str]:
    if _MARKDOWN_HINT_RE.search(content):
        return "post", _build_markdown_post_payload(content)
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
```

**What this means**: When a cron job or agent sends text/markdown output, the gateway automatically wraps it as either `text` or `post` (rich text). There is NO auto-detection for `interactive` card type.

## Interactive Card: Only via `send_exec_approval` (feishu.py:1726)

The gateway CAN send interactive cards, but only through the `send_exec_approval()` method (used for dangerous command approval buttons). This method:
- Builds card JSON with `config`, `header`, `elements` structure
- Sends with `msg_type="interactive"` via `_feishu_send_with_retry()`
- Is NOT accessible from cron jobs or normal message flow

## How to Send Cards from Cron Jobs

Since the gateway's `send()` doesn't support interactive cards, cron jobs must **bypass the gateway** and send cards directly via Feishu REST API:

1. **Set `deliver: local`** — suppresses the default text/post delivery
2. **Write a card sender script** — uses `urllib` + tenant token to POST to `/im/v1/messages`
3. **Agent calls script via `terminal`** — `python3 send_xxx_card.py`
4. **Agent outputs `[SILENT]`** — prevents duplicate delivery

This is the pattern used by news/weather broadcasts (see broadcast-cronjobs skill §9).

## Card Size Limits (Feishu Platform)

| Limit | Value |
|-------|-------|
| Max elements per card | 30 |
| Max chars per markdown element | ~4,000 |
| Max total card JSON size | 64 KB |
| Max actions per action block | 5 |

**Implication for long reports** (like daily fund analysis with 8+ holdings): split content across multiple cards or use a hybrid approach (card for summary + post for details).

## Header Template Colors

`blue`, `green`, `red`, `orange`, `purple`, `grey`, `wathet`, `turquoise`, `yellow`, `violet`, `carmine`, `indigo`

## Key Code Locations (feishu.py)

| Function | Line | Purpose |
|----------|------|---------|
| `_build_outbound_payload` | ~3831 | text/post auto-detection |
| `send_exec_approval` | ~1726 | interactive card sending |
| `_feishu_send_with_retry` | ~1776 | low-level send with retry |
| `_send_raw_message` | ~3901 | actual API call |
| `send` | ~1634 | main send entry point |
