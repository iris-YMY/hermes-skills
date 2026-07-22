---
name: lark-cli
description: "lark-cli: Go CLI for Feishu/Lark APIs — calendar, contacts, docs, messages, mail, drive, wiki, tasks, sheets, base, meetings. Token-efficient JSON output for AI assistants."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# lark-cli — Feishu/Lark API CLI

A Go CLI tool (`github.com/yjwong/lark-cli`) designed for AI assistants to interact with Feishu/Lark APIs efficiently. Returns compact JSON by default — far more token-efficient than the official MCP server.

## Install (from source)

Requires Go. Clone, build, install to `~/.local/bin/`:

```bash
git clone https://github.com/yjwong/lark-cli.git ~/lark-cli
cd ~/lark-cli
go build -o ~/.local/bin/lark ./cmd/lark/
lark version  # verify
```

Binary available at: `~/.local/bin/lark`
Source at: `~/lark-cli/`

### Adding Scopes to a Group
If you need additional Feishu scopes (e.g., `drive:drive` for folder creation):
1. Edit `~/lark-cli/internal/scopes/scopes.go` — add the scope to the relevant group
2. Rebuild: `cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/`
3. Re-authorize: `rm -f ~/.lark/tokens.json && lark auth login` (user must re-grant new scopes)

## Configure

### 🔴 Per-Profile Configuration (UPDATED 2026-06-05)
Each Hermes profile has its **own isolated `.lark/` directory** with matching app_id + secret. **NEVER mix configs across profiles.**

```
~/.hermes/profiles/default/home/.lark/        ← 黑执事 (default)
~/.hermes/profiles/hr-assistant/home/.lark/   ← 凛子小姐 (hr-assistant)
~/.hermes/profiles/data-master/home/.lark/    ← 数据大师 (data-master)
~/.lark/                                      ← Global fallback (default only)
```

Each directory contains:
- `config.yaml` — app_id + region
- `app_secret` — Feishu app secret (one line, no quotes)
- `tokens.json` — OAuth tokens (after auth login)

### Setup for Current Profile
```bash
# hr-assistant (凛子小姐):
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"

# default (黑执事):
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/default/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"

# data-master (数据大师):
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/data-master/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"
```

### 🔴 Critical: Environment Variables (Both Must Be Set)
lark-cli **requires** both `LARK_CONFIG_DIR` and `LARK_APP_SECRET` to be set:
- **`LARK_CONFIG_DIR`** — without it, ALL commands fail with `CONFIG_ERROR`
- **`LARK_APP_SECRET`** — without it, token exchange fails with "app secret not configured"

**Per-profile setup (recommended)**: Load both from the profile's `.lark/` directory:
```bash
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"
```

**Global fallback** (default profile only):
```bash
echo 'export LARK_CONFIG_DIR="$HOME/.lark"' >> ~/.bashrc
echo 'export LARK_APP_SECRET="$(cat $HOME/.lark/app_secret)"' >> ~/.bashrc
source ~/.bashrc
```

**⚠️ Before OAuth: verify app_id and secret match** (multi-profile setups commonly mismatch):
```bash
curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"$(grep app_id ~/.lark/config.yaml | cut -d\" -f2)","app_secret":"'$LARK_APP_SECRET'"}'
# code:0 = OK. code:10014 = mismatch → OAuth will fail with 20002 invalid_client
```
In this setup, `LARK_APP_SECRET` belongs to default profile (`cli_aa9970856879dcd8`). Keep config.yaml aligned.

### 🔴 Multi-Profile Token Path Resolution (CRITICAL for Hermes multi-agent)

**⚠️ UPDATED 2026-06-05: Per-profile isolation is now enforced.**

In a multi-agent Hermes setup, each profile has its **own** `.lark/` directory for **isolated app identity and OAuth tokens**:

```
~/.lark/                              ← Global fallback (default profile only)
~/.hermes/profiles/default/home/.lark/        ← Default profile (黑执事)
~/.hermes/profiles/hr-assistant/home/.lark/   ← HR assistant (凛子小姐)
~/.hermes/profiles/data-master/home/.lark/    ← Data master (数据大师)
```

**Each profile directory contains:**
- `config.yaml` — app_id and region (unique per profile)
- `app_secret` — the Feishu app secret (unique per profile)
- `tokens.json` — OAuth user access token (if authenticated)

**`LARK_CONFIG_DIR` determines which profile's identity and tokens are used.**

**How to use a specific profile:**
```bash
# For hr-assistant (凛子小姐):
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"

# For default (黑执事):
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/default/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"

# For data-master (数据大师):
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/data-master/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"
```

**⚠️ NEVER modify `~/.lark/config.yaml` from a non-default profile.** Each profile must only touch its own `~/.hermes/profiles/<name>/home/.lark/` directory.

**⚠️ OAuth tokens are per-app.** If you authenticate with profile A's app_id, the resulting `tokens.json` belongs to that app. Profile B needs its own OAuth flow unless both apps share the same Feishu tenant and the token is user-level (OAuth tokens work across apps in the same tenant, but it's cleaner to keep them separate).

### Feishu App Setup (required before `auth login`)
Create app at https://open.feishu.cn and enable these permissions:
- `calendar:calendar` — calendar read/write
- `contact:contact.base:readonly` — contacts
- `docx:document:readonly` + `docs:document.content:read` — cloud docs
- `im:message` + `im:message:send_as_bot` — messages
- `drive:drive` — cloud space
- `wiki:wiki:readonly` — wiki/knowledge base
- `im:message:readonly` — read chat history
- `offline_access` — refresh tokens
- **Redirect URI**:
  - For **local/localhost** usage: `http://localhost:9999/callback`
  - For **remote/cloud server** usage: `http://<YOUR_SERVER_PUBLIC_IP>:9999/callback` (e.g. `http://1.2.3.4:9999/callback`)
- Enable "Refresh user_access_token" in Security Settings

## Commands (11 Business Domains)

### Auth

#### Method 1: Interactive (local machine with browser)
```bash
lark auth login                  # OAuth login (all scopes)
lark auth login --scopes cal     # Calendar only
lark auth status                 # Check auth + granted scopes
lark auth logout                 # Clear tokens
```

#### Method 2: Headless (cloud server — RECOMMENDED)

**When source is patched** (redirect uses server public IP — see Pitfalls), the callback server on port 9999 **works automatically**. Use this simple flow:

```bash
# 1. Kill any zombie auth processes
fuser -k 9999/tcp 2>/dev/null

# 2. Set profile environment
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/<profile>/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"

# 3. Launch in background, redirect output to log
lark auth login > /tmp/lark_login.log 2>&1 &
sleep 3

# 4. Extract the authorization URL
grep "https://accounts.feishu.cn" /tmp/lark_login.log
```

Send the URL to the user. They open it in their browser, click「同意」, and the callback server on port 9999 **receives the redirect and saves tokens automatically**. No manual curl exchange needed.

**Verify after user authorizes:**
```bash
lark auth status  # Should show: {"authenticated": true, ...}
```

**Only if the simple flow fails** (e.g., source not patched, port not reachable), fall back to the manual curl exchange flow below:

<details>
<summary>Manual curl exchange (fallback)</summary>

**Step 3b**: User copies the `code` from the browser address bar
After authorization, browser redirects to `http://<SERVER_IP>:9999/callback?code=XXXXXX&state=YYYYYY` — the page shows "connection refused" which is normal. User copies the `code=XXXXXX` value.

**Step 4b**: Kill the background process first (it may consume the code):
```bash
fuser -k 9999/tcp 2>/dev/null
```

**Step 5b**: Exchange code for tokens via curl
```bash
curl -s -X POST "https://open.feishu.cn/open-apis/authen/v2/oauth/token" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "grant_type": "authorization_code",
    "client_id": "cli_YOUR_APP_ID",
    "client_secret": "YOUR_APP_SECRET",
    "code": "CODE_FROM_BROWSER",
    "redirect_uri": "http://YOUR_SERVER_IP:9999/callback"
  }'
```

**Step 6b**: Write tokens to `$LARK_CONFIG_DIR/tokens.json`
```json
{
  "access_token": "<from response>",
  "refresh_token": "<from response>",
  "expires_at": "<ISO 8601, current time + expires_in seconds>",
  "refresh_token_expires_at": "<ISO 8601, current time + refresh_token_expires_in seconds>",
  "scope": "<from response>"
}
```
</details>

### Calendar (`cal`)
```bash
lark cal list --week             # This week's events
lark cal create --summary "..." --start "2026-05-26T10:00:00+08:00" --end "2026-05-26T11:00:00+08:00"
lark cal create --summary "..." --start "..." --end "..." --location "..." --description "..." --reminder 60
lark cal show <event_id>
lark cal attendee add <event_id> --user <open_id>   # Invite attendee (triggers Feishu notification)
lark cal attendee list <event_id>
lark cal attendee remove <event_id> --user <open_id>
lark cal freebusy --user_ids "ou_xxx,ou_yyy" --from "2026-05-26" --to "2026-05-27"
lark cal common-freetime --user_ids "ou_xxx,ou_yyy" --duration 60
```

#### ⚠️ Calendar Event Share API Returns 404 (FOUND 2026-06-15)
`POST /calendar/v4/calendars/{cal_id}/events/{event_id}/share` with `chat_id_list` returns **404 page not found**.
**Workaround**: To send a calendar event card to a group, use `lark cal attendee add` to invite the person (triggers real calendar notification), then send an **interactive card** message to the group with event details + @mention. See "Sending Interactive Cards" below.

#### 🔴 Calendar API Quirks (FOUND 2026-06-05)

**Event creation uses Unix timestamps, NOT ISO date_time:**
```json
{
  "summary": "🎬 Movie Title",
  "start_time": {"timestamp": "1749794400"},
  "end_time": {"timestamp": "1749804000"}
}
```
- ⚠️ `date_time` + `tz_name` format returns **400 Bad Request**
- Use Unix epoch seconds (UTC-based) for `timestamp`
- Reminders work: `"reminder": {"use_default": false, "reminders": [{"minutes": 60}]}`

**List events API parameter constraints:**
- `page_size` minimum is **50** (not 10). Lower values return `99992402 field validation failed`
- `time_min` and `time_max` must be ISO 8601 with timezone offset

**Primary calendar ID format:**
- User's primary calendar: `feishu.cn_<hash>@group.calendar.feishu.cn`
- Discover via `GET /calendar/v4/calendars`

### Contacts (`contact`)
```bash
lark contact get <user_id>           # Get user by Open ID
lark contact list-dept [dept_id]     # List dept members
lark contact search-dept <query>     # Search departments
```

### Sending Interactive Cards (Calendar Invitations, Event Cards)

**When to use**: Instead of plain text messages, use interactive cards for calendar invitations, event summaries, or any structured information display.

**⚠️ CRITICAL: Use Tenant Token, NOT User Token**
Interactive cards must be sent via tenant access token (bot identity), not user OAuth token. User token lacks `im:message.send_as_user` scope.

**⚠️ Card JSON Building Pitfall**
Building card JSON inline with curl's `-d` flag is error-prone due to nested escaping. **Best practice: write to a temp file first**:
```bash
cat > /tmp/card.json << 'EOF'
{
  "receive_id": "oc_xxx",
  "msg_type": "interactive",
  "content": "{\"config\":{...}}"
}
EOF
curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/card.json
```

**⚠️ Card Structure Pitfalls (FOUND 2026-06-15)**:
- `column_set` with `background_style` using string padding values (e.g., `"padding":"12px 12px 12px 12px"`) causes parse error 230099
- Stick to simple `div` + `fields` layout — reliable and well-supported
- `@mention` in `lark_md`: use `<at id=ou_xxx></at>` syntax
- Button `multi_url` needs `url`, `pc_url`, `android_url`, `ios_url` keys

**Calendar Invitation Card Template**:
```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "📅 日程邀请"},
    "template": "blue"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "<at id=ou_xxx></at> 收到一条日程邀请 👇"}},
    {"tag": "hr"},
    {"tag": "div", "text": {"tag": "lark_md", "content": "**Event Title**"}},
    {"tag": "div", "fields": [
      {"is_short": true, "text": {"tag": "lark_md", "content": "📅 **日期**\nYYYY年MM月DD日"}},
      {"is_short": true, "text": {"tag": "lark_md", "content": "⏰ **时间**\nHH:MM - HH:MM"}}
    ]},
    {"tag": "div", "fields": [
      {"is_short": true, "text": {"tag": "lark_md", "content": "📍 **场馆**\nLocation"}},
      {"is_short": true, "text": {"tag": "lark_md", "content": "🎫 **票种**\nDetails"}}
    ]},
    {"tag": "hr"},
    {"tag": "action", "actions": [
      {"tag": "button", "text": {"tag": "plain_text", "content": "✅ 接受邀请"}, "type": "primary", "multi_url": {"url": "https://e1kg6bc4dl9.feishu.cn/calendar", "pc_url": "https://e1kg6bc4dl9.feishu.cn/calendar"}},
      {"tag": "button", "text": {"tag": "plain_text", "content": "📋 查看日历"}, "type": "default", "multi_url": {"url": "https://e1kg6bc4dl9.feishu.cn/calendar", "pc_url": "https://e1kg6bc4dl9.feishu.cn/calendar"}}
    ]}
  ]
}
```

**Workflow for Calendar Invitation**:
1. Create calendar event: `lark cal create --summary "..." --start "..." --end "..." --location "..." --reminder 60`
2. Add attendee: `lark cal attendee add <event_id> --user <open_id>` (triggers real Feishu calendar notification)
3. Send interactive card to group with event details + @mention (see template above)
```bash
lark msg history --chat_id oc_xxx --limit 20
lark msg send --to oc_xxx --text "Hello world"
lark msg send --to ou_xxx --text "Hi @{ou_yyy} please review"   # mentions
lark msg send --to oc_xxx --text "Check this: {{image}}" --image /path/to/img.png
lark msg resource --message_id om_xxx    # Download attachments
lark chat search <query>                 # Find chats/groups
```

### Documents (`doc`)
```bash
lark doc get <document_id>              # Get as markdown
lark doc list [folder_token]            # List folder contents (positional arg, NOT --folder_token)
lark doc create --title "My Doc" [--folder folder_token]
lark doc append <document_id> --text "New paragraph"
lark doc search <query>                 # Search across all accessible docs
lark doc wiki <node_token>              # Resolve wiki to doc token
lark doc comments <document_id>
lark doc download <file_token> -o ./output.pdf
```

#### ⚠️ `lark doc list` — Positional Argument, NOT Flag
**`lark doc list` takes folder_token as a positional argument, NOT `--folder_token`:**
```bash
lark doc list PdkOfBF0nlUKlkdVABZcYuKFneh    # ✅ Correct
lark doc list --folder_token PdkOfBF0nlUKlkdVABZcYuKFneh  # ❌ "unknown flag"
```

#### Direct docx creation via API (when `lark doc create` lacks folder support)
```bash
# Create docx in a specific folder (requires drive:drive scope)
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"folder_token":"<folder_token>","title":"Doc Title"}'

# Append text blocks to a document
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_id>/blocks/<doc_id>/children" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"children":[{"block_type":2,"text":{"elements":[{"text_run":{"content":"Hello","style":{}}}]}}]}'
```
⚠️ **Critical**: `text_run` uses `"content"` key, NOT `"text"`. Using `"text"` returns error 99992402.

### Mail (`mail`) — IMAP-based with local SQLite cache
```bash
lark mail setup              # Interactive IMAP config
lark mail sync               # Fetch new emails (supports --workers N)
lark mail search "from:boss" # Fast local search
lark mail show --uid <uid>
lark mail list               # List mailboxes
lark mail status             # Cache status
```

### Other Domains
| Command | Description |
|---------|-------------|
| `lark task ...` | Task management (create, assign, deadlines) |
| `lark sheets ...` | Spreadsheet cell read/write, formulas |
| `lark drive ...` | Cloud space file management |
| `lark meeting ...` | Meeting room booking, recordings |

**⚠️ `lark base` command does NOT exist** — Bitable (多维表格) operations must use direct API calls (curl). See `references/feishu-bitable-api.md` for endpoints, field types, and limitations (no dashboard/chart creation via API, **no view filter/sort/group setting via API** — filters must be configured manually in Bitable UI).

**📎 Downloading files from Feishu file URLs**: Extract the file token from the URL path (e.g., `https://e1kg6bc4dl9.feishu.cn/file/IYLnbGDcuo5KQuxpdDhcw1LLnlb` → token is `IYLnbGDcuo5KQuxpdDhcw1LLnlb`), then use `lark doc download <file_token> -o /path/to/output.ext`. Works with user access token. Content type is returned in the response JSON for identifying the file format.

## Key Architecture Details

- **JSON output by default** — all commands return structured JSON (use `--human` for readable)
- **Mail uses IMAP, not REST API** — local SQLite cache at `~/.lark/mail_cache.db` for O(1) search
- **Credentials**: App ID in `~/.lark/config.yaml`, secret in `LARK_APP_SECRET` env var
- **OAuth tokens**: stored in `~/.lark/tokens.json` (auto-refreshed)
- **Message sending**: supports `\n` line breaks, `@{ou_xxx}` mentions, `{{image}}` placeholders

## User vs Tenant Access Token — Document Ownership (CRITICAL)

### Token Types
| Token Type | Used For | Document Location | Visibility |
|------------|----------|-------------------|------------|
| **Tenant Access Token** (`/auth/v3/tenant_access_token/internal`) | App-level operations, shared resources | App Shared Space | User must manually find in "Shared with me" |
| **User Access Token** (OAuth via `lark auth login`) | User personal documents, "My Space" writes | User's 「云文档-我的文件夹」 | Immediately visible to user |

### ⛔ CRITICAL: bitable:app Scope Required for Write Operations (FOUND 2026-06-12)
The default `bitable` scope group in `internal/scopes/scopes.go` only has `bitable:app:readonly`.
**Writing records, creating fields, or creating Bitable apps requires `bitable:app` (full read-write).**
- **Fix**: Add `"bitable:app"` to the Scopes slice:
  ```go
  "bitable": {
      Scopes: []string{"bitable:app", "bitable:app:readonly"},
      ...
  }
  ```
- Then rebuild: `cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/`
- Re-authorize: `rm -f $LARK_CONFIG_DIR/tokens.json && lark auth login`
- See `references/feishu-bitable-api.md` for full Bitable API patterns and pitfalls

### ⚠️ Tenant Token CANNOT Access User-Owned Folders (FOUND 2026-06-09)
Even with a valid tenant access token, the app **cannot list or access user-owned folders** (e.g., Skills folder `PdkOfBF0nlUKlkdVABZcYuKFneh`, personal folders like "用户小艾").
- **Error**: `1061004 "forbidden"` when calling `GET /drive/v1/files?folder_token=<user_folder>`
- **Reason**: The app was not added as a collaborator to the user folder
- **Workaround**: Create documents in the **Root folder** (`folder_token: ""`) where the app always has write access, then share with the user via permissions API
- **Tenant token CAN**: search docs via Suite API (`POST /suite/docs-api/search/object`), access app-created documents, access shared spaces the app is in
- **Tenant token CAN**: send messages via `POST /im/v1/messages` (bot identity) — this is the ONLY way to send messages (user OAuth token lacks `im:message.send_as_user` scope, error 230027)

### ⚠️ Suite Docs API Search Scope (FOUND 2026-06-09)
The Suite docs API (`POST /open-apis/suite/docs-api/search/object?docs=1`) works with tenant token but **only returns docs the app can see** — not docs in user's personal space. Use this for broad searches but expect gaps in user-owned content.

### ⚠️ Rule: Always use User Access Token for user-visible documents
When creating documents the user needs to find in their personal drive (e.g., 「我的文件夹」, 「我的空间」), you **MUST** use the `User Access Token` from `~/.lark/tokens.json` (obtained via OAuth), NOT the tenant access token.

### OAuth Setup (Headless Server Flow)
1. Run `lark auth login` in background to get authorization URL (redirect to log file).
2. User opens URL in **desktop browser** (Chrome/Edge), NOT mobile or Feishu embedded browser.
3. User clicks 「同意」, browser redirects to callback URL.
4. **If source is patched** (public IP in redirect URI): callback server on 9999 receives the redirect and saves tokens automatically → skip to step 7.
5. **If source is NOT patched** (redirects to localhost): user must copy `code` from URL bar. Kill background process first (`fuser -k 9999/tcp`), then exchange `code` for tokens via `POST /authen/v2/oauth/token`.
6. **Auth codes are one-time use only.** If the code exchange fails (e.g., network retry used the code), the code is dead. Must generate a new authorization URL and re-authorize.
7. Verify with `lark auth status` — should show `authenticated: true`.

### ⚠️ Pitfall: One-Time Auth Code
Feishu authorization codes (`code=XXXX`) are **single-use**. If a network retry or double-call consumes the code before the main handler processes it, you get `invalid_grant` (code 20065). Solution: generate a fresh auth URL, have user re-authorize, and use the new code immediately without retries.

### Creating Documents in Specific Folders

`lark doc create --folder <folder_token>` uses the **user OAuth token** and requires `drive:drive` scope. If it fails with `no folder permission`, ensure:
1. `drive:drive` and `space:folder:create` are in the lark-cli scopes (see scope patch above)
2. User has re-authorized with the new scopes (`rm -f ~/.lark/tokens.json && lark auth login`)

#### ⚠️ Creating in "My Folder" vs Shared Space
When using `lark auth login` (User OAuth), documents created via `lark doc create` **will appear in the user's "My Folder"** if no `folder_token` is specified.
However, if you use a **Tenant Access Token** (App identity), documents **always** go to the App's Shared Space, NOT "My Folder".
To write to a user's personal "My Folder", you **MUST** use a valid `user_access_token` obtained via `lark auth login`.
**Required Scopes for "My Folder" access**: `drive:drive`, `drive:drive:readonly`, `space:folder:create`.

If `lark doc create` still fails, use the tenant access token + direct `docx/v1/documents` API:

```bash
# 1. Get tenant access token
TENANT_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"cli_YOUR_APP_ID\",\"app_secret\":\"$LARK_APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

# 2. Create doc in folder
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"folder_token":"<folder_token>","title":"Doc Name"}'
```

**Adding content to a doc**: Use `content` (not `text`) in `text_run`:
```bash
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"children":[{"block_type":2,"text":{"elements":[{"text_run":{"content":"Hello","style":{}}}]}}]}'
```
⚠️ Field is `content`, NOT `text` — using `text` returns error 99992402.

## Writing Content to Documents

### Method 1: `lark doc append` (RECOMMENDED)
```bash
lark doc append <document_id> --text "Line 1\nLine 2\n### Heading\n- Bullet"
```
- Supports multiline text with `\n` — each line becomes a paragraph block
- Uses user_access_token from `~/.lark/tokens.json`
- Best for: quick content writes, appending to existing docs
- ⚠️ **Comma pitfall**: Numbers with commas (e.g., `¥15,654`) get **split into multiple bullet/text blocks** by the CLI parser. Avoid commas in `--bullet` and `--text` flags — use spaces or remove commas from numbers (write `¥15654` or `15654元` instead of `¥15,654`).

### Method 2: Direct docx API (for bulk writes)
```bash
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_id>/blocks/<doc_id>/children" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"children":[{"block_type":2,"text":{"elements":[{"text_run":{"content":"Hello","style":{}}}]}}]}'
```
⚠️ **Critical**: `text_run` uses `"content"` key, NOT `"text"`. Using `"text"` returns error 99992402.

### 🔴 Drive Folder Creation Endpoint (FOUND 2026-06-04)
The endpoint to create a folder is `POST /drive/v1/files/create_folder` (NOT `/drive/v1/files`).
Payload: `{"folder_token": "", "name": "folder name"}`. Returns `{code: 0, data: {token: "..."}}`.

### 🔴 Drive File Creation — Sheets Only (FOUND 2026-06-04)
`POST /drive/v1/files` with `{"type": "bitable"}` returns 404. Bitable creation requires `bitable:app` or `base:app:create` scope (not available on this app).
`POST /sheets/v3/spreadsheets` works for creating spreadsheets. Sheet write uses `valueRange` (camelCase) at `/sheets/v2/spreadsheets/{token}/values` with PUT.
**Sheet ID** is obtained via `GET /sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query`, not from the creation response. Use this `sheet_id` in the range param (e.g., `"8b6dde!A1:J8"`).

### 🔴 Docx Block Type Limitations with Tenant Access Token (FOUND 2026-06-04)
When using **tenant_access_token** with `POST /docx/v1/documents/{doc_id}/blocks/{doc_id}/children`:
- **Block type 2 (paragraph)** ✅ works — this is the ONLY reliable type with tenant token.
- **Block type 3, 4, 5 (headings)** ❌ fail with `code: 1770001 "invalid param"`.
- **Block type 31 (divider)** ❌ fails with `code: 1770001 "invalid param"`.
- **Block type 2 with `text_element_style.bold: true`** ✅ works — use bold paragraphs as fake headings.

**Workaround**: Use bold paragraph text (`block_type: 2` + `bold: true`) for all content. Do NOT attempt headings or dividers with tenant token.

### 🔴 Drive File Move Returns 404 (FOUND 2026-06-04)
`POST /drive/v1/files/move` with `{"file_token":"...","type":"docx","folder_token":"..."}` returns `404 page not found`.
**Workaround**: Always create documents directly in the target folder using `POST /docx/v1/documents` with `folder_token` in the payload. Never create then move.

### 🔴 Drive Permissions — Add Member Works, Set Public Fails (FOUND 2026-06-04)
- `POST /drive/v1/permissions/{token}/members?type=docx` with `{"member_type":"openid","member_id":"ou_xxx","perm":"full_access"}` ✅ works.
- `PATCH /drive/v1/permissions/{token}/public?type=docx` returns `1063001 "Invalid parameter"` ❌.
- `PUT /drive/v1/permissions/{token}/public?type=sheets` returns `404` ❌.
- **Workaround**: Use `members` API to add specific users with permissions. Link sharing via `public` endpoint is unreliable.
- See `references/feishu-drive-permissions.md` for full details.

### ⚠️ Block Deletion is Unreliable
The `DELETE /docx/v1/documents/{doc_id}/blocks/{block_id}` endpoint returns 404 even for valid blocks. If you need to replace all content in a document:
1. **Delete the document** via `DELETE /drive/v1/files/{doc_id}?type=docx` (if you have permission), then recreate
2. **Or create a new document** and update your mapping — this is more reliable

### 🔴 Drive DELETE Requires `?type=docx` Query Parameter
The `DELETE /drive/v1/files/{doc_id}` endpoint **returns 99992402 "field validation failed"** without the type parameter. Always append `?type=docx` for documents or `?type=folder` for folders:
```bash
# ✅ Correct — document deletion
curl -s -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/{doc_id}?type=docx" \
  -H "Authorization: Bearer <token>"

# ✅ Correct — folder deletion
curl -s -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/{folder_id}?type=folder" \
  -H "Authorization: Bearer <token>"

# ❌ Wrong — returns 99992402 "field validation failed"
curl -s -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/{doc_id}" ...
```

### Feishu Sheets API
For spreadsheet creation and cell writing, see `references/feishu-sheets-api.md`. For cell styling (bold, colors, wrap text), see `references/feishu-sheets-styling.md`. Key gotchas:
- `POST /drive/v1/files` does NOT work for bitable/sheets — use `POST /sheets/v3/spreadsheets`
- Must query sheet_id first via `GET /sheets/v3/spreadsheets/{token}/sheets/query` before writing
- `valueRange` (camelCase) required, and range must use `sheet_id` not `spreadsheet_token`
- Styling uses `appendStyle` (NOT `updateStyle`) — using `updateStyle` returns error 9499
- Column width adjustment via `dimension_range` endpoint returns 404 — not supported via API

### ⚠️ `lark doc get` Returns Escaped Markdown
The `lark doc get` API output contains escaped markdown characters (e.g., `\#`, `\*`, `\&#34;` instead of `"`, `\_` instead of `_`). This is an API-level encoding artifact — **the actual content in the Feishu web UI renders correctly**. Do not try to "unescape" the API output; it's only relevant for programmatic comparison. When verifying content, trust the web UI view or use `lark doc blocks` for structured inspection.

### 🔴 `lark doc blocks` Can Time Out on This Server (FOUND 2026-06-05)
The `lark doc blocks <doc_id>` command **may hang indefinitely** on this server. Use the direct API as a reliable fallback:
```bash
export LARK_CONFIG_DIR="$HOME/.lark"
USER_TOKEN=$(python3 -c "import json; f=open('$HOME/.lark/tokens.json'); d=json.load(f); print(d['access_token'])")
curl -s "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_id>/blocks/<doc_id>/children?page_size=100" \
  -H "Authorization: Bearer $USER_TOKEN"
```
This returns the same block structure in JSON and completes within seconds.

### Agent Profile/Memory File Locations on This Server
```
~/.hermes/memories/MEMORY.md          # Default profile (黑执事) memory
~/.hermes/memories/USER.md            # Default profile user info
~/.hermes/profiles/hr-assistant/SOUL.md          # 凛子小姐 profile
~/.hermes/profiles/hr-assistant/memories/USER.md # 凛子小姐 user info
~/.hermes/profiles/hr-assistant/memories/MEMORY.md # 凛子小姐 memory (may be empty)
~/.hermes/profiles/data-master/SOUL.md           # 数据大师 profile
~/.hermes/profiles/data-master/memories/         # 数据大师 memory (directory may be empty)
```

## Token Lifecycle & Keep-Alive

### Token Validity
- **access_token**: 2 hours, auto-refreshed by lark-cli when expired
- **refresh_token**: 7 days, **ONE-TIME USE** — once consumed (by any refresh call), it is revoked by Feishu server
- ⚠️ `refresh_token_expires_at` in `tokens.json` becomes STALE after use — may show future date while token is already dead

### Diagnostic: Verify Token Actually Works
`tokens.json` timestamps can be stale/misleading. Confirm with an actual API call:
```bash
LARK_CONFIG_DIR="$HOME/.lark" LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)" lark doc list 2>&1
```
If response contains `code 20064: The refresh token has been revoked`, the token is dead even if `refresh_token_expires_at` shows a future date.

### Keep-Alive Strategy (UPDATED 2026-06-17)
1. **Token pre-refresh**: System crontab (`0 * * * *`) runs `~/.hermes/scripts/lark_token_refresh.py` every hour — zero LLM cost, 1-2 seconds execution
   - Covers both profiles: default (黑执事) + hr-assistant (凛子小姐)
   - Skips refresh if access_token has > 30 min remaining
   - Writes results to `~/.hermes/logs/lark_token_refresh.log` and `~/.hermes/logs/lark_token_alert.json`
2. **Alert cron**: Lightweight Hermes cron daily at 9:00 reads `lark_token_alert.json`, sends Feishu notification only if `needs_attention` is non-empty
3. **No more skill-based keep-alive cron jobs** — replaced by system crontab (old approach consumed ~5000 LLM tokens per run, every 3 days)

**Script location**: `scripts/lark_token_refresh.py` (also deployed at `~/.hermes/scripts/lark_token_refresh.py`)
**Crontab**: `0 * * * *` (every hour on the hour)
**Alert cron**: `飞书 Token 异常预警` (job `4a4f6b4f9e54`), daily 09:00, reads `~/.hermes/logs/lark_token_alert.json`

### ⚠️ Multiple Token Files Can Desync
- `~/.lark/tokens.json` (system-level) and `~/.hermes/profiles/<profile>/home/.lark/tokens.json` (Hermes profile) are INDEPENDENT files
- System-level may hold stale/revoked tokens while profile copy has fresh ones (or vice versa)
- When diagnosing token issues, check BOTH files and compare

### ⚠️ `lark auth status` Unreliability
- `scope_groups` can show `documents: false` even when most doc scopes ARE granted
- `refresh_token_expires_at` shows `0001-01-01T00:00:00Z` despite actual value being in `tokens.json`
- **Always check `tokens.json` directly** as source of truth: `cat $LARK_CONFIG_DIR/tokens.json | python3 -m json.tool`
- Trust `authenticated: false` as accurate indicator of dead refresh_token

---

### Feishu Sheets Styling API

Use `appendStyle` (NOT `updateStyle`) to style cells. The `PUT /sheets/v2/spreadsheets/{token}/style` endpoint:
```bash
curl -s -X PUT "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{token}/style" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"appendStyle":{"range":"{sheet_id}!A1:G1","style":{"bold":true,"backColor":"#4472C4","foreColor":"#FFFFFF"}}}'
```
- ⚠️ Key is `appendStyle`, NOT `updateStyle` — using `updateStyle` returns 9499 "Missing required parameter: AppendStyle"
- Style properties: `bold`, `backColor`, `foreColor`, `fontSize`, `wrapText`
- Colors use hex format: `"#4472C4"`, `"#FFFFFF"`, `"#FFF2CC"`
- `wrapText: true` for cells with `\n` line breaks

### 🔴 Cross-App Open ID for Calendar Attendees (FOUND 2026-06-18)
When adding attendees to calendar events, **open_id must match the app that created the calendar event**:
- If calendar event created with App A's token → attendee open_id must be from App A
- Using open_id from App B (e.g., data-master) → error 99992361 "open_id cross app"
- **Fix**: Get the attendee's open_id via the same app used to create the event, or use `union_id` (cross-app) with `user_id_type=union_id`
- **Workaround**: If cross-app, send a @mention message in group chat instead — bot in the shared group can @ anyone regardless of app

### 🔴 Bot DM Availability (FOUND 2026-06-18)
`POST /im/v1/messages` to a user via open_id returns 230013 "Bot has NO availability to this user" when:
- User is not in the bot's contact scope
- User hasn't interacted with the bot
- **Workaround**: Send message in a shared group chat where both bot and user are members (works reliably)

## Pitfalls

- **🔴 Bitable Creation Requires `bitable:app` Scope (PATCHED 2026-06-12)**:
  - The default `bitable` scope group only had `bitable:app:readonly` — **read-only, cannot create or write Bitables**.
  - Creating a Bitable (`POST /bitable/v1/apps`) returns `99991679 Unauthorized` with `required privileges: [bitable:app, base:app:create]`.
  - **Fix**: Add `"bitable:app"` to the Scopes slice in `~/lark-cli/internal/scopes/scopes.go`:
    ```go
    "bitable": {
        Scopes: []string{"bitable:app", "bitable:app:readonly"},
    ```
  - Rebuild: `cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/`
  - Re-authorize: `rm -f $LARK_CONFIG_DIR/tokens.json && lark auth login`
  - The user must also enable `bitable:app` permission in the Feishu app console and publish a new version.

- **🔴 `$HOME` in Hermes profiles resolves to profile home, NOT `/home/ubuntu` (FOUND 2026-06-15)**:
  - When running inside a Hermes profile (e.g., `hr-assistant`), `$HOME` is already set to `/home/ubuntu/.hermes/profiles/hr-assistant/home`.
  - So `$HOME/.hermes/profiles/hr-assistant/home/.lark` becomes a double-nested path that **does not exist**.
  - **Correct value**: Simply `export LARK_CONFIG_DIR="$HOME/.lark"` — this resolves to the profile's `.lark/` directory.
  - The per-profile paths in the "Configure" section above are **absolute paths for reference only** — always use `$HOME/.lark` at runtime.
- **Feishu vs Lark region**: Set `region: "feishu"` in config for China users, otherwise API calls fail silently
- **🔴 Remote/Cloud Server Auth (CRITICAL — Source Patch Required)**:
  - `lark auth login` starts a callback server on port **9999**.
  - The source code (`internal/auth/server.go`) **hardcodes `localhost`** in `GetRedirectURI()`:
    ```go
    return fmt.Sprintf("http://localhost:%d/callback", s.port)
    ```
  - **This means on a cloud server, OAuth will ALWAYS redirect to localhost (the user's device), not the server.**
  - **FIX**: Patch `GetRedirectURI()` to use the server's public IP:
    ```bash
    sed -i 's|http://localhost:%d/callback|http://<YOUR_PUBLIC_IP>:%d/callback|' ~/lark-cli/internal/auth/server.go
    cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/
    ```
  - After patching, the **Redirect URL in Feishu console MUST match EXACTLY**: `http://<YOUR_PUBLIC_IP>:9999/callback`
  - **Error 20043**: Means "Redirect URI mismatch". Check that the URL in Feishu console matches the link EXACTLY (no trailing slashes).
  - **After changing Feishu app settings (permissions, Redirect URL, etc.), you MUST create a new version and publish it.**
- **🔴 LARK_CONFIG_DIR is MANDATORY**:
  - Without `export LARK_CONFIG_DIR="$HOME/.lark"`, **every lark command fails** with `{"code": "CONFIG_ERROR", ...}`.
  - Add it to `~/.bashrc` for persistence across sessions.
  - `LARK_APP_SECRET` must also be exported as an env var (not in config.yaml) — add both to `~/.bashrc`.
- **🔴 Missing `drive:drive` scope in default `documents` group**:
  - The `documents` scope group in `internal/scopes/scopes.go` originally only had `drive:drive:readonly` (read-only).
  - **`drive:drive` (full read-write)** is required for creating folders in user's personal drive space.
  - **`space:folder:create`** is also needed for folder creation.
  - **Fix**: Add both scopes to the documents group in `internal/scopes/scopes.go`:
    ```go
    Scopes: []string{..., "drive:drive", "drive:drive:readonly", ..., "space:folder:create"}
    ```
  - Then rebuild: `cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/`
  - Re-authorize: `rm -f ~/.lark/tokens.json && lark auth login`
- **⚠️ Feishu Drive Visibility (My Folder vs Shared Space)**:
  - Documents created by an **App (Tenant Token)** are **owned by the App** and will appear in the user's **"Shared with me" (与我共享)** list, NOT in "My Space" (云文档-我的文件夹).
  - **User Expectation**: Users often expect files to appear in their "My Space".
  - **Workaround**:
    1. Inform the user to check "Shared with me" or use the direct link.
    2. Ask the user to manually move the file to their "My Space" after creation.
    3. If **User Access Token (OAuth)** is available (via `lark auth login`), the doc **will** be created in the user's "My Space" (specifically the root folder unless a `folder_token` is specified).
- **⚠️ Version Publishing**:
  - After changing **ANY** settings (permissions, Redirect URL, etc.), you **MUST create a new version and publish it**.
  - If you don't publish, the CLI will still use the old configuration and fail silently or with permission errors.
- **Open ID is per-app**: A user's Open ID in one Feishu app differs from another app — always verify with `lark contact get`
- **Port 9999 conflict**: If `lark auth login` fails with "address already in use", a previous auth process is zombie. Fix: `fuser -k 9999/tcp` then retry
- **🔧 `minutes:minute:download` Permission Unavailable (FIXED)**:
  - The `minutes:minute:download` scope (in `internal/scopes/scopes.go` line 57) **is not available** in this Feishu app, causing the OAuth authorization page to fail with "权限无法开通" (permission cannot be enabled).
  - **Fix**: Remove it from the minutes scope group:
    ```bash
    # Edit ~/lark-cli/internal/scopes/scopes.go — change line 57:
    #   Scopes: []string{"minutes:minutes:readonly", "minutes:minute:download"}
    # To:
    #   Scopes: []string{"minutes:minutes:readonly"}
    # Then rebuild:
    cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/
    ```
  - After patching, kill any existing auth process (`fuser -k 9999/tcp`), restart `lark auth login`, and retry.
- **Mobile Browser Issues**:
- **⚠️ OAuth Code 一次性消耗陷阱（新增 2026-06-04）**:
  - 飞书授权码（`code`）**只能使用一次**。如果 `lark auth login` 后台进程或手动 curl 其中一方先消耗了 code，另一方会收到 `20065 invalid_grant` 错误。
  - **症状**：`lark auth login` 在后台运行并可能自动尝试交换 code，导致用户手动提供的 code 被标记为已使用。
  - **修复**：在手动交换 code 前，**必须先 kill 掉 `lark auth login` 后台进程**：
    ```bash
    fuser -k 9999/tcp 2>/dev/null  # 杀掉 lark auth 监听进程
    # 然后再用 curl 手动交换 code
    ```
  - **推荐流程**：使用纯手动 curl 交换（Auth Method 2），不要依赖 `lark auth login` 的自动回调机制，因为云端环境下回调服务器不可靠且会抢消耗 code。

- **🔴 OAuth Refresh Token 只能用一次 + access_token 2h 有效期（新增 2026-06-05）**
  - 飞书的 **refresh_token 只能用一次**，调用刷新接口后即被吊销。如果刷新失败（`20064 invalid_grant`），必须重新走完整 OAuth 流程。
  - `lark auth login` 后台进程可能在其内部自动调用刷新接口，**消耗掉你手动写入的 refresh_token**。
  - **症状**：手动 curl 交换到 code 后写入 tokens.json，之后尝试刷新时返回 `invalid_grant`。
  - **修复**：
    1. 拿到 code 后，**手动 curl 交换 token 前，必须先 `fuser -k 9999/tcp` 杀掉所有 lark auth 后台进程**，防止它偷偷刷新
    2. 写入 tokens.json 后，**立刻用 access_token 执行目标操作**，不要等待
    3. access_token 有效期仅 **2 小时**（7200 秒），超时返回 `99991677 Authentication token expired`
    4. 如果操作预计超过 2 小时，应在过期前主动刷新 refresh_token

  - **推荐流程（避免 refresh_token 被吃）**：
    ```bash
    # 1. 杀掉所有 lark auth 相关进程
    fuser -k 9999/tcp 2>/dev/null
    pkill -f "lark auth" 2>/dev/null

    # 2. 手动 curl 交换 code
    curl -s -X POST "https://open.feishu.cn/open-apis/authen/v2/oauth/token" \
      -H "Content-Type: application/json; charset=utf-8" \
      -d '{"grant_type":"authorization_code","client_id":"cli_XXX","client_secret":"$LARK_APP_SECRET","code":"CODE_FROM_USER","redirect_uri":"http://YOUR_IP:9999/callback"}'

    # 3. 写入 tokens.json（注意 expires_at 计算正确）

    # 4. 立即用 access_token 执行操作，不要拖延
    ```

- **⚠️ Cross-Profile Token Fallback (FOUND 2026-06-22)**:
  - In multi-agent setups, a specific profile's OAuth may be expired while the **default profile's token is still valid**.
  - Example: `data-master` profile shows `authenticated: false`, but `default` profile (`/home/ubuntu/.lark`) has a live token and can access the same docs.
  - **Diagnostic step**: When a profile's auth fails, try `export LARK_CONFIG_DIR="/home/ubuntu/.lark"` (default profile) as a fallback before re-authenticating.
  - Both profiles share the same Feishu tenant, so the default profile's user_access_token has access to docs owned by the same user across all profiles.
  - This avoids unnecessary re-auth flows when only one profile's token is stale.

- **🔴 Calendar 事件 Unix 时间戳计算必须精确（新增 2026-06-05）**
  - 飞书日历 API 的 `start_time`/`end_time` 使用 **Unix epoch timestamp（秒级）**，不是 ISO 日期字符串。
  - **手工估算极易出错**（如算成 2025 年的日期）。
  - **正确做法**：用 Python `datetime` 精确计算，指定 `tzinfo=timezone(timedelta(hours=8))`：
    ```python
    from datetime import datetime, timezone, timedelta
    CST = timezone(timedelta(hours=8))
    dt = datetime(2026, 6, 13, 12, 0, tzinfo=CST)
    timestamp = str(int(dt.timestamp()))  # 精确的秒级时间戳
    ```
  - 创建日历事件前，**先用 `lark cal list --from YYYY-MM-DD --to YYYY-MM-DD` 验证当前日历可见范围**，确保时间正确。

## References
- Cloud server setup & source patch: `references/cloud-server-setup.md`
- Headless OAuth: `references/headless-auth.md`
- Build notes: `references/build-notes.md`
- Feishu API patterns (create folder/doc, append content, token types): `references/feishu-api-patterns.md`
- Feishu Drive permissions behavior (add member vs set public, file move): `references/feishu-drive-permissions.md`
- Feishu Sheets API (create, write cells, sheet_id query): `references/feishu-sheets-api.md`
- **Feishu OAuth gotchas (refresh token single-use, app_id/secret mismatch)**: `references/feishu-oauth-gotchas.md`
- **Token access patterns (tenant vs user, folder permissions, troubleshooting)**: `references/feishu-token-access.md`
- **OAuth code exchange with passive listener (no lark auth competition)**: `references/feishu-oauth-code-exchange.md`
