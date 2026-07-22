#!/usr/bin/env python3
"""Elasticity Report Card Sender for Feishu.

Reads JSON report data from /tmp/elasticity_report_data.json,
builds a Feishu interactive card, and sends it via tenant token.

Architecture:
  monthly_elasticity_report.py (pre-fetch) → stdout JSON → agent writes to file
  → this script reads file → builds card → sends via API

App: hr-assistant profile (cli_aa9ebcbfc6e35cba)
Target: oc_d811c650f76f16e98ac7a65517e0128f
"""

import json, sys, os, urllib.request

# ── Feishu App Credentials (hr-assistant profile) ──
APP_ID = "cli_aa9ebcbfc6e35cba"
APP_SECRET = "gGLTewRMXcyS1dRU3PO4DfqRMMTDkIQa"
CHAT_ID = "oc_d811c650f76f16e98ac7a65517e0128f"

def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=10)
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
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def make_bar(value, max_val, width=20):
    if max_val <= 0:
        return "░" * width
    filled = int(value / max_val * width)
    return "█" * filled + "░" * (width - filled)

def build_card(data):
    """Build Feishu interactive card from elasticity report data."""
    last_3 = data.get("last_3_months", [])
    report_month = last_3[-1] if last_3 else "N/A"
    gen_time = data.get("generated_at", "")

    grand_total = data.get("grand_total", 0)
    grand_baseline = data.get("grand_baseline", 0)
    grand_recent_avg = data.get("grand_recent_avg", 0)
    grand_excess = data.get("grand_excess", 0)

    tier_data = data.get("tier_summary", {})
    flex_total = tier_data.get("高弹性", {}).get("total", 0)
    e_ratio = f"{flex_total / grand_total * 100:.1f}%" if grand_total > 0 else "N/A"

    elements = []

    # ── KPI Overview ──
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "## 📋 总览"}})
    elements.append({
        "tag": "column_set", "flex_mode": "none", "background_style": "default",
        "columns": [
            {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**总支出**\n¥{grand_total:,.0f}"}}]},
            {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**基准线**\n¥{grand_baseline:,.0f}/月"}}]},
            {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**近期月均**\n¥{grand_recent_avg:,.0f}/月"}}]},
            {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**弹性系数**\n{e_ratio}"}}]},
        ]
    })
    elements.append({"tag": "hr"})

    # ── Tier Breakdown ──
    tier_labels = {"刚性": "🟢 刚性", "半弹性": "🟡 半弹性", "高弹性": "🔴 高弹性"}

    for tier_name in ["刚性", "半弹性", "高弹性"]:
        t = tier_data.get(tier_name, {})
        t_total = t.get("total", 0)
        t_pct = f"{t_total / grand_total * 100:.1f}%" if grand_total > 0 else "0%"
        t_baseline = t.get("baseline", 0)
        t_recent_avg = t.get("recent_avg", 0)
        t_excess = t.get("excess", 0)
        cats = t.get("categories", [])

        diff = t_recent_avg - t_baseline
        status = f"⚠️ +¥{diff:,.0f}/月" if diff > 0 else "✅"

        header = f"## {tier_labels[tier_name]} — ¥{t_total:,.0f} ({t_pct})"
        summary = f"基准线 ¥{t_baseline:,.0f}/月 | 近期 ¥{t_recent_avg:,.0f}/月 | {status}"
        if t_excess > 0:
            summary += f" | 近3月超额 ¥{t_excess:,.0f}"

        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"{header}\n{summary}"}})

        if cats:
            cat_stats = data.get("cat_stats", {})
            rows_md = "| 分类 | 合计 | 近3月 | 超额 |\n|------|------|-------|------|\n"
            for cat_name in cats:
                cs = cat_stats.get(cat_name, {})
                c_total = cs.get("total", 0)
                c_recent = cs.get("recent", [0, 0, 0])
                c_excess = cs.get("excess", 0)
                recent_str = f"{c_recent[0]:,.0f}/{c_recent[1]:,.0f}/{c_recent[2]:,.0f}"
                excess_str = f"¥{c_excess:,.0f}" if c_excess > 0 else "—"
                rows_md += f"| {cat_name} | ¥{c_total:,.0f} | {recent_str} | {excess_str} |\n"
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": rows_md}})

        elements.append({"tag": "hr"})

    # ── Cost-Saving Suggestions ──
    cat_stats = data.get("cat_stats", {})
    excess_cats = [(name, cs) for name, cs in cat_stats.items() if cs.get("excess", 0) > 500]
    excess_cats.sort(key=lambda x: -x[1]["excess"])

    if excess_cats:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "## 🎯 节流建议"}})

        for priority, (cat_name, cs) in enumerate(excess_cats, 1):
            c_excess = cs.get("excess", 0)
            c_median = cs.get("median", 0)
            c_top5 = cs.get("top5", [])
            c_monthly = cs.get("monthly", {})
            tier = cs.get("tier", "")

            max_month_val = max(c_monthly.values()) if c_monthly else 0
            months_above = sum(1 for v in c_monthly.values() if v > c_median * 1.2)
            total_months = len(c_monthly)

            if max_month_val > c_median * 3 and months_above <= total_months * 0.3:
                pattern = "季节性飙升"
                suggestion = f"大促前制定购物清单，设置月度提醒上限 ¥{c_median * 1.5:,.0f}"
            elif months_above > total_months * 0.5:
                pattern = "持续超支"
                suggestion = f"设定月度硬性上限 ¥{c_median:,.0f}，超支时暂停该类消费"
            elif c_top5 and c_top5[0]["amt"] > c_median * 2:
                pattern = "单次大额"
                suggestion = "标记为一次性支出，后续排除基准线计算"
            else:
                pattern = "频率增加"
                suggestion = f"控制消费频率，目标每月不超过 ¥{c_median:,.0f}"

            top3_md = ""
            for t in c_top5[:3]:
                top3_md += f"  - {t['month']} ¥{t['amt']:,.0f} {t['note'][:30]}\n"

            monthly_sorted = sorted(c_monthly.items())
            trend_md = "  "
            if monthly_sorted:
                max_v = max(v for _, v in monthly_sorted)
                for m, v in monthly_sorted[-6:]:
                    bar = make_bar(v, max_v, 10)
                    trend_md += f"{m[-5:]} ¥{v:>6,.0f} {bar}\n  "

            tier_emoji = {"刚性": "🟢", "半弹性": "🟡", "高弹性": "🔴"}.get(tier, "")
            block = f"**P{priority} {tier_emoji} {cat_name}** — 近3月超额 ¥{c_excess:,.0f}\n"
            block += f"模式: {pattern}\n"
            block += f"Top 3 交易:\n{top3_md}"
            block += f"近6月趋势:\n{trend_md}\n"
            block += f"💡 {suggestion}\n"
            block += f"预估月度节省: ~¥{c_excess / 3:,.0f}/月"
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": block}})

        total_potential = sum(cs["excess"] / 3 for _, cs in excess_cats)
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": f"### 💰 潜在月度节省: ~¥{total_potential:,.0f}/月 ≈ ¥{total_potential * 12:,.0f}/年"}})
    else:
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": "## 🎯 节流建议\n✅ 近3月各分类均在基准线内，无需特别节流。"}})

    elements.append({"tag": "hr"})

    # ── Monthly Trend ──
    monthly_trend = data.get("monthly_trend", [])
    if monthly_trend:
        trend_content = "## 📈 弹性系数月度趋势\n"
        max_expense = max(m["expense"] for m in monthly_trend) if monthly_trend else 1
        for m in monthly_trend:
            ratio_str = m.get("ratio", "N/A")
            try:
                ratio_val = float(ratio_str.replace("%", ""))
                flag = "🔴" if ratio_val > 30 else ("⚠️" if ratio_val > 10 else "✅")
            except:
                flag = "❓"
            bar = make_bar(m["expense"], max_expense, 15)
            trend_content += f"{m['month']} {ratio_str:>6} {bar} {flag}\n"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": trend_content}})

    # ── Footer ──
    elements.append({"tag": "note", "elements": [
        {"tag": "plain_text", "content": f"📊 数据来源: 飞书多维表格 | 生成时间: {gen_time}"}]})
    elements.append({"tag": "action", "actions": [{
        "tag": "button", "text": {"tag": "plain_text", "content": "📋 查看多维表格"},
        "url": "https://e1kg6bc4dl9.feishu.cn/base/TcxxbfP05adgltsZpJEcGKi9nme",
        "type": "primary"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 家庭弹性支出分析报告 | {report_month}"},
            "template": "blue"
        },
        "elements": elements
    }

def main():
    data_path = "/tmp/elasticity_report_data.json"
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    card = build_card(data)

    try:
        result = send_card(CHAT_ID, card)
        if result.get("code") == 0:
            msg_id = result.get("data", {}).get("message_id", "unknown")
            print(f"✅ Card sent successfully. message_id: {msg_id}")
        else:
            print(f"❌ Send failed: code={result.get('code')} msg={result.get('msg')}")
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
