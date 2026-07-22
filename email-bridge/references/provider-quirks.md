# Email Provider IMAP/SMTP Quirks

## 163 / 126 / NetEase Enterprise Email

### IMAP ID Command (CRITICAL)

163/126 requires an IMAP `ID` command before login. Without it, `SELECT` fails with:
```
SELECT Unsafe Login. Please contact kefu@188.com for help
```

**Fix**:
```python
imaplib.Commands['ID'] = ('NONAUTH',)

mail = imaplib.IMAP4_SSL("imap.163.com", 993)
id_args = '("name" "ImapMailClient" "version" "1.0.0" "vendor" "MyClient" "support-email" "user@163.com")'
mail._simple_command('ID', id_args)
mail._untagged_response('ID', [None], 'ID')
mail.login(EMAIL_ADDR, AUTH_CODE)
```

The server responds with its own ID:
```
("name" "Coremail Imap" "vendor" "Mailtech" ...)
```

### IMAP SEARCH Limitations

163 uses Coremail IMAP server. Server-side `SEARCH` with `CHARSET UTF-8` and Chinese keywords often returns empty results even when matching emails exist. English keywords may also fail silently.

**Recommendation**: Always implement client-side fallback — fetch all headers, filter in Python by checking `keyword.lower() in subject.lower() or keyword.lower() in from_.lower()`.

### Auth Code (授权码)

- NOT the login password. Must be generated in 163 web settings → POP3/SMTP/IMAP.
- 16-character alphanumeric string.
- Regenerating invalidates the previous code.
- For enterprise 163 email (网易企业邮箱), admin may need to enable IMAP per-user.

### Mailbox Names (Modified UTF-7)

163 uses modified UTF-7 encoding for non-ASCII folder names:
```
&g0l6P3ux-     = 草稿箱 (Drafts)
&XfJT0ZAB-     = 已发送 (Sent)
&XfJSIJZk-     = 已删除 (Trash)
&V4NXPpCuTvY-  = 垃圾邮件 (Junk)
```

Use the English name `INBOX` for inbox — it always works.

---

## QQ Mail

### IMAP Settings
- IMAP: `imap.qq.com:993` (SSL)
- SMTP: `smtp.qq.com:465` (SSL)
- Auth: 授权码 (same pattern as 163)

### Quirks
- May also require ID command (untested — if `SELECT` fails, try the same ID fix as 163)
- Generally more permissive than 163

---

## Gmail

### IMAP Settings
- IMAP: `imap.gmail.com:993` (SSL)
- SMTP: `smtp.gmail.com:465` (SSL)
- Auth: App Password (16 chars, generated in Google Account → Security → App Passwords)

### Quirks
- Must enable "Less secure apps" OR use App Passwords with 2FA enabled
- No ID command required
- Server-side search works well with UTF-8

---

## Outlook / Office365

### IMAP Settings
- IMAP: `outlook.office365.com:993` (SSL)
- SMTP: `smtp.office365.com:587` (STARTTLS)
- Auth: Account password or App Password depending on org policy

### Quirks
- Some org tenants disable IMAP — check admin settings
- OAuth2 may be required for some tenants (more complex setup)

---

## General IMAP Best Practices

1. **Use SSL (port 993)**, not STARTTLS (port 143) — most Chinese providers prefer direct SSL.
2. **Use BODY.PEEK[] for listing/searching** to avoid marking emails as read.
3. **Decode headers properly** — Chinese subjects use various encodings (GB2312, UTF-8, GBK). Use `email.header.decode_header()` and try multiple encodings.
4. **Connection timeout** — set a reasonable timeout (15-30s) for IMAP connections, as Chinese providers can be slow.
5. **Reconnect on failure** — IMAP connections can drop; implement reconnection logic in long-running scripts.
