# Cronjob Diagnostic Checklist

Systematic debugging flow when a cronjob "isn't working."

## Step 1: Status Check
```bash
# List all jobs, check last_status and last_delivery_error
hermes cron list
# Or via cronjob tool: cronjob(action='list')
```
- `last_status: "ok"` + `last_delivery_error: null` → job ran and delivered, problem is elsewhere
- `last_status: "error"` → check `last_error` field
- `last_delivery_error` set → delivery target problem

## Step 2: Read Full Job Config
```bash
cat ~/.hermes/profiles/<profile>/cron/jobs.json
```
Check:
- `model` / `provider`: null → 400 error at runtime
- `skill`: references a skill that exists? (use `skill_view` to verify)
- `enabled_toolsets`: appropriate for the job?
- `deliver` / `origin`: correct target chat?

## Step 3: Stale Skill References
If `skill` field names a skill that no longer exists:
- Job still runs (doesn't crash), but loses skill-provided context
- Fix: update job to remove stale reference, or recreate the skill

## Step 4: Toolset vs API Key Mismatch
```bash
grep -i "TAVILY\|EXA_API\|PARALLEL\|FIRECRAWL" ~/.hermes/.env
```
- `web` in enabled_toolsets but no search API key → 0 web tools loaded
- Fix: either add API key or remove `web` from enabled_toolsets
- Jobs that only need `terminal` (e.g., lark-cli commands) should use `["terminal"]` only

## Step 5: Command/API Verification
Run the core command manually to verify it works:
```bash
# Example: lark calendar
lark cal list --from "2026-06-30" --to "2026-07-01"
```
- If returns empty → API works, just no data (not a bug)
- If errors → auth/config issue

## Step 6: Broader Date Range Test
When API returns 0 results, expand the range to confirm API health:
```bash
lark cal list --from "2026-06-29" --to "2026-07-05"
```
- If broader range returns results → API healthy, original range just empty
- If still empty → API/auth problem

## Step 7: Session Logs (if available)
```bash
find ~/.hermes -name "session_cron*<job_id>*" -type f | sort -r | head -5
```
- Check message count: 2 messages = no tool calls made
- Check tools array: 0 tools = toolset/config problem

## Common Diagnoses

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Job runs ok but no message delivered | Wrong deliver target / chat_id | Update origin.chat_id |
| Job runs ok, message sent, but content wrong | Tool injection failure / hallucination | See tool-injection-failure-20260618.md |
| Job runs ok but skill context missing | Stale skill reference | Remove or recreate skill |
| 400 error at runtime | Missing model/provider | Add to jobs.json |
| 401 error at runtime | Provider name mismatch | Match config.yaml providers key |
| Job hangs / never completes | browser in toolsets, or approval prompts | Remove browser, use pre-fetch script |
| `RuntimeError: Connection error` | API endpoint temporarily unreachable | Retry; if persistent, check base_url and network |
| Card send fails with 230002 | Bot not in target chat | Use correct chat_id or add bot to chat |
| Card send fails with 230027 | User Token lacks send_as_user scope | Use Tenant Token instead |
