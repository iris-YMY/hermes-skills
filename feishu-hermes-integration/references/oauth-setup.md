# Feishu OAuth Setup Reference

## Current Configuration (2026-06-04)

### App Details
- **App ID**: `cli_aa9ebcbfc6e35cba` (hr-assistant / 凛子小姐)
- **Server IP**: `106.54.37.126`
- **Callback Port**: `9999`
- **Redirect URI**: `http://106.54.37.126:9999/callback`

### Granted Scopes (via OAuth)
- `drive:drive` — Full cloud space read/write
- `docx:document:write` — Document editing
- `docx:document` — Document access
- `docx:document:create` — Document creation
- `offline_access` — Refresh token support
- Plus existing scopes: `im:message`, `calendar:calendar`, `contact:contact.base:readonly`, etc.

### Token File Location
- Profile path: `~/.hermes/profiles/hr-assistant/home/.lark/tokens.json`
- Global path (symlinked): `~/.lark/tokens.json`

### Required Permissions (Feishu Console)
These must be enabled AND published as a new app version:
1. `drive:drive` (管理云空间中的文件)
2. `docx:document:write` or `docs:document.content:write` (云文档内容读写)
3. `docx:document:create` (创建云文档)

### Headless OAuth Flow Steps

```bash
# 1. Kill any existing auth listener
fuser -k 9999/tcp 2>/dev/null

# 2. Set env vars
export LARK_CONFIG_DIR="/home/ubuntu/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="<secret>"

# 3. Start auth in background
rm -f ~/.lark/tokens.json
lark auth login 2>&1 | tee /tmp/lark_auth.log &
sleep 2

# 4. Extract URL
grep "https://accounts.feishu.cn" /tmp/lark_auth.log

# 5. User opens URL in DESKTOP browser (NOT mobile/Feishu), clicks 同意
# 6. Copy code=XXXX from browser address bar after redirect

# 7. Exchange code for token via curl
curl -s -X POST "https://open.feishu.cn/open-apis/authen/v2/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{"grant_type":"authorization_code","client_id":"cli_aa9ebcbfc6e35cba","client_secret":"<secret>","code":"CODE_HERE","redirect_uri":"http://106.54.37.126:9999/callback"}'

# 8. Save response tokens to ~/.lark/tokens.json
# 9. Verify: lark auth status
```

### ⚠️ Critical Pitfalls

1. **Auth Code is One-Time Use**: If consumed by a retry/duplicate call, returns `invalid_grant` (20065). Must regenerate URL and re-authorize.
2. **Desktop Browser Required**: Mobile browsers and Feishu embedded browsers may not redirect properly.
3. **Redirect URI Must Match Exactly**: No trailing slashes. Must match Feishu console setting.
4. **Tenant vs User Token**: 
   - Tenant token → docs in App Shared Space (用户看不到)
   - User token (OAuth) → docs in 「我的文件夹」(用户可见)
   - Always use User Token for user-facing document creation.

### Token Refresh
User Access Token expires in ~2 hours. Refresh token lasts ~30 days.
Auto-refresh is handled by `lark-cli` when using `lark doc ...` commands.
