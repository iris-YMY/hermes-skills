#!/usr/bin/env python3
"""
Cron check script for email bridge.
Checks for new unread emails and prints a formatted summary.
If no new emails, prints nothing (silent — cron job should output [SILENT]).

Usage in cron prompt:
  Run `python3 /home/ubuntu/scripts/mail163/cron_check.py`
  If output exists → send to user. If no output → respond [SILENT].

Place this file next to mail_manager.py and adjust the sys.path accordingly.
"""
import sys
import os

# Adjust path to import mail_manager
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from mail_manager import cmd_check_new

result = cmd_check_new()

if result["success"] and result["new_count"] > 0:
    print(f"📬 您的邮箱收到 {result['new_count']} 封新邮件：")
    print()
    for i, mail in enumerate(result["emails"], 1):
        print(f"📧 新邮件 #{i}")
        print(f"   发件人：{mail['from']}")
        print(f"   主  题：{mail['subject']}")
        print(f"   时  间：{mail['date']}")
        if mail.get("preview"):
            preview = mail["preview"].replace("\n", " ").replace("\r", "")[:100]
            print(f"   预  览：{preview}...")
        print()
    print("回复「读取邮件 <编号>」可查看完整内容，或直接告诉我如何处理。")
# else: no output — cron job should respond [SILENT]
