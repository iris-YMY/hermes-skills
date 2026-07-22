# Feishu Token Access Patterns & Troubleshooting

## Token Types Quick Reference

| Token | How to Get | Scope | Can Access |
|-------|-----------|-------|-----------|
| **Tenant Access Token** | `POST /auth/v3/tenant_access_token/internal` with app_id + app_secret | App-level | App-created docs, shared spaces, Suite docs API search |
| **User Access Token (OAuth)** | `lark auth login` → browser auth → code exchange | User-level | User's "My Folder", personal docs, all user-visible content |

## Common Error Codes

| Code | Meaning | Likely Cause | Fix |
|------|---------|-------------|-----|
| `AUTH_ERROR` (lark-cli) | No valid OAuth tokens | tokens.json expired or missing | Re-run `lark auth login` |
| `1061004 "forbidden"` | App lacks folder permission | Tenant token accessing user-owned folder | Use root folder (`""`) or OAuth token |
| `99991672` | Missing wiki scope | App doesn't have `wiki:wiki` permission | Add scope in Feishu console + publish |
| `99991677` | Token expired | access_token > 2h old | Refresh or re-auth |
| `20026` | Invalid refresh token | refresh_token already used or expired | Full OAuth re-auth required |

## Diagnosing Document Access Issues

### Step 1: Get a Tenant Access Token
```bash
curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"cli_XXX","app_secret":"YOUR_SECRET"}'
```

### Step 2: Try Suite Docs API Search
```bash
curl -s "https://open.feishu.cn/open-apis/suite/docs-api/search/object?docs=1" \
  -H "Authorization: Bearer $TAT" \
  -H "Content-Type: application/json" \
  -d '{"search_key":"keyword","offset":0,"limit":20}'
```
This searches across all docs the app can see. If the target doc doesn't appear here, it's in user's personal space.

### Step 3: Try Direct Drive API
```bash
curl -s "https://open.feishu.cn/open-apis/drive/v1/files?folder_token=TOKEN" \
  -H "Authorization: Bearer $TAT"
```
- `1061004 forbidden` → User-owned folder, app not a collaborator
- `code: 0` with empty files → Folder exists but empty (or app has no visibility)

### Step 4: For User-Owned Folders
Only OAuth User Access Token can access these. If tokens are expired:
1. Guide user through browser re-auth
2. Exchange code for tokens
3. Retry with `lark doc list`

## Key Insight
**Tenant token ≠ User token.** They have fundamentally different scopes:
- Tenant token sees what the App owns or is shared with
- User token sees what the User owns
- The Skills folder (`PdkOfBF0nlUKlkdVABZcYuKFneh`) is **user-owned** — tenant token returns forbidden
- There is **no API workaround** — only OAuth re-auth or the user adding the app as a folder collaborator
