# 飞书互动卡片模板库

## 通用卡片结构

```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "emoji 标题 · 日期（星期）"},
    "template": "blue"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "正文内容"}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "**汇总信息**"}},
    {"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 签名栏 · 时间"}]}
  ]
}
```

## Header 颜色对照

| 场景 | 颜色 | 值 |
|------|------|-----|
| TODO/信息 | 🔵 蓝 | `blue` |
| 邮件/正常 | 🟢 绿 | `green` |
| 预警/错误 | 🔴 红 | `red` |
| 晴天/温暖 | 🟠 橙 | `orange` |
| 阴天/多云 | 🟢 绿 | `green` |
| 雨雪/冷色 | 🟣 靛蓝 | `indigo` |
| 天气默认 | 🩵 青 | `turquoise` |
| 其他可选 | — | `purple`, `grey`, `wathet`, `yellow`, `violet`, `carmine` |

## TODO 播报卡片（🔵 blue）

```python
def build_todo_card(todos, today):
    date_str = today.strftime("%Y-%m-%d")
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[today.weekday()]
    today_date = today.strftime("%Y-%m-%d")

    # Group by priority
    high, medium, low = [], [], []
    for t in todos:
        priority = t.get("priority", "medium")
        overdue = t.get("due") and t["due"] < today_date
        item = t.get("content", "")
        if t.get("due"): item += f"  📅 {t['due']}"
        if overdue: item = f"⚠️ {item}"
        {"high": high, "medium": medium, "low": low}[priority].append(item)

    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": "早安，小艾主人！☀️\n管家已为您整理好今日待办～"}}
    ]
    if high:
        items = "\n".join(f"• {h}" for h in high)
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**🔴 紧急任务**\n{items}"}})
    if medium:
        items = "\n".join(f"• {m}" for m in medium)
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**🟡 普通任务**\n{items}"}})
    if low:
        items = "\n".join(f"• {l}" for l in low)
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**🟢 低优先级**\n{items}"}})

    total = len(todos)
    overdue_count = sum(1 for t in todos if t.get("due") and t["due"] < today_date)
    summary = f"💡 今天共 **{total}** 项待办"
    if overdue_count: summary += f"，**{overdue_count}** 项已过期，建议优先处理！"
    else: summary += "，加油！"

    elements.append({"tag": "hr"})
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": summary}})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 黑执事 · 10:30 播报"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"📋 每日待办播报 · {date_str}（{weekday}）"}, "template": "blue"},
        "elements": elements
    }
```

## 邮件巡检卡片（🟢 green）

```python
def build_email_card(emails, now_str):
    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": f"📨 发现 **{len(emails)}** 封新邮件"}}
    ]
    for i, email in enumerate(emails[:5], 1):
        content = f"**{i}️⃣ {email.get('from', '未知发件人')}**\n"
        content += f"📌 {email.get('subject', '无主题')}\n"
        content += f"🕐 {email.get('time', '')}"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})
    if len(emails) > 5:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"...还有 {len(emails)-5} 封邮件"}})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 邮件管家 · 自动巡检"}]})
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"📬 邮件巡检报告 · {now_str}"}, "template": "green"},
        "elements": elements
    }
```

## Token 预警卡片（🔴 red）

```python
def build_alert_card(alerts, today_str):
    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": "⚠️ 发现 Token 异常"}}
    ]
    for alert in alerts:
        content = f"🔸 **{alert.get('profile', '未知')}**\n"
        content += f"问题：{alert.get('issue', '未知')}\n"
        content += f"修复：{alert.get('fix', 'lark auth login')}"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 系统管家 · 自动监控"}]})
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"🚨 系统预警 · {today_str}"}, "template": "red"},
        "elements": elements
    }
```

## 发送函数（通用）

```python
def get_tenant_token():
    APP_ID = "cli_aa9970856879dcd8"  # 黑执事 app
    APP_SECRET = ""
    with open(os.path.expanduser("~/.bashrc")) as f:
        for line in f:
            if "LARK_APP_SECRET" in line:
                APP_SECRET = line.split("=")[1].strip().strip('"').strip("'")
                break
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
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"
    }, method="POST")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())
```

## ⚠️ 注意事项

- **必须用 Tenant Token** 发卡片（User Token 缺 `im:message.send_as_user` scope）
- **Bot 必须在目标 chat 中** — 否则报 `230002: Bot/User can NOT be out of the chat`
- **`ensure_ascii=False` + `.encode('utf-8')`** — 中文内容必须这样编码
- **DM chat_id** — 黑执事当前 DM: `oc_c97273917a903eabd3d81fd9e384b429`
- **脚本路径** — `~/.hermes/scripts/` 下，cron job 配置用 bare filename
