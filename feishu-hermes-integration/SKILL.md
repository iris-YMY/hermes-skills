---
name: feishu-hermes-integration
category: devops
description: Feishu/Lark integration with Hermes Agent — deployment SOP, multi-agent setup, diagnostics, cron isolation, and operational workflows.
---

# Feishu/Lark + Hermes Agent Integration

Complete guide for deploying, configuring, and troubleshooting Hermes Agent with Feishu/Lark messaging platform. Covers single and multi-agent setups, profile isolation, cron job management, and diagnostics.

---

## 1. Profile Configuration & Deployment SOP

### Profile Setup
- **Create**: `hermes profile create <name>`
- **Config files**:
  - `.env` in profile dir: Feishu App ID/Secret, `FEISHU_ALLOWED_USERS`
  - `config.yaml`: Model Provider and API Key
  - `SOUL.md`: Agent persona
- **Start**: `hermes -p <name> gateway restart`

### Credential Loading Priority
1. **Per-profile `.env`**: `~/.hermes/profiles/<name>/.env` (recommended, isolated)
2. **Global `.env`**: `~/.hermes/.env` (fallback, shared by all profiles)

If profile has no `.env`, it inherits global config.

### Environment Variables
```bash
FEISHU_APP_ID=cli_xxxxx           # Feishu App ID
FEISHU_APP_SECRET=xxxxx            # Feishu App Secret
FEISHU_DOMAIN=feishu               # Domain (feishu=lark, lark=lark)
FEISHU_CONNECTION_MODE=websocket   # Connection mode
FEISHU_ALLOW_ALL_USERS=false       # Allow all users
FEISHU_ALLOWED_USERS=ou_xxxxx      # Allowed user IDs (comma-separated)
FEISHU_GROUP_POLICY=open           # Group policy
FEISHU_HOME_CHANNEL=oc_xxxxx       # Home channel ID (optional)
```

### Feishu Backend Setup (Critical Order)
1. Enable "App Functionality -> Robot" (应用功能 -> 机器人)
2. "Event Subscription" (事件订阅): Add `im.message.receive_v1`. **Leave URL empty** (uses long connection)
3. "Permissions" (权限管理): Enable `im:message`, `im:message:send_as_bot`, `im:chat:readonly`
4. **Version Release (Crucial)**: After ANY config change, MUST create a new version and publish in "Version Management & Release" (版本管理与发布), otherwise changes won't take effect!

---

## 2. Open ID Mechanism

- **App-Bound**: Open ID (`ou_...`) is bound to the specific App ID, not the user globally
- Different apps get different Open IDs for the same user
- **Known IDs**:
  - 小艾(Iris)/HR助手 App (`cli_aa9ebcbfc6e35cba`): `ou_9ad597120b1fb0c113f4ebc7b27527d4`
  - Kimy(李昊龙)/HR助手 App (`cli_aa9ebcbfc6e35cba`): `ou_9af5f46df9657438e37f5cac3f27598b` (added 2026-06-24)
  - 小艾(Iris)/数据大师 App (`cli_aa9ea34aaff85cda`): `ou_45b9fa03f5b8a239ea1b395f50c16b58`
  - 小艾(Iris)/理财大师 App (`cli_aa9e8a8423785cb0`): `ou_77692bfe69b5b961f0bf40dc8f871d83` (added 2026-06-29)
- **Troubleshooting**: If `Unauthorized user` on new profile, extract the Open ID from `errors.log` and add to `FEISHU_ALLOWED_USERS` in the profile's `.env`, then restart gateway

---

## 3. Diagnostic Workflow

When an Agent doesn't reply to messages, follow this sequence:

### Quick All-Profile Health Check (3-command recipe)
When diagnosing which gateways are alive/dead across all profiles, run these three commands in parallel:

```bash
# 1. Running processes
ps aux | grep 'hermes_cli.main.*gateway' | grep -v grep

# 2. Listening ports
ss -tlnp | grep -E "864[0-9]"

# 3. Configured ports per profile
for p in ~/.hermes/profiles/*/config.yaml; do
  profile=$(echo $p | sed 's|.*/profiles/||;s|/config.yaml||')
  port=$(grep "port:" "$p" | head -1 | awk '{print $2}')
  echo "$profile → port $port"
done
# Also check main config:
grep "port:" ~/.hermes/config.yaml
```

Cross-reference the three outputs:
- **Process exists + port listening** → ✅ Healthy
- **No process + no port but gateway_state.json says "running"** → ⚠️ Zombie state (process died, state file stale)
- **Process exists + no port** → 🔴 Startup conflict (port already taken)
- **No process + config exists** → ⏸️ Gateway not started

### Quick Scan: Check all listening ports
```bash
ss -tlnp | grep -E "864[0-9]"
```
This instantly reveals which gateways/webhooks are actually listening. Cross-reference with `~/.hermes/config.yaml` and profile directories to spot gaps (configured but not running).

### Quick Scan: List all existing profiles
```bash
ls ~/.hermes/profiles/
```
This instantly reveals which agents are configured. If the agent name isn't listed, skip to Step 0.

### Quick Scan: List all systemd units
```bash
systemctl --user list-unit-files | grep hermes
```
Profiles need BOTH a directory in `~/.hermes/profiles/` AND a systemd unit `hermes-gateway-<name>.service` to be restartable via `hermes gateway start`. If the unit is missing, the profile can only be started via direct process: `hermes --profile <name> gateway run --replace`.

### Step 0: Verify profile exists (CRITICAL — check THREE layers)
A profile can appear in `hermes profile list` but be completely broken. You MUST check all three layers:

```bash
# Layer 1: Profile registry (may show ghosts)
hermes profile list

# Layer 2: Profile directory on disk (config files)
ls -d ~/.hermes/profiles/<name>/ 2>/dev/null && echo "EXISTS" || echo "MISSING"

# Layer 3: systemd unit (needed for hermes gateway start)
systemctl --user list-unit-files | grep "hermes-gateway-<name>"
```

⚠️ **CRITICAL PITFALL — Ghost Profiles**: `hermes profile list` reads from a registry/cache and will show profiles that no longer have config files on disk. A profile can be "registered" but completely non-functional. Always verify with `ls -d ~/.hermes/profiles/<name>/` and check that `config.yaml` or `.env` actually exists.

⚠️ **CRITICAL PITFALL — Orphaned systemd Units**: The systemd unit file may survive even when the profile directory is deleted. `systemctl --user start hermes-gateway-<name>` will fail with exit code 5 if the profile config is missing. Conversely, the profile dir may exist but no systemd unit — in that case, start manually: `hermes --profile <name> gateway run --replace`.

If profile directory is `MISSING`, the agent was deleted or never created. Check historical sessions to determine if it was ever configured. Recreate with `hermes profile create <name>` and reconfigure from scratch.

### Step 1: Check gateway_state.json
```bash
cat ~/.hermes/profiles/<name>/gateway_state.json
```
Key fields: `gateway_state`, `platforms.feishu.state`, `platforms.feishu.error_code`

### Step 2: Check errors.log (MOST IMPORTANT)
```bash
tail -n 50 ~/.hermes/profiles/<name>/logs/errors.log
```

| Log Signal | Meaning | Fix |
|------------|---------|-----|
| `Unauthorized user: ou_xxxx on feishu` | User not in `FEISHU_ALLOWED_USERS` — message silently dropped (gateway still shows `connected`!) | Add user ID to `FEISHU_ALLOWED_USERS`, restart gateway |
| `feishu_app_lock` + PID | Another Hermes instance holds this App ID | Check PID: is it another profile or a "wild" process? |
| `Gateway hit a non-retryable startup conflict` | Multi-platform conflict at startup | Resolve conflicts, restart |

### Step 3: Check for "wild" gateway processes
```bash
ps aux | grep 'hermes_cli.main' | grep -v 'profile' | grep -v grep
```
A process without `--profile` uses global `.env` and may steal a profile's App ID. Kill it.

### Step 4: Check running profile processes
```bash
ps aux | grep hermes | grep 'profile' | grep -v grep
```

### Step 5: Verify App ID uniqueness
```bash
grep FEISHU_APP_ID ~/.hermes/.env
grep FEISHU_APP_ID ~/.hermes/profiles/*/.env 2>/dev/null
```
No two profiles should share the same App ID (triggers `feishu_app_lock`).

### ⚠️ Hidden Trap: Connected but Not Replying
When `gateway_state.json` shows `feishu: connected` but Agent doesn't reply, **99% it's an `Unauthorized user` issue**. Gateway connects fine, but messages are blocked at entry — won't appear in agent.log. **Must check errors.log**.

### Troubleshooting User Access Issues (ADDED 2026-06-25)
When user reports "X @ you but no response" or asks "is X in the allowed list":

**Step 1: Check FEISHU_ALLOWED_USERS**
```bash
cat ~/.hermes/profiles/<name>/.env | grep FEISHU_ALLOWED_USERS
```
Parse the comma-separated list of `ou_` IDs.

**Step 2: Verify Gateway Restart Time**
```bash
ps aux | grep 'hermes_cli.main.*--profile <name>' | grep -v grep
```
Check the `STARTED` column. If gateway started BEFORE the user was added to `FEISHU_ALLOWED_USERS`, the config hasn't loaded yet — gateway restart required.

**Step 3: Use session_search for Historical Context**
```
session_search(query="<user_id> OR allowed_users OR <username>")
```
This reveals when users were added, who requested it, and any related configuration changes. Much faster than guessing or asking the user to repeat themselves.

**Step 4: Identify Users (LIMITED)**
- **Don't rely on contact API**: `GET /contact/v3/users/<ou_id>` requires `contact:contact.base:readonly` scope (not granted for hr-assistant app)
- **Alternative**: Match `ou_` IDs against known mappings in this skill's "Open ID Mechanism" section
- **If ID not in known list**: Ask user directly, or check `errors.log` for "Unauthorized user: ou_xxx" messages which show the ID of rejected users

**Step 5: Search Gateway Log for User's Messages (CRITICAL DIAGNOSTIC 2026-06-25)**
```bash
cd / && grep -c "ou_<USER_ID>" ~/.hermes/profiles/<name>/logs/gateway.log
cd / && grep "ou_<USER_ID>" ~/.hermes/profiles/<name>/logs/gateway.log | tail -5
```
This is the **definitive test** for whether messages reach the gateway at all:

| Result | Meaning | Action |
|--------|---------|--------|
| Messages found in log | Gateway received them → check if dropped by allowlist | Check `errors.log` for "Unauthorized user" |
| **Zero messages in log** | Messages never reached gateway → **Feishu platform issue** | See "Feishu Platform-Level Message Loss" below |

⚠️ Use `cd /` before grep — log paths can get doubled by CWD issues (e.g., `~/.hermes/profiles/<name>/home/.hermes/...`).

### Feishu Platform-Level Message Loss (CONFIRMED 2026-06-25)
When `gateway.log` shows **zero messages from a whitelisted user**, the issue is upstream of Hermes — Feishu never delivered the message to the WebSocket.

**Common causes:**
1. **Improper @-mention**: User typed "at" or "@botname" as plain text instead of using Feishu's native @-mention picker (name should turn blue/highlighted). Plain text mentions do NOT trigger `im.message.receive_v1`.
2. **Missing event subscription**: Feishu app needs `im.message.receive_v1` event configured (see §1 Feishu Backend Setup Step 2). Without it, group messages are not pushed to the bot.
3. **Bot not in group**: Bot must be added to the group chat. Check via `/im/v1/chats` API.
4. **Version not published**: After adding/modifying event subscriptions, MUST publish a new version in "版本管理与发布" (see §1 Step 4).

**Quick verification**: Ask the user to have the other person @-mention the bot using the **@ picker** (select bot name from dropdown, not typing text). If still no log entry → check Feishu open platform event subscription configuration.

**Common Scenario**: User added someone yesterday, but gateway hasn't been restarted → config not loaded → messages still blocked. Always verify gateway restart time matches or postdates the config change.

### ⚠️ Timestamp Interpretation
`gateway_state.json` timestamps are **ISO 8601 UTC** (`2026-05-26T10:13:10.633569+00:00`), NOT local time. Use `updated_at` to determine how recently a gateway connected or errored. If the timestamp is days old and `gateway_state` is stale, the process may be a zombie — verify with `ps aux`.

### 📜 Historical Investigation for Missing Agents
If a profile directory is gone but the user references a known agent:
- Search logs: `grep -r "<agent-name>" ~/.hermes/profiles/*/logs/gateway.log` to find historical mentions
- Check `session_search` for past configuration sessions
- Look for old `.env` or profile configs that may have been migrated or deleted
- The `channel_directory.json` in each profile shows which Feishu chats the agent has interacted with

### ⚠️ Cross-Organization Contact Limitation (CONFIRMED 2026-06-17)
**Kimy (李昊龙/OMD-Kimy) is NOT in the same Feishu organization as Iris.** This means:
- `GET /search/v1/user?query=Kimy` returns empty (both user token and tenant token)
- `POST /contact/v3/users/batch_get_id` requires `contact:user.id:readonly` scope (not granted)
- Cannot add Kimy as a calendar attendee via `lark cal attendee add`
- Cannot send Kimy direct messages or calendar invitation cards via Feishu

**Workaround when user asks to "send a schedule/invitation to Kimy":**
1. Create the calendar event on Iris's own calendar (she'll see it)
2. Inform user that Kimy isn't in the workspace — suggest manual sharing or WeChat notification
3. If Kimy's email is known, could potentially invite via email attendee (untested)

### Error Codes
| Error Code | Cause | Fix |
|------------|-------|-----|
| `feishu_app_lock` | Another Hermes instance holds App ID | Stop conflict, or use unique App ID |
| `weixin-bot-token_lock` | WeChat Bot Token conflict | Same as above |
| `1770032 forBidden` | Doc not shared with app — tenant token cannot read | User must share doc with app as collaborator, OR use User OAuth token (`lark doc get <doc_id>`), OR user pastes content directly |
| `99991672 Access denied` (Bitable) | App lacks `bitable:app` or `base:app:create` scope | Authorize at `https://open.feishu.cn/app/{APP_ID}/auth?q=bitable:app` — required for creating/writing Bitable apps via REST API (viral-video-studio asset library, etc.) |
| No error but state=stopped | Gateway not started | `gateway restart` |

---

## 4. Gateway Conflicts & Wild Processes

- Each profile must use a **unique Feishu App ID**. Sharing IDs triggers `feishu_app_lock`
- **Wild gateway**: Process running `hermes gateway run` **without `--profile`** uses global `.env` and may steal a profile's App ID
- **TERMINAL_CWD warning**: `.env` with `TERMINAL_CWD=/home/ubuntu` produces startup warnings. Move to `config.yaml` under `terminal.cwd` and remove from `.env`

---

## 5. Cron Job Isolation

### Architecture
| Location | Read By | Isolation |
|----------|---------|-----------|
| `~/.hermes/cron/jobs.json` | Default profile only (no `--profile`) | Global scope |
| `~/.hermes/profiles/<name>/cron/jobs.json` | Only that profile's gateway | Profile-specific |

### Identity Guard Template
Add this block at the **end** of every cron job's prompt:

**Default profile (no --profile flag):**
```
## AGENT IDENTITY
- **Name**: [Agent Name] (Default Profile)
- **Profile**: Default (no --profile flag)
- **Action**: Only execute if running as the default profile (i.e., NO --profile flag). If running as any named profile, skip.
```

**Named profile (e.g., data-master):**
```
## AGENT IDENTITY
- **Name**: [Agent Name]
- **Profile**: [profile-name]
- **Action**: Only execute if running as '[profile-name]' profile (i.e., --profile [profile-name] flag present). If running as any other profile, skip.
```

### ⚠️ Orphaned Cron on Profile Deletion
When deleting a profile (`rm -rf ~/.hermes/profiles/<name>/`), its cron jobs remain in `~/.hermes/cron/jobs.json` and run on the default profile as orphans. They self-skip if they have AGENT IDENTITY guards, but waste execution cycles. **Always clean up cron before deleting a profile.**

### Profile Deletion Checklist
1. Check for orphaned cron: `cat ~/.hermes/cron/jobs.json` — clean up or migrate the profile's jobs
2. Confirm skills safety: All profiles share the same skills directory (same inode), deleting a profile does NOT affect skills
3. Confirm process stopped: `ps aux | grep 'hermes_cli.main' | grep '<name>'`

---

## 6. Logs & Debugging

| Log | Path | Purpose |
|-----|------|---------|
| Gateway Log | `~/.hermes/profiles/<name>/logs/gateway.log` | General gateway activity |
| Error Log | `~/.hermes/profiles/<name>/logs/errors.log` | **Most important for diagnosing message delivery issues** |
| System Log | `journalctl --user -u hermes-gateway-<name> -f` | Systemd-level logs |

---

## 7. Architecture Facts

- **Skills sharing**: All profiles' `skills/` dirs point to the same physical directory (same inode), not symlinks. Any skill created in any profile is globally visible.
- **Cron isolation**: Each profile has an independent `cron/` dir. Global `~/.hermes/cron/` is the default profile's cron.
- **External skills dir**: `~/.agents/skills/` is configured in `external_dirs` but currently empty. Skills live in `~/.hermes/skills/`.
- **read_file path bug**: Using `~/.hermes/profiles/<name>/.env` paths, `read_file` may double the path. Use absolute `/home/ubuntu/.hermes/profiles/<name>/.env` or `search_files` instead.
- **Credentials in .env only**: Never store credentials in memory. Memory content is injected into every system prompt — leakage risk.
- **Email integration**: For connecting external email (163, Gmail, QQ Mail) into Feishu — including Feishu Mail enablement, Hermes email bridge pattern, and Chinese provider IMAP/SMTP settings, see `references/feishu-email-integration.md`.

---

## 8. lark-cli Tool Reference

The full `lark-cli` Go CLI tool reference (11 business domains: calendar, contacts, docs, messages, mail, drive, wiki, tasks, sheets, base, meetings) is in `references/lark-cli-reference.md`. Key integration notes:
- lark-cli requires `LARK_CONFIG_DIR` and `LARK_APP_SECRET` env vars (both mandatory)
- Cloud server auth requires patching `internal/auth/server.go` to use public IP instead of localhost
- After ANY Feishu app config change, MUST publish a new version
- Open ID is per-app — a user's Open ID differs across Feishu apps
- Token management: see `references/feishu-oauth-gotchas.md`, `references/feishu-token-access.md`, `references/headless-auth.md`
- Bitable API patterns: see `references/feishu-bitable-api.md`
- Docx image upload & embedding: see `references/feishu-docx-image-upload.md` — ⛔ `im/v1/images` keys cannot embed in docx; must use `drive/v1/medias/upload_all` (needs `drive:drive` scope)
- Sheets API: see `references/feishu-sheets-api.md` and `references/feishu-sheets-styling.md`
- Drive permissions: see `references/feishu-drive-permissions.md`
- Docx block API (create + update blocks): see `references/feishu-docx-blocks.md` — ⚠️ heading2/heading3 blocks fail, use bold text workaround; ⚠️ block PATCH (update) requires User OAuth token, tenant token gets 403; ⚠️ image blocks (type 27) require 3-step method — see `references/feishu-docx-image-embedding.md`
- Script for creating Feishu docx from markdown: `scripts/create_feishu_docx.py`
- Script for batch image embedding: `scripts/embed_docx_images.py` — 3-step method for embedding images into docx
- Reference for image embedding: `references/feishu-docx-image-embedding.md` — full API details on parent_type, token types, pitfalls
- Reference for file move/transfer: `references/feishu-file-move-transfer.md` — cross-ownership move pattern (transfer_owner + user token)
- Token refresh script: `scripts/lark_token_refresh.py` (system crontab, hourly)
  - ⚠️ Uses absolute `/home/ubuntu` base paths — `$HOME` is profile-scoped when run from hr-assistant gateway (e.g. `/home/ubuntu/.hermes/profiles/hr-assistant/home`), causing `~` expansion to double the path prefix. Never use `os.path.expanduser("~/.hermes/...")` in cron scripts.

---

### Known Gateway Port Mapping (updated 2026-06-29)

| Profile | Feishu App ID | Gateway Port | Status |
|---------|--------------|--------------|--------|
| `hr-assistant` | `cli_aa9ebcbfc6e35cba` | **8645** | Active |
| `data-master` | `cli_aa9ea34aaff85cda` | **8646** | Active |
| `finance-master` | `cli_aa9e8a8423785cb0` | **8647** | ⚠️ Zombie (process dead, state.json says running — confirmed 2026-06-29) |
| `default` | `cli_aa9970856879dcd8` | **8640** | Active (configured 2026-06-03) |
| `new-service` | `.env lost` | ~~8644~~ | **DELETED** — profile dir empty, systemd unit gone, config.yaml exists but orphaned |

⚠️ **Ghost profile phenomenon**: A profile can be listed by `hermes profile list` but have zero config files on disk. `hermes config show --profile <name>` will report the expected config path but the file doesn't exist. `hermes config path` can locate the expected paths. Always verify with `ls -la ~/.hermes/profiles/<name>/`. If empty, the profile needs full recreation.

### Restarting a Specific Gateway
```bash
# Find the PID
ps aux | grep 'hermes_cli.main.*--profile <name>' | grep -v grep

# Kill and restart
kill <pid> && sleep 2 && hermes -p <name> gateway run --replace

# Verify (gateway picks port dynamically — check actual port)
ss -tlnp | grep <new-pid>
curl -s http://localhost:<port>/health
```

⚠️ **PID quirk**: When restarting via `kill && hermes -p <name> gateway run --replace`, the new Python process may have a different PID than expected. The shell wrapper gets one PID, the actual gateway Python process gets another. Always verify with `ss -tlnp | grep <name>` rather than relying on PID from `ps` immediately after restart.

⚠️ **PID instability (CONFIRMED 2026-06-22)**: Gateway PIDs can change spontaneously between `ps aux` and `kill`. Observed: data-master PID 3881366 gone, replaced by 3881476 within seconds. **Fix**: Always re-run `ps aux | grep` immediately before `kill`, or use `pkill -f "hermes_cli.main.*--profile <name>"` for pattern-based killing. If `kill` returns "No such process", re-check with `ps aux` and kill the new PID.

### ⛔ Tenant Token vs User Token Folder Access (UPDATED 2026-06-26)
**Tenant Token** capabilities (after user updated Skills folder permissions):
- ✅ `POST /docx/v1/documents` with `folder_token=PdkOfBF0nlUKlkdVABZcYuKFneh` → creates doc in Skills folder
- ✅ Can write content to docs via block API (`/docx/v1/documents/{id}/blocks/{id}/children`)
- ✅ Can list root folder (`folder_token=""`) — returns app-created docs
- ✅ Can search docs via Suite API (`POST /suite/docs-api/search/object?docs=1`)
- ❌ `GET /drive/v1/files?folder_token=<user_folder>` → still `1061004 "forbidden"` (cannot list folder contents)
- ❌ Cannot access other user personal folders (e.g., "用户小艾")

**User OAuth Token** (from `~/.lark/tokens.json`):
- ✅ Full access to user's personal drive, all folders, shared folders
- ✅ Required for listing folder contents, renaming, moving files
- ❌ access_token expires in 2 hours, refresh_token in 7 days

**Key change (2026-06-26)**: Skills folder now allows tenant token doc creation. This means skill→Feishu sync can work without OAuth token when it's expired.

### ⛔ CRITICAL: Never Auto-Restart HR Gateway
The `hr-assistant` gateway (port 8645) must **NEVER be restarted without explicit user approval**. Always confirm with the user before any `kill` or restart operation on this profile. This rule is absolute — no exceptions.

## 9. Feishu Message Sending: Location Identification SOP

### ⛔ CRITICAL PITFALL: Home Channel ≠ Current Conversation (CONFIRMED 2026-06-17)
**Never assume Home Channel ID is the current conversation location.** This caused a critical failure where agent sent a message to the wrong chat and incorrectly reported group membership.

**The Failure**: User asked to send a calendar invite card to Kimy in the "AI在这里" group. Agent used Home Channel ID (`oc_d811c650...`) instead of the actual group ID (`oc_a0422f2a...`), sent the card to Iris's private chat, then told user "Kimy is not in the group" — when Kimy was actually a group member all along.

**Root Cause**: 
- Home Channel (`FEISHU_HOME_CHANNEL`) is the **default message delivery target** (Iris's private chat), NOT the current conversation
- Context metadata (`Source: Feishu (group: AI在这里)`) explicitly states the conversation location but was ignored
- Agent queried members of Home Channel instead of the actual group, got misleading results (1 person in p2p vs 3 people in group), and didn't question the anomaly

### Mandatory Workflow: Verify Conversation Environment Before Sending

**Step 1: Parse Context Metadata**
- Check `Source` field in conversation context:
  - `Source: Feishu (dm)` → Private chat
  - `Source: Feishu (group: <name>)` → Group chat named `<name>`
- **NEVER** skip this step or assume Home Channel = current location

**Step 2: Get Current Chat ID**
```bash
# List all chats the bot is in
curl -s -X GET 'https://open.feishu.cn/open-apis/im/v1/chats?page_size=100' \
  -H "Authorization: Bearer $TENANT_TOKEN" | jq '.data.items[] | {chat_id, name, chat_mode}'
```
- Match by group name from context (e.g., "AI在这里")
- Verify `chat_mode`: `group` for group chats, `p2p` for private chats
- **Cross-reference with context** — if context says "group" but you find `p2p`, you have the wrong chat

**Step 3: Validate Member List**
```bash
# Get members of the target chat
curl -s -X GET 'https://open.feishu.cn/open-apis/im/v1/chats/<CHAT_ID>/members?page_size=100' \
  -H "Authorization: Bearer $TENANT_TOKEN"
```
- **Sanity check**: If context says "group" but member count is 1, **STOP** — you queried the wrong chat
- Group chats should have 2+ members; p2p chats have exactly 1 human member (+ bot if applicable)

**Step 4: Send to Correct Target**
- Use the **group's chat_id** (from Step 2), NOT Home Channel ID
- For calendar invites, mention cards, or any "send to group" request:
  ```json
  {
    "receive_id": "<ACTUAL_GROUP_CHAT_ID>",
    "msg_type": "interactive",
    "content": "..."
  }
  ```

### Quick Decision Checklist
```
□ Context says "group" or "dm"? → Check Source field
□ What's the group name? → Extract from context
□ What's the group's chat_id? → Query /im/v1/chats API
□ Does member count match expectation? → If group but only 1 member, WRONG CHAT
□ Am I about to use Home Channel ID for a group operation? → STOP, that's wrong
```

### Key IDs Reference (hr-assistant profile)
| Chat | chat_id | chat_mode | Members |
|------|---------|-----------|---------|
| **Home Channel** (Iris private) | `oc_d811c650f76f16e98ac7a65517e0128f` | `p2p` | 1 (Iris) |
| **AI在这里** (group) | `oc_a0422f2a7bebf7c3b831a4ff05b8c6db` | `group` | 3 (Iris, Kimy, 姚梦寅) + 2 bots |

**Remember**: When user says "send to the group" or "post in [group name]", they mean the actual group chat, NOT your Home Channel.

---

## 10. Feishu Message Formatting Rules

### ⚠️ Markdown Tables DO NOT Render in Feishu
Feishu's Markdown renderer **silently drops or hides tables**. If the user says "列表呢？没看到啊" or similar, the table didn't render.

**Always use plain text lists for tabular data in Feishu:**

```
**hr-assistant**
端口：8645
飞书 App ID：cli_aa9ebcbfc6e35cba
状态：运行中

**data-master**
端口：8646
飞书 App ID：cli_aa9ea34aaff85cda
状态：运行中
```

This works. Tables don't. Inline code blocks and bold text render fine.

### ⚠️ Interactive Cards vs Bitable Dashboards (USER PREFERENCE 2026-06-12)
When user asks for "BI看板" or "数据看板", they mean a **real interactive Bitable with dashboard/charts**, NOT a static interactive card message.
- **Interactive card** (msg_type: interactive): Static message with text, buttons, dividers. Good for summaries + action buttons.
- **Bitable dashboard**: Multi-dimensional table with built-in chart/dashboard views, filters, pivot tables. This is what "BI看板" means.
- **If user wants BI dashboard**: Create Bitable (`POST /bitable/v1/apps`, requires `bitable:app` scope) → populate data → user opens dashboard tab.

### Sending Interactive Cards
- **User OAuth token** lacks `im:message.send_as_user` scope → returns `230027` error.
- **Must use tenant_access_token** to send interactive cards via `POST /im/v1/messages`.
- Card JSON: `{"config": {"wide_screen_mode": true}, "header": {...}, "elements": [...]}`
- Wrap in payload: `{"receive_id": "chat_id", "msg_type": "interactive", "content": "<card_json_string>"}`
- `content` must be a **JSON string** (escaped), not a raw object.
- **Gateway cannot auto-send cards** — `_build_outbound_payload` only supports text/post. Cards must bypass gateway via direct API call. See `references/feishu-gateway-card-internals.md` for code locations and limits.

---

## 10. Profile Setup Playbook

### When to Use
User provides a new Feishu App ID + Secret and wants a new Hermes gateway.

### Steps
1. `hermes profile create <name>` (name must be lowercase alphanumeric)
2. Write `SOUL.md` — agent persona/identity (Chinese display name goes here)
3. Write `memories/MEMORY.md` — copy from existing profile or write fresh rules
4. Write `memories/USER.md` — copy from existing profile (user info is shared)
5. Write `config.yaml` with `providers:` block (profiles do NOT inherit providers from global config) — include unique webhook port
6. Write `.env` with `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_ALLOWED_USERS`
7. Check port availability: `ss -tlnp | grep -E "864[0-9]"` — assign next free port in config.yaml
8. Start: `hermes --profile <name> gateway run --replace` (or `hermes gateway start --profile <name>` if systemd unit exists)
9. Discover user Open ID from errors.log (first message triggers "Unauthorized user: ou_xxx")
10. Add Open ID to `FEISHU_ALLOWED_USERS`, restart gateway
11. Verify `gateway_state.json` shows feishu: connected

### Key Pitfalls
- **Profile name must be lowercase alphanumeric** — `[a-z0-9][a-z0-9_-]{0,63}`. Chinese characters, uppercase, or special chars will be rejected. Use English slug (e.g. `finance-master`) and put the Chinese display name in SOUL.md.
- **Webhook port conflict** — Each profile's `config.yaml` needs a unique `platforms.webhook.extra.port`. Ports 8640–8646 are commonly taken. Check existing ports with `ss -tlnp | grep -E "864[0-9]"` before assigning. If gateway fails with "Port already in use", increment port and patch config.yaml.
- **`FEISHU_ALLOWED_USERS` is MANDATORY** — without it, gateway connects but silently rejects all messages
- **`providers:` block required** — profiles don't inherit from global config.yaml
- **`hermes gateway start` requires systemd unit** — if missing, use `hermes --profile <name> gateway run --replace`
- **Never restart gateways via messaging platform** — the restart child process is orphaned when parent dies
- **Open IDs are per-app** — don't copy `FEISHU_ALLOWED_USERS` between profiles; each new app needs fresh Open ID discovery from errors.log
- **MEMORY.md/USER.md sync** — `hermes profile create` creates empty `memories/` dir. Copy from existing profile or write fresh. Path: `~/.hermes/profiles/<name>/memories/MEMORY.md` and `USER.md`

## 10b. Cross-Agent SOUL.md Batch Update

### When to Use
User requests adding the same rule/setting to "所有agent" (all agents) or "every agent's SOUL".

### Workflow
1. **Find all agent SOUL.md files**:
   ```bash
   search_files path="~/.hermes/profiles" pattern="SOUL.md" target="files"
   ```

2. **Read each SOUL.md** to understand current structure and find appropriate insertion point — don't assume uniform format across agents.

3. **Patch each file** with the new content, adapting to each agent's existing format:
   ```bash
   patch mode="replace" path="~/.hermes/profiles/<name>/SOUL.md" old_string="..." new_string="..."
   ```

4. **Verify with grep** that content landed in all files:
   ```bash
   grep -n "关键内容" ~/.hermes/profiles/*/SOUL.md ~/.hermes/SOUL.md
   ```

5. **Report completion** with table showing updated agents.

6. **Inform user about gateway restart** — SOUL.md is loaded at gateway startup and NOT hot-reloaded. Running gateways still use the old SOUL. Ask user for approval before restarting (per 操作红线).

### Key Pitfalls
- **Different agents have different SOUL.md structures** — always read each file first
- **SOUL.md changes require gateway restart** — always inform user and ask for approval
- **Preserve existing content** — use `patch` with `old_string`/`new_string`, never full overwrite
- **Profile memory paths**: Per-profile memory/user files live in `memories/` subdirectory, not at profile root: `~/.hermes/profiles/<name>/memories/MEMORY.md` and `USER.md`. Root agent uses the `memory` tool (injected into system prompt), not file-based memory.

### Profile-Specific vs Global Operations
| Operation | Scope | Location |
|-----------|-------|----------|
| SOUL.md | Per-profile | `~/.hermes/profiles/<name>/SOUL.md` or `~/.hermes/SOUL.md` (root) |
| Memory | Per-profile | `~/.hermes/profiles/<name>/memories/MEMORY.md` |
| User Profile | Per-profile | `~/.hermes/profiles/<name>/memories/USER.md` |
| Skill creation | Global (shared) | `~/.hermes/skills/` (same inode for all profiles) |
| Cron job | Per-profile or global | `~/.hermes/profiles/<name>/cron/` or `~/.hermes/cron/` |
| Gateway | Per-profile | PID-based management (see §5) |

## 11. Feishu Doc Sync SOP

### Batch Agent Sync Workflow
For syncing all agents' SOUL/Memory/User to Feishu docs in batch, see `references/batch-agent-sync-workflow.md`.

### Searching Feishu Docs
When looking for documents in the Skills folder or user personal drive, you have two options depending on available token:

**With Tenant Token** (app identity — limited to app-visible docs):
```bash
TENANT_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"cli_aa9970856879dcd8","app_secret":"$LARK_APP_SECRET"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")
curl -s "https://open.feishu.cn/open-apis/suite/docs-api/search/object?docs=1" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_key":"keyword","offset":0,"limit":20}'
```
⚠️ Only returns app-created docs and docs in shared spaces. Does NOT return user personal "My Folder" content.

**With User OAuth Token** (broader, includes user personal docs):
```bash
export LARK_CONFIG_DIR="$HOME/.lark" && export LARK_APP_SECRET="$(cat $HOME/.lark/app_secret)"
lark doc search "keyword"
```

### Sync Scope
- Agent Profile/Memory documents (per-profile doc IDs)
- User-built skills → Skills folder (Token: `PdkOfBF0nlUKlkdVABZcYuKFneh`)

### Core Rules
1. New skill → confirm with user → create new doc in Skills folder
2. Update skill → confirm with user → append to existing doc (NEVER create new)
3. **Pure text only** — Feishu API mangles markdown escape chars (`\#` → `\\#`). Script uses `to_plain_text()` filter.
4. Must use User Access Token (OAuth) for user-visible docs in "My Folder"

### ⛔ MANDATORY: Skill → Feishu Doc Sync After Every SKILL.md Update (USER RULE 2026-06-12)
**User explicitly requires**: After EVERY `skill_manage` update to a SKILL.md, you MUST also sync the corresponding Feishu doc in the Skills folder. This is not optional.

**Workflow**:
1. Update SKILL.md via `skill_manage(action='patch')` or `edit`
2. Immediately use `lark doc append <doc_id> --text "..."` to add the new/changed content to the corresponding Feishu doc
3. Do NOT wait for user to ask — do it proactively in the same turn

**Known Skill → Feishu Doc mappings** (updated 2026-06-23):
| Skill | Feishu Doc ID |
|-------|--------------|
| broadcast-cronjobs | `YPc0dQn7SoNkd6xMPvJcePKEnOb` |
| email-bridge-163 | `OxZTdycmqoA97axPNJNcb7GWnmd` |
| extract-archives | `JTtvdK4vvoNocuxcu0BcCJFenAf` |
| feishu-hermes-integration | `QoVndSwTNof3YBxLGm2cOE2Mnff` |
| hermes-agent | `WlkYdS8sRoZTHmxLAPOc5yoFnCc` |
| image-analysis | `UpicdnhRXoWIdhxSa2Nc98iOnje` |
| japan-visa | `SCfcdMOYroXdDSxrPgPc0h3gnif` |
| memory-management | `WXiXd8RR1od4tGxuYjacnOb2n7b` |
| personal-finance-dashboard | `XZFadOW1xoBXsIxhROccihmNnob` |
| skill-standard | `YtrKdTOPVoGiVBxv6tfc1RQ7n8c` |
| tencent-docs-api | `CtIDdLYoCoSCTbxgeL0cF4H7ngf` |
| web-research | `FwvHdpOfHoe7CjxuXCicBdMfncg` |
| monthly-finance-dashboard | `KMiCdBQGTogJCzxz9s6cpHmwnid` |
| family-expense-bitable | `RGUKdRQHRoVKybxSiEgcchbDn7e` |
| skill-standard | `YtrKdTOPVoGiVBxv6tfc1RQ7n8c` |
| daily-stock-analysis | `OrzgdLa2QoPtvDxHk7acAG6Vnce` |
| todo-reminder-system | `Dyvbdsgf1oXSflxJ3eGcRVdGnKe` |

**Feishu doc API quirks for appending**:
- Commas in numbers (e.g. `¥15,654`) get split into multiple bullet blocks — use no commas or write without separators
- Use `lark doc append` with `--text`, `--bullet`, `--ordered`, `--code`, `--todo`, `--divider` flags
- `--code` flag: accepts multi-line code blocks as a single argument — use for bash/python/config snippets
- `--bullet` flag cannot contain raw double quotes — escape or avoid them
- Each `lark doc append` call is a separate API request — batch related content together to reduce calls

### ⛔ Feishu Image Upload API Permissions (CONFIRMED 2026-07-21)

Three different upload APIs exist, each with different permission requirements. **None work out-of-the-box for docx image embedding.**

| API | Endpoint | Token | Result | Required Scope |
|-----|----------|-------|--------|----------------|
| Drive Media Upload | `POST /drive/v1/medias/upload_all` (parent_type=ccm_import_open, parent_node=doc_image) | Tenant + User | `1061004 forbidden` | Unknown — not granted |
| IM Image Upload | `POST /im/v1/images` | Tenant | `99991672` missing scope | `im:resource:upload` or `im:resource` |
| IM Image Upload | `POST /im/v1/images` | User OAuth | `99991679` unauthorized | `im:resource:upload` or `im:resource` |
| Drive File Upload | `POST /drive/v1/files/upload_all` (parent_type=explorer) | User OAuth | ✅ **Works** — returns `file_token` | `drive:drive` |

**Key pitfall**: `drive/v1/files/upload_all` succeeds and returns a `file_token`, but this token **cannot be used in docx image blocks** (block_type 27). The image block requires a **media token** from `drive/v1/medias/upload_all`, which is blocked.

**Workaround when image embedding fails**:
1. Upload images to Drive as files (`drive/v1/files/upload_all`) — user can download from Drive
2. Add image CDN URLs as text links in the document — user clicks to view in browser
3. Request `im:resource` scope for the Feishu app to enable IM image upload
4. Request `drive/v1/medias` access for direct docx image embedding

### ⛔ CRITICAL: Skills Folder Docs MUST Use User OAuth Token (lark-cli)
The Skills folder (`PdkOfBF0nlUKlkdVABZcYuKFneh`) is in the **user's personal drive**. Tenant tokens from ANY app (hr-assistant, default, data-master) CANNOT read or write to it — they get `1061004 "forbidden"` or `1770040 "no folder permission"`.

**CORRECT workflow for creating skill docs in Feishu:**
```bash
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"
lark doc create --title "skill-name 描述" --folder "PdkOfBF0nlUKlkdVABZcYuKFneh"
lark doc append <doc_id> --text "content..."
```

**WRONG workflow (will fail silently or create in wrong folder):**
```python
# ❌ Using tenant token to create docs — lands in app root, invisible to user
api("POST", "/docx/v1/documents", {"title": "...", "folder_token": "PdkOfBF0nlUKlkdVABZcYuKFneh"})
# ❌ Using hr-assistant app root folder — user can't see it
api("POST", "/docx/v1/documents", {"title": "...", "folder_token": "B5Z0f5bVVlOvwLdQRnXc9LLInEh"})
# ❌ Using any tenant token (hr-assistant, default, data-master) — ALL get 1061004 forbidden
api("POST", "/docx/v1/documents", {"title": "...", "folder_token": "PdkOfBF0nlUKlkdVABZcYuKFneh"})
```

**⛔ COMMON FAILURE PATTERN (CONFIRMED 2026-06-23)**: Agent skips reading this skill and goes straight to `curl`/`urllib` with tenant token → creates doc in app root (invisible to user) → user says "找不到" → agent tries folder_token → gets `1770040 no folder permission` → wastes 10+ turns. Variant (2026-06-26): Agent used raw `urllib.request` with tenant token to create doc in root, then tried to move it to skills folder → move also failed with `1062535 destination parent no permission` → had to add user as full_access member and send link via chat.

**⚠️ UPDATE (CONFIRMED 2026-06-26)**: Tenant token CAN now create docs directly in Skills folder (`PdkOfBF0nlUKlkdVABZcYuKFneh`) via `POST /docx/v1/documents` with `folder_token`. User confirmed folder permissions were updated. However, `drive/v1/files?folder_token=...` (listing folder contents) still returns 403 with tenant token. Use `lark doc list` (OAuth) for listing.

**Preferred workflow** (still use User OAuth when possible):
```bash
export LARK_CONFIG_DIR="$HOME/.lark"
export LARK_APP_SECRET="$(cat $HOME/.lark/app_secret)"
lark doc create --title "skill-name 描述" --folder "PdkOfBF0nlUKlkdVABZcYuKFneh"
lark doc append <doc_id> --text "content..."
```

**Fallback workflow** (when OAuth expired — tenant token works for creation):
```python
# Create doc in skills folder with tenant token
api("POST", "/docx/v1/documents", {"title": "...", "folder_token": "PdkOfBF0nlUKlkdVABZcYuKFneh"})
# Then write content via block API
api("POST", f"/docx/v1/documents/{doc_id}/blocks/{doc_id}/children", {"children": [...], "index": 0})
```

**⛔ UPDATE vs CREATE rule (CONFIRMED 2026-06-26)**: When a skill already has a Feishu doc mapping, ALWAYS update the existing doc (via `lark doc append` or block API), NEVER create a new doc. Creating a new doc orphans the old one and confuses the mapping table. Check the mapping table above FIRST — if the skill is listed, use the existing doc_id.

**lark CLI quick setup (CONFIRMED 2026-06-23)**:
```bash
export LARK_CONFIG_DIR="$HOME/.lark"
export LARK_APP_SECRET="$(cat $HOME/.lark/app_secret)"
```
The `~/.lark/` directory contains: `config.yaml` (app_id), `app_secret`, `tokens.json` (OAuth tokens), `tenant_tokens.json`. This is the **primary** lark-cli config. Per-profile configs at `~/.hermes/profiles/<name>/home/.lark/` are alternatives but may have stale tokens.

**Skill sync comparison pattern** — to find which local skills need Feishu update:
```bash
export LARK_CONFIG_DIR="$HOME/.lark" && export LARK_APP_SECRET="$(cat $HOME/.lark/app_secret)"
lark doc list PdkOfBF0nlUKlkdVABZcYuKFneh  # list all Feishu skill docs
lark doc get <doc_token>                      # get content for comparison
```
Then compare local `SKILL.md` content length vs Feishu content length. If local is significantly longer or Feishu is empty, the doc needs updating.

**If OAuth token is expired**: Re-authorize via `lark auth login` headless flow (see §13). Do NOT fall back to tenant token.

### Sync Commands
```bash
# Use primary lark-cli config (recommended — has freshest OAuth tokens)
export LARK_CONFIG_DIR="$HOME/.lark"
export LARK_APP_SECRET="$(cat $HOME/.lark/app_secret)"
python3 ~/.hermes/skills/productivity/feishu-agent-doc-sync/scripts/sync_feishu_docs.py --skills
```

⚠️ **Config path priority**: Always use `$HOME/.lark/` first. Per-profile paths like `$HOME/.hermes/profiles/<name>/home/.lark/` may have stale tokens.

### lark-cli Doc Commands (常用)
```bash
# List folder contents
lark doc list <folder_token>

# Create new doc in folder
lark doc create --title "Title" --folder "<folder_token>"

# Append content to existing doc (flags: --text, --divider, --bullet, --ordered, --code, --todo)
lark doc append <doc_id> --divider --text "content here"

# Read doc content
lark doc get <doc_id>

# Search docs
lark doc search "keyword"
```
⚠️ `lark doc create` creates an empty doc. To add content, follow with `lark doc append`.
⚠️ `lark doc append` flags cannot be mixed with `--text` in one call for complex content. Chain multiple `--text` and `--divider` flags in one command.
⚠️ Avoid `&` in `--text` AND `--title` content — both trigger terminal backgrounding error. Use variable substitution or rephrase (e.g. replace `&` with `与` or `and`). Use variable substitution: `LARK_APP_SECRET=$(cat ...) ; export LARK_APP_SECRET`.

### ⚠️ Agent Rename Workflow (CONFIRMED 2026-06-18)
When an agent's SOUL.md is changed (e.g., data-master → 添添开心), Feishu docs are NOT auto-synced. Must manually:

**Full Workflow**:

**Full Workflow**:
1. Rename the Feishu folder (API: `PATCH /drive/v1/files/<folder_token>` with new name)
2. Rename the Memory and Profile docs inside
3. Update Profile doc content to match new SOUL.md
4. Update `feishu-hermes-integration` Skill mapping table
5. Sync updated Skill to Feishu Skills folder

**⛔ PERMISSION LIMITATION (CONFIRMED)**:
- Feishu OAuth scope `drive:file:upload` is required for folder/file rename operations
- Current OAuth scopes do NOT include this permission
- **Workaround when permission missing**:
  1. Create NEW docs with new names (`lark doc create --title "Memory - 新名称" --folder <folder_token>`)
  2. Write content to new docs (`lark doc append <doc_id> --text "..."`)
  3. Update skill mapping table with new Doc IDs
  4. Inform user to manually rename folder and delete old docs in Feishu web UI

**Detection**: Check `SOUL.md` in profile dir vs Feishu Profile doc content. If mismatched, sync needed.

### ⚠️ lark doc append: Multiple --text Flags Pitfall (CONFIRMED 2026-06-18)
**`lark doc append` with multiple `--text` flags in a single call silently drops all but the last text block.** Only the final `--text` argument appears in the document.

**Correct approach**: Call `lark doc append` separately for each text block.
```bash
# WRONG — only the last --text is appended
lark doc append <doc_id> --text "Line 1" --text "Line 2" --text "Line 3"

# CORRECT — call separately
lark doc append <doc_id> --text "Line 1"
lark doc append <doc_id> --text "Line 2"
lark doc append <doc_id> --text "Line 3"
```
This applies to all append flags (`--bullet`, `--ordered`, `--code`) as well — each needs its own call.

### ⚠️ SOUL.md Changes Require Gateway Restart (CONFIRMED 2026-06-18)
SOUL.md is loaded into the system prompt at gateway startup. **Changes to SOUL.md do NOT auto-refresh in running sessions.** After editing any agent's SOUL.md, you MUST restart that agent's gateway for changes to take effect.

### ⚠️ Profile Memory Directory Structure
Per-profile memory and user files live in a `memories/` subdirectory, NOT at the profile root:
```
~/.hermes/profiles/<name>/memories/MEMORY.md   # NOT ~/.hermes/profiles/<name>/MEMORY.md
~/.hermes/profiles/<name>/memories/USER.md
```
The root agent (`~/.hermes/`) does NOT have MEMORY.md or USER.md files — it uses the internal `memory` tool (injected into system prompt). Only named profiles have file-based memory.

### Key Pitfalls
- OAuth auth codes are one-time use — re-authorize if consumed
- Desktop browser required for OAuth (not Feishu embedded browser)
- Memory cleanup requires deleting and recreating Feishu docs (script is append-only)
- `needs_update` 80% match rate can cause false negatives on small additions
- lark-cli quirks: see `references/lark-cli-quirks.md` in feishu-agent-doc-sync skill
- `lark doc append` multiple `--text` flags: only last one survives — call separately (see above)

## 12. Feishu Docs Configuration Reference

### Agent Folders (App-Managed)
| Agent | Folder Token | 飞书文件夹名 |
|-------|-------------|-------------|
| 黑执事 | OSJtfkVXrl8q0SdzU24c6LsMnNf | 黑执事 |
| 凛子小姐 | IdI2f33ZCljdE6dIAgBcomQonNe | 凛子小姐 |
| 添添开心 | SpYKfg5t0l9s4qdQbh0cgqFdnXe | 数据大师（无法重命名，缺 drive:file:upload 权限） |

### Profile & Memory Doc IDs
| Agent | Profile Doc ID | Memory Doc ID |
|-------|---------------|---------------|
| 黑执事 (Default) | LQbndYO2vowyN3xSAPNcJc6Vnyg | VHEvdPsrXooUFYxcGZjcyg9mnxl |
| 凛子小姐 (hr-assistant) | Z7nadOQNnoVlzQxgBkEcq6BznMc | THxNdml89olQ5bxPXaAcvnESnne |
| 添添开心 (data-master) | CpFAd7dQaosdA1xOgK5clFeUnwf | XT3kdqL7Ao09Z9x4hCkci44Snic |

### Skills Folder Token: PdkOfBF0nlUKlkdVABZcYuKFneh

### OAuth Config
- Token location: `/home/ubuntu/.hermes/profiles/hr-assistant/home/.lark/tokens.json`
- Granted scopes: `drive:drive`, `docx:document:write`, `docx:document`, `offline_access`
- App token vs User token: Tenant token creates files in "App Shared Space"; User OAuth needed for "My Folder"

## 13. Browser & External Service Automation

### GitHub Automation Pitfalls
For details on automating GitHub signup, login, and CLI setup in headless environments, see `references/github-automation-pitfalls.md`. Key points:
- Arkose Labs CAPTCHA blocks headless browser signup — manual registration required
- Username rules: no underscores, only alphanumerics + single hyphens
- Device verification codes expire quickly — input immediately after receiving
- Windows without admin: use `.zip` (not `.msi`) for gh CLI
- CDP timeouts common — `pkill -9 -f chrome` to recover
- Prefer JavaScript DOM manipulation over `browser_type` for form filling (refs can become stale)

### General Browser Pitfalls

---

## 13b. Feishu Agent Doc Sync (Script-Level Detail)

For the detailed sync script usage, manual REST fallback, full agent doc mappings (4 agents), and踩坑记录, see `references/feishu-agent-doc-sync-detail.md`.

## 13c. Feishu Card Cron Reports (:::CARD Gateway Pattern)

For the gateway-level `:::CARD...:::ENDCARD` auto-extraction pattern (used by 理财大师 profile), card JSON spec, color rules, and the "卡片与MD严禁重复" design principle, see `references/feishu-card-cron-pattern.md`.

---

## 14. Operational Notes

### Daily News & Weather Broadcasts (updated 2026-07-02)
- **News**: Job `e402e3a86482` on **data-master** profile (添添开心), Schedule: `0 10 * * *`, Model: `qwen3.7-max`, Deliver: `local` (Feishu Interactive Card via `send_news_card.py`)
- **Weather**: Job `844cde709d24` on **data-master** profile (添添开心), Schedule: `0 8 * * *`, Model: `qwen3.6-plus`, Deliver: `local` (Feishu Interactive Card via `send_weather_card.py`)
- Both deliver to AI在这里 group (`oc_a0422f2a7bebf7c3b831a4ff05b8c6db`) via card scripts, NOT cron delivery
- Previous jobs `c85928e4d430` (news) and `7cc3e2941131` (weather) on default profile are **paused**, kept for rollback
- Scripts must exist in `~/.hermes/profiles/data-master/scripts/` (copied from `~/.hermes/scripts/`)
- Full SOP: see `broadcast-cronjobs` skill

### Calendar Events → Group Chat Broadcast Pattern (CONFIRMED 2026-07-14)
**Daily schedule broadcast cron jobs automatically push calendar events to group chats.** This is the primary mechanism for calendar-based notifications.

**Workflow for removing specific calendar events from group broadcasts:**
1. **Identify the event**: Use `lark cal list --from "YYYY-MM-DD" --to "YYYY-MM-DD"` to find events by keyword
2. **Verify broadcast source**: Check which profile's cron job runs the daily schedule broadcast (typically hr-assistant's `每日日程播报` job `411a940ba449`)
3. **Delete the event**: Use `lark cal delete <event_id>` to remove it — this automatically stops it from being pushed to group chats
4. **No separate cron cleanup needed**: There are no dedicated "visa reminder" or topic-specific cron jobs — the broadcast job reads ALL calendar events dynamically

**Multi-token fallback pattern** (when OAuth expired):
```bash
# Try global config first
export LARK_CONFIG_DIR="/home/ubuntu/.lark"

# If expired, try hr-assistant profile
export LARK_CONFIG_DIR="/home/ubuntu/.hermes/profiles/hr-assistant/home/.lark"

# Check token freshness before use
python3 -c "import json; d=json.load(open('$LARK_CONFIG_DIR/tokens.json')); print('access_expires:', d.get('expires_at','?'))"
```

**Key insight**: Calendar events and group chat broadcasts are tightly coupled via the daily schedule cron job. Managing calendar events IS the way to control what gets pushed to groups — no need to hunt for separate notification cron jobs.

### lark-cli OAuth Token Management
- OAuth User Access Tokens expire (access_token ~2h, refresh_token ~7 days)
- When expired, `lark doc list/search/get` returns `AUTH_ERROR`
- **Headless re-auth flow** (confirmed working 2026-06-12):
  1. Background `lark auth login > /tmp/lark_login.log 2>&1 &` (it starts its own callback server on port 9999)
  2. Extract authorize URL from log, send to user
  3. User opens URL in browser, authorizes
  4. If browser completes redirect → token saved automatically
  5. If user pastes `code=...` instead → manually trigger: `curl -s "http://127.0.0.1:9999/callback?code=<CODE>&state=<STATE>"` (extract state from auth URL)
  6. Verify: `lark auth status` — check `authenticated: true` and `scope_groups`
- See `feishu-user-token-refresh` skill for full workflow details
- See `references/lark-cli-quirks.md` for token locations, command map, and troubleshooting

#### Multi-Platform Cron Delivery Pattern
To deliver the same cron task to multiple platforms (e.g. Feishu + Weixin):
1. Create a second cron job with identical prompt/schedule, different `deliver` target
2. Supported `deliver` values: `origin` (original platform where task was created), `weixin`, `feishu`, `telegram`, `discord`, etc.
3. Both jobs run independently at the same schedule — no coordination needed

### Browser/Search Pitfalls
- Browser (CDP) frequently times out or gets blocked by bot detection
- Terminal `curl` also frequently times out
- Prefer `search_files` or `terminal` with short timeout retries for file lookups
