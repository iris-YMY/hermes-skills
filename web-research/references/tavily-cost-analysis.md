# Tavily API Pricing & Cost Analysis (July 2026)

## Tavily Pricing Tiers

| Plan | Price | Credits | Notes |
|------|-------|---------|-------|
| Free (Researcher) | $0/mo | 1,000/mo | No CC required |
| Pay As You Go | $0.008/credit | - | Cancel anytime |
| Project | $30/mo | 4,000/mo | Slider to adjust |
| Enterprise | Custom | Custom | Contact sales |

- 1 credit = 1 search or 1 extract call
- Student plan: free

## DashScope/Qwen Model Pricing (per million tokens, ¥)

| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| qwen3.7-max | ¥12 | ¥36 | Primary model |
| qwen3.6-plus | ¥2 | ¥12 | Fallback model |
| qwen3.7-plus | ¥2 | ¥8 | Compression candidate |
| qwen-max | ¥2.4 | ¥9.6 | Batch 50% off |

## Cost Per Web Research Task (Estimated)

| Approach | Input Tokens | Output Tokens | Cost |
|----------|-------------|---------------|------|
| Browser-based (current) | ~50K | ~2K | ~¥0.67 |
| Tavily API | ~8K | ~1K | ~¥0.30 (incl. $0.024 API fee) |
| Savings | - | - | ~55% per task |

## Monthly Cost Projection

| Frequency | Browser/mo | Tavily/mo | Monthly Savings |
|-----------|-----------|-----------|-----------------|
| 10 tasks | ¥6.7 | ¥3.0 | ¥3.7 |
| 30 tasks | ¥20 | ¥9 | ¥11 |
| 50 tasks | ¥33.5 | ¥15 | ¥18.5 |

## Registration Status (2026-07-13)
- **Registered**: Free tier (1,000 searches/mo)
- **Account**: ymy_iris@163.com
- **API Key**: saved to `~/.env` as `TAVILY_API_KEY`
- **Verified**: working — tested with search API

## Registration Pitfalls
- **Cloudflare Turnstile blocks headless browsers**: Cannot register via Hermes browser automation. The security challenge fails to load. Must register manually via user's own browser.
- Workaround: Guide user to register at tavily.com manually, then provide API key for agent to save.

## Usage Pattern
```bash
source ~/.env
curl -s -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$TAVILY_API_KEY\", \"query\": \"...\", \"max_results\": 5}"
```

## Recommendation (updated 2026-07-13)
- Free tier active — monitor usage via Tavily dashboard
- Defer paid upgrade until usage pattern established
- Existing cron jobs use dedicated free APIs — no Tavily needed for those

## ⚠️ XHS Limitation (tested 2026-07-13)
- **Tavily extract on XHS URLs returns only nav/footer** — XHS is a JS SPA, Tavily cannot render dynamic content
- **Tavily search with `site:xiaohongshu.com`** also returns no substantive note content
- For XHS content extraction, use TikHub API instead (see `references/chinese-platform-extraction.md`)
- Tavily remains useful for general web search and non-SPA site extraction
