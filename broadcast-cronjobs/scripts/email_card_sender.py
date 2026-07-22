#!/usr/bin/env python3
"""Send 163 email check result as Feishu Interactive Card."""
import json, os, subprocess, urllib.request, urllib.error
from datetime import datetime

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

def check_emails():
    result = subprocess.run(
        ["python3", "/home/ubuntu/scripts/mail163/cron_check.py"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def parse_emails(output):
    if not output:
        return []
    # Parse email output - each email separated by newlines
    emails = []
    current = {}
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("发件人:"):
            if current:
                emails.append(current)
            current = {"from": line.replace("发件人:", "").strip()}
        elif line.startswith("主题:"):
            current["subject"] = line.replace("主题:", "").strip()
        elif line.startswith("时间:"):
            current["time"] = line.replace("时间:", "").strip()
    if current:
        emails.append(current)
    return emails

def build_card(emails):
    now = datetime.now().strftime("%H:%M")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not emails:
        # No new emails - return None to signal SILENT
        return None

    elements = []
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"📨 发现 **{len(emails)}** 封新邮件"}})

    for i, email in enumerate(emails[:5], 1):  # Limit to 5 emails
        emoji = "1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣"[i-1*2-1:i*2-1] if i <= 5 else "•"
        content = f"**{i}️⃣ {email.get('from', '未知发件人')}**\n"
        content += f"📌 {email.get('subject', '无主题')}\n"
        content += f"🕐 {email.get('time', '')}"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})

    if len(emails) > 5:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"...还有 {len(emails)-5} 封邮件"}})

    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "🤵 邮件管家 · 自动巡检"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📬 邮件巡检报告 · {now}"},
            "template": "green"
        },
        "elements": elements
    }

def main():
    output = check_emails()
    emails = parse_emails(output)
    card = build_card(emails)
    
    if card is None:
        # No emails - output SILENT
        print("[SILENT]")
    else:
        send_card(card)
        print("[SILENT]")

if __name__ == "__main__":
    main()
