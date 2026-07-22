# TikHub CLI Troubleshooting

## Error: "Unknown tool: xxx"

**Cause**: Local tool catalog (`references/tools-{platform}.json`) is stale.

**Fix**:
```bash
export PATH="$HOME/.local/bin:$PATH"
export TIKHUB_API_KEY="YOUR_KEY"
cd ~/.hermes/skills/social-media/social-account-doctor/tikhub
python3 scripts/refresh_tools.py xiaohongshu
```

Expected output: `[xiaohongshu] wrote N tool(s) → .../tools-xiaohongshu.json`

After refresh, verify: `tikhub list xiaohongshu search`

---

## Error: "RetryError[HTTPStatusError]" on all calls (session init succeeds)

**Cause**: Cloudflare CDN blocking the server IP (Error 1010: browser signature banned).

**Diagnosis**:
1. `tikhub --health` → works (health endpoint doesn't use sessions)
2. Session init works: `[tikhub] initialized xiaohongshu session=xxx`
3. But ALL `tools/call` fail with RetryError

**This is NOT an API key problem.** The key is valid; Cloudflare blocks the IP before the request reaches TikHub.

**Confirmed affected environments**: Tencent Cloud servers (China region), likely other cloud providers.

**Fix**: Use REST API fallback (see Fallback 1 below). REST API (`api.tikhub.io`) is NOT blocked by the same Cloudflare rule.

---

## Error: "missing TIKHUB_API_KEY"

**Cause**: Key not found in env or `~/.claude/.env`.

**Fix**:
```bash
mkdir -p ~/.claude
echo 'TIKHUB_API_KEY=YOUR_KEY' > ~/.claude/.env
chmod 600 ~/.claude/.env
```

Note: tikhub client reads from `~/.claude/.env` (NOT `~/.env`).

---

## Session cache issues after key change

**Cause**: Old session cached in `/tmp/.tikhub-session-{platform}.json`.

**Fix**:
```bash
rm -f /tmp/.tikhub-session-*.json
```

The session file has a 5-minute TTL, but if you switch keys and the old session is still valid, it will keep using the old (possibly invalid) session.

---

## Error: "API Token lacks required permissions" (403)

**Cause**: API Token was created without the required scopes (e.g., `xiaohongshu:read`).

**Diagnosis** (REST API returns explicit message):
```json
{"code":403, "message":"API Token lacks required permissions, please edit the API Token scopes at user dashboard, go to: https://user.tikhub.io/dashboard/api"}
```

**Fix**: Go to https://user.tikhub.io/dashboard/api → edit token → enable required platform scopes.

Note: MCP endpoint may just timeout silently instead of returning this error. Always test with REST API first to see the real error.

---

## Fallback 1: REST API (when MCP endpoint times out)

TikHub has **two endpoints**: MCP (`mcp.tikhub.io`) and REST (`api.tikhub.io`). When MCP times out (hangs 60s+ with 0 bytes), REST API often still works. **This is the primary fallback — always try REST before giving up.**

```bash
# REST API direct call (bypasses MCP entirely)
curl -s --max-time 30 \
  "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes?keyword=咖啡&page=1" \
  -H "Authorization: Bearer $TIKHUB_API_KEY" \
  -H "Accept: application/json"
```

### REST API Response Structure (confirmed 2026-07-15)

- Outer: `{"code":200, "data": {...}, "message":"..."}`
- Inner data at `resp["data"]["data"]` (**double data nesting**)
- Search users: `resp["data"]["data"]["users"]` — each user has `id`, `name`, `sub_title` (e.g. "Fans 51.7k"), `red_official_verified`
- User posted notes: `resp["data"]["data"]["notes"]` — each note has `id` (=note_id), `type` ("normal"=image, "video"=video), `display_title`, `liked_count`, `collected_count`, `comments_count`, `create_time` (Unix timestamp), `xsec_token`
- Note detail: `resp["data"]["data"]["data"]` (triple data nesting)

### REST API Endpoints (36 XHS endpoints confirmed)

- `/api/v1/xiaohongshu/app_v2/search_users?keyword=X&page=1`
- `/api/v1/xiaohongshu/app_v2/search_notes?keyword=X&page=1`
- `/api/v1/xiaohongshu/app_v2/get_user_info?user_id=X`
- `/api/v1/xiaohongshu/app_v2/get_user_posted_notes?user_id=X&cursor=`
- `/api/v1/xiaohongshu/app_v2/get_image_note_detail?note_id=X`
- `/api/v1/xiaohongshu/app_v2/get_note_comments?note_id=X`
- Full list: `curl -s https://api.tikhub.io/openapi.json` (2.6MB)

### Building URLs

- Note URL: `https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}`
- User profile URL: `https://www.xiaohongshu.com/user/profile/{user_id}`

**Advantage**: REST returns explicit error messages (scope issues, auth errors) while MCP just times out silently.

---

## Fallback 2: Tavily + Manual Data Collection

When BOTH tikhub endpoints are unavailable, use this workflow:

1. **Search brand data via Tavily API**:
```bash
source ~/.env  # TAVILY_API_KEY
curl -s -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"小红书 品牌名 官方账号 运营\",\"max_results\":5,\"include_answer\":true}"
```

2. **Parallel data collection**: Use `delegate_task` with 3 parallel subagents:
   - Subagent 1: International brands search
   - Subagent 2: Local brands search
   - Subagent 3: Industry analysis + XHS URL collection

3. **Generate Excel report** with openpyxl:
```bash
pip3 install openpyxl --break-system-packages -q
/usr/bin/python3 your_report_script.py
```

4. **Report data limitations**: Mark all estimated data as "(估)" and cite sources.
5. **URL integrity**: When collecting URLs via Tavily search, distinguish between:
   - URLs from brand-specific search results (more reliable)
   - URLs from general XHS link pools (must mark as "AI推测，未验证")
   - Never fabricate post titles or descriptions — always annotate "(AI推测，基于品牌特征撰写)"

---

## XHS Search Keyword Pitfalls (confirmed 2026-07-15)

### Chinese-first principle
When searching XHS brand accounts, **always search in Chinese first**. English names (especially with special characters) may return different/incomplete results.

**Case**: Searching Häagen-Dazs
- `Häagen-Dazs` (with umlaut ä) → returned many unofficial personal accounts (fans <50)
- `哈根达斯` → found the verified blue-V account "哈根达斯Haagen-Dazs" (44.1k fans)

**Best practice**:
1. Search with brand's Chinese name first
2. If results are poor, try English name (without special characters)
3. If still not found, try Chinese name + "官方"
4. Check for `red_official_verified=True` in results

### Same-name account trap
XHS may have multiple accounts with the same brand name:
- Verified official account (usually most fans but not always)
- Distributor/franchise accounts (sometimes more fans but not official)
- Old/abandoned accounts
- Personal accounts

**Judgment**: Prefer `red_official_verified=True` accounts as the official brand account.

### Hidden likes
Some brands hide their like counts. API returns `liked_count=0`. This is not necessarily a data error — it may be an intentional brand setting. In this case, rely on `collected_count` and `comments_count` for engagement assessment.

---

## execute_code Sandbox Limitations

The `execute_code` sandbox **cannot make outbound HTTP requests** (all API calls are blocked).

**Impact**:
- Cannot call TikHub REST API from execute_code
- Cannot call Tavily API from execute_code
- openpyxl and other pip-installed packages are not available in the sandbox

**Workaround**:
1. All API calls must go through `terminal` (bash + curl)
2. Complex scripts: use `write_file` to `/tmp/`, then execute with `terminal` using `/usr/bin/python3`
3. Install openpyxl first: `pip3 install openpyxl --break-system-packages -q`
4. System Python path: `/usr/bin/python3` (Python 3.12, has geopandas/matplotlib/openpyxl)
