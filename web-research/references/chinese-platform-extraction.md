# Chinese Platform Data Extraction — Tested Methods (2026-07)

## Summary
Xiaohongshu (XHS), Douyin, Bilibili are all JS SPAs with aggressive anti-bot. From Chinese cloud servers (Tencent Cloud), most extraction methods fail. Only **TikHub API** reliably returns full note/video content.

## Xiaohongshu Extraction Test Results

| Method | Result | Details |
|--------|--------|---------|
| Tavily extract | ❌ Nav/footer only | XHS is JS SPA, Tavily can't render dynamic content |
| Tavily search (`site:xiaohongshu.com`) | ❌ No substantive content | Same SPA issue |
| Jina Reader (`r.jina.ai`) | ❌ Empty response | Cannot handle XHS SPA |
| Browser direct (Browserbase) | ❌ IP risk (error 300012) | Cloud server IP blacklisted by XHS anti-bot |
| curl + Mobile UA | ⚠️ Shell only | Gets `__INITIAL_STATE__` but `noteData.data` is empty without login cookie |
| **TikHub API** | ✅ Full content | 71 XHS tools: note detail V2-V7, search, comments, user info, images |

### TikHub XHS Key Endpoints
- `xiaohongshu_web_get_note_info_v2/v4/v7` — Note detail (V5 requires self-provided cookie)
- `xiaohongshu_web_search_notes` / `_v3` — Search notes
- `xiaohongshu_web_get_note_comments` — Comments
- `xiaohongshu_web_get_user_info` / `_v2` — User profile
- `xiaohongshu_web_get_user_notes_v2` — User's notes list
- `xiaohongshu_web_v2_fetch_feed_notes_v2/v3` — Feed + single note (V3 supports short links)
- `xiaohongshu_web_v2_fetch_note_image` — Note images
- `xiaohongshu_web_get_visitor_cookie` — Visitor cookie generation

### Cost
- TikHub: $0.01/call (pay-as-you-go)
- Free tier available for initial testing
- CLI bundled in `social-account-doctor/tikhub/`

## Douyin Extraction

| Method | Result |
|--------|--------|
| yt-dlp (no cookies) | ❌ "Fresh cookies needed" |
| yt-dlp + `--cookies-from-browser chrome` | ✅ Works (needs local Chrome with Douyin login) |
| yt-dlp (short link `v.douyin.com`) | ✅ Sometimes works without cookies |

## Bilibili Extraction

| Method | Result |
|--------|--------|
| yt-dlp (no cookies) | ❌ HTTP 412 Precondition Failed |
| yt-dlp + cookies | ✅ Expected to work |

## Alternative: User-Provided Content
When automated extraction fails, ask user to:
1. Paste note content directly
2. Provide screenshot of the note
3. Share the URL for manual extraction via their browser

## Recommendation
- **Automated pipeline**: TikHub API (most reliable, $0.01/call)
- **Fallback**: User manually provides content
- **Not recommended**: Tavily/Jina/browser direct for XHS from cloud servers
