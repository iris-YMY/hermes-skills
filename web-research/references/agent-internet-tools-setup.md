# Agent Internet Tools — Installation & Platform Reference

> Absorbed from `agent-internet-tools` skill (2026-07-06 consolidation)

## Agent-Reach

GitHub: https://github.com/Panniantong/Agent-Reach (40k+ stars, MIT, Python 3.10+)

A capability layer — not a wrapper. After install, agents call upstream tools directly. Handles routing, diagnostics, multi-backend failover.

### Supported platforms (13)

Zero-config: Web (Jina Reader), YouTube (yt-dlp), RSS (feedparser), Exa Search (MCP), Bilibili (search API), V2EX (API)
Cookie-required: Twitter/X (twitter-cli), Reddit (OpenCLI/rdt-cli), XiaoHongShu (OpenCLI/xiaohongshu-mcp), Xueqiu (API), LinkedIn (MCP)
Podcast: Xiaoyuzhou (Whisper transcription)

### Install on Chinese server (pitfalls)

```bash
# 1. PyPI: Tencent mirror doesn't have agent-reach. Clone from GitHub mirror first:
git clone --depth 1 https://mirror.ghproxy.com/https://github.com/Panniantong/agent-reach.git /tmp/agent-reach
# Alternatives: https://ghfast.top/https://github.com/...

# 2. Externally-managed Python (Ubuntu 24.04): use --break-system-packages
cd /tmp/agent-reach && pip install --break-system-packages .

# 3. gh CLI: apt install from GitHub repo is VERY slow from China. Use direct binary:
#    Download from https://github.com/cli/cli/releases, extract, copy to /usr/local/bin/

# 4. mcporter (Exa search): npm works fine
sudo npm install -g mcporter
mcporter config add exa https://mcp.exa.ai/mcp
```

### Post-install
```bash
agent-reach doctor              # Full status check
agent-reach doctor --json       # Machine-readable (for skill routing)
agent-reach install --channels=twitter,xiaohongshu  # Unlock specific channels
agent-reach install --channels=all                   # Unlock everything
```

### Cookie configuration flow
For Twitter/X, XiaoHongShu, Xueqiu, Reddit:
1. User logs into platform in browser (recommend alt account — ban risk)
2. Install Chrome extension Cookie-Editor
3. Export cookies → send to agent
4. Agent configures: platform-specific CLI reads cookie from `~/.agent-reach/config.yaml`

### Uninstall
```bash
agent-reach uninstall           # Full removal
agent-reach uninstall --dry-run # Preview only
pip uninstall agent-reach       # Remove Python package
```

## MCP Server Configuration (Hermes)

```bash
hermes mcp add NAME --url <url>       # Add HTTP MCP server
hermes mcp add NAME --command <cmd>   # Add stdio MCP server
hermes mcp list                        # Show configured servers
hermes mcp test NAME                   # Test connection
hermes mcp configure NAME              # Toggle tool selection
hermes mcp remove NAME                 # Remove
```

## Platform-specific CLI quick reference

| Platform | Command | Auth |
|----------|---------|------|
| Web | `curl -s "https://r.jina.ai/URL"` | None |
| Search | `mcporter call 'exa.web_search_exa(query: "...", numResults: 5)'` | None (free MCP) |
| YouTube | `yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"` | None |
| GitHub | `gh repo view owner/repo` / `gh search repos "query"` | `gh auth login` |
| Twitter | `twitter search "query" -n 10` | Cookie |
| Reddit | `opencli reddit search "query"` (desktop) / `rdt search` (server) | Cookie/login |
| Bilibili | `bili search "query" --type video -n 5` | None (search only) |
| XiaoHongShu | `opencli xiaohongshu search "query"` | Cookie |
| RSS | Python feedparser | None |

## Pitfalls

- **yt-dlp for Bilibili**: BROKEN as of 2026-06 (412 风控). Use bili-cli or B站搜索 API instead.
- **Reddit anonymous .json API**: DEAD. Must use login-state (OpenCLI or rdt-cli + Cookie).
- **Chinese server + GitHub**: Use mirror proxies (ghfast.top, mirror.ghproxy.com). Direct git clone will timeout.
- **Chinese server + V2EX/Reddit**: May need proxy configured (`agent-reach configure proxy http://...`).
- **Cookie platforms**: Always recommend alt accounts. Ban risk is real.
- **mcporter config path**: On server installs, config may land in `/tmp/agent-reach/config/mcporter.json` rather than global. Verify with `mcporter config list`.
