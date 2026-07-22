# Feishu Email Integration

Connecting external email accounts (e.g. 163, Gmail, QQ Mail) into Feishu for unified email management.

## 1. Feishu Mail (飞书邮箱) — Native Integration

### Enablement Requirements
- Feishu Mail is NOT enabled by default — requires **workspace admin** to turn it on
- Admin path: Feishu Admin Console (https://feishu.cn/admin) → App Management → enable Mail
- Once enabled, users can add external email accounts via IMAP/SMTP in the Mail app
- If user can't find the Mail app in Feishu workspace, 99% it's not enabled by admin

### Adding External Account (after Mail is enabled)
1. Open Feishu → Mail app → Account Settings → Add Account
2. Select "Other" (manual IMAP/SMTP configuration)
3. Fill in IMAP/SMTP server details + authorization code (NOT login password)

## 2. Hermes Email Bridge — Alternative When Mail Is Unavailable

When Feishu Mail cannot be enabled (no admin access, plan limitation), Hermes can act as an email bridge:

| Function | Implementation |
|----------|---------------|
| Receive notifications | Cron job checks inbox via IMAP → push summary to Feishu chat |
| Send email | User instructs in Feishu → Hermes sends via SMTP |
| Search email | User asks in Feishu → Hermes queries via IMAP → returns summary |
| Important alerts | Cron checks for specific senders/subjects → immediate notification |

### Architecture
```
163/Gmail/QQ ──IMAP──→ Hermes (Python imaplib) ──→ Feishu message
                     ←──SMTP── Hermes (smtplib) ←── Feishu message
```

### Prerequisites
- IMAP/SMTP credentials (authorization code for Chinese providers — NOT login password)
- Hermes terminal access (for Python imaplib/smtplib)
- Cron job for periodic inbox checks

### Limitations vs Native Feishu Mail
- No folder management (move, label, archive)
- No attachment preview inline
- No full-text search UI — conversational only
- Good enough for: receive notifications, send replies, basic search

## 3. Common Chinese Email Provider IMAP/SMTP Settings

### NetEase 163 Personal (个人邮箱)
| Protocol | Server | Port | Encryption |
|----------|--------|------|------------|
| IMAP | imap.163.com | 993 | SSL |
| SMTP | smtp.163.com | 465 | SSL |

Auth: 16-digit authorization code (授权码), obtained from 163 web → Settings → POP3/SMTP/IMAP → enable IMAP

### NetEase Enterprise Email (网易企业邮箱)
| Protocol | Server | Port | Encryption |
|----------|--------|------|------------|
| IMAP | qyimap.qiye.163.com | 993 | SSL |
| SMTP | qysmtp.qiye.163.com | 994 | SSL |

Auth: Client-specific password set by enterprise admin, or authorization code if admin enabled it

⚠️ Enterprise email users may NOT have direct access to IMAP settings — admin must enable client access first. If user reports "can't get authorization code" for 163 enterprise email, advise contacting IT admin.

### QQ Mail
| Protocol | Server | Port | Encryption |
|----------|--------|------|------------|
| IMAP | imap.qq.com | 993 | SSL |
| SMTP | smtp.qq.com | 465 | SSL |

Auth: 16-digit authorization code from QQ Mail → Settings → Accounts → enable IMAP

## 4. Security Practice

- **NEVER accept email authorization codes from users** — guide them to enter it in the actual UI themselves
- For Hermes email bridge: store credentials in `.env` file, NEVER in memory (memory is injected into every system prompt)
- Reference himalaya skill for CLI-based email operations (read, send, search via terminal)

## 5. Feishu Help Center Scraping Pitfall

Feishu help center (https://www.feishu.cn/hc/) is a JavaScript-rendered SPA. `curl` returns only the HTML shell — article content is loaded dynamically. Category pages and search results return empty when grepping for article content.

**Workaround**: Use browser-based extraction (web-research skill) instead of curl for Feishu help center articles. The category ID for Mail articles is `6933474571806916609`.
