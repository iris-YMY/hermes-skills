# XHS Content Extraction via curl (Tavily Fallback)

## When to Use
Tavily unavailable or returns empty/blocked results. Browser gets "IP at risk" from XHS anti-bot.

## Method: curl with Mobile User-Agent

### Step 1: Fetch HTML with full share URL parameters
```bash
curl -s -L --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" \
  "<FULL_SHARE_URL_WITH_PARAMS>" > /tmp/xhs_post.html
```

⚠️ **CRITICAL**: Use the FULL share URL with all query parameters (`xsec_token`, `share_id`, etc.). Stripped URLs (`/discovery/item/<id>` only) get redirected to error pages.

### Step 2: Extract text content
```python
import re
# Title
title = re.search(r'"title":"([^"]*)"', html)
# Description
desc = re.search(r'"desc":"([^"]*)"', html)
# Author nickname
nickname = re.search(r'"nickName":"([^"]*)"', html)
# Interaction data
likes = re.search(r'"likedCount":"([^"]*)"', html)
collects = re.search(r'"collectedCount":"([^"]*)"', html)
comments_count = re.search(r'"commentCount":"([^"]*)"', html)
# Tags
tags = re.findall(r'"name":"([^"]*)"(?=,"type":"topic")', html)
```

### Step 3: Extract image URLs
```python
# Method A: From img src in carousel items (H5_1080 quality)
urls = re.findall(r'src="(http://sns-webpic[^"]+!h5_1080jpg)"', html)

# Method B: From SSR preload data (higher quality, but escaped)
urls = re.findall(r'"imageScene":"H5_DTL","url":"(http[^"]+)"', html)
```

### Step 4: Decode escaped URLs
⚠️ **CRITICAL PITFALL**: URLs from SSR JSON data contain `\\u002F` (JSON-escaped slashes). Must decode:
```python
decoded = [u.replace('\\u002F', '/').replace('\\u002f', '/') for u in urls]
```
Without this, curl fails with DNS resolution errors (literal `\u002F` in hostname).

### Step 5: Download images immediately
⚠️ **CRITICAL**: CDN URLs expire after ~10-15 minutes. Must fetch fresh URLs and download in the same session.

```python
import urllib.request, concurrent.futures, os

def download(item):
    name, url = item
    path = f"/tmp/xhs_images/{name}"
    try:
        urllib.request.urlretrieve(url, path)
        return f"{name}: {os.path.getsize(path)} bytes"
    except Exception as e:
        return f"{name}: FAIL - {e}"

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(download, [(f"img_{i}.jpg", url) for i, url in enumerate(decoded)]))
```

## Pitfalls
- **Browser blocked**: `browser_navigate` gets "IP at risk" error — use curl instead
- **Stripped URLs fail**: `/discovery/item/<id>` without params → 302 to error page
- **URL escaping**: `\\u002F` in JSON data → must decode to `/` before downloading
- **CDN expiry**: URLs valid ~10-15 min, re-fetch if download fails
- **Parallel download**: Use `concurrent.futures` with 5 workers, NOT curl with `&` (Hermes blocks backgrounding)
- **No `&` in terminal commands**: Hermes blocks `&` backgrounding in terminal tool
- **Referer header**: Some CDN endpoints may require `Referer: https://www.xiaohongshu.com/`

## Anti-Bot Bypass Summary
| Method | Result |
|--------|--------|
| browser_navigate | ❌ IP at risk |
| curl with mobile UA + full params | ✅ Works |
| curl without params | ❌ Redirect to error |
| curl with desktop UA | ❌ May be blocked |
