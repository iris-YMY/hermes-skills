---
name: web-research
description: Web search and browser-based data extraction — engine selection, regional pitfalls, JS scraping patterns, and Chinese site quirks.
---

# Web Research & Data Extraction

## Overview
Finding information via search engines and extracting structured data from websites. Covers engine selection, browser scraping techniques, and regional/site-specific pitfalls.

---

## 1. Web Search

### Engine Selection Guide

| Engine | Best For | Pitfalls |
|--------|----------|----------|
| Bing (intl) | General queries, good English results | Use `bing.com`, NOT `cn.bing.com` |
| Bing China (`cn.bing.com`) | Chinese government/official info | **Heavily filtered for entertainment/anime; returns unrelated results** |
| DuckDuckGo (lite) | Quick lightweight queries | May timeout on heavy pages |
| Wikipedia | Factual/reference content | May block/timeout from China servers |
| Baidu | Chinese-language content | Often triggers captcha/verification |
| Google | Broadest coverage | Often blocked from China servers |

### Recommended Approach
1. **Start with Bing international**: `https://www.bing.com/search?q=QUERY`
2. **For Chinese content**: Baidu Baike via browser navigation works better than curl
3. **For anime/manga news**: Try AnimeNewsNetwork, MyAnimeList, or official studio sites
4. **Avoid**: `cn.bing.com` for entertainment content

### Pitfalls
- **Bing China region lock**: Even with English queries, may redirect to domestic results
- **Wikipedia timeouts**: `en.m.wikipedia.org` often times out; use `en.wikipedia.org`
- **Empty curl responses**: If curl returns 0 bytes, connection was likely blocked — try browser navigation
- **Punycode domains**: Chinese IDN domains arrive as `xn--` labels. Decode before analysis:
  ```python
  import idna
  decoded = idna.decode("xn--9kqq05d")  # → "云梯"
  ```
  Full domain `xn--9kqq05d.xn--cesw6hd3s99f.com` → `云梯.浙地珠宝.com`
- **CDN-fronted HTTPS timeouts**: When DNS resolves to a blocked/wrong IP but the site is reachable via CDN, use `--resolve` to force the correct IP:
  ```bash
  curl -sL "https://example.com/path" \
    --resolve "example.com:443:210.16.166.154" \
    --max-time 30
  ```
  Discovery method: HTTP (port 80) often resolves to a different (working) IP than HTTPS. Check both, and use `dig +short` to find CDN CNAME chains.

---

## 2. Browser-Based Web Scraping

### Core Workflow
1. Navigate to the data page with `browser_navigate`
2. Inspect structure with `browser_snapshot`
3. Find hidden URLs via `browser_console` JS queries
4. Extract structured data — iterate table rows or cards via console JS
5. Handle pagination/lazy load with `browser_scroll` then re-query

### Console JS Patterns
```js
// ✅ Use 'var' — 'let'/'const' persist across evaluations
var rows = document.querySelectorAll('table tr');
var data = [];
rows.forEach(function(row) {
  var cells = row.querySelectorAll('td');
  if (cells.length >= 4) {
    data.push({title: cells[0].innerText.trim()});
  }
});
JSON.stringify(data);
```

```js
// ✅ IIFE pattern — allows 'return' for cleaner flow control
// Use when logic needs multiple branches or early returns
(() => {
  var text = document.body.innerText;
  var idx = text.indexOf('TARGET_KEYWORD');
  if (idx > -1) {
    return text.substring(Math.max(0, idx - 200), idx + 1500);
  }
  return 'Not found';
})()
```

### Finding Hidden URLs
```js
var links = Array.from(document.querySelectorAll('a'));
links.filter(function(a) { return a.textContent.includes('KEYWORD'); })
     .map(function(a) { return {text: a.textContent.trim(), href: a.href}; });
```

---

## 3. Chinese Site Quirks

- **Damai.cn**: Good for concerts/theater/sports, does NOT host film festival schedules
- **SIFF official** (siff.com): Full schedule with table-based layout, provides Excel download
- **Ticketing vs Content separation**: Ticketing platforms (Damai, Taopiaopiao) handle sales; event official sites host detailed schedules
- **Anti-bot measures**: Set realistic User-Agent, add delays, or use browser over curl

### Documentation Platforms (Mintlify / llms.txt pattern)
Many modern docs sites (Mintlify, etc.) expose raw markdown even when the main site is a JS SPA.

**Pattern**: Append `.md` to any docs URL → get raw markdown via curl.
**Index**: Fetch `/llms.txt` at the docs root → get a full sitemap of all pages with URLs.

**Z.ai / Zhipu AI (confirmed working 2026-06)**:
- `zhipuai.cn`, `open.bigmodel.cn`, `www.bigmodel.cn` — all JS SPAs, curl returns empty/loading page only
- `docs.z.ai` — Mintlify-based, fully accessible via curl with `.md` suffix
- Step 1: `curl https://docs.z.ai/llms.txt` → get sitemap (all doc URLs)
- Step 2: `curl https://docs.z.ai/guides/llm/glm-5.2.md` → get full model documentation
- Works for ALL pages: `/guides/*`, `/api-reference/*`, etc.
- See `references/zai-docs-access.md` for full details and page inventory.

### External Search API Services
For cost comparison between external search APIs (Tavily, etc.) vs LLM token costs for browser-based research, see `references/tavily-cost-analysis.md`.

For tested extraction methods on Chinese platforms (XHS/Douyin/Bilibili) — including which tools fail and why — see `references/chinese-platform-extraction.md`. **Key finding**: XHS cannot be scraped from cloud servers via Tavily/Jina/browser; only TikHub API ($0.01/call) reliably returns full content.
- API Key 配置在 `~/.env` → `TAVILY_API_KEY`
- 免费档：1,000次/月（Researcher plan）
- 用法：`POST https://api.tavily.com/search` with `api_key` in body
- 1 credit = 1 search or 1 extract call
- ⚠️ **JS SPA Limitation (CONFIRMED 2026-07-13)**: Tavily `/extract` CANNOT render JavaScript SPAs. Tested on Xiaohongshu: extract returns only navigation/footer HTML (2,891 chars of boilerplate). Tavily `/search` finds XHS URLs but raw_content is equally useless. Jina Reader (`r.jina.ai`) also fails on XHS SPA (empty response). **For JS SPA content extraction, use TikHub API or browser automation with login cookies instead.**

For cost comparison between external search APIs vs LLM token costs for browser-based research, see `references/tavily-cost-analysis.md`. **Tavily free tier is now registered and configured** (2026-07-13).

**Xiaohongshu Data Extraction (CONFIRMED 2026-07-13)**:
XHS is a JS SPA — all standard extraction methods fail. See `references/xhs-data-extraction-methods.md` for the full comparison matrix. Summary:
- ❌ Tavily extract/search — JS not rendered
- ❌ Jina Reader — empty response
- ❌ Browser direct — IP risk control (error 300012) on cloud servers
- ⚠️ curl + Mobile UA (bare URL) — gets `__INITIAL_STATE__` shell but note data requires login cookie
- ✅ **curl + Mobile UA + full WeChat share URL** — `xsec_token` grants temp access; full data in `window.__SETUP_SERVER_STATE__` (title, desc, interactions, images, comments). See `references/xhs-data-extraction-methods.md` for workflow.
- ✅ **TikHub API** ($0.01/call) — 71 XHS tools (note detail, search, comments, user info). CLI bundled at `~/.hermes/skills/social-media/social-account-doctor/tikhub/bin/tikhub`. Requires `TIKHUB_API_KEY` in `~/.env`.
- 🔄 **User manual input** — user pastes note content directly (zero-cost fallback)

**Tavily (CONFIGURED 2026-07-13)**:
- Free tier activated (1,000 credits/month, no CC required)
- API Key stored in `~/.env` as `TAVILY_API_KEY`
- Usage: `curl -s -X POST https://api.tavily.com/search -H "Content-Type: application/json" -d '{"api_key":"$TAVILY_API_KEY","query":"...","max_results":5}'`
- Endpoints: `/search` (web search), `/extract` (URL content extraction), `/crawl` (site crawling), `/research` (deep research)
- Registration blocked by Cloudflare Turnstile on headless browsers — user must register manually in their own browser For Tavily registration, API key setup, and headless browser pitfalls, see `references/tavily-setup.md`.

### Chinese News/Finance APIs (No Auth Required)
These work via `curl` from the cron server — valuable for automated data gathering:

| API | URL Pattern | Returns |
|-----|-------------|---------|
| Sina 7×24 Live | `zhibo.sina.com.cn/api/zhibo/feed?page={N}&page_size=20&zhibo_id=152&tag_id=0&type=0` | Financial/macro/company/intl news with timestamps+tags |
| EastMoney Indices | `push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006&fields=f2,f3,f4,f12,f14` | Real-time 上证/深证/创业板 data |
| EastMoney Sectors | `push2.eastmoney.com/api/qt/clist/get?...fs=m:90+t:2...` (industry) or `t:3` (concept) | Sector performance rankings |
| Sina News Feed | `feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=30&page=1` | Article titles+intros (unreliable JSON parsing) |

**Blocked/unreliable from cron server**: Google News RSS, BBC Chinese RSS, Weibo hot search API, Baidu hot search, CLS.cn, `news.qq.com`

See `broadcast-cronjobs` skill → `references/chinese-news-apis.md` for full code examples.

### Proxy/VPN Service Panels (机场/梯子)
Chinese proxy services commonly use SSPanel + Metron theme. For investigation techniques (panel identification, `loginConfig` extraction for real domain + captcha flags, obfuscated JS analysis, email endpoint liveness probe, server recon), plus full registration + login + pricing retrieval workflows, post-registration dashboard/node/client analysis, protocol upgrade detection, and SOP generation, see `references/sspanel-investigation.md`. For JS deobfuscation details and API endpoint reference, see `references/sspanel-metron-reference.md`.

**Registration via API (SSPanel)**:
- **Critical quirk**: API parameter is `emailcode` (NO underscore), but HTML form field is `email_code` (WITH underscore). This mismatch is the #1 registration failure cause.
- Workflow: `POST /auth/send` (send verification code) → `POST /auth/register` (register with `emailcode`) → `POST /auth/login` (get session cookies) → `GET /user/shop` (view pricing)
- No cookies needed for send/register — server binds codes by email address
- Rate limiting: `/auth/send` limits per email (~60s between attempts)

**Evaluation checklist**: Decode Punycode domain → DNS/IP (`dig`, `ipinfo.io`) → TLS cert (`openssl s_client`) → Panel type (HTML theme markers) → Pricing (requires login) → Registration → Client compatibility

**Platform compatibility** (key clients):
| Client | Win | Mac | Linux | iOS | Android | HarmonyOS NEXT | VLESS |
|--------|:---:|:---:|:-----:|:---:|:-------:|:--------------:|:-----:|
| FlClash | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| Clash/ClashX | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Surge | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Shadowrocket | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |

**HarmonyOS NEXT (纯血鸿蒙)**: Cannot install APK files — all Android proxy clients incompatible. No native HarmonyOS proxy clients support subscription links (VLESS/VMess/SSR). System VPN only supports L2TP/IPSec. Alternatives: computer as proxy gateway + phone Wi-Fi proxy, or router-level proxy (OpenWrt).

**Subscription URL format**: `https://SUBSCRIPTION_SERVER/PATH?token=TOKEN&via=CLIENT_NAME` — the `via` parameter selects client-specific subscription format. Import via one-click URL scheme (`clash://install-config?url=`, `flclash://install-config?url=`), QR code, or manual copy.

---

## 4. Browser vs Terminal

| Approach | Best For |
|----------|----------|
| `browser_navigate` + `browser_snapshot` | Heavy JS rendering, captcha protection |
| `browser_console` | Interactive DOM inspection, live data extraction |
| `curl` with User-Agent | Simple API endpoints, lightweight HTML |
| `browser_vision` | Fallback when console JS fails (visual extraction) |

### Pitfalls
- **Console `let`/`const` persistence** — most common error; always use `var`
- **Dynamic content not in snapshot** — `browser_snapshot` may miss JS-rendered content
- **Truncated results** — `JSON.stringify` on large datasets may hit output limits; use `.slice(0, N)`
- **Vision fallback** — `browser_vision` may return 404 if model unavailable; have JS fallback ready
- **`browser_navigate` timeout but page loaded** — some sites (GitHub) trigger timeout errors even when the page loads. Recovery pattern:
  1. Check `document.title` via `browser_console` — if it returns a valid title, the page IS loaded
  2. Use `browser_snapshot` to get the DOM state (may show elements even after timeout error)
  3. If snapshot is empty but title exists, try `browser_console` with `document.body.innerHTML` to inspect content
### Cloudflare Turnstile Pitfalls (Auth Sites)
- **Turnstile widget fails silently**: On auth pages (e.g. `auth.tavily.com`), the Cloudflare Turnstile iframe may render as present in `browser_snapshot` but fail to execute the challenge JS. Check DOM for hidden error messages: `document.querySelectorAll('[role="alert"], .error')` — often reveals "We couldn't load the security challenge."
- **Fix**: Navigate directly to the signup/login URL with the full `?state=...` parameter instead of clicking through from the landing page. The redirect chain sometimes drops Turnstile initialization.
- **`browser_snapshot` misses password fields**: After clicking "Sign up" from a login page, `browser_snapshot` may show only the email field even though a password field is visually present. Use `browser_vision` or `document.querySelectorAll('input')` to discover hidden form fields before assuming the form is incomplete.
- **Headless browser detection**: Turnstile is specifically designed to detect automation. If the widget consistently fails, fall back to asking the user to register manually in their own browser and provide credentials.

### CAPTCHA blocks headless automation
Sites like GitHub (Arkose Labs), Cloudflare Turnstile, DataDome detect headless browsers and block form submission. The CAPTCHA iframe stays empty (`src=""`), and the site shows generic errors. Solution: manual intervention required.

### Cloudflare Turnstile on Auth0 signup pages
Tavily (`auth.tavily.com`) uses Auth0 + Turnstile. In headless mode: Turnstile stuck on "Verifying...", password field never renders, form submit fails with `"We couldn't load the security challenge"`. Fallback: manual registration or social login (Google/GitHub).

---

## 6. Agent-Reach (Internet Capability Layer)

**Agent-Reach** is a Python CLI tool that gives AI agents read/search access to 13 internet platforms (Twitter, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu, etc.) via a unified routing layer with multi-backend failover.

- **Install on Chinese cloud servers**: See `references/agent-reach-china-server.md` for the full pitfall chain (PyPI unavailable, GitHub TLS fails, mirror proxy workaround, mcporter/Exa setup, expected channel availability).
- **Quick usage**: `agent-reach doctor` for health check, `mcporter call 'exa.web_search_exa(query: "...")'` for AI search, `curl -s "https://r.jina.ai/URL"` for web reading.

---

## 6b. Agent Internet Tools — Installation & Platform Reference

For Agent-Reach install (Chinese server pitfalls), MCP server configuration, cookie setup, and platform-specific CLI commands, see `references/agent-internet-tools-setup.md`.

---

## 7. Verification
After extraction, report:
- Total record count
- Sample of first/last entries
- Data completeness (are all fields populated?)
- Any pagination or lazy-loaded content remaining
