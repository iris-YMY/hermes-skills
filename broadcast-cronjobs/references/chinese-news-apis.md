# Chinese News APIs (No Auth Required)

Verified working from the cron server (updated 2026-06-18). Use via `execute_code` → `terminal("curl ...")`.

## ⭐ Primary Data Source: 60s API

**See `references/60s-api-endpoints.md` for full details.** The 60s API (`https://60s.viki.moe`) provides 19 free endpoints covering ~70% of news broadcast sections. No API key required.

Key endpoints:
- `/v2/60s` — Daily 15-item news digest (perfect for 今日看点)
- `/v2/ai-news` — AI news with title+detail+source
- `/v2/it-news` — IT/tech news 20 items
- `/v2/weibo` — Weibo hot search 50 items
- `/v2/toutiao` — Toutiao hot 50 items
- `/v2/baidu/hot` — Baidu hot search 50 items with descriptions
- `/v2/rednote` — Xiaohongshu trending 20 items
- `/v2/douban/weekly/movie` — Douban movies
- `/v2/maoyan/realtime/movie` — Maoyan real-time box office
- `/v2/exchange-rate` — Exchange rates (base CNY)

---

## Supplementary Direct APIs

### 1. Sina Rolling News Feed (国内/国际/社会)

**Requires proper User-Agent and Referer headers.**

| Channel | lid | Example Content |
|---------|-----|----------------|
| 国内新闻 | 2509 | 政策解读、社会事件 |
| 国际新闻 | 2511 | 地缘政治、外交 |
| 社会新闻 | 2510 | 民生、地方动态 |
| 体育/军事 | 2512 | 体育赛事、军事 |

```python
from hermes_tools import terminal
import json

def fetch_sina_news(lid=2509, num=10):
    cmd = (
        f"curl -sL --max-time 10 "
        f"'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&num={num}' "
        f"-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' "
        f"-H 'Referer: https://news.sina.com.cn/' 2>/dev/null"
    )
    r = terminal(cmd, timeout=15)
    data = json.loads(r['output'])
    items = data.get('result', {}).get('data', [])
    return [(i['title'], i.get('intro', '')) for i in items]
```

⚠️ **科技频道 (pageid=207) returns 0 items** — use 60s API `/v2/ai-news` and `/v2/it-news` instead.
⚠️ **财经频道 (pageid=21, lid=1199) returns 0 items** — use Sina 7×24 and stock APIs instead.

### 2. Sina 7×24 Live Financial Feed

**Endpoint**: `https://zhibo.sina.com.cn/api/zhibo/feed?page={N}&page_size=20&zhibo_id=152&tag_id=0&type=0`

- Pages 1-10 cover ~08:00-10:30 morning session
- Returns 20 items per page with: `rich_text` (HTML), `create_time`, `tag[]` (分类标签)
- Tags include: 宏观, 市场, 公司, 国际, 央行, 焦点
- Strip HTML: `re.sub(r'<[^>]+>', '', text)`
- **No User-Agent header required**

```python
import json, re
from hermes_tools import terminal
r = terminal("curl -sL --max-time 10 'https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=20&zhibo_id=152&tag_id=0&type=0' 2>/dev/null", timeout=15)
data = json.loads(r['output'])
feeds = data['result']['data']['feed']['list']
for f in feeds:
    text = re.sub(r'<[^>]+>', '', f.get('rich_text', ''))
    time = f.get('create_time', '')
    tags = [t.get('name','') for t in (f.get('tag') or [])]
    print(f"[{time}] {''.join(tags)} {text[:200]}")
```

### 3. Tencent Stock Index Data

**Endpoint**: `https://qt.gtimg.cn/q=sh000001,sz399001,sz399006`

- Returns GBK-encoded data; needs `iconv -f GBK -t UTF-8`
- Format: `~name~code~price~prev_close~open~...~change~change_pct~...`
- secids: sh000001=上证指数, sz399001=深证成指, sz399006=创业板指

```bash
curl -sL --max-time 10 'https://qt.gtimg.cn/q=sh000001,sz399001,sz399006' 2>/dev/null | iconv -f GBK -t UTF-8 2>/dev/null | tr ';' '\n'
```

Key field positions (0-indexed, `~`-delimited):
- [1]: name, [2]: code, [3]: current price, [4]: prev close
- [31]: change amount, [32]: change percent, [33]: high, [34]: low

### 4. EastMoney Stock Index (via 60s API preferred)

**Note**: EastMoney direct APIs (`push2.eastmoney.com`) returned **empty** in 2026-06-18 tests. Use `/v2/exchange-rate` from 60s API or Tencent `qt.gtimg.cn` for market data.

---

## APIs That DON'T Work (from cron server, 2026-06-18)

| API | Issue |
|-----|-------|
| `hermes tools web_search` | Requires interactive terminal, fails in cron |
| Google News RSS | Connection timeout |
| BBC Chinese RSS | Connection timeout |
| Weibo direct (`weibo.com/ajax/side/hotSearch`) | Returns Forbidden — use 60s API `/v2/weibo` |
| Baidu direct (`top.baidu.com/api/board`) | Works but 60s API `/v2/baidu/hot` is cleaner |
| CLS.cn (财联社) direct API | Returns empty data |
| EastMoney push2 APIs | Returns empty from cron server |
| Sina tech feed (`pageid=207`) | Returns 0 items — use 60s `/v2/it-news` |
| Sina finance (`pageid=21`) | Returns 0 items — use Sina 7×24 |
| 36Kr API | Returns 404 |
| Huxiu API | Returns error (wrong platform param) |
| RSSHub public instance | All endpoints timeout |
| 今日头条 direct | Works but 60s API `/v2/toutiao` is cleaner |
| 60s `/v2/bili` | Returns 500 error |
| 60s `/v2/gold-price` | Returns empty |

## Recommended Data Gathering Strategy (Updated)

1. **Primary**: 60s API — fetch all relevant endpoints via `execute_code`
   - `/v2/60s` for daily digest (今日看点)
   - `/v2/ai-news` + `/v2/it-news` for tech
   - `/v2/weibo` + `/v2/rednote` for social media
   - `/v2/baidu/hot` + `/v2/toutiao` for comprehensive news
   - `/v2/douban/weekly/*` + `/v2/maoyan/*` for entertainment
2. **Stock data**: Tencent `qt.gtimg.cn` for index data + 60s `/v2/exchange-rate`
3. **Supplement**: Sina rolling news (lid=2509/2511) for detailed domestic/international news
4. **Supplement**: Sina 7×24 feed for financial macro news
5. **AI inference**: For sections without direct APIs (电商, 国潮, 实体行业, 时尚, 上海本地, 基金分析) — model analyzes collected data to produce informed commentary

## Toolset Configuration

The cron job needs `terminal` and `execute_code` tools (both are in default toolset).
- `enabled_toolsets: []` (empty = all defaults) works ✅
- `enabled_toolsets: ["web", "search"]` does NOT work without API keys ❌
- **Do NOT include `browser`** — causes hangs on Chinese sites
