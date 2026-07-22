# Lark CLI — Headless Server OAuth Workaround

## Problem
On headless cloud servers, `lark auth login` fails because:
1. No browser available (`xdg-open` not found)
2. **The OAuth callback URL**: The callback server runs on the cloud server, but the user's browser is on a different machine. Even with the IP patch applied, the callback may not reach the server reliably depending on network routing.

## Prerequisite: Feishu Configuration
**CRITICAL**: In Feishu Open Platform -> Security Settings -> Redirect URL, you MUST set:
`http://<SERVER_PUBLIC_IP>:9999/callback`
(e.g., `http://106.54.37.126:9999/callback`)
**AND PUBLISH A NEW VERSION** of the app for the change to take effect.
If you use `localhost`, the remote auth flow WILL FAIL with Error 20043 or timeout.

**CRITICAL**: Also patch `~/lark-cli/internal/auth/server.go` to use the public IP instead of localhost, then `go build`. See SKILL.md for the exact sed command.

## Full OAuth Flow (Manual Code Exchange — RECOMMENDED)

### Step 1: Start the listener in background
```bash
fuser -k 9999/tcp 2>/dev/null  # Clear zombie processes first
export LARK_CONFIG_DIR=~/.lark
export LARK_APP_SECRET='your_secret'
lark auth login 2>&1 | tee /tmp/lark_auth.log &
sleep 3
```

### Step 2: Get the authorization URL
```bash
grep "https://accounts.feishu.cn" /tmp/lark_auth.log
```
Send this URL to the user. They open it in their **computer browser** (not mobile).

### Step 3: User authorizes and copies the code
After the user clicks「同意」(Authorize):
- The browser redirects to `http://<SERVER_IP>:9999/callback?code=XXXXXX&state=YYYYYY`
- The page shows **"Connection refused"** or **"Unable to connect"** — this is NORMAL
- **DO NOT close the page** — the user must copy the `code=XXXXXX` value from the browser's address bar
- Send the code back to the agent

### Step 4: Exchange code for tokens via curl (PROVEN WORKING)
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

The response contains:
- `access_token` — valid for 2 hours (expires_in: 7200)
- `refresh_token` — valid for 7 days (refresh_token_expires_in: 604800)
- `scope` — space-separated list of granted scopes

### Step 5: Write tokens to `~/.lark/tokens.json`
Create the file manually with the correct format. The timestamps must be ISO 8601 UTC:

```bash
# Using Python for reliable timestamp math:
python3 -c "
import json, sys
from datetime import datetime, timezone, timedelta

resp = json.loads(sys.stdin.read())
now = datetime.now(timezone.utc)
tokens = {
    'access_token': resp['access_token'],
    'refresh_token': resp['refresh_token'],
    'expires_at': (now + timedelta(seconds=resp['expires_in'])).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'refresh_token_expires_at': (now + timedelta(seconds=resp['refresh_token_expires_in'])).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'scope': resp['scope']
}
print(json.dumps(tokens, indent=2))
" > ~/.lark/tokens.json <<'EOF'
<paste_the_curl_response_json_here>
EOF
```

Or write the file directly if doing it manually — the format is:
```json
{
  "access_token": "<from response>",
  "refresh_token": "<from response>",
  "expires_at": "<ISO 8601 UTC: current_time + expires_in seconds>",
  "refresh_token_expires_at": "<ISO 8601 UTC: current_time + refresh_token_expires_in seconds>",
  "scope": "<from response>"
}
```

### Step 6: Kill background auth and verify
```bash
fuser -k 9999/tcp 2>/dev/null  # Clean up the auth listener

# Verify:
export LARK_CONFIG_DIR=~/.lark
export LARK_APP_SECRET='your_secret'
lark auth status
# Should show: {"authenticated": true, "expires_at": "...", ...}
```

## Pitfalls

### Port 9999 Conflict
If `lark auth login` fails with `listen tcp :9999: bind: address already in use`:
```bash
fuser -k 9999/tcp 2>/dev/null
sleep 1
# Then retry
```

### `minutes:minute:download` Permission Unavailable
If the OAuth page fails with "权限无法开通" (permission cannot be enabled), the `minutes:minute:download` scope is not available in your Feishu app. Fix:
1. Edit `~/lark-cli/internal/scopes/scopes.go` — remove `"minutes:minute:download"` from the minutes group (line ~57)
2. Rebuild: `cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/`
3. Kill old auth: `fuser -k 9999/tcp`
4. Restart from Step 1

### Redirect URI Must Match Exactly
The `redirect_uri` in the curl request MUST match the URL in Feishu console EXACTLY (no trailing slashes, no http vs https mismatch).

### Mobile Browser Issues
Mobile browsers may struggle with IP-based callbacks. Always prefer a **computer browser** for the auth step. If mobile is the only option, the user must carefully copy the `code=` value from the address bar.
