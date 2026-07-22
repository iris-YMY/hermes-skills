---
name: email-bridge
description: "Bridge external email accounts to Hermes/Feishu via Python IMAP/SMTP — list, read, search, send, and auto-notify on new mail."
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, Python, Feishu, Notification, Cronjob]
---

# Email Bridge — Python IMAP/SMTP to Hermes/Feishu

When native email integration (e.g. Feishu Mail) is unavailable or the user's plan doesn't include it, bridge external email accounts to Hermes using Python's built-in `imaplib` + `smtplib`. The agent handles email operations conversationally, and a cron job pushes new-mail notifications to Feishu automatically.

## When to Use

- User wants to manage email from within Feishu but native Feishu Mail is unavailable (requires Enterprise Flagship plan)
- User wants email notifications pushed to Feishu on a schedule
- Himalaya CLI is not installed or the user prefers a script-based approach integrated with Hermes cronjobs
- Email account supports IMAP/SMTP (most providers do)

## Architecture

```
163/Gmail/QQ ──IMAP──→ Python script ──→ Hermes agent ──→ Feishu message
                   ←──SMTP──              ←── user command
                         ↑
                   Hermes cronjob (every 30m)
```

## Files

- `templates/mail_manager.py` — Full email manager script (list/read/search/send/check_new/unread_count/mark_read). Copy and adapt with provider-specific credentials.
- `templates/cron_check.py` — Cron-friendly wrapper: prints new-mail summary or nothing (for [SILENT] handling). Place next to mail_manager.py.
- `references/provider-quirks.md` — IMAP/SMTP quirks per provider (163, Gmail, QQ, etc.)

## Setup Steps

### 1. Get IMAP/SMTP credentials

| Provider | IMAP Server | IMAP Port | SMTP Server | SMTP Port | Auth |
|---|---|---|---|---|---|
| 163 / 126 | imap.163.com | 993 (SSL) | smtp.163.com | 465 (SSL) | 授权码 |
| QQ Mail | imap.qq.com | 993 (SSL) | smtp.qq.com | 465 (SSL) | 授权码 |
| Gmail | imap.gmail.com | 993 (SSL) | smtp.gmail.com | 465 (SSL) | App Password |
| Outlook | outlook.office365.com | 993 (SSL) | smtp.office365.com | 587 (STARTTLS) | Password |

> ⚠️ Chinese providers (163, QQ, 126) use **授权码** (authorization code), NOT the login password. The user must enable IMAP service in their email settings and generate an auth code.

### 2. Deploy the mail manager script

Copy `templates/mail_manager.py` to `~/scripts/mail163/` (or appropriate dir). Edit the configuration section:

```python
IMAP_SERVER = "imap.163.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
EMAIL_ADDR = "user@example.com"
AUTH_CODE = "the-authorization-code"
```

### 3. Test connectivity

```bash
python3 ~/scripts/mail163/mail_manager.py list 5
python3 ~/scripts/mail163/mail_manager.py unread_count
```

### 4. Set up cron job for auto-notification

Create a `cron_check.py` that calls `cmd_check_new()` and prints a formatted summary. Then create a Hermes cronjob:

- **Schedule**: `every 30m` (adjustable)
- **Repeat**: `0` (forever)
- **Model**: must specify a **registered** provider+model. Use `qwen3.7-max` via `qwen` provider. ⚠️ Do NOT use `custom` provider — it fails in cron context with `RuntimeError: No LLM provider configured`.
- **Prompt**: run the check script, if output exists → send to user, else silent

### 5. User interaction

Users interact conversationally — no commands to memorize:

| User says | Agent runs |
|---|---|
| "查收邮件" / "看看邮箱" | `python3 mail_manager.py list 10` |
| "读取第2封" | `python3 mail_manager.py read 2` |
| "搜索Tiffany" | `python3 mail_manager.py search Tiffany` |
| "给xxx发邮件，主题是…" | `python3 mail_manager.py send xxx@xx.com "主题" "内容"` |
| "多少封未读" | `python3 mail_manager.py unread_count` |

## ⚠️ Critical Pitfalls

### 1. 163/NetEase "Unsafe Login" Error

163 email requires an IMAP `ID` command **before login**, or `SELECT` fails with `"SELECT Unsafe Login. Please contact kefu@188.com"`.

**Fix**: Register the ID command in imaplib and send it before login:

```python
imaplib.Commands['ID'] = ('NONAUTH',)  # Must add this — imaplib doesn't know 'ID'

mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
id_args = '("name" "ImapMailClient" "version" "1.0.0" "vendor" "MyClient" "support-email" "user@example.com")'
mail._simple_command('ID', id_args)
mail._untagged_response('ID', [None], 'ID')
mail.login(EMAIL_ADDR, AUTH_CODE)  # Now SELECT will work
```

### 2. UnicodeEncodeError on IMAP SEARCH with Chinese

Python's `imaplib` encodes command args as ASCII by default. Searching with Chinese keywords throws `UnicodeEncodeError`.

**Fix**: Try server-side UTF-8 search first, fall back to client-side filtering:

```python
try:
    mail._simple_command('SEARCH', 'CHARSET', 'UTF-8', f'SUBJECT "{keyword}"'.encode('utf-8'))
    typ, data = mail._untagged_response('OK', [None], 'SEARCH')
except Exception:
    pass  # Fall through to client-side
```

If server-side returns nothing (163's Coremail often does), fetch all headers and filter in Python:

```python
for mid in all_ids:
    # Fetch headers only, check if keyword matches subject or sender
```

### 3. Fetch Marks Emails as Read

`mail.fetch(mid, "(RFC822)")` marks the email as seen. Use `BODY.PEEK[]` instead to avoid side effects during listing/searching:

```python
# ❌ Marks as read
mail.fetch(mid, "(RFC822)")

# ✅ Does NOT mark as read
mail.fetch(mid, "(BODY.PEEK[])")
```

Only use RFC822 (or call `mail.store(mid, '+FLAGS', '\\Seen')`) when the user explicitly reads an email.

### 4. Cronjob Model Provider (CRITICAL)

Per house rules, new cronjobs **must** specify the `model` parameter. However:

- ⚠️ **`provider: "custom"` does NOT work in cron context** — it fails with `RuntimeError: No LLM provider configured`.
- ✅ **Use a registered provider**: `{"model": "qwen3.7-max", "provider": "qwen"}` is known to work.
- After creating, **always verify** by checking `last_status` or manually running once via `cronjob action=run`.
- Check the output log at `~/.hermes/cron/output/<job_id>/` for error details.

### 5. Home Directory Permissions

The Hermes environment may run as `ubuntu` user, not `hermes`. Scripts go in `~/scripts/` (which resolves to `/home/ubuntu/scripts/`), not `/home/hermes/`.

## Verification

After setup, verify each component:

1. `python3 mail_manager.py list 5` — shows recent emails
2. `python3 mail_manager.py unread_count` — shows unread count
3. `python3 mail_manager.py search "test"` — search works (client-side fallback)
4. Cronjob `last_status` is `success` after first scheduled run
