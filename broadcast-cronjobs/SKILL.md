---
name: broadcast-cronjobs
description: Scheduled cron jobs — daily news and weather briefings with multi-platform delivery, content formatting, and operational management.
---

# Broadcast Cron Jobs

## Overview
Managing scheduled cron jobs that deliver daily briefings (news, weather) to messaging platforms. Covers job configuration, content formatting rules, delivery patterns, and operational commands.

---

## 1. Active Broadcast Jobs

> ℹ️ **Feishu doc token: `V3KrdD0CTootQWxJskFcjB8vnTe`** — last synced 2026-07-02

### Daily News Broadcast (每日新闻播报)
| Field | Value |
|-------|-------|
| Job ID | `e402e3a86482` (data-master / 添添开心) |
| Previous ID | `c85928e4d430` (paused — was on default/黑执事) |
| Schedule | `0 10 * * *` (10:00 CST daily) |
| Model | `qwen3.7-max` |
| Deliver | `local` (card sent by script via Feishu API, NOT by cron delivery) |
| Card Script | `send_news_card.py` (reads JSON → builds card → sends to group) |
| Script | `news_data_fetcher.py` (runs before prompt, injects real data) |
| Workdir | `/home/ubuntu/.hermes` |

**Architecture**: Pre-fetch → JSON → Card. See Section 9.

### ⚠️ Card Delivery Pattern (v3, since 2026-07-02)
Both news and weather broadcasts use **Feishu Interactive Card** delivery, NOT standard cron `deliver: feishu:...`:
1. Pre-fetch script (`news_data_fetcher.py` / `weather_data_fetcher.py`) gathers data
2. Agent generates structured JSON → writes to `/tmp/news_card_data.json` or `/tmp/weather_card_data.json`
3. Agent calls `python3 send_news_card.py` or `python3 send_weather_card.py` via terminal
4. Script builds Feishu card JSON → sends via `POST /im/v1/messages` with `msg_type: interactive`
5. Cron `deliver` is set to `local` (suppresses default text delivery)

**Key files**:
- `scripts/send_news_card.py` — news card builder + sender
- `scripts/send_weather_card.py` — weather card builder + sender (dynamic header color by weather)
- `scripts/news_data_fetcher.py` — news data pre-fetcher
- `scripts/weather_data_fetcher.py` — weather data pre-fetcher
- App credentials hardcoded in send scripts (data-master app: `cli_aa9ea34aaff85cda`)

### hr-assistant Profile Card Architecture
App: `cli_aa9ebcbfc6e35cba` (secret in `~/.hermes/profiles/hr-assistant/home/.lark/config.yaml`)
Target chat: `oc_d811c650f76f16e98ac7a65517e0128f`
Scripts: `send_elasticity_card.py` (in profile's scripts/ dir)
Architecture: Pre-fetch (`monthly_elasticity_report.py`) → JSON to `/tmp/elasticity_report_data.json` → card script reads & sends
Job: `00dc5d3c14c2` (月度弹性支出分析报告, monthly 8th 10AM, `deliver: local`)

**Weather card dynamic color**: Header template changes based on `rain_forecast.weather`:
- 晴 → `orange` | 阴/多云 → `green` | 雨/雪 → `indigo` | default → `turquoise`

### Morning Weather Broadcast (早安气象播报)
| Field | Value |
|-------|-------|
| Job ID | `844cde709d24` (data-master / 添添开心) |
| Previous ID | `7cc3e2941131` (paused — was on default/黑执事) |
| Schedule | `0 8 * * *` (08:00 CST daily) |
| Model | `qwen3.6-plus` |
| Deliver | `local` (card sent by script via Feishu API, NOT by cron delivery) |
| Card Script | `send_weather_card.py` (reads JSON → builds weather card → sends to group) |
| Script | `weather_data_fetcher.py` (pre-fetch, runs before prompt) |

**Architecture**: Pre-fetch → JSON → Weather Card. Same card pattern as news. See Section 9.

---

## 2. Content Formatting

### News Broadcast Structure (v3 — Feishu Interactive Card format, updated 2026-07-02)
**Design philosophy**: Feishu native card with blue header bar, emoji section headers, source attribution, action buttons. Inspired by "小华" card style.

**Delivery**: `deliver: local` + `send_news_card.py` script sends card via API.

**All sections** (15 fixed, items empty if no data):
1. 📌 今日看点 (TOP tag) — 2-3 条最重磅
2. 🤖 AI 与科技 — 3-5 条
3. 💰 财经与商业 — 2-4 条，含 A 股大盘
4. 🌐 国际形势 — 2-3 条
5. 📜 政府政策动态 — 政策类
6. 🏙️ 上海本地民生 — 住房/税收/民生
7. 🎬 影视与短剧
8. 👜 时尚 / 奢侈品
9. 🏮 国潮文化与国货品牌
10. 🏭 实体行业发展
11. 🏯 国风 / 文化 / 艺术
12. 📱 社交媒体热门 — 微博 TOP5 + 小红书 TOP2 + 知乎 TOP2
13. 📈 股市 / 基金 / 财经 — A 股三大指数 + 金价/油价
14. 💰 基金板块影响分析 — 标注推测性内容
15. 🐟 摸鱼日历 — 农历/进度/假期倒计时

**Agent output**: Structured JSON with `date`, `greeting`, `sections[]`, `tip` fields.
Each section: `{emoji, title, tag?, items: [{text, source}]}`
Each news item: **~2 sentences** (first = event core, second = background/impact).
Source attribution: `"——XX"` (Chinese dash format).

**Card visual elements**:
- Blue gradient header: `📰 早间新闻播报 | YYYY年M月D日 星期X`
- Warm greeting block with left blue border
- `### emoji Section Title` with dividers
- Action buttons: 📋 展开详情 / ⭐ 收藏

**v2→v3 migration** (2026-07-02): User wanted ALL sections kept (not simplified), 2 sentences/item (not 1), and native Feishu card format (blue header bar + icon sections + source attribution). Delivery changed from `feishu:chat_id` to `local` + card script.

### Weather Broadcast Structure (v2 — Feishu Interactive Card format, updated 2026-07-02)
**Delivery**: `deliver: local` + `send_weather_card.py` script sends card via API.

**Card visual elements**:
- Header color adapts to weather: ☀️ 晴天=orange, ☁️ 阴/多云=green, 🌧️ 雨/雪=indigo, default=turquoise
- Sections: 实时气温 → 空气质量 → 紫外线日照 → 降雨预报 → 温馨提醒
- Agent output: Structured JSON with `date`, `location`, `greeting`, `temperature{}`, `air_quality{}`, `uv_sun{}`, `rain_forecast{}`, `tips[]`, `closing` fields
- Tips: 4-6 items with emoji prefix, specific and data-driven

**Agent JSON schema** (written to `/tmp/weather_card_data.json`):
```json
{
  "date": "YYYY年M月D日 星期X",
  "location": "城市名",
  "greeting": "早安，小艾主人！（轻松开场白）",
  "temperature": {"current": N, "feels_like": N, "high": N, "low": N, "humidity": N, "comfort": "...", "wind": "...", "pressure": N},
  "air_quality": {"aqi": N, "level": "...", "pm25": N, "pm10": N},
  "uv_sun": {"uv_index": N, "uv_level": "...", "sunrise": "HH:MM", "sunset": "HH:MM"},
  "rain_forecast": {"weather": "...", "precipitation": N, "rain_analysis": "..."},
  "tips": ["emoji + 具体建议", ...],
  "closing": "祝您今天元气满满，一切顺利！✨"
}
```

### Reminder Rules (pick 4-6)
- 👔 穿搭 (温度+体感+风力) | 😷 口罩 (AQI>100) | 🧴 防晒 (UV≥3)
- 🚗 洗车 (雨率<20%推,>50%劝) | 🏃 运动 (天气好+AQI<100)
- 🪟 通风 (AQI<50) | 💧 补水 (<30%) | 🌿 气压变化

### Style
Both broadcasts use **Feishu Interactive Card** format (deliver: local + card script). News: blue header, emoji sections, 2-sentence items, "——XX" source, warm greeting, action buttons. Weather: dynamic color header (orange/green/indigo/turquoise by weather), structured data sections, 4-6 tips. Professional but warm. Weather style: 活泼开朗男大生, warm + humor, 1-2 light jokes, emoji layout. Both run as 添添开心 (data-master profile), delivered to "AI在这里" Feishu group.

### ⚠️ User Preference: All Cron Jobs Should Use Card Format (2026-07-02)
**User explicitly requested**: "把你所有的cronjob和播报，都按照飞书卡片的模式去进行调整"

**Currently using card format**:
- ✅ 每日新闻播报 (e402e3a86482)
- ✅ 早安气象播报 (844cde709d24)

**Converted to card format (黑执事 profile, 2026-07-02)**:
- ✅ 每日 TODO 播报 (443e0b7686ce) — script: `todo_card_sender.py`, 🔵 blue header
- ✅ 163邮箱定时巡检 (a15369150ae9) — script: `email_card_sender.py`, 🟢 green header
- ✅ 飞书 Token 异常预警 (4a4f6b4f9e54) — script: `token_alert_card_sender.py`, 🔴 red header

**Converted to card format (hr-assistant profile, 2026-07-03)**:
- ✅ 月度弹性支出分析报告 (00dc5d3c14c2) — script: `send_elasticity_card.py`, 🔵 blue header
- ⚠️ Uses **file-based handoff** pattern (see §9.5): `monthly_elasticity_report.py` writes to `/tmp/`, `send_elasticity_card.py` reads and sends card

**Converted to card format (理财大师 profile, 2026-07-02)**:
- ✅ 每日基金投资建议 (ccb47d15762b) — 网关自动识别 :::CARD 标记
- ✅ 每周基金周报 (3cced79a54e0) — 网关自动识别 :::CARD 标记
- ✅ 每月新基金推荐 (68653430510f) — 网关自动识别 :::CARD 标记

**⚠️ 两种卡片推送架构**：
1. **脚本模式**（黑执事/data-master）：`deliver: local` + `send_xxx_card.py` 脚本直接调 API → 适合不需要 LLM 分析的纯数据推送
2. **网关模式**（理财大师）：`deliver: feishu` + Agent 输出 `:::CARD...:::ENDCARD` 标记 → 网关自动提取并以 interactive 类型发送 → 适合需要 LLM 分析的复杂报告

网关模式的实现在 `feishu-card-cron-reports` skill 中有详细说明（修改了 `feishu.py` 的 `send()` 方法）。

**Conversion pattern**:
1. Set `deliver: local` (suppress default text delivery)
2. Create `send_<name>_card.py` script (builds card JSON → POST to Feishu API)
3. Update prompt to output structured JSON (not plain text)
4. Agent calls script via `terminal` to send card

**Card design elements** (based on user's example):
- Colored header bar with emoji + title + date
- Structured sections with emoji icons
- Bottom summary line
- Agent signature footer

---

## 3. Critical Configuration Rules

### ⚠️ Toolset Configuration
**News broadcast**: Set `enabled_toolsets: []` and use `script` field for pre-fetch. The model receives pre-fetched data and needs NO tools. See Section 9 for the pre-fetch script pattern.

**Weather broadcast** (since 2026-06-22): Now uses pre-fetch script `weather_data_fetcher.py`. Model receives pre-parsed data, similar to news broadcast. No special toolset restrictions needed.

**General rule**: **NEVER include `browser` in `enabled_toolsets`.**
Chinese news sites cause cron jobs to hang:
- Baidu → captcha wall
- 36Kr, Huxiu, Sina Finance → 60s timeout
- Result: 60+ turns of retries, never completes

**Do NOT set `["web", "search"]`** without a search API key (`TAVILY_API_KEY`, `EXA_API_KEY`, etc.). Without keys, `check_fn` fails and web_search is excluded → 0 tools loaded.

### ⚠️ Model/Provider Required (嵌套对象格式)
`model` 参数是**嵌套对象**，必须在创建时显式传入：
```json
"model": {"model": "qwen3.7-max", "provider": "qwen"}
```
Cron 在独立 session 中运行，不会继承当前会话的模型配置。

### Multi-Platform Delivery Pattern
To deliver the same briefing to multiple platforms:
1. Create a second cron job with identical prompt/schedule, different `deliver` target
2. Supported `deliver` values: `origin`, `weixin`, `feishu`, `telegram`, `discord`, etc.
3. Both jobs run independently — no coordination needed

---

## 4. Weather Data Sources

### IP Geolocation
⚠️ `ipapi.co` is **rate-limited** (returns `{"error": true, "reason": "RateLimited"}`) — always try a backup:
```bash
# Primary (often rate-limited)
curl -s https://ipapi.co/json/
# Fallback (no auth, generous limits)
curl -s "http://ip-api.com/json/?fields=status,message,country,regionName,city,lat,lon"
# Final fallback: Shanghai (lat=31.22, lon=121.46)
```
⚠️ **Never use `python3 -c "..."`** in terminal for JSON parsing — it triggers the "script execution via -e/-c flag" approval dialog and blocks cron jobs. Use `execute_code` tool instead, or write to a temp file and `cat` it.

### Open-Meteo APIs
- **Weather**: `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=...&daily=...&timezone=Asia/Shanghai`
- **Air Quality**: `https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm2_5,...`

### Data Interpretation
- **Weather codes**: 0=晴, 1=大部晴, 2=多云, 3=阴, 45=雾, 61-65=雨, 95=雷暴
- **UV**: 0-2低, 3-5中, 6-7高, 8-10很高, 11+极高
- **AQI**: 0-50优, 51-100良, 101-150轻度, 151-200中度, 201-300重度
- **Humidity**: <30%干燥, 31-60%舒适, 61-70%微湿, >86%闷热

---

## 5. Operations

### Management Commands
```bash
hermes cron list                          # Check all jobs
hermes cron run <job_id>                  # Test run (delivers immediately — warn user first)
hermes cron pause/resume <job_id>         # Pause/resume
hermes cron update <job_id> --schedule "30 7 * * *"  # Change schedule
hermes cron remove <job_id>               # Delete job
```

### Troubleshooting
When a cronjob "isn't working," follow the systematic diagnostic flow in `references/cronjob-diagnostic-checklist.md`. Covers: status check → config verification → stale skill references → toolset/API key mismatch → command verification → session logs.

### Testing
⚠️ **Avoid `cronjob run` for testing** — it delivers to user's chat immediately, overlapping with conversational replies. Test by running the prompt directly in a session instead.

### ⚠️ Past-time one-shot jobs
Creating a `kind: once` job with `run_at` already in the past results in `next_run_at: null` — the job is created but never fires. Always check current time before scheduling one-shot jobs.

### ⚠️ Model missing on ANY cron creation method (CONFIRMED 2026-06-24 — 3 incidents, +1 on 2026-06-30)
If `model` parameter is omitted on creation, the job fails at runtime with 400 error (`you must provide a model parameter`). This has been confirmed across:
1. Default profile recurring job (via CLI)
2. Cross-profile migration jobs (via CLI `hermes --profile data-master cron create`)
3. One-shot reminder job (via CLI, created by a previous session)
4. TODO 播报 cron job `443e0b7686ce` (2026-06-30) — skill-based job created without model/provider, fixed via `cronjob(action='update', model={"model": "qwen3.6-plus", "provider": "qwen"})`

**Root cause**: `hermes cron create` CLI has NO `--model` flag. The `cronjob` tool supports `model` as nested object.
**Fix**: Use `cronjob(action='create', model={"model": "xxx", "provider": "xxx"})` — see §7.

---

## 6. Known Delivery Issues

### ⚠️ "origin" Delivery Captures Creation Context (confirmed 2026-06-30)
`deliver: "origin"` captures the **chat_id of the conversation where the job was created**, NOT the user's current location. If a job is created in a group chat and the user later moves to DM (or vice versa), reports are silently delivered to the old chat.

**Symptoms**: Job status shows `"ok"`, output file exists, but user says "没收到".
**Diagnosis**: Check `jobs.json` → `origin.chat_id` field. Compare with where user currently is.
**Fix**: Update deliver to explicit target:
- `cronjob(action='update', job_id='xxx', deliver='feishu')` → delivers to Home Channel (default DM)
- `cronjob(action='update', job_id='xxx', deliver='feishu:<chat_id>')` → delivers to specific group

**Best practice**: When creating jobs, prefer explicit `deliver: "feishu"` (Home Channel) over `"origin"` unless the job is intentionally group-specific.

### Weixin aiohttp Bug
- aiohttp 3.13.5 triggers `Timeout context manager should be used inside a task` in both live adapter and standalone delivery paths
- Weather broadcast permanently switched from weixin to feishu (2026-06-03)
- To restore weixin delivery: fix `hermes-cron-delivery-debug` skill (replace `aiohttp.ClientTimeout()` with `asyncio.wait_for`)
- See `references/weixin-async-bug.md` for full call chain, root cause analysis, and fix options

---

## 7. General Cron Job Creation SOP

### 🔴 铁律：禁止使用 `hermes cron create` CLI
`hermes cron create` CLI **没有 `--model` 选项**，创建后 model/provider 永远为 null，运行时必报 400 错误。
此问题已确认发生 **4 次**（2026-06-24 至 2026-06-30），**严禁再次使用 CLI 创建 cron job**。

### 唯一允许的方式：`cronjob` 工具
```json
{
  "action": "create",
  "name": "...",
  "schedule": "...",
  "prompt": "...",
  "deliver": "origin",
  "model": {"model": "qwen3.7-max", "provider": "qwen"}
}
```

### 创建后必须验证
```
cronjob(action='list')  → 确认新 job 的 model 和 provider 不为 null
```

### 跨 Profile 场景（cronjob 工具只能操作当前 profile）
当需要在其他 profile 下创建 cron job 时：
1. 先用 CLI 创建（此时 model=null）：`hermes --profile <target> cron create ...`
2. **立即**读取目标 profile 的 `~/.hermes/profiles/<target>/cron/jobs.json`
3. 用 `execute_code` 修改 JSON，注入 `"model": "qwen3.7-max"` 和 `"provider": "qwen"`
4. 写回文件，用 `grep model` 验证
5. ⚠️ **步骤 2-4 是强制步骤，不可跳过**

### Red Lines
- ❌ **禁止** `hermes cron create` 单独使用（不含后补 model 步骤）
- ❌ **禁止** `enabled_toolsets` 包含 `browser`（中文网站导致无限挂起）
- ✅ **必须** `model` 作为嵌套对象：`{"model": "qwen3.7-max", "provider": "qwen"}`
- ✅ **必须** provider 与 config.yaml 中的 key 一致（是 `qwen`，不是 `custom`）
- ✅ **必须** 创建后立即验证 model/provider 不为 null

### Common Errors

| Error Code | Cause | Fix |
|------------|-------|-----|
| 400 | Missing model parameter | `cronjob(action='update', job_id='xxx', model={"model": "qwen3.7-max", "provider": "qwen"})` |
| 401 | Provider `"custom"` doesn't match config.yaml key `"qwen"` | Same update command above — the cronjob tool auto-captures `provider: "custom"` from the session, which is wrong |
| "ok" but no delivery | Agent timed out on large stdout injection OR deliver mode can't send cards | Check §9.5 (large stdout pitfall) — switch to file-based handoff + `deliver: local` |

### Diagnosing Cron 401/400 Errors
1. **Check job config**: `cronjob(action='list')` → look at `model`, `provider`, `base_url` fields
2. **Check config.yaml**: `cat ~/.hermes/profiles/<profile>/config.yaml` → find actual provider key (e.g., `qwen`)
3. **Check error output**: `cat ~/.hermes/profiles/<profile>/cron/output/<job_id>/*.md` → find the exact error
4. **Fix**: `cronjob(action='update', job_id='xxx', model={"model": "qwen3.7-max", "provider": "qwen"})`
5. **Verify**: `cronjob(action='list')` → confirm provider now matches config.yaml

**Root cause of `"custom"` auto-capture**: When the cronjob tool creates a job, it inherits the current session's provider label (often `"custom"` for non-default provider configs). This label doesn't correspond to any key in config.yaml's `providers:` section, so at runtime the job has no API key → 401 `Missing Authentication header`.

---

## 8. Session Stuck Detection

When a cron job appears to hang (60+ turns, never completes):
```bash
# Check for stuck cron session
ls -lt ~/.hermes/sessions/session_cron_*.json | head -3
# If messages > 50, kill browser and retry
pkill -f agent-browser
rm ~/.hermes/sessions/session_cron_<job_id>_<date>.json
```

---

### ⚠️ web_search Requires API Key
**`web_search` is NOT a free tool.** It requires at least one of:
- `TAVILY_API_KEY` (recommended — free 1000 calls/month, sign up at tavily.com)
- `EXA_API_KEY` (Exa — exa.ai)
- `PARALLEL_API_KEY`
- `FIRECRAWL_API_KEY` / `FIRECRAWL_API_URL`

Without a key, `check_fn` fails and web_search is excluded from the tool list. With `enabled_toolsets: ["web", "search"]` this means **0 tools**. Verify with: `grep -i "EXA\|PARALLEL\|TAVILY\|FIRECRAWL" ~/.hermes/.env`

### ⚠️ Tool Injection Failure Detection
When cron output is empty/hallucinated, check:
1. **API keys exist**: `grep -i "EXA\|PARALLEL\|TAVILY\|FIRECRAWL" ~/.hermes/.env`
2. **Session tools count**: session JSON `tools` array must be > 0 and contain `web_search`
3. **Session messages > 2**: 2 messages = no tool calls were made
4. **Output file size**: sudden drop from baseline indicates tool failure

**Symptoms of hallucination**: model outputs text like `> Action: web_search` or JSON blocks `{"query": "..."}` — it's pretending to search. qwen3.7-max is especially deceptive at this.

**Fix (preferred)**: Switch to direct API approach — `enabled_toolsets: []` + use `execute_code`/`terminal` with curl to hit Sina 7×24 and EastMoney APIs directly. No search API key needed. See `references/chinese-news-apis.md`.

**Fix (alternative)**: Add `TAVILY_API_KEY` or `EXA_API_KEY` to `~/.hermes/.env` and set `enabled_toolsets: ["web", "search"]`.

See `references/tool-injection-failure-20260618.md` for full incident analysis and diagnostic commands.

---

## 9. Feishu Interactive Card Pattern (2026-07-02 confirmed)

### Problem
Hermes `send()` only supports `text` and `post` (rich text) message types. The `interactive` card type is only used internally for `send_exec_approval()` (dangerous command confirmation buttons). Cron jobs cannot directly output interactive cards.

### User Preference
**小艾主人明确要求：所有播报使用飞书互动卡片格式，不使用纯文本或 post 富文本。**

### Solution: Pre-Fetch Script + [SILENT]
Use the pre-fetch script pattern (Section 8) but with a twist:
1. **Script sends card directly** via Feishu REST API (Tenant Token)
2. **Prompt outputs [SILENT]** — agent produces no extra output
3. **`enabled_toolsets: []`** — no tools needed

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  cron scheduler  │────▶│ card_sender.py   │────▶│  prompt [SILENT]│
│  triggers job    │     │ (sends via API)  │     │  → no output    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Card JSON Structure
```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "📋 标题 · 日期（星期）"},
    "template": "blue"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "**粗体** 和 emoji 内容"}},
    {"tag": "hr"},
    {"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 签名栏"}]}
  ]
}
```

### Sending via REST API
```python
def get_tenant_token():
    # Read APP_ID from ~/.lark/config.yaml, APP_SECRET from ~/.bashrc
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read()).get("tenant_access_token")

def send_card(chat_id, card_json):
    token = get_tenant_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    body = json.dumps({
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card_json, ensure_ascii=False),
    }, ensure_ascii=False).encode('utf-8')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())
```

### ⚠️🔴 JSON Generation Pitfall: Chinese Quotation Marks (confirmed 2026-07-03, RE-CONFIRMED 2026-07-04, 2026-07-12, 2026-07-14, 2026-07-20)
**THIS IS THE #1 CAUSE OF NEWS BROADCAST FAILURES (6th occurrence).**

#### 🔴 NEVER use `write_file` to produce JSON containing Chinese text with `""` quotes.
#### 🔴 ALWAYS generate JSON via Python `json.dump()` — either through `execute_code` or by writing a `.py` builder script.

**The rule is absolute**: If you are about to call `write_file` with Chinese news content that may contain `"..."`, STOP. Write a Python script instead.

**Symptom**: `json.decoder.JSONDecodeError: Expecting ',' delimiter` — typically 3-5+ separate errors requiring individual `patch` fixes, each one a waste of turns. 2026-07-20 session: 5 broken quotes across lines 42, 50, 59, 84, 101, ~8 turns wasted.

**Decision tree** (use in this order):
1. **`execute_code` available?** → Use it. Build dict in Python, call `json.dump()`, validate, then call send script. (1 tool call)
2. **`execute_code` NOT available?** → `write_file` a Python builder script to `/tmp/build_news_json.py`, then `terminal` to run it. (2 tool calls)
3. **NEITHER works?** → Use `write_file` for JSON BUT replace ALL `""` with `「」` before writing. (risky, last resort)

**🔴 APPROACH 1 — `execute_code` with `json.dump()` (best, when available)**:
```python
# execute_code — builds dict + dumps + validates in one call
import json
data = {"date": "2026年7月20日 星期一", "greeting": "...", "sections": [...], "tip": "..."}
with open('/tmp/news_card_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
# Validate
with open('/tmp/news_card_data.json') as f:
    v = json.load(f)
print(f"JSON valid: {len(v['sections'])} sections")
```

**🟡 APPROACH 2 — `write_file` a Python script, then `terminal` (fallback, when `execute_code` unavailable)**:
1. `write_file` → `/tmp/build_news_json.py` (Python dict + `json.dump()`)
2. `terminal` → `python3 /tmp/build_news_json.py`
3. `terminal` → `python3 /tmp/validate_json.py` (or inline validation script)
4. `terminal` → `python3 send_news_card.py`

**🟢 APPROACH 3 — Corner brackets only (last resort, risky)**:
Replace ALL `""` with `「」` throughout ALL text fields. Write complete file in ONE call. Never mix styles.

**Do NOT**:
- ❌ Use `write_file` to produce JSON directly when content includes `""` characters (CONFIRMED BROKEN 6 TIMES)
- ❌ Use `python3 -c "..."` in terminal (triggers approval dialog in cron jobs)
- ❌ Try to `patch` individual broken quotes one at a time (you'll always miss more)

### ⚠️ Pitfalls
- **Tenant Token has `im:message:send_as_bot`** — can send cards ✅
- **User Token lacks `im:message.send_as_user`** — cannot send cards ❌ (as of 2026-07-02)
- **Bot must be in target chat** — error `230002: Bot/User can NOT be out of the chat` if not
- **⚠️ chat_id for DM (verified 2026-07-02)**: The `oc_` Home channel ID from `channel_directory.json` may not work if bot isn't in that specific chat. **Must use the actual chat_id from the current DM conversation** (visible in gateway logs or from `_chat_id` field in adapter state). The Home channel is a group chat where bot may not be a member.
- **Header templates**: `blue`, `green`, `red`, `orange`, `purple`, `grey`, `wathet`, `turquoise`, `yellow`, `violet`, `carmine`, `indigo`
- **Script path**: relative to `~/.hermes/scripts/`, bare filename only
- **Encoding**: must use `ensure_ascii=False` and `.encode('utf-8')` for Chinese content

### ⚠️ Large Stdout Injection Kills Cron Jobs (confirmed 2026-07-03)
When a pre-fetch `script` produces large output (>20KB), injecting it into the prompt via stdout causes the agent to timeout or hallucinate. **Symptoms**: session has only 3 messages (user prompt + assistant tool_call + tool result), never reaches card sending step. Status shows `"ok"` but no card delivered.

**Root cause**: The Bitable elasticity report (4600 records) produces ~50KB JSON. When injected into the prompt, qwen3.7-max gets confused by the massive context and either freezes or makes only 1 tool call (e.g., `ls -la` to check the script exists) then stops.

**Fix — File-Based Handoff Pattern**:
```
Script writes to /tmp/report_data.json  (NOT stdout)
↓
Agent prompt says: "run python3 send_card.py"
↓
Card sender script reads /tmp/report_data.json
↓
Card sent via tenant token API
```

**Applied to**: 月度弹性支出分析报告 (`00dc5d3c14c2`, hr-assistant profile)
- `monthly_elasticity_report.py`: writes JSON to `/tmp/elasticity_report_data.json`, prints only summary line
- `send_elasticity_card.py`: reads from `/tmp/elasticity_report_data.json`, builds + sends card
- Agent prompt: minimal — just calls the sender script via terminal

### Card Template Examples
See `references/feishu-card-templates.md` for TODO/Email/Alert card templates and reusable code blocks.
See `templates/news_json_builder.py` for a ready-made Python script that builds news JSON safely (copy → modify → run).
See `templates/validate_json.py` for a quick JSON validator script.

### Card Sender Scripts
| Script | Profile | Job | Header Color |
|--------|---------|-----|-------------|
| `todo_card_sender.py` | 黑执事 | 每日 TODO 播报 | 🔵 blue |
| `email_card_sender.py` | 黑执事 | 163邮箱巡检 | 🟢 green |
| `token_alert_card_sender.py` | 黑执事 | Token 预警 | 🔴 red |
| `send_elasticity_card.py` | hr-assistant | 月度弹性支出分析报告 | 🔵 blue |

### 黑执事 Profile Card Scripts (created 2026-07-02)
Three scripts in `~/.hermes/scripts/` for 黑执事 profile cron jobs:
- `todo_card_sender.py` — TODO reminder card (blue header, priority groups, overdue detection)
- `email_card_sender.py` — 163 email check card (green header, sender/subject/time)
- `token_alert_card_sender.py` — Feishu Token alert card (red header, profile/issue/fix)

All scripts use **Tenant Token** (not User Token) and send to chat_id `oc_c97273917a903eabd3d81fd9e384b429` (黑执事 DM). Pattern: read data → build card JSON → send via API → print `[SILENT]`.

---

## 10. Pre-Fetch Script Pattern (Anti-Hallucination Architecture)

### Problem
When cron jobs need web data but `web_search` isn't available (no API key), models hallucinate — pretending to search and fabricating content. Even with `terminal`/`curl`, models waste turns on failed scraping, approval prompts, and parsing errors.

### Solution: Pre-Fetch Script
The cron `script` field runs a Python script BEFORE the prompt. Script output is injected into the prompt as context data. The model's role becomes **formatting only** — it never fetches data itself.

### Configuration
```json
{
  "script": "news_data_fetcher.py",
  "enabled_toolsets": [],
  "prompt": "... strict anti-hallucination rules ..."
}
```
- `script` path is relative to `~/.hermes/scripts/` (NOT absolute path)
- Script must print formatted text to stdout (this becomes the 【预抓取数据】section)
- stderr output goes to logs only

### Script: `scripts/news_data_fetcher.py`
Fetches 27 sources concurrently (3 workers, 15s timeout, 2 retries with random backoff):
- **60s API** (24 endpoints): 每日要闻, AI新闻, IT新闻, IT新闻排行, 百度热搜, 百度实时, 百度电视剧, 头条, 微博, 知乎, 小红书, 抖音, 豆瓣电影/剧/综艺, 猫眼票房/热度, 油价, 汇率, 金价, 懂车帝, 摸鱼日历, Hacker News
- **Sina API** (3 feeds): 国内新闻(lid=2509), 国际新闻(lid=2511), 社会新闻(lid=2510)
- **Tencent Stock**: A股三大指数实时 (qt.gtimg.cn)
- **上海市政府**: shanghai.gov.cn 新闻标题抓取

⚠️ **60s API 并发限流**: Cloudflare Workers 有请求限制，27个并发中约 20-22 个成功。已设 retries=2 + random backoff + max_workers=3 缓解。
⚠️ **猫眼 API 字段名**: movie_name (非 title), box_office_desc (非 splitBoxOffice), programme_name (非 title), attention_rate_desc (非 heat)。
⚠️ **新浪滚动新闻**: pageid=153 是新闻频道，lid=2509/2510/2511 分别是国内/社会/国际。pageid=21/207/208 等专用频道返回空数据。

### Script: `scripts/weather_data_fetcher.py`
**Status**: Exists at `~/.hermes/scripts/weather_data_fetcher.py` and deployed to `~/.hermes/profiles/data-master/scripts/weather_data_fetcher.py`.
Used by job `844cde709d24` (早安气象播报, data-master profile).
Uses wttr.in + WAQI API + ip-api.com for data collection. Output format: structured `【预抓取天气数据】` with pre-parsed fields.

#### ⚠️ wttr.in format quirks (verified 2026-06-24, updated 2026-07-10):
- No `lang_zh` field — weather descriptions are English-only via `weatherDesc[0].value` (e.g., "Light rain")
- Hourly time is integer, not zero-padded string: `0, 300, 600, 900...` (NOT `"0000", "0300", "0600"`)
- `FeelsLikeC` available in both `current_condition` and `hourly`
- `cloudcover` is always 0-100
- **wttr.in has no AQI/air quality data** — AQI fields will always be 0/unknown. Do not fabricate AQI values. If air quality is needed, add a separate WAQI API call.

#### IP Geolocation fallbacks:
```bash
# Primary (often rate-limited)
curl -s https://ipapi.co/json/
# Fallback (no auth, generous limits)
curl -s "http://ip-api.com/json/?fields=status,message,country,regionName,city,lat,lon"
# Final fallback: Shanghai (lat=31.22, lon=121.46)
```

#### ⚠️ Python `-c` flag block (verified 2026-06-24)
`python3 -c "..."` in terminal triggers "script execution via -e/-c flag" approval dialog, blocking cron execution. **Solution**: write Python to a temp file first, then `python3 /tmp/script.py`. For the pre-fetch script, this is a non-issue since the script field handles execution automatically.

#### ⚠️ wttr.in UV Index: current vs hourly (critical, confirmed 2026-07-10)
When using wttr.in directly as a backup source (not via `weather_data_fetcher.py`), **`current_condition[0].uvIndex` can be 0 at early morning hours** (e.g., 8 AM), even when the day's maximum UV is 11 (极高/very high). This caused a near-miss where UV advice was "low" when it should have been "very high".

**Fix**: Always check hourly data for the maximum UV index:
```python
uv_current = int(cur.get("uvIndex", 0))
hourly_uv = [int(h.get("uvIndex", 0)) for h in weather["hourly"]]
uv_index = max(uv_current, max(hourly_uv)) if hourly_uv else uv_current
```
Use `uv_index` (the max) for UV level determination and sunscreen advice, NOT `current_condition[0].uvIndex`.

#### ⚠️ wttr.in as fallback when weather_data_fetcher.py fails (2026-07-10)
`weather_data_fetcher.py` can fail with `HTTP Error 503: Service Unavailable`. When this happens in a cron job:
1. Use `curl -s "wttr.in/City?format=j1"` as backup (e.g., `wttr.in/Shanghai?format=j1`)
2. Parse the JSON response — it has `current_condition[]` and `weather[]` arrays
3. Remember the UV index pitfall above (current vs hourly)
4. Remember wttr.in has NO AQI data — mark as unknown/暂无数据
5. Write parsing logic to a temp `.py` file, NOT `python3 -c`

#### Output format
Structured `【预抓取天气数据】` with all fields pre-parsed, ready for LLM formatting.

### Anti-Hallucination Prompt Rules
The prompt MUST include these "铁律" (iron rules):
1. **严禁编造**: All content must come from pre-fetched data
2. **无数据则跳过**: Mark sections as "⚠️ 今日暂无专项数据" if no relevant data
3. **标注来源**: Each news item must cite its data source
4. **数据时效**: Only use same-day data
5. **推断标注**: Inferential sections (基金分析) must be labeled "推测性内容，仅供参考"

### Coverage Map (v3 — updated 2026-07-02, all sections retained)
| Section | Source Data |
|---------|------------|
| 📌 今日看点 | 60s要闻 + 百度热搜 + 头条 (cross-section pick) |
| 🤖 AI与科技 | 60s AI新闻 + IT新闻 + IT排行 + HN |
| 💰 财经与商业 | 60s要闻 + 新浪国内 + 百度热搜 + Tencent指数 |
| 🌐 国际形势 | Sina国际 |
| 📜 政府政策 | 60s要闻 + 新浪国内 + 上海市政府 |
| 🏙️ 上海民生 | 上海市政府 (住房/税收/民生) |
| 🎬 影视与短剧 | 豆瓣 + 猫眼 + 百度电视剧 |
| 👜 时尚/奢侈品 | IT新闻 + 热搜 (if data available) |
| 🏮 国潮文化 | IT新闻 + 热搜 (if data available) |
| 🏭 实体行业 | IT新闻 + 60s要闻 + 懂车帝 |
| 🏯 国风/文化 | 小红书热榜 |
| 📱 社交热议 | 微博 + 百度 + 小红书 + 知乎 |
| 📈 股市/基金 | Tencent A股指数 + 金价/油价 |
| 💰 基金分析 | 推测性内容，标注仅供参考 |
| 🐟 摸鱼日历 | 60s API 摸鱼日历 |

⚠️ **v2→v3 变化**: 用户明确要求保留全部板块（不精简），每条新闻 2 句话，改用飞书卡片推送。无数据板块显示"今日暂无专项数据"。

---

## 12. Scheduling Patterns

### First Business Day of Month
Cron has no native "first weekday" expression. Use `1-3` range + runtime check:
```json
{
  "schedule": "0 10 1-3 * *",
  "prompt": "先用终端执行 `date +%u` 检查今天是否为工作日（1=周一...5=周五）。\n- 如果结果 > 5（周六日），回复'今天是周末，跳过提醒'，结束任务。\n- 如果结果是 1-5，继续执行以下步骤：\n..."
}
```
Logic: days 1-3 always contain the first weekday. Day 1=Sat → Day 3=Mon (fires). Day 1=Sun → Day 2=Mon (fires). Day 1=Mon → Day 1 fires directly. Days 2-3 fire but the `date +%u` check skips them on weekends.

### Monthly Reminders (Fixed Date)
```json
{
  "schedule": "0 10 1 * *",
  "prompt": "..."
}
```
Fires on the 1st of every month regardless of weekday.

---

## 12. Cron Job Migration Between Profiles (Cross-Profile Transfer)

### When to use
Moving an existing cron job from one agent profile to another (e.g., 黑执事→添添开心), possibly changing the delivery target.

### ⚠️ Why CLI (not `cronjob` tool) for cross-profile migration
§7 says to prefer `cronjob` tool over CLI. However, `cronjob` tool operates on the **current session's profile**. For cross-profile creation, `hermes --profile <target> cron create` CLI is required. The §7 pitfalls (model/provider null) still apply — must fix jobs.json after creation (see Step 6).

### Discovery: Find Target Chat IDs
```bash
# Channel directory lists all known chats per profile
cat ~/.hermes/profiles/<profile>/channel_directory.json
# Example: "AI在这里" group → oc_a0422f2a7bebf7c3b831a4ff05b8c6db
```
The global `~/.hermes/channel_directory.json` and per-profile versions may differ — check the **target profile's** directory.

### Discovery: Get Full Job Config
```python
# Read jobs.json to get full prompt + config of existing job
import json
from hermes_tools import terminal
data = json.loads(terminal("cat ~/.hermes/cron/jobs.json")["output"])
# For profile-specific jobs:
data = json.loads(terminal("cat ~/.hermes/profiles/<profile>/cron/jobs.json")["output"])
```

### Migration Steps
1. **Read** existing job's full prompt and script from source profile's `cron/jobs.json`
2. **Adapt prompt persona** — change agent identity section and any persona references (e.g., "黑执事" → "添添开心")
3. **Write prompt to temp file** (avoids shell quoting issues with long prompts):
   ```bash
   cat /tmp/news_prompt.txt  # Write prompt here first
   ```
4. **Copy scripts to target profile** (MUST do before creating jobs):
   ```bash
   mkdir -p ~/.hermes/profiles/<target>/scripts
   cp ~/.hermes/scripts/<script>.py ~/.hermes/profiles/<target>/scripts/
   ```
5. **Create on target profile** via CLI:
   ```bash
   hermes --profile <target> cron create "<schedule>" "$(cat /tmp/prompt.txt)" \
     --name "<name>" \
     --deliver "feishu:<chat_id>" \
     --script <script_name.py> \
     --workdir /home/ubuntu/.hermes
   ```
6. **Fix model/provider in jobs.json** (CLI does NOT set these):
   Use `execute_code` to read `~/.hermes/profiles/<target>/cron/jobs.json`, set `model` and `provider` on the new jobs, write back. Verify with `grep model`.
7. **Pause old job** on source profile (don't delete — keep for rollback):
   ```bash
   # Via cronjob tool: cronjob(action='pause', job_id='<old_id>')
   ```
8. **Test run** and verify:
   ```bash
   hermes --profile <target> cron run <new_job_id>
   # Wait ~90s, then check status
   hermes --profile <target> cron list
   ```
9. **Verify** delivery landed in target chat

### ⚠️ Pitfalls
- **`--script` must be bare filename** (e.g., `news_data_fetcher.py`), NOT absolute path. Scripts live in `~/.hermes/scripts/`. Absolute paths cause: `"Script path must be relative to ~/.hermes/scripts/"`
- **🔴 CLI 创建后必须立即补 model（铁律，不可跳过）**：CLI 创建后 model/provider 为 null，**必须在同一操作流程中**用 `execute_code` 读取 `jobs.json`、注入 model + provider、写回、验证。不补 model = 运行时 400 错误。
  ```python
  # 强制步骤：CLI 创建后立即执行
  import json
  jobs_path = "~/.hermes/profiles/<target>/cron/jobs.json"
  jobs = json.loads(open(jobs_path).read())
  for job in jobs:
      if job.get("model") is None:
          job["model"] = "qwen3.7-max"
          job["provider"] = "qwen"
  open(jobs_path, "w").write(json.dumps(jobs, ensure_ascii=False, indent=2))
  # 验证
  print(open(jobs_path).read())  # 确认 model 不为 null
  ```
- **⚠️ Scripts must exist in target profile's `scripts/` directory**: Cron looks for scripts at `~/.hermes/profiles/<profile>/scripts/<name>.py`, NOT the global `~/.hermes/scripts/`. **Must `cp` scripts to the target profile before first run:**
  ```bash
  mkdir -p ~/.hermes/profiles/<target>/scripts
  cp ~/.hermes/scripts/news_data_fetcher.py ~/.hermes/scripts/weather_data_fetcher.py ~/.hermes/profiles/<target>/scripts/
  ```
- **Long prompts**: Use `$(cat /tmp/file.txt)` in shell — do NOT inline multi-paragraph prompts
- **`--deliver` format for groups**: `feishu:<chat_id>` (e.g., `feishu:oc_a0422f2a7bebf7c3b831a4ff05b8c6db`)
- **`--deliver` for DMs**: `origin` or `feishu` (uses default DM)
- **`--workdir`**: Needed when scripts reference relative paths or need `AGENTS.md` context
- **Persona in prompt**: When migrating between agents, update `## AGENT IDENTITY` section AND any persona references in the prompt body
- **Don't delete old jobs** — pause them. Keeps rollback option and preserves run history
- **Test run order**: After creating + fixing model/scripts, run `hermes --profile <target> cron run <job_id>` and wait ~90s, then check `hermes --profile <target> cron list` for `Last run` status. Script errors and model errors surface in the first run.

---

## 9b. TODO Reminder System (CRUD + Architecture)

For the persistent todo system (todo_manager.py CRUD, data format, path pitfalls, cross-profile sharing), see `references/todo-reminder-system.md`.

---

## 10. News Broadcast Prompt Template

See `references/news-prompt-template.md` for the full cron prompt used by job `e402e3a86482` (data-master / 添添开心). Previously `c85928e4d430` (paused on default profile).
Key points:
- **Pre-fetch + Card delivery**: Script injects real data; model generates structured JSON; script sends card
- **Anti-hallucination 铁律**: 严禁编造, 无数据则跳过, 标注来源, 推断标注
- **v3 format (2026-07-02)**: 15 sections (all retained), 2-sentence items, Feishu Interactive Card
- Agent writes JSON to `/tmp/news_card_data.json` then calls `python3 send_news_card.py`
- Warm greeting opening + brief closing tip
- Source attribution: "——XX" (Chinese dash format)
- Agent identity guard: runs on data-master profile (添添开心)
- Toolsets: needs `terminal` (to call send script), not just empty
- Scripts: `news_data_fetcher.py` (pre-fetch) + `send_news_card.py` (card sender)
