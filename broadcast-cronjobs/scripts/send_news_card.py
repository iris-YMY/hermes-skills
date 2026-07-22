#!/usr/bin/env python3
"""
飞书新闻卡片发送脚本
读取结构化 JSON → 构建飞书 Interactive Card → 发送到指定群聊

Usage: python3 send_news_card.py [json_file_path]
Default input: /tmp/news_card_data.json

JSON schema:
{
  "date": "YYYY年M月D日 星期X",
  "greeting": "小艾主人早上好呀～...",
  "sections": [
    {
      "emoji": "📌",
      "title": "今日看点",
      "tag": "TOP",           // optional badge
      "items": [
        {"text": "新闻概要（2句话）", "source": "来源"}
      ]
    }
  ],
  "tip": "温馨提示文字"
}
"""

import json
import sys
import urllib.request
import os
from datetime import datetime

# === Config ===
APP_ID = "cli_aa9ea34aaff85cda"
APP_SECRET = "LpTsYpJKYDBfDtl0qw4i8gV1PwTN2nSr"
CHAT_ID = "oc_a0422f2a7bebf7c3b831a4ff05b8c6db"  # AI在这里 group
INPUT_FILE = "/tmp/news_card_data.json"

def get_tenant_token():
    payload = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET})
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=payload.encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if resp.get("code") != 0:
        raise Exception(f"Token error: {resp}")
    return resp["tenant_access_token"]

def build_card(data):
    """Build Feishu interactive card from structured data."""
    
    date_str = data.get("date", datetime.now().strftime("%Y年%m月%d日"))
    greeting = data.get("greeting", "早上好～")
    sections = data.get("sections", [])
    tip = data.get("tip", "")
    
    elements = []
    
    # Greeting block
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"☀️ {greeting}"
        }
    })
    elements.append({"tag": "hr"})
    
    # Sections
    for sec in sections:
        emoji = sec.get("emoji", "📰")
        title = sec.get("title", "")
        tag_label = sec.get("tag", "")
        items = sec.get("items", [])
        no_data_msg = sec.get("no_data", "")
        
        # Section title
        title_text = f"**{emoji} {title}**"
        if tag_label:
            title_text += f"  `{tag_label}`"
        
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": title_text}
        })
        
        if items:
            item_lines = []
            for item in items:
                text = item.get("text", "")
                source = item.get("source", "")
                if source:
                    item_lines.append(f"• {text} ——{source}")
                else:
                    item_lines.append(f"• {text}")
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(item_lines)}
            })
        elif no_data_msg:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"_{no_data_msg}_"}
            })
        else:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "_⚠️ 今日暂无专项数据_"}
            })
        
        elements.append({"tag": "hr"})
    
    # Tip footer
    if tip:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**💝 添添温馨提醒**\n{tip}"
            }
        })
    
    # Action buttons
    elements.append({
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📋 展开详情"},
                "type": "default",
                "multi_url": {"url": "https://feishu.cn"}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "⭐ 收藏"},
                "type": "default"
            }
        ]
    })
    
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"📰 早间新闻播报 | {date_str}"
            },
            "template": "blue"
        },
        "elements": elements
    }
    
    return card

def send_card(token, card):
    payload = json.dumps({
        "receive_id": CHAT_ID,
        "msg_type": "interactive",
        "content": json.dumps(card, ensure_ascii=False)
    })
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=payload.encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"📦 Loaded news data from {input_file}")
    print(f"   Date: {data.get('date', 'N/A')}")
    print(f"   Sections: {len(data.get('sections', []))}")
    
    token = get_tenant_token()
    print(f"🔑 Token obtained")
    
    card = build_card(data)
    print(f"🎨 Card built with {len(card['elements'])} elements")
    
    resp = send_card(token, card)
    
    if resp.get("code") == 0:
        msg_id = resp.get("data", {}).get("message_id", "unknown")
        print(f"✅ Card sent successfully! Message ID: {msg_id}")
    else:
        print(f"❌ Send failed: {json.dumps(resp, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
