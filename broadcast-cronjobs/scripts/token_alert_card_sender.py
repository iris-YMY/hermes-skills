#!/usr/bin/env python3
"""Send Feishu Token alert as Interactive Card."""
import json, os, urllib.request, urllib.error
from datetime import datetime

ALERT_FILE = "/home/ubuntu/.hermes/logs/lark_token_alert.json"
FEISHU_CHAT_ID = "oc_c97273917a903eabd3d81fd9e384b429"

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
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("code") == 0

def read_alerts():
    if not os.path.exists(ALERT_FILE):
        return []
    with open(ALERT_FILE) as f:
        data = json.load(f)
    return data.get("needs_attention", [])

def build_card(alerts):
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not alerts:
        # No alerts - return None to signal SILENT
        return None

    elements = []
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "⚠️ 发现 Token 异常"}})

    for alert in alerts:
        profile = alert.get("profile", "未知")
        issue = alert.get("issue", "未知问题")
        fix = alert.get("fix", "执行 `lark auth login`")
        content = f"🔸 **{profile}**\n问题：{issue}\n修复：{fix}"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})

    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 系统管家 · 自动监控"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"🚨 系统预警 · {today}"},
            "template": "red"
        },
        "elements": elements
    }

def main():
    alerts = read_alerts()
    card = build_card(alerts)
    
    if card is None:
        # No alerts - output SILENT
        print("[SILENT]")
    else:
        send_card(card)
        print("[SILENT]")

if __name__ == "__main__":
    main()
