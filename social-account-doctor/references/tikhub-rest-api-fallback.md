# TikHub REST API Fallback

> Last verified: 2026-07-15

## When to Use

The TikHub MCP endpoint (`mcp.tikhub.io`) frequently times out or returns `RetryError` from cloud servers. The REST API (`api.tikhub.io`) is more stable and serves as a direct fallback.

**Trigger conditions:**
- `tikhub --health` succeeds but all `tools/call` return `RetryError` or timeout
- MCP session initializes but any tool call hangs >60s
- `Unknown tool` errors for known tool names

## REST API Basics

```
Base URL: https://api.tikhub.io/api/v1
Auth:     Authorization: Bearer {TIKHUB_API_KEY}
Accept:   application/json
```

### Endpoint Pattern

MCP tool names map directly to REST paths:

| MCP Tool | REST Path |
|---|---|
| `xiaohongshu_app_v2_search_notes` | `/xiaohongshu/app_v2/search_notes` |
| `xiaohongshu_app_v2_search_users` | `/xiaohongshu/app_v2/search_users` |
| `xiaohongshu_app_v2_get_user_info` | `/xiaohongshu/app_v2/get_user_info` |
| `xiaohongshu_app_v2_get_user_posted_notes` | `/xiaohongshu/app_v2/get_user_posted_notes` |
| `xiaohongshu_app_v2_get_note_comments` | `/xiaohongshu/app_v2/get_note_comments` |

**Pattern**: `/api/v1/{platform}/{version}/{tool_suffix}?params`

### Example Call

```bash
KEY="your_api_key"
curl -s --max-time 30 \
  "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_users?keyword=蓝瓶咖啡&page=1" \
  -H "Authorization: Bearer $KEY" \
  -H "Accept: application/json"
```

## Response Structure

**Top level:**
```json
{
  "code": 200,
  "message": "Request successful. This request will incur a charge.",
  "data": { ... }
}
```

**XHS search_users** (`data.data`):
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "5c0577210000000007004b60",
        "name": "% Arabica",
        "sub_title": "Fans 77.8k",
        "red_official_verified": true,
        "red_official_verify_type": 2,
        "desc": "餐饮服务"
      }
    ]
  }
}
```

**XHS get_user_posted_notes** (`data.data`):
```json
{
  "success": true,
  "data": {
    "notes": [
      {
        "id": "6a3b40970000000006020d07",
        "type": "video",          // "normal" = 图文, "video" = 视频
        "display_title": "...",
        "desc": "...",
        "likes": 24007,            // NOTE: "likes" not "liked_count"
        "collected_count": 1057,
        "comments_count": 16,
        "share_count": 92,
        "create_time": 1782349231  // Unix timestamp, NOT "timestamp"
      }
    ]
  }
}
```

## Field Name Mapping (MCP → REST)

| MCP Field | REST Field | Notes |
|---|---|---|
| `note_id` | `id` | Note identifier |
| `liked_count` | `likes` | Like count |
| `timestamp` | `create_time` | Unix timestamp |
| `title` | `display_title` or `title` | May need fallback |
| `xsec_token` | (not in REST list) | May need separate detail call |

## Note URL Construction

```
https://www.xiaohongshu.com/explore/{note_id}
```

The `xsec_token` is optional for explore URLs — the note is accessible without it.

## Token Scope Requirements

API tokens need specific scopes enabled in the TikHub dashboard:
- Dashboard URL: https://user.tikhub.io/dashboard/api
- Error when scopes missing: `403 - API Token lacks required permissions`
- Enable scopes for each platform you need (xiaohongshu, douyin, etc.)

## TikTok REST Patterns

| MCP Tool | REST Path | Status |
|---|---|---|
| `tiktok_app_v3_fetch_video_search_result` | `/tiktok/app/v3/fetch_video_search_result` | ✅ Working |
| `tiktok_web_fetch_search_video` | `/tiktok/web/fetch_search_video` | ❌ Returns 400 |

**Key difference from XHS**: TikTok uses `aweme_id` (not `note_id`), `digg_count` (not `likes`), `collect_count` (not `collected_count`). Video URL: `tiktok.com/@{unique_id}/video/{aweme_id}`.

Full reference: `references/tiktok-search-api.md`

## Limitations

- `execute_code` sandbox blocks outbound HTTP — use `terminal` tool for curl calls
- Rate limiting still applies (~10 req/s max)
- Some note detail fields (full image_list, video URLs) may require separate detail API calls
- The REST API doesn't support all MCP tools — check OpenAPI spec at `https://api.tikhub.io/openapi.json`

## Quick Health Check

```bash
# Test REST API directly (bypasses MCP)
curl -s --max-time 10 \
  "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_users?keyword=咖啡&page=1" \
  -H "Authorization: Bearer $TIKHUB_API_KEY" \
  -H "Accept: application/json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
code = data.get('code')
users = data.get('data',{}).get('data',{}).get('users',[])
print(f'API Status: {code}, Users found: {len(users)}')
for u in users[:3]:
    v = '✅' if u.get('red_official_verified') else '❌'
    print(f'  {u[\"name\"]} | {u.get(\"sub_title\",\"?\")} | {v}')
"
```
