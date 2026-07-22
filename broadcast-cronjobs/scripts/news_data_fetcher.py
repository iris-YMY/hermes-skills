#!/usr/bin/env python3
"""
新闻播报数据预抓取脚本
在 cron job 执行前运行，将真实数据注入到 prompt 中。
所有数据来自免费公开 API，无需 API Key。

Usage: Configured via cron job `script` field (relative to ~/.hermes/scripts/)
Data sources: 60s API (19 endpoints), Sina (3 feeds), Tencent stock index
Architecture: Pre-fetch → inject into prompt → model formats only (no tools needed)
"""

import json
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

TIMEOUT = 10  # seconds per request
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


def fetch_json(url, headers=None, method="GET", data=None):
    """Generic JSON request with timeout"""
    try:
        hdrs = {"User-Agent": UA}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, headers=hdrs, method=method)
        if data:
            req.data = json.dumps(data).encode("utf-8")
            hdrs["Content-Type"] = "application/json"
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}


def fetch_raw(url, headers=None):
    """Fetch raw text (for GBK-encoded APIs like Tencent stock)"""
    try:
        hdrs = {"User-Agent": UA}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            for enc in ["utf-8", "gbk", "gb2312"]:
                try:
                    return raw.decode(enc)
                except:
                    continue
            return raw.decode("utf-8", errors="replace")
    except Exception as e:
        return f"ERROR: {e}"


# ========== 60s API Endpoints (https://60s.viki.moe) ==========
# Free, no auth, Cloudflare Workers. See references/60s-api-endpoints.md

def get_60s(endpoint):
    """Fetch from 60s API, return data or None"""
    d = fetch_json(f"https://60s.viki.moe{endpoint}")
    if d.get("code") == 200:
        return d["data"]
    return None


# ========== Sina News Feeds ==========
# pageid=153 (news channel), lid varies by section
# Requires User-Agent + Referer headers

def get_sina_feed(lid, num=10, referer="https://news.sina.com.cn/"):
    d = fetch_json(
        f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&num={num}",
        headers={"Referer": referer}
    )
    items = d.get("result", {}).get("data", [])
    return [{"title": i.get("title", ""), "summary": i.get("summary", ""),
             "url": i.get("url", "")} for i in items]


# ========== Tencent Stock Index ==========
# Returns GBK-encoded real-time stock data

def get_tencent_index():
    raw = fetch_raw("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006")
    if "ERROR" in raw:
        return None
    indices = {}
    for line in raw.strip().split("\n"):
        line = line.strip().rstrip(";")
        if not line or "=" not in line:
            continue
        key_part, val_part = line.split("=", 1)
        val = val_part.strip('"')
        fields = val.split("~")
        if len(fields) > 10:
            name = fields[1]
            price = fields[3]
            change_pct = fields[32] if len(fields) > 32 else fields[4]
            change_amt = fields[31] if len(fields) > 31 else fields[5]
            indices[name] = {"price": price, "change_pct": change_pct, "change_amt": change_amt}
    return indices


# ========== Source Registry ==========

SOURCES = {
    # 60s API (19 endpoints)
    "daily_60s": lambda: get_60s("/v2/60s"),
    "ai_news": lambda: get_60s("/v2/ai-news"),
    "it_news": lambda: get_60s("/v2/it-news"),
    "it_rank": lambda: get_60s("/v2/it-news/rank"),
    "baidu_hot": lambda: get_60s("/v2/baidu/hot"),
    "toutiao": lambda: get_60s("/v2/toutiao"),
    "weibo": lambda: get_60s("/v2/weibo"),
    "zhihu": lambda: get_60s("/v2/zhihu"),
    "rednote": lambda: get_60s("/v2/rednote"),
    "douyin": lambda: get_60s("/v2/douyin"),
    "douban_movie": lambda: get_60s("/v2/douban/weekly/movie"),
    "douban_tv_cn": lambda: get_60s("/v2/douban/weekly/tv_chinese"),
    "douban_tv_global": lambda: get_60s("/v2/douban/weekly/tv_global"),
    "maoyan_movie": lambda: get_60s("/v2/maoyan/realtime/movie"),
    "maoyan_tv": lambda: get_60s("/v2/maoyan/realtime/tv"),
    "fuel_price": lambda: get_60s("/v2/fuel-price"),
    "exchange_rate": lambda: get_60s("/v2/exchange-rate"),
    "hacker_news": lambda: get_60s("/v2/hacker-news/top"),
    # Sina feeds
    "sina_domestic": lambda: get_sina_feed(2509),
    "sina_international": lambda: get_sina_feed(2511),
    "sina_society": lambda: get_sina_feed(2510),
    # Tencent stock
    "tencent_index": get_tencent_index,
}


def fetch_all():
    """Fetch all sources concurrently (8 workers)"""
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fn): name for name, fn in SOURCES.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = {"_error": str(e)}
    return results


# ========== Output Formatting ==========

def fmt_list(data, max_items=10, title_key="title", extra_keys=None):
    if not data or isinstance(data, dict) and "_error" in data:
        return "  (数据获取失败)"
    if not isinstance(data, list):
        return "  (数据格式异常)"
    lines = []
    for i, item in enumerate(data[:max_items]):
        if isinstance(item, dict):
            t = item.get(title_key, item.get("word", str(item)))
            extras = ""
            if extra_keys:
                parts = []
                for k in extra_keys:
                    v = item.get(k, "")
                    if v:
                        parts.append(f"{k}={v}")
                if parts:
                    extras = f" [{', '.join(parts)}]"
            lines.append(f"  {i+1}. {t}{extras}")
        else:
            lines.append(f"  {i+1}. {item}")
    return "\n".join(lines) if lines else "  (无数据)"


def format_report(data):
    today = datetime.now().strftime("%Y年%m月%d日 %A")
    cn_weekday = {"Monday": "星期一", "Tuesday": "星期二", "Wednesday": "星期三",
                  "Thursday": "星期四", "Friday": "星期五", "Saturday": "星期六", "Sunday": "星期日"}
    for en, cn in cn_weekday.items():
        today = today.replace(en, cn)

    lines = [f"# 📊 新闻播报数据源（真实抓取时间: {datetime.now().strftime('%H:%M:%S')}）"]
    lines.append(f"# 日期: {today}")
    lines.append("")
    lines.append("⚠️ **重要提醒: 以下内容全部来自真实 API 数据，严禁编造任何信息。**")
    lines.append("⚠️ **如果某个板块没有数据，必须明确标注「今日暂无专项数据」，不可捏造。**")

    # Daily 60s
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 📌 每日60秒看世界（综合要闻）")
    d = data.get("daily_60s")
    if d:
        lines.append(f"日期: {d.get('date', '')}")
        if d.get("tip"):
            lines.append(f"微语: {d['tip']}")
        for n in d.get("news", []):
            lines.append(f"  • {n}")
    else:
        lines.append("  (获取失败)")

    # AI News
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🤖 AI 新闻")
    d = data.get("ai_news")
    if d and isinstance(d, dict):
        lines.append(f"日期: {d.get('date', '')}")
        for n in d.get("news", []):
            if isinstance(n, dict):
                lines.append(f"  • {n.get('title', '')}")
                if n.get("detail"):
                    lines.append(f"    详情: {n['detail'][:200]}")
                if n.get("source"):
                    lines.append(f"    来源: {n['source']}")
            else:
                lines.append(f"  • {n}")
    else:
        lines.append("  (获取失败)")

    # IT News
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 💻 IT/科技新闻")
    lines.append(fmt_list(data.get("it_news"), max_items=15, extra_keys=["description"]))

    # IT Rank
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🔥 IT 新闻排行")
    lines.append(fmt_list(data.get("it_rank"), max_items=10))

    # Hacker News
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🌐 Hacker News Top（国际科技）")
    lines.append(fmt_list(data.get("hacker_news"), max_items=10))

    # Sina feeds
    for key, title in [("sina_domestic", "🏛️ 新浪-国内新闻"),
                       ("sina_international", "🌍 新浪-国际新闻"),
                       ("sina_society", "🏘️ 新浪-社会新闻")]:
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"## {title}")
        d = data.get(key)
        if d and isinstance(d, list) and len(d) > 0:
            for i, item in enumerate(d[:8]):
                lines.append(f"  {i+1}. {item['title']}")
                if item.get("summary"):
                    lines.append(f"     摘要: {item['summary'][:150]}")
        else:
            lines.append("  (获取失败或无数据)")

    # Hot searches
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🔍 百度热搜 TOP20")
    lines.append(fmt_list(data.get("baidu_hot"), max_items=20, extra_keys=["desc"]))

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 📰 头条热榜 TOP20")
    lines.append(fmt_list(data.get("toutiao"), max_items=20, extra_keys=["hot_value"]))

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🔥 微博热搜 TOP15")
    lines.append(fmt_list(data.get("weibo"), max_items=15, extra_keys=["hot_value"]))

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 💡 知乎热榜 TOP10")
    lines.append(fmt_list(data.get("zhihu"), max_items=10, extra_keys=["detail"]))

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 📕 小红书热榜 TOP10")
    lines.append(fmt_list(data.get("rednote"), max_items=10, extra_keys=["score"]))

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🎵 抖音热榜 TOP10")
    lines.append(fmt_list(data.get("douyin"), max_items=10, extra_keys=["hot_value"]))

    # Stock index
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 📈 A股三大指数（实时）")
    d = data.get("tencent_index")
    if d and isinstance(d, dict):
        for name, info in d.items():
            pct = info.get("change_pct", "?")
            try:
                pct_f = float(pct)
                arrow = "📈" if pct_f > 0 else ("📉" if pct_f < 0 else "➡️")
            except:
                arrow = "➡️"
            lines.append(f"  {arrow} {name}: {info.get('price', '')} ({pct}%, {info.get('change_amt', '')})")
    else:
        lines.append("  (获取失败)")

    # Fuel & exchange
    lines.append("")
    lines.append("=" * 60)
    lines.append("## ⛽ 油价")
    d = data.get("fuel_price")
    if d and isinstance(d, dict) and "_error" not in d:
        lines.append(f"  地区: {d.get('region', '')}")
        if d.get("trend"):
            lines.append(f"  趋势: {d['trend']}")
        for item in d.get("items", [])[:5]:
            lines.append(f"  • {item}")
    else:
        lines.append("  (获取失败)")

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 💱 汇率")
    d = data.get("exchange_rate")
    if d and isinstance(d, dict) and "_error" not in d:
        base = d.get("base_code", "?")
        lines.append(f"  基准: {base}")
        rates = d.get("rates", d.get("data", {}))
        if isinstance(rates, dict):
            for currency in ["USD", "EUR", "JPY", "GBP", "HKD"]:
                if currency in rates:
                    lines.append(f"  • {base}/{currency}: {rates[currency]}")
    else:
        lines.append("  (获取失败)")

    # Entertainment
    for key, title in [("douban_movie", "🎬 豆瓣一周口碑电影 TOP5"),
                       ("douban_tv_cn", "📺 豆瓣一周国产剧 TOP5"),
                       ("douban_tv_global", "📺 豆瓣一周全球剧 TOP5")]:
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"## {title}")
        d = data.get(key)
        if d and isinstance(d, list):
            for item in d[:5]:
                if isinstance(item, dict):
                    lines.append(f"  {item.get('rank', '?')}. {item.get('title', '')} (评分:{item.get('rating', '?')})")
        else:
            lines.append("  (获取失败)")

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 🎥 猫眼实时票房 TOP5")
    d = data.get("maoyan_movie")
    if d and isinstance(d, dict):
        box = d.get("list", d.get("data", []))
        if isinstance(box, list):
            for item in box[:5]:
                if isinstance(item, dict):
                    lines.append(f"  • {item.get('title', item.get('movieName', ''))}: {item.get('splitBoxOffice', item.get('boxOffice', ''))}")
        else:
            lines.append(f"  {json.dumps(d, ensure_ascii=False)[:300]}")
    else:
        lines.append("  (获取失败)")

    lines.append("")
    lines.append("=" * 60)
    lines.append("## 📺 猫眼全网热度 TOP5")
    d = data.get("maoyan_tv")
    if d and isinstance(d, dict):
        tv_list = d.get("list", [])
        if isinstance(tv_list, list):
            for item in tv_list[:5]:
                if isinstance(item, dict):
                    lines.append(f"  • {item.get('title', item.get('name', ''))}: 热度{item.get('heat', item.get('hotValue', ''))}")
        else:
            lines.append(f"  {json.dumps(d, ensure_ascii=False)[:300]}")
    else:
        lines.append("  (获取失败)")

    # Coverage summary
    lines.append("")
    lines.append("=" * 60)
    lines.append("## 📋 数据覆盖情况")
    lines.append("以下板块有真实数据，请据此撰写:")
    lines.append("  ✅ 今日看点（从60秒要闻+热搜综合提取）")
    lines.append("  ✅ 政治与综合（新浪国内+百度热搜+头条热榜）")
    lines.append("  ✅ AI与科技（AI新闻+IT新闻+HackerNews）")
    lines.append("  ✅ 国际形势（新浪国际）")
    lines.append("  ✅ 影视与短剧（豆瓣+猫眼）")
    lines.append("  ✅ 社交媒体（微博+小红书+知乎）")
    lines.append("  ✅ 股市/基金/财经（A股指数+油价+汇率）")
    lines.append("")
    lines.append("以下板块**没有专项数据**，只能从已有数据中关联提取，无关联则标注「今日暂无专项数据」:")
    lines.append("  ⚠️ 电商与商业")
    lines.append("  ⚠️ 国潮文化与国货品牌")
    lines.append("  ⚠️ 实体行业发展")
    lines.append("  ⚠️ 政府政策动态")
    lines.append("  ⚠️ 上海本地民生（住房/税收/民生）")
    lines.append("  ⚠️ 时尚/奢侈品/服饰")
    lines.append("  ⚠️ 国风/文化/艺术")
    lines.append("  ⚠️ 基金板块影响分析（可基于指数+热点推断，但须标明为推测）")

    return "\n".join(lines)


if __name__ == "__main__":
    print("正在抓取新闻数据...", file=sys.stderr)
    data = fetch_all()
    report = format_report(data)
    print(report)
    print("数据抓取完成。", file=sys.stderr)
