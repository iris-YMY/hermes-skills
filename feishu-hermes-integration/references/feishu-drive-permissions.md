# Feishu Drive Permissions API — Observed Behavior (2026-06-04)

## File Move — Endpoint Returns 404
`POST /drive/v1/files/move` with `{"file_token": "...", "type": "docx", "folder_token": "..."}` returns `404 page not found`.
**Workaround**: Create the document directly in the target folder using `POST /docx/v1/documents` with `folder_token` in the payload. Do NOT attempt to move files after creation.

## Drive Permissions — Add Member (works)
`POST /drive/v1/permissions/{token}/members?type=docx` with:
```json
{"member_type": "openid", "member_id": "ou_xxx", "perm": "full_access"}
```
Returns `code: 0`. Works for `type=docx`, `type=folder`.

## Drive Permissions — Set Public (fails for docx)
`PATCH /drive/v1/permissions/{token}/public?type=docx` returns `code: 1063001 "Invalid parameter"`.
Likely requires `link_share_setting` field or different payload structure. Unresolved.

## Drive Permissions — Sheets Public (fails)
`PUT /drive/v1/permissions/{token}/public?type=sheets` returns `404 page not found`.
The `/permissions/.../public` endpoint appears to not support sheets type on this API version.

## Sharing Folders with Bots — UX Limitation (CONFIRMED 2026-07-20)

**Problem**: Feishu folder share dialog cannot find bot applications — only searches for people and groups.

**Workarounds** (in order of preference):

### Method 1: Group Relay (最简单)
1. Create a Feishu group (can be just you)
2. Add the bot to the group
3. Share folder → search for the group name → add as collaborator
4. Bot inherits folder access via group membership

### Method 2: API Direct Authorization
```
POST /drive/v1/permissions/{folder_token}/members?type=folder
{"member_type": "app", "member_id": "{APP_ID}", "perm": "full_access"}
```
Requires admin permissions. Works for `type=folder`, `type=docx`.

### Method 3: User OAuth Token
Bot operates as user identity — can access all docs the user can see.
- Pros: No per-folder sharing needed
- Cons: Token expires (access 2h, refresh 7d), needs periodic refresh

### Method 4: Knowledge Base (Wiki) Member
If folder is in a Wiki, add bot as Wiki member → access to all Wiki docs.

### Method 5: Open Platform Permission Scopes
Ensure bot app has cloud doc permissions enabled at `https://open.feishu.cn/app/{APP_ID}/auth`:
- `drive:drive`, `drive:drive:readonly`, `docx:document`, `docx:document:write`
- **Must publish new version** after enabling permissions

## Summary
- **Add members**: ✅ works for docx, folder, sheets
- **Set public/link sharing**: ❌ fails or returns 404 for all types
- **Move files between folders**: ❌ 404 on `/drive/v1/files/move`
- **Create in folder**: ✅ use `folder_token` at creation time (not after)
- **Share folder with bot via UI**: ❌ bot not searchable — use group relay or API
