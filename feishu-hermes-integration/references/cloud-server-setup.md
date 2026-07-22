# lark-cli Cloud Server Setup Reference

## Problem
The lark-cli source code hardcodes `localhost` in the OAuth callback server, making remote/cloud server auth impossible without modification.

## Required Environment Variables
Both MUST be set globally (in `~/.bashrc`):
```bash
export LARK_CONFIG_DIR="$HOME/.lark"
export LARK_APP_SECRET="your_app_secret"
```

Without `LARK_CONFIG_DIR`, every lark command fails with:
```json
{"code": "CONFIG_ERROR", "error": true, "message": "LARK_CONFIG_DIR environment variable is not set"}
```

## Source Patch for Cloud Servers

```bash
# 1. Patch the redirect URI in server.go
sed -i 's|http://localhost:%d/callback|http://<YOUR_PUBLIC_IP>:%d/callback|' ~/lark-cli/internal/auth/server.go

# 2. Verify the patch
grep "GetRedirectURI" -A2 ~/lark-cli/internal/auth/server.go

# 3. Rebuild
cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/

# 4. Start auth login (captures the URL)
timeout 5 lark auth login 2>&1
```

## Feishu Console Configuration
1. Go to https://open.feishu.cn → your app → Security Settings
2. Set Redirect URL to: `http://<YOUR_PUBLIC_IP>:9999/callback`
3. **Publish a new version** — changes don't take effect until published!
4. Wait ~30 seconds for propagation

## Auth Flow (Manual Code Exchange — RECOMMENDED)

On a cloud server, the browser runs on the user's machine, so the callback to the server's port 9999 is unreliable. Use the manual flow:

1. Run `lark auth login 2>&1 | tee /tmp/lark_auth.log &` (listens on port 9999)
2. Extract the auth URL: `grep "https://accounts.feishu.cn" /tmp/lark_auth.log`
3. Open the URL in a **desktop browser** (not mobile)
4. Authorize the app — browser redirects to a "connection refused" page
5. **Copy the `code=XXXXXX` value from the browser address bar**
6. Exchange code for tokens via curl (see `references/headless-auth.md` for the full command)
7. Write tokens to `~/.lark/tokens.json` manually
8. Kill auth listener: `fuser -k 9999/tcp`
9. Verify: `lark auth status` → `{"authenticated": true, ...}`

For the complete step-by-step with curl commands, see `references/headless-auth.md`.

## Port Conflicts
If port 9999 is already in use:
```bash
fuser -k 9999/tcp
sleep 1
lark auth login
```
