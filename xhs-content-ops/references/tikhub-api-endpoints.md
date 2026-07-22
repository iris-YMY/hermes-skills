# TikHub REST API Endpoint Reference

> Base URL: `https://api.tikhub.io`
> Auth: `Authorization: Bearer <TIKHUB_API_KEY>` (from `~/.env`)
> OpenAPI spec: `GET /openapi.json`

## Working Endpoints (verified 2026-07)

### TikTok Video Search ✅
```
GET /api/v1/tiktok/app/v3/fetch_video_search_result
  keyword (required) - URL encode multi-word: "crumbl+cookies"
  offset (default: 0)
  count (default: 20)
  sort_type (default: 0) — 0=relevance, others untested
  publish_time (default: 0) — 0=all, others untested
  region (default: US)
```

### TikTok User Search ✅
```
GET /api/v1/tiktok/app/v3/fetch_user_search_result
  keyword (required)
  offset (default: 0)
  count (default: 20)
```
Response: `data.user_list[].user_info.{uid, sec_uid, unique_id, nickname, custom_verify, follower_count}`

### TikTok User Posts — Pagination ⚠️
```
# v3 endpoint (cursor param) BROKEN — always returns same items regardless of cursor!
GET /api/v1/tiktok/app/v3/fetch_user_post_videos_v3
  sec_user_id (required)
  count (default: 20)
  cursor (default: 0) — IGNORED, always returns same results

# v1 endpoint (max_cursor param) WORKS — use this for pagination
GET /api/v1/tiktok/app/v3/fetch_user_post_videos
  sec_user_id (required)
  max_cursor (default: 0) — use value from previous response for next page
  count (default: 35, but typically returns ~10 per page)
Response: data.aweme_list[], data.max_cursor=<next_cursor>, data.has_more=1
```
**Pagination loop:** Call with max_cursor=0, extract `data.max_cursor`, use it for next call.

### TikTok User Profile ✅
```
GET /api/v1/tiktok/web/fetch_user_profile
  secUid (required) — same as sec_user_id
```
Response: `data.userInfo.user.{signature, followerCount, ...}`
- `profileTab.showPlayListTab` — whether user has TikTok Playlists enabled
- `canExpPlaylist` — whether user can export playlists

### TikTok App v3 User Profile ✅
```
GET /api/v1/tiktok/app/v3/handler_user_profile
  sec_user_id (required)
```
Returns: `data.user.{follower_count, aweme_count, custom_verify, ...}`
- `data.user.tab_settings` — tab visibility settings
- `data.user.music_tab_info` — music tab settings

### TikTok General Search ✅
```
GET /api/v1/tiktok/app/v3/fetch_general_search_result
  keyword (required)
  offset (default: 0)
  count (default: 20)
  sort_type (default: 0)
  region (default: US)
```

## Broken / Unreliable Endpoints

| Endpoint | Status | Workaround |
|---|---|---|
| `/api/v1/tiktok/web/fetch_search_video` | 400 error or RetryError | Use `app/v3/fetch_video_search_result` |
| `/api/v1/tiktok/app/v3/fetch_hashtag_search_result` | Returns 0 results | Use video search with hashtag as keyword |
| `/api/v1/tiktok/web/search/*` | 404 | Use app/v3 endpoints |

## Response Structure

### Video Search Results
```json
{
  "code": 200,
  "data": {
    "search_item_list": [
      {
        "aweme_info": {
          "aweme_id": "7238234014321118510",
          "desc": "video description...",
          "create_time": 1685282709,
          "author": {
            "unique_id": "username",
            "nickname": "Display Name",
            "sec_uid": "MS4wLjABAAA...",
            "custom_verify": "Verified account",
            "follower_count": 10846174
          },
          "statistics": {
            "digg_count": 4455162,
            "comment_count": 41976,
            "share_count": 751695,
            "play_count": 83089706,
            "collect_count": 3123751
          }
        }
      }
    ],
    "cursor": 20,
    "has_more": 1
  }
}
```

### User Post Results
```json
{
  "data": {
    "aweme_list": [
      {
        "aweme_id": "...",
        "desc": "...",
        "author": {...},
        "statistics": {...}
      }
    ]
  }
}
```

## CLI Notes

The `tikhub` CLI at `~/.local/bin/tikhub` wraps MCP endpoints (unstable).

### Before first use, refresh tool catalog:
```bash
python3 ~/.hermes/skills/social-media/social-account-doctor/tikhub/scripts/refresh_tools.py tiktok
```

### CLI commands (if MCP works):
```bash
tikhub --health                    # check status
tikhub --platforms                 # list platforms
tikhub list tiktok search          # list search tools
tikhub describe tiktok <tool>      # show schema
tikhub tiktok <tool> --key val     # call tool
```

**Recommendation:** Use REST API + curl for reliability. CLI only when MCP is responsive.

## Platform Coverage

17 platforms supported, 1017 total endpoints:
- TikTok (174), Douyin (289), Instagram (87), Xiaohongshu (43)
- YouTube (38), Twitter (12), Bilibili (41), Weibo (64)
- Kuaishou, WeChat, Zhihu, LinkedIn, Reddit, Threads, etc.

## Cost

- Each API call incurs a charge (check dashboard)
- Cached responses available for 24h at no extra cost via `cache_url` in response

## Useful Video Fields (for content analysis)

| Field | Location | Description |
|---|---|---|
| `aweme_id` | `aweme_info` / `aweme_list[]` | Video ID |
| `desc` | `aweme_info` / `aweme_list[]` | Video description/caption |
| `create_time` | `aweme_info` / `aweme_list[]` | Unix timestamp |
| `duration` | `video.duration` | Duration in milliseconds |
| `is_top` | `aweme_info` / `aweme_list[]` | Whether video is pinned |
| `cha_list` | `aweme_info` / `aweme_list[]` | Array of hashtags: `[{cha_name, cid, type}]` |
| `text_extra` | `aweme_info` / `aweme_list[]` | Hashtag metadata: `[{hashtag_name, hashtag_id, start, end}]` |
| `content_type` | `aweme_info` / `aweme_list[]` | Usually "video" |
| `suggest_words` | `aweme_info` / `aweme_list[]` | TikTok's suggested related queries |
| `playlist_blocked` | `aweme_info` / `aweme_list[]` | Playlist restriction info |
| `statistics.digg_count` | nested | Likes |
| `statistics.comment_count` | nested | Comments |
| `statistics.share_count` | nested | Shares |
| `statistics.play_count` | nested | Views |
| `statistics.collect_count` | nested | Saves/Favorites |
| `author.unique_id` | nested | @username |
| `author.nickname` | nested | Display name |
| `author.sec_uid` | nested | User ID for profile/posts queries |
| `author.custom_verify` | nested | Verification badge text |

## Content Analysis Workflow

For brand account deep analysis, use this approach:

1. **Collect posts**: Use `fetch_user_post_videos` (v1) with pagination loop (max_cursor)
2. **Classify content**: Parse `desc` for keywords → categorize (e.g., 每周菜单/新品发布/互动投票/...)
3. **Generate Excel**: Use openpyxl with `/usr/bin/python3` (system Python 3.12, has openpyxl)
   - Sheet 1: 全部内容明细 (all videos with metrics + classification)
   - Sheet 2: 内容大类统计 (category aggregation)
   - Sheet 3: 内容子类统计 (subcategory aggregation)
   - Sheet 4: 时长分布分析 (duration buckets)
   - Sheet 5: Hashtag分析 (top hashtags)
   - Sheet 6: 发布节奏分析 (weekly publishing cadence)
   - Sheet 7: 策略洞察 (key findings)

**Important**: Use `/usr/bin/python3` for openpyxl scripts, not hermes venv (which lacks pip/openpyxl).
