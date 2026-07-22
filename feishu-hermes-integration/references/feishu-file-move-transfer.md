# Feishu File Move & Transfer Ownership

## Moving Files Between Folders

### API: `POST /drive/v1/files/{file_token}/move`

```python
POST /drive/v1/files/{file_token}/move
{"folder_token": "TARGET_FOLDER", "type": "docx"}
```

### ⛔ CRITICAL: Cross-Ownership Move Requires Transfer First

When moving files from **app-owned space** (created with tenant token) to **user-owned folders**:

1. `drive/v1/files/move` with **tenant token** → `1062535 destination parent no permission`
2. `drive/v1/files/move` with **user token** → `1062524 source parent no permission`

**Root cause**: User token can access destination but not source; tenant token can access source but not destination.

### Solution: Transfer Ownership First

```python
# Step 1: Transfer file ownership to user
POST /drive/v1/permissions/{file_token}/members/transfer_owner?type=docx&need_notification=false
{"member_type": "openid", "member_id": "ou_USER_OPEN_ID"}
# Tenant token works ✅

# Step 2: Move file (now user-owned)
POST /drive/v1/files/{file_token}/move
{"folder_token": "TARGET_FOLDER", "type": "docx"}
# User OAuth token works ✅
```

### Batch Move Script Pattern

```python
TENANT_TOKEN = get_tenant_token()
USER_TOKEN = get_user_oauth_token()
USER_OU = "ou_xxx"

for doc_id in doc_ids:
    # Transfer ownership (tenant token)
    api("POST", f"/drive/v1/permissions/{doc_id}/members/transfer_owner?type=docx&need_notification=false",
        TENANT_TOKEN, {"member_type": "openid", "member_id": USER_OU})
    
    # Move (user token)
    api("POST", f"/drive/v1/files/{doc_id}/move",
        USER_TOKEN, {"folder_token": target_folder, "type": "docx"})
```

### Optional: Grant User Access Before Transfer

If the user needs to see/access the file before transfer:
```python
POST /drive/v1/permissions/{file_token}/members?type=docx&need_notification=false
{"member_type": "openid", "member_id": "ou_USER_OPEN_ID", "perm": "full_access"}
```

### Optional: Set Public Permissions

```python
PATCH /drive/v1/permissions/{file_token}/public?type=docx
{"external_access_entity": "open", "security_entity": "anyone_can_view",
 "share_entity": "anyone", "manage": "full_access"}
```
Note: This alone does NOT enable cross-ownership move. Transfer is still required.

### Known Limitations
- `transfer_owner` requires tenant token
- `move` requires user OAuth token for user-owned destinations
- `drive/v1/files/move` does NOT accept `"index"` parameter for positioning
- lark-cli has no `drive move` command (as of 2026-07-21)
