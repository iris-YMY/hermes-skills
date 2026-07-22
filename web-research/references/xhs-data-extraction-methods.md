# XHS Data Extraction Methods — Comparison (2026-07-13)

Tested extracting content from `xiaohongshu.com/explore/{note_id}` on Tencent Cloud server.

## Results Matrix

| Method | Result | Detail |
|--------|--------|--------|
| Tavily `/extract` | ❌ | Returns 2,891 chars of navigation/footer only. JS SPA not rendered. |
| Tavily `/search` with `site:xiaohongshu.com` | ❌ | Finds URLs but `raw_content` is 20K chars of base64 images + boilerplate, no note text. |
| Jina Reader (`r.jina.ai/URL`) | ❌ | Empty response (0 bytes). Cannot handle XHS SPA. |
| `browser_navigate` (headless Chrome) | ❌ | IP risk control: error 300012 "IP at risk. Switch to a secure network." |
| `curl` + Mobile UA (bare URL `/explore/{id}` or `/discovery/item/{id}`) | ⚠️ | Gets `__INITIAL_STATE__` shell (817K HTML) but `noteData.data` is empty — note details require login cookie. |
| **`curl` + Mobile UA + full WeChat share URL** (2026-07-21) | ✅ | Full note data in `window.__SETUP_SERVER_STATE__`. **Must include ALL share params** (`xsec_token`, `share_id`, `xsec_source`, `app_platform`, `app_version`, etc.) from the WeChat share link. See workflow below. |
| `curl` + Desktop UA | ⚠️ | Same as bare — `__INITIAL_STATE__` exists but `noteData.data` empty, only `collectionData` has basic metadata. |
| **TikHub API** | ✅ | 71 XHS tools: note info (v2/v4/v5/v7), search, comments, user info, images. $0.01/call. |
| User manual input | ✅ | Zero cost, user pastes content directly. |

## TikHub XHS Tool Inventory

Bundled CLI: `~/.hermes/skills/social-media/social-account-doctor/tikhub/bin/tikhub`
Tool specs: `tikhub/references/tools-xiaohongshu.json` (71 tools)

Key tools:
- `xiaohongshu_web_get_note_info_v2` — Note details (title, desc, images, interactions)
- `xiaohongshu_web_search_notes` — Search notes by keyword
- `xiaohongshu_web_get_note_comments` — Note comments
- `xiaohongshu_web_get_user_info` — User profile
- `xiaohongshu_web_get_user_notes_v2` — User's note list
- `xiaohongshu_web_get_visitor_cookie` — Get visitor cookie (no login needed)
- `xiaohongshu_web_v2_fetch_feed_notes_v3` — Note detail via short link

Setup: Add `TIKHUB_API_KEY=xxx` to `~/.env` (register at tikhub.io)

## yt-dlp Platform Support (tested 2026-07-13)

| Platform | yt-dlp Result | Workaround |
|----------|--------------|------------|
| Douyin | ❌ "Fresh cookies needed" | `--cookies-from-browser chrome` or export cookies file |
| Bilibili | ❌ HTTP 412 Precondition Failed | Need Referer header or cookies |
| Kuaishou | Untested | Likely needs cookies |
| Xiaohongshu | Not supported | Browser fallback required |

## ffmpeg Frame Extraction (WORKING)

```bash
# Extract duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO")

# Extract keyframes: start, middle, climax
ffmpeg -i "$VIDEO" -vf "select='eq(n\,0)+eq(n\,15)+eq(n\,30)'" -vsync vfr /tmp/frame_start_%03d.jpg
ffmpeg -i "$VIDEO" -ss $((DURATION/2)) -t 5 -vf "fps=2" /tmp/frame_mid_%03d.jpg
ffmpeg -i "$VIDEO" -ss $((DURATION*3/4)) -t 5 -vf "fps=2" /tmp/frame_climax_%03d.jpg
```

Tested: 5s test video → 3 frames extracted successfully.

## XHS curl + Share URL Method (CONFIRMED 2026-07-21)

WeChat share URLs contain `xsec_token` granting temporary read access. Server returns full SSR HTML with `window.__SETUP_SERVER_STATE__` JSON — no login cookie needed.

**Prerequisites**: Full share URL with ALL query params (`xsec_token`, `share_id`, `xsec_source`, etc.). Bare note ID URLs → empty data.

```bash
# Fetch with mobile UA
curl -s -L \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" \
  "FULL_SHARE_URL" > /tmp/xhs_page.html

# Quick extract with grep
grep -oP '"title":"[^"]*"|"desc":"[^"]*"|"nickname":"[^"]*"|"likedCount":"[^"]*"|"collectedCount":"[^"]*"|"commentCount":"[^"]*"|"name":"[^"]*"(?=,"type":"topic")' /tmp/xhs_page.html
```

**Data structure** in `__SETUP_SERVER_STATE__ → LAUNCHER_SSR_STORE_PAGE_DATA`:
- `noteData`: title, desc, interactInfo {likedCount, collectedCount, commentCount, shareCount}, tagList, imageList, user
- `commentData`: comments [{content, user.nickname, likeCount, ipLocation}]
- `userOtherNotesData`: [{title, collects, likes, type}]

**Limitations**: `xsec_token` may expire; only works on WeChat-forwarded share links; image CDN URLs have time-limited signatures.

---

## GitHub Download from China Servers

`git clone` times out (60s+) on Tencent Cloud. Use `raw.githubusercontent.com` + curl instead:

```bash
# Get file tree
curl -sL "https://api.github.com/repos/OWNER/REPO/contents/" | python3 -c "..."

# Download each file
curl -sL --connect-timeout 10 --max-time 20 \
  "https://raw.githubusercontent.com/OWNER/REPO/main/PATH" -o /dest/PATH
```

API rate limit: 60 req/hour unauthenticated. For large repos, use `git clone --depth 1` (sometimes works when full clone doesn't).
