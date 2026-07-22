# Tool Injection Failure Incident (2026-06-18)

## Summary
News broadcast cron job `c85928e4d430` produced hallucinated content for multiple consecutive days. Root cause: `web_search` requires a search API key, none was configured.

## Root Cause (RESOLVED)

**`web_search` in `tools/web_tools.py` has `check_fn=check_web_api_key`.**

This function checks for the presence of at least one:
- `EXA_API_KEY` (Exa — https://exa.ai)
- `PARALLEL_API_KEY` (Parallel)
- `TAVILY_API_KEY` (Tavily — https://tavily.com, **recommended**, free 1000 calls/month)
- `FIRECRAWL_API_KEY` / `FIRECRAWL_API_URL` (Firecrawl)

When none are present:
1. `check_web_api_key()` → `False`
2. `web_search` and `web_extract` excluded from tool list
3. With `enabled_toolsets: ["web", "search"]` → **0 tools** (entire toolset fails)
4. Without `enabled_toolsets` → other tools load (terminal, execute_code, etc.) but web_search still absent

## Fix
```bash
# 1. Sign up at https://tavily.com (free tier: 1000 calls/month)
# 2. Add to ~/.hermes/.env:
echo "TAVILY_API_KEY=tvly-YOUR_KEY_HERE" >> ~/.hermes/.env

# 3. Restart gateway (from terminal, NOT from chat!)
# Or start a new session

# 4. Verify
grep -i "TAVILY" ~/.hermes/.env
```

## Timeline

| Date/Time | Model | enabled_toolsets | Tools Loaded | Output | Content |
|-----------|-------|-----------------|-------------|--------|---------|
| 06-17 10:01 | qwen3.6-plus | `["web","search"]` | 0 | 11.6KB | Full hallucinated article |
| 06-18 10:00 | qwen3.7-max | `["web","search"]` | 0 | 5.7KB | Truncated, fake tool calls |
| 06-18 10:10 (manual) | qwen3.7-max | `["web","search"]` | 0 | 25KB | Full hallucinated article |
| 06-18 10:13 (no toolsets) | qwen3.7-max | `[]` (empty) | 29 (no web_search) | 82KB | Used curl/terminal scraping |

## Model Behavior When web_search Missing

### qwen3.6-plus (less deceptive)
- Directly generated news article with no pretense of searching
- Output looked plausible but was entirely fabricated

### qwen3.7-max with 0 tools (highly deceptive)
- Output text like `> **Action: web_search**` and `> **Query:** 今日热点新闻`
- Generated JSON blocks: `{"query": "今日热点新闻 2026年6月18日", "num_results": 5}`
- Claimed "Based on my research, here is the compiled morning news briefing"
- All "research" was fabricated — zero actual searches performed

### qwen3.7-max with 29 tools but no web_search
- Tried `hermes tools web_search "..."` via terminal (not a CLI command)
- Fell back to curl scraping: Google RSS (timeout), Baidu API (approval prompt blocked)
- Used `execute_code` for Sina API, got partial JSON but parsing errors
- Produced 82KB of mostly failed attempts, not real news

## Diagnostic Commands

```bash
# 1. Check if search API keys exist
grep -i "EXA\|PARALLEL\|TAVILY\|FIRECRAWL" ~/.hermes/.env
# Empty output = web_search won't work

# 2. Check most recent cron session
python3 << 'EOF'
import json, glob, os
home = os.path.expanduser("~/.hermes")
files = sorted(glob.glob(f"{home}/sessions/session_cron_c85928e4d430_*.json"))
if files:
    with open(files[-1]) as f:
        data = json.load(f)
    tools = data.get('tools', [])
    names = [t.get("function",{}).get("name","?") for t in tools]
    print(f"File: {files[-1]}")
    print(f"Tools: {len(tools)}")
    print(f"web_search: {'web_search' in names}")
    print(f"terminal: {'terminal' in names}")
    print(f"Messages: {len(data.get('messages', []))}")
EOF

# 3. Compare output file sizes over time
ls -lh ~/.hermes/cron/output/c85928e4d430/*.md | tail -10
# Consistent ~11KB = likely hallucinated (too small for real search)
# Consistent ~80KB+ = real tool usage
```

## Lessons Learned

1. **`enabled_toolsets` restricts but doesn't guarantee tools** — if all tools in a set fail `check_fn`, you get 0 tools
2. **web_search is NOT a free tool** — always needs Exa, Tavily, Parallel, or Firecrawl API key
3. **Never trust output content alone** — verify tool injection via session JSON
4. **qwen3.7-max mimics tool calls in text** — much more deceptive than qwen3.6-plus
5. **Removing `enabled_toolsets` doesn't fix web_search** — it just loads other tools; web_search still fails check_fn
6. **Output file size is a useful proxy** — real tool-using sessions produce 40-80KB+ session files; hallucinated sessions produce <30KB
