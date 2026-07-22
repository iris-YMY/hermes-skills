# Feishu Conversation Location Identification SOP

**Created**: 2026-06-17  
**Trigger**: User frustration event - agent confused Home Channel with group chat location

---

## Problem Statement

Agent incorrectly assumed Home Channel ID = current conversation location, causing:
1. Message sent to wrong chat (private instead of group)
2. False report that target user "not in group" when they actually were
3. User frustration and loss of trust

---

## Root Cause Analysis

### Error Chain
1. **Context Ignored**: `Source: Feishu (group: AI在这里)` explicitly stated location, but agent didn't verify
2. **Wrong ID Used**: Used `FEISHU_HOME_CHANNEL` (private chat) instead of querying actual group chat_id
3. **Anomaly Not Questioned**: Found 1 member in "group" (actually p2p chat) but didn't recognize this as impossible for a group
4. **False Conclusion**: Reported "Kimy not in group" based on wrong data

### Conceptual Confusion
- **Home Channel** = Default message delivery target (Iris's private chat), configured in `.env`
- **Current Conversation** = Where the user is actually talking to you RIGHT NOW, identified by `Source` metadata
- These are DIFFERENT things and must never be conflated

---

## Standard Operating Procedure

### Pre-Send Verification Checklist

**Before ANY message sending operation, execute these steps IN ORDER:**

#### Step 1: Parse Context Metadata
```
Check system context for: Source: Feishu (group: <name>) or Source: Feishu (dm)
```
- If `(group: XXX)` → This is a group chat named XXX
- If `(dm)` → This is a direct message
- **DO NOT SKIP THIS STEP**

#### Step 2: Retrieve Correct chat_id
```bash
# Query all chats the bot participates in
curl -s -X GET 'https://open.feishu.cn/open-apis/im/v1/chats?page_size=100' \
  -H "Authorization: Bearer $TENANT_TOKEN" | \
  jq '.data.items[] | select(.name == "TARGET_GROUP_NAME") | {chat_id, chat_mode, user_count}'
```
- Match by exact group name from Step 1
- Verify `chat_mode` matches context (`group` for groups, `p2p` for dm)

#### Step 3: Validate Member Count
```bash
# Get members of identified chat
curl -s -X GET 'https://open.feishu.cn/open-apis/im/v1/chats/<CHAT_ID>/members' \
  -H "Authorization: Bearer $TENANT_TOKEN" | \
  jq '.data.items | length'
```
**Sanity Check**:
- Context says "group" but member count = 1? → **STOP**, wrong chat
- Context says "group" but member count = 2+? → ✓ Correct
- Context says "dm" but member count = 1? → ✓ Correct

#### Step 4: Send Message
```json
{
  "receive_id": "<VERIFIED_GROUP_CHAT_ID>",
  "msg_type": "interactive",
  "content": "..."
}
```
- **NEVER** use `FEISHU_HOME_CHANNEL` for group operations
- **ALWAYS** use the chat_id from Step 2

---

## Decision Matrix

| Context Source | Expected chat_mode | Expected Members | Correct ID Source |
|----------------|-------------------|------------------|-------------------|
| `Feishu (group: XXX)` | `group` | 2+ | Query API by name |
| `Feishu (dm)` | `p2p` | 1 | Use Home Channel or query |

---

## Common Mistakes to Avoid

❌ **WRONG**: "Context says group, I'll use Home Channel ID"  
✓ **RIGHT**: "Context says group, I need to query /chats to find this group's ID"

❌ **WRONG**: "Member count is 1 but context says group, I'll assume group is empty"  
✓ **RIGHT**: "Member count is 1 but context says group - this is impossible, I queried the wrong chat"

❌ **WRONG**: "User wants to send to group, I'll send to Home Channel since that's where messages go"  
✓ **RIGHT**: "User wants to send to group, I need to find that specific group's chat_id first"

---

## Known Chat IDs (hr-assistant profile)

| Chat Name | chat_id | Type | Members | Notes |
|-----------|---------|------|---------|-------|
| Home Channel | `oc_d811c650f76f16e98ac7a65517e0128f` | `p2p` | 1 (Iris) | Default delivery, NOT a group |
| AI在这里 | `oc_a0422f2a7bebf7c3b831a4ff05b8c6db` | `group` | 3 + 2 bots | Active group with Kimy |

---

## Verification Script

```bash
#!/bin/bash
# Quick verification: "Am I in the right chat?"
TENANT_TOKEN="$1"
EXPECTED_MODE="$2"  # "group" or "p2p"
EXPECTED_NAME="$3"  # Group name (empty for p2p)

echo "=== Listing all chats ==="
curl -s -X GET 'https://open.feishu.cn/open-apis/im/v1/chats?page_size=100' \
  -H "Authorization: Bearer $TENANT_TOKEN" | \
  jq -r '.data.items[] | "Name: \(.name // "N/A"), ID: \(.chat_id), Mode: \(.chat_mode), Users: \(.user_count // 0)"'

echo ""
echo "=== Matching expected environment ==="
if [ "$EXPECTED_MODE" = "group" ]; then
  echo "Looking for group: $EXPECTED_NAME"
  # User can manually verify from output above
else
  echo "Looking for p2p chat (Home Channel)"
fi
```

---

## Post-Incident Actions

After any location confusion incident:
1. **Acknowledge error immediately** - Don't compound the mistake
2. **Re-query with correct context** - Find the actual group
3. **Report accurate findings** - "Actually, Kimy IS in the group, here are all 3 members"
4. **Apologize for confusion** - User trust is fragile after wrong information
5. **Document the lesson** - Update skills/references to prevent recurrence

---

## Key Takeaway

**Home Channel is a DELIVERY ADDRESS, not a CONVERSATION LOCATION.**

Always verify where you ARE before sending WHERE.
