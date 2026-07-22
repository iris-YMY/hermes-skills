#!/usr/bin/env python3
"""
Email Manager — IMAP/SMTP bridge for Hermes.
Supports: list, read, search, send, check_new, unread_count, mark_read.

Usage:
  python3 mail_manager.py list [limit]
  python3 mail_manager.py unread
  python3 mail_manager.py read <id>
  python3 mail_manager.py search <keyword>
  python3 mail_manager.py send <to> <subject> <body>
  python3 mail_manager.py check_new
  python3 mail_manager.py unread_count
  python3 mail_manager.py mark_read <id>
"""
import imaplib
import smtplib
import email
import json
import os
import sys
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate
from datetime import datetime

# === Configuration (EDIT THESE) ===
IMAP_SERVER = "imap.163.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
EMAIL_ADDR = "your_email@163.com"
AUTH_CODE = "your_auth_code"
DISPLAY_NAME = "Your Name"
# === End Configuration ===

# Register ID command for 163/NetEase
imaplib.Commands['ID'] = ('NONAUTH',)

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mail_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_seen_uid": None, "notified_ids": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def decode_str(s):
    if not s:
        return ""
    decoded = decode_header(s)
    parts = []
    for part, enc in decoded:
        if isinstance(part, bytes):
            parts.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return "".join(parts)

def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break
        if not body:
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="replace")
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
    return body.strip()

def connect_imap():
    """Connect and login. Sends ID command for 163 compatibility."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    # Send ID command (required by 163/NetEase)
    id_args = f'("name" "ImapMailClient" "version" "1.0.0" "vendor" "MyClient" "support-email" "{EMAIL_ADDR}")'
    mail._simple_command('ID', id_args)
    mail._untagged_response('ID', [None], 'ID')
    mail.login(EMAIL_ADDR, AUTH_CODE)
    return mail

def connect_smtp():
    smtp = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    smtp.login(EMAIL_ADDR, AUTH_CODE)
    return smtp

def cmd_list(folder="INBOX", limit=10):
    """List recent emails (does NOT mark as read)."""
    mail = connect_imap()
    mail.select(folder)
    typ, data = mail.search(None, "ALL")
    mail_ids = data[0].split()
    if not mail_ids:
        mail.logout()
        return {"success": True, "total": 0, "emails": [], "message": "No emails found."}
    total = len(mail_ids)
    fetch_ids = mail_ids[-limit:]
    results = []
    for mid in reversed(fetch_ids):
        # BODY.PEEK avoids marking as read
        typ, msg_data = mail.fetch(mid, "(BODY.PEEK[])")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                results.append({
                    "id": mid.decode(),
                    "subject": decode_str(msg.get("Subject", "")),
                    "from": decode_str(msg.get("From", "")),
                    "date": msg.get("Date", ""),
                })
    mail.logout()
    return {"success": True, "total": total, "folder": folder, "emails": results}

def cmd_read(mail_id, folder="INBOX"):
    """Read a specific email by ID (marks as read)."""
    mail = connect_imap()
    mail.select(folder)
    typ, msg_data = mail.fetch(mail_id, "(RFC822)")
    result = {"success": False}
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            result = {
                "success": True,
                "id": mail_id,
                "subject": decode_str(msg.get("Subject", "")),
                "from": decode_str(msg.get("From", "")),
                "to": decode_str(msg.get("To", "")),
                "date": msg.get("Date", ""),
                "body": get_body(msg)[:5000],
            }
            break
    mail.store(mail_id, '+FLAGS', '\\Seen')
    mail.logout()
    return result

def cmd_search(keyword, folder="INBOX", limit=20):
    """Search emails by keyword. Tries server-side first, falls back to client-side."""
    mail = connect_imap()
    mail.select(folder)
    mail_ids = []
    # Try server-side UTF-8 search
    try:
        typ, data = mail._simple_command('SEARCH', 'CHARSET', 'UTF-8', f'SUBJECT "{keyword}"'.encode('utf-8'))
        typ, data = mail._untagged_response('OK', [None], 'SEARCH')
        if data[0]:
            mail_ids = data[0].split()
    except Exception:
        pass
    # Try FROM search
    if not mail_ids:
        try:
            typ, data = mail.search(None, f'FROM "{keyword}"')
            if data[0]:
                mail_ids = data[0].split()
        except Exception:
            pass
    # Client-side fallback
    if not mail_ids:
        typ, data = mail.search(None, "ALL")
        all_ids = data[0].split() if data[0] else []
        results = []
        for mid in reversed(all_ids):
            typ, msg_data = mail.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_str(msg.get("Subject", ""))
                    from_ = decode_str(msg.get("From", ""))
                    if keyword.lower() in subject.lower() or keyword.lower() in from_.lower():
                        results.append({
                            "id": mid.decode(),
                            "subject": subject,
                            "from": from_,
                            "date": msg.get("Date", ""),
                        })
                        if len(results) >= limit:
                            break
            if len(results) >= limit:
                break
        mail.logout()
        return {"success": True, "total": len(results), "keyword": keyword, "method": "client-side", "emails": results}
    # Server-side results
    total = len(mail_ids)
    fetch_ids = mail_ids[-limit:]
    results = []
    for mid in reversed(fetch_ids):
        typ, msg_data = mail.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                results.append({
                    "id": mid.decode(),
                    "subject": decode_str(msg.get("Subject", "")),
                    "from": decode_str(msg.get("From", "")),
                    "date": msg.get("Date", ""),
                })
    mail.logout()
    return {"success": True, "total": total, "keyword": keyword, "method": "server-side", "emails": results}

def cmd_send(to_addr, subject, body, html=False):
    """Send an email."""
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((DISPLAY_NAME, EMAIL_ADDR))
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    if html:
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        import re
        plain = re.sub(r'<[^>]+>', '', body)
        msg.attach(MIMEText(plain, 'plain', 'utf-8'))
    else:
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
    smtp = connect_smtp()
    smtp.sendmail(EMAIL_ADDR, [to_addr], msg.as_string())
    smtp.quit()
    return {"success": True, "to": to_addr, "subject": subject}

def cmd_check_new():
    """Check for new unread emails since last check."""
    state = load_state()
    notified = set(state.get("notified_ids", []))
    mail = connect_imap()
    mail.select("INBOX")
    typ, data = mail.search(None, "UNSEEN")
    unseen_ids = data[0].split() if data[0] else []
    new_emails = []
    for mid in unseen_ids:
        mid_str = mid.decode()
        if mid_str not in notified:
            typ, msg_data = mail.fetch(mid, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body_preview = get_body(msg)[:200]
                    new_emails.append({
                        "id": mid_str,
                        "subject": decode_str(msg.get("Subject", "")),
                        "from": decode_str(msg.get("From", "")),
                        "date": msg.get("Date", ""),
                        "preview": body_preview,
                    })
            notified.add(mid_str)
    state["notified_ids"] = list(notified)[-200:]
    state["last_check"] = datetime.now().isoformat()
    save_state(state)
    mail.logout()
    return {"success": True, "new_count": len(new_emails), "emails": new_emails}

def cmd_unread_count():
    """Get unread email count."""
    mail = connect_imap()
    mail.select("INBOX")
    typ, data = mail.search(None, "UNSEEN")
    count = len(data[0].split()) if data[0] else 0
    mail.logout()
    return {"success": True, "unread": count}

def cmd_mark_read(mail_id, folder="INBOX"):
    """Mark an email as read."""
    mail = connect_imap()
    mail.select(folder)
    mail.store(mail_id, '+FLAGS', '\\Seen')
    mail.logout()
    return {"success": True, "id": mail_id, "marked": "read"}

# === CLI ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 mail_manager.py <command> [args]")
        print("Commands: list [n], unread, read <id>, search <keyword>, send <to> <subject> <body>, check_new, unread_count, mark_read <id>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = cmd_list(limit=limit)
    elif cmd == "unread":
        result = cmd_list(unread_only=True) if hasattr(cmd_list, 'unread_only') else cmd_unread_count()
    elif cmd == "read":
        result = cmd_read(sys.argv[2])
    elif cmd == "search":
        result = cmd_search(sys.argv[2])
    elif cmd == "send":
        result = cmd_send(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "check_new":
        result = cmd_check_new()
    elif cmd == "unread_count":
        result = cmd_unread_count()
    elif cmd == "mark_read":
        result = cmd_mark_read(sys.argv[2])
    else:
        result = {"error": f"Unknown command: {cmd}"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
