# TikTok Search API — Working Patterns

> Last verified: 2026-07-16

## Endpoint

**Working (App V3):**
```
GET https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_video_search_result
```

**Broken (Web):**
```
GET https://api.tikhub.io/api/v1/tiktok/web/fetch_search_video  → returns 400
```
Do NOT use the web search endpoint. It consistently returns 400 errors.

## Parameters

| Param | Type | Default | Notes |
|---|---|---|---|
| `keyword` | string | **required** | URL-encode. English keywords work far better than Chinese for food/lifestyle content |
| `count` | int | 20 | Max results per page |
| `offset` | int | 0 | Pagination cursor |
| `sort_type` | int | 0 | 0=relevance, 1=likes, 2=date, 3=views (AI推测) |
| `publish_time` | int | 0 | 0=any, 1=last day, 7=last week, 180=last 6 months (AI推测) |
| `region` | string | US | Region code |

## Example Call

```bash
curl -s "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_video_search_result?keyword=chocolate+chip+cookie&count=15&offset=0&sort_type=0&region=US" \
  -H "Authorization: Bearer $TIKHUB_API_KEY"
```

## Response Structure

```json
{
  "code": 200,
  "data": {
    "search_item_list": [
      {
        "aweme_info": {
          "aweme_id": "7238234014321118510",
          "desc": "the best browned butter chocolate chip cookies...",
          "create_time": 1685282709,
          "author": {
            "unique_id": "bromabakery",
            "nickname": "Broma Bakery",
            "sec_uid": "MS4wLjABAAAA..."
          },
          "statistics": {
            "play_count": 83089706,
            "digg_count": 4455162,      // likes
            "comment_count": 41976,
            "share_count": 751695,
            "collect_count": 3123751    // saves/bookmarks
          }
        }
      }
    ],
    "has_more": 1,
    "cursor": 10
  }
}
```

## Key Field Mapping

| Concept | Field Path |
|---|---|
| Video ID | `aweme_info.aweme_id` |
| Description | `aweme_info.desc` |
| Author handle | `aweme_info.author.unique_id` |
| Author name | `aweme_info.author.nickname` |
| Likes | `aweme_info.statistics.digg_count` |
| Comments | `aweme_info.statistics.comment_count` |
| Shares | `aweme_info.statistics.share_count` |
| Views | `aweme_info.statistics.play_count` |
| Saves | `aweme_info.statistics.collect_count` |
| Publish time | `aweme_info.create_time` (Unix timestamp) |

## Video URL Construction

```
https://www.tiktok.com/@{unique_id}/video/{aweme_id}
```

## Keyword Strategy

**Chinese keywords return poor results on TikTok.** For food content:
- ❌ "美式大曲奇" → 15 results, most irrelevant (cars, BBQ, audiobooks)
- ✅ "chocolate chip cookie" → 15 results, all highly relevant baking content

Use English keywords for TikTok search even when the user's query is in Chinese.

## Parsing Script

```bash
curl -s "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_video_search_result?keyword=$KEYWORD&count=15&offset=0&sort_type=0&region=US" \
  -H "Authorization: Bearer $TIKHUB_API_KEY" -o /tmp/tiktok_results.json

python3 -c "
import json
with open('/tmp/tiktok_results.json') as f:
    d = json.load(f)
for it in d['data']['search_item_list']:
    info = it['aweme_info']
    s = info['statistics']
    a = info['author']
    print(f'{a[\"nickname\"]} | {a[\"unique_id\"]}')
    print(f'  {info[\"desc\"][:80]}')
    print(f'  👀 {s[\"play_count\"]:,} ❤️ {s[\"digg_count\"]:,} 💬 {s[\"comment_count\"]:,} 🔄 {s[\"share_count\"]:,} ⭐ {s[\"collect_count\"]:,}')
    print(f'  https://www.tiktok.com/@{a[\"unique_id\"]}/video/{info[\"aweme_id\"]}')
"
```

## User Posts (Brand Account Content Analysis)

**Working endpoint (V1 — supports pagination):**
```
GET https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos
```

| Param | Type | Default | Notes |
|---|---|---|---|
| `sec_user_id` | string | "" | From user search or profile |
| `unique_id` | string | "" | Alternative to sec_user_id |
| `max_cursor` | int | 0 | Pagination: use value from response's `max_cursor` field |
| `count` | int | 20 | Results per page (max ~35) |

**Pagination pattern:**
```python
# Page 1: max_cursor=0 → response returns next max_cursor
# Page N: use response's max_cursor as next request's max_cursor
curl "...?sec_user_id=XXX&max_cursor=0&count=35"  # → max_cursor=1783549451000
curl "...?sec_user_id=XXX&max_cursor=1783549451000&count=35"  # → next cursor
```

**⚠️ V3 endpoint (`fetch_user_post_videos_v3`) does NOT paginate properly** — returns the same 20 items regardless of `cursor` parameter. Always use V1.

**Response structure:** Uses `aweme_list` (not `search_item_list`). Each item has same fields as search results.

## User Search

```
GET https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_search_result?keyword=crumbl&count=5&offset=0
```
Returns `user_list` array. Each entry has `user_info.sec_uid` needed for post fetching.

## Hashtag Search — BROKEN

**`fetch_hashtag_search_result` returns empty results for ALL tested keywords.** Do NOT use this endpoint.

**Workaround:** Use `fetch_video_search_result` with the hashtag name as keyword:
- ❌ `/fetch_hashtag_search_result?keyword=crumbl` → 0 results
- ✅ `/fetch_video_search_result?keyword=crumbl+asmr` → 20 relevant results
- ✅ `/fetch_video_search_result?keyword=crumbl+mukbang` → 20 relevant results

Combine hashtag names with content keywords for best results.

## Playlist/Album Data — NOT AVAILABLE

**TikHub does NOT expose TikTok playlist/album contents via any API endpoint.** Only Douyin, Weibo, and WeChat have collection/album endpoints.

TikTok profile shows `profileTab.showPlayListTab: True` and `canExpPlaylist: True` but there is no API to fetch the actual playlist list or playlist video contents.

**Workaround for content categorization:** Analyze video descriptions, hashtags, and posting patterns to infer content groupings (e.g., Crumbl's "Weekly Rotating Menu" series identified by `🖤 WEEKLY ROTATING MENU 🖤` pattern in descriptions).

## MCP vs REST

- **MCP** (`mcp.tikhub.io`): Consistently times out from cloud servers → returns `RetryError`
- **REST** (`api.tikhub.io`): Stable and fast (~5-10s response)
- **CLI** (`tikhub tiktok ...`): Uses MCP under the hood, so also times out

**Always use REST API directly for TikTok search.** The `tikhub` CLI and MCP endpoints are unreliable for TikTok.

## Tool Catalog Refresh

Before first use, refresh the local tool catalog:
```bash
python3 ~/.hermes/skills/social-media/social-account-doctor/tikhub/scripts/refresh_tools.py tiktok
# Output: [tiktok] wrote 174 tool(s) → .../references/tools-tiktok.json
```

## OpenAPI Discovery

Full endpoint list available at:
```bash
curl -s "https://api.tikhub.io/openapi.json" -H "Authorization: Bearer $KEY" | python3 -c "
import sys, json
paths = json.load(sys.stdin).get('paths', {})
for k in sorted(k for k in paths if 'tiktok' in k and 'search' in k.lower()):
    print(k)
"
```
