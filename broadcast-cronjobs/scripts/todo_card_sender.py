#!/usr/bin/env python3
"""Send TODO reminder as Feishu Interactive Card via REST API."""
import json, os, urllib.request, urllib.error
from datetime import datetime

TODO_FILE = "/home/ubuntu/.hermes/todo.json"
FEISHU_CHAT_ID = "oc_c97273917a903eabd3d81fd9e384b429"  # 黑执事 DM

def get_tenant_token():
    APP_ID = "cli_aa9970856879dcd8"
    APP_SECRET = ""
    with open(os.path.expanduser("~/.bashrc")) as f:
        for line in f:
            if "LARK_APP_SECRET" in line:
                APP_SECRET = line.split("=")[1].strip().strip('"').strip("'")
                break
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("tenant_access_token")

def send_card(card_json):
    token = get_tenant_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    body = json.dumps({
        "receive_id": FEISHU_CHAT_ID,
        "msg_type": "interactive",
        "content": json.dumps(card_json, ensure_ascii=False),
    }, ensure_ascii=False).encode('utf-8')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        if result.get("code") == 0:
            print("✅ Card sent successfully")
            return True
        else:
            print(f"❌ Send failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def read_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE) as f:
        data = json.load(f)
    return [t for t in data if t.get("status") != "completed"]

def build_card(todos):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[today.weekday()]
    today_date = today.strftime("%Y-%m-%d")

    if not todos:
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"📋 每日待办播报 · {date_str}（{weekday}）"},
                "template": "blue"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": "早安，小艾主人！☀️\n今天没有待办事项，清闲的一天～"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": "💡 需要管家帮您添加新任务吗？"}},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 黑执事 · 10:30 播报"}]}
            ]
        }

    high, medium, low = [], [], []
    for t in todos:
        priority = t.get("priority", "medium")
        overdue = t.get("due") and t["due"] < today_date
        item_text = t.get("content", "")
        if t.get("due"):
            item_text += f"  📅 {t['due']}"
        if overdue:
            item_text = f"⚠️ {item_text}"
        if priority == "high":
            high.append(item_text)
        elif priority == "low":
            low.append(item_text)
        else:
            medium.append(item_text)

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
    if overdue_count:
        summary += f"，**{overdue_count}** 项已过期，建议优先处理！"
    else:
        summary += "，加油！"

    elements.append({"tag": "hr"})
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": summary}})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 黑执事 · 10:30 播报"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📋 每日待办播报 · {date_str}（{weekday}）"},
            "template": "blue"
        },
        "elements": elements
    }

def main():
    todos = read_todos()
    card = build_card(todos)
    send_card(card)
    print("[SILENT]")

if __name__ == "__main__":
    main()
