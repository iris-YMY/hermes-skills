# Feishu OAuth Code Exchange — Session Pattern (2026-06-09)

## Problem
`lark auth login` background process competes for the authorization code on headless servers. The OAuth refresh tokens expired (6/5) and a new auth was needed.

## Reliable Code Exchange Flow

### Step 1: Start a passive HTTP listener (NOT `lark auth login`)
Use a Python one-liner to listen on port 9999 WITHOUT consuming the code:

```bash
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if '/callback' in self.path:
            p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            with open('/tmp/lark_auth_code.txt', 'w') as f:
                f.write(p.get('code', [''])[0])
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>OK</h1></body></html>')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass
HTTPServer(('0.0.0.0', 9999), H).handle_request()
" &
```

### Step 2: Get the authorize URL
```bash
export LARK_CONFIG_DIR="$HOME/.lark"
export LARK_APP_SECRET="$(cat $HOME/.hermes/.env | grep FEISHU_APP_SECRET | cut -d= -f2)"
lark auth login 2>&1 | grep "https://accounts.feishu.cn"
```

### Step 3: User authorizes, code captured in `/tmp/lark_auth_code.txt`
The Python listener saves the code to file without calling any Feishu API.

### Step 4: Exchange code for tokens
```bash
APP_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"cli_aa9970856879dcd8\",\"app_secret\":\"$LARK_APP_SECRET\"}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('app_access_token',''))")

CODE=$(cat /tmp/lark_auth_code.txt)
REDIRECT_URI="http://106.54.37.126:9999/callback"

curl -s -X POST "https://open.feishu.cn/open-apis/authen/v2/oauth/token" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"grant_type\":\"authorization_code\",\"code\":\"$CODE\",\"client_id\":\"cli_aa9970856879dcd8\",\"client_secret\":\"$LARK_APP_SECRET\",\"redirect_uri\":\"$REDIRECT_URI\"}"
```

### Step 5: Save tokens
```python
python3 -c "
import json
from datetime import datetime, timedelta, timezone
tokens = json.loads('<response_above>')
tz8 = timezone(timedelta(hours=8))
now = datetime.now(tz8)
output = {
    'access_token': tokens['access_token'],
    'refresh_token': tokens['refresh_token'],
    'expires_at': (now + timedelta(seconds=tokens['expires_in'])).isoformat(),
    'refresh_token_expires_at': (now + timedelta(seconds=tokens['refresh_token_expires_in'])).isoformat(),
    'scope': tokens['scope']
}
with open('/home/ubuntu/.lark/tokens.json', 'w') as f:
    json.dump(output, f, indent=2)
"
```

## Key Discovery: Tenant Token vs User Token Folder Access

| Action | Tenant Token | User OAuth Token |
|--------|-------------|------------------|
| List root folder (`folder_token=""`) | ✅ Works (empty result if no app docs) | ✅ Works |
| List user-owned folder | ❌ 1061004 forbidden | ✅ Works |
| Search via Suite API | ✅ Works (app-visible docs only) | ✅ Works (broader) |
| Create doc in app space | ✅ Works | N/A |
| Create doc in user "My Folder" | ❌ Cannot | ✅ Works |

**Takeaway**: For Skills folder and user personal drive operations, you MUST use User OAuth Token. Tenant Token is only useful for app-managed resources and broad searches.
