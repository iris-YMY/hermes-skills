# Agent-Reach Installation on Chinese Cloud Servers

**Repo**: https://github.com/Panniantong/Agent-Reach (⭐40K+, MIT, Python CLI)
**What it does**: Gives AI agents read/search access to 13 internet platforms (Twitter, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu, etc.) via a unified capability layer.

---

## Installation Pitfalls (Tencent Cloud / Chinese VPS)

### Chain of failures encountered 2026-06-25:

1. **`pip install agent-reach` fails** — package not published on PyPI. Tencent mirror (`mirrors.tencentyun.com`) returns "No matching distribution". Must install from source.

2. **`pip install git+https://github.com/...` fails** — GnuTLS TLS connection error from Chinese servers. GitHub direct HTTPS is unreliable.

3. **`git clone https://github.com/...` times out** — same network issue, even with `GIT_SSL_NO_VERIFY=1`.

### Working solution: GitHub mirror proxy

```bash
# Clone via mirror (either works)
git clone --depth 1 https://ghfast.top/https://github.com/Panniantong/agent-reach.git /tmp/agent-reach
# OR
git clone --depth 1 https://mirror.ghproxy.com/https://github.com/Panniantong/agent-reach.git /tmp/agent-reach

# Then install from local
cd /tmp/agent-reach
pip install --break-system-packages .
```

### Externally-managed Python environment
Ubuntu 24.04+ uses PEP 668. Use `--break-system-packages` flag or install via the hermes venv:
```bash
pip install --break-system-packages .
# OR find hermes venv pip and use that
```

### Post-install: mcporter + Exa (MCP search)
```bash
sudo npm install -g mcporter          # needs sudo for global install
mcporter config add exa https://mcp.exa.ai/mcp
```

### gh CLI (GitHub CLI)
`apt install gh` times out on Chinese servers due to slow international links. Options:
- Download binary directly: https://github.com/cli/cli/releases
- Use a mirror/apt proxy
- Skip if not needed (GitHub search works via `gh` commands only after auth)

---

## Expected Result on Chinese Server

After installation, `agent-reach doctor` typically shows:

| Channel | Status | Notes |
|---------|--------|-------|
| YouTube | ✅ | yt-dlp works |
| RSS | ✅ | feedparser works |
| Exa Search | ✅ | MCP via mcporter |
| Web pages | ✅ | Jina Reader (`curl https://r.jina.ai/URL`) |
| Bilibili | ✅ | Search API (curl direct) |
| GitHub | ⚠️ | Needs gh CLI install |
| V2EX | ⚠️ | API blocked from China |
| Twitter/Reddit/XHS | 🔒 | Need Cookie + login state |

---

## Quick Commands After Install

```bash
# Health check
agent-reach doctor

# Exa web search
mcporter call 'exa.web_search_exa(query: "keyword", numResults: 5)'

# Read any web page
curl -s "https://r.jina.ai/URL"

# YouTube subtitles
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"

# Bilibili search
curl -s "https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=QUERY"
```

## Unlocking Login-Based Platforms

For Twitter/X, Reddit, XiaoHongShu — need Cookie authentication:
1. Install Cookie-Editor Chrome extension
2. Login to the platform in browser
3. Export cookies via Cookie-Editor
4. Send to agent for configuration

**Warning**: Use dedicated test accounts, not primary accounts — risk of platform bans for API-like access patterns.

## Uninstall
```bash
agent-reach uninstall          # Removes config, skills, MCP config
agent-reach uninstall --dry-run  # Preview only
pip uninstall agent-reach      # Remove Python package
```
