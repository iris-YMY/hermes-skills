# Batch Agent Sync to Feishu Docs — Workflow Reference

When updating all agents' SOUL/Memory/User and syncing to Feishu docs in batch.

## Step 1: Read All Local Agent Files

```bash
# Root agent (default profile)
cat ~/.hermes/SOUL.md
# Root agent uses internal memory tool — no MEMORY.md/USER.md files

# Named profiles
cat ~/.hermes/profiles/<name>/SOUL.md
cat ~/.hermes/profiles/<name>/memories/MEMORY.md
cat ~/.hermes/profiles/<name>/memories/USER.md
```

⚠️ Profile memory files are in `memories/` subdirectory, NOT at profile root.

## Step 2: Compare & Identify Changes

Build a comparison table:
- Which SOUL.md entries are present/missing per agent
- Which MEMORY rules are shared vs agent-specific
- Which USER entries need syncing across agents

## Step 3: Apply Local Changes

Edit files directly with `patch` or file write operations.

## Step 4: Restart Gateways (for SOUL.md changes)

SOUL.md is loaded at gateway startup. After editing:
```bash
# Find PID
ps aux | grep 'hermes_cli.main.*--profile <name>' | grep -v grep

# Kill and restart
kill -9 <pid>
hermes --profile <name> gateway run --replace  # (use background=true in Hermes terminal)

# Verify
ss -tlnp | grep <port>
```

⚠️ **ALWAYS get user approval before restarting gateways** — this is an operation red line.

## Step 5: Sync to Feishu Docs

### Profile Docs — Append new content
```bash
export LARK_CONFIG_DIR="$HOME/.hermes/profiles/hr-assistant/home/.lark"
export LARK_APP_SECRET="$(cat $LARK_CONFIG_DIR/app_secret)"

# Append operation red line or new sections
lark doc append <profile_doc_id> --divider --text "### ⚠️ 操作红线" --bullet "严禁自动关闭或重启任何网关..."
```

### Memory Docs — Append new rules
⚠️ **CRITICAL**: Call `lark doc append` separately for each text block. Multiple `--text` flags in one call silently drops all but the last.

```bash
# CORRECT — separate calls
lark doc append <memory_doc_id> --text "Rule 1"
lark doc append <memory_doc_id> --text "Rule 2"
lark doc append <memory_doc_id> --text "Rule 3"
```

## Step 6: Verify

```bash
lark doc get <doc_id> | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content'][-500:])"
```

## Agent → Feishu Doc ID Mapping

| Agent | Profile Doc ID | Memory Doc ID | Folder Token |
|-------|---------------|---------------|--------------|
| 黑执事 (default) | LQbndYO2vowyN3xSAPNcJc6Vnyg | VHEvdPsrXooUFYxcGZjcyg9mnxl | OSJtfkVXrl8q0SdzU24c6LsMnNf |
| 凛子 (hr-assistant) | Z7nadOQNnoVlzQxgBkEcq6BznMc | THxNdml89olQ5bxPXaAcvnESnne | IdI2f33ZCljdE6dIAgBcomQonNe |
| 添添开心 (data-master) | CpFAd7dQaosdA1xOgK5clFeUnwf | XT3kdqL7Ao09Z9x4hCkci44Snic | SpYKfg5t0l9s4qdQbh0cgqFdnXe |

## Notes
- 凛子's Memory doc already contains extensive history (multiple dated update blocks) — it's append-heavy by design
- 黑执事 and 添添开心 Memory docs are cleaner (newer)
- Feishu API cannot delete/replace doc blocks — only append. To "clean" a doc, create new and inform user to delete old manually.
