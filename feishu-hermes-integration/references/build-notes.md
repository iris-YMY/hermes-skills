# lark-cli Build Notes (Ubuntu/Cloud Server)

## Prerequisites
Go is required. If not installed:
```bash
# Option A: apt (needs sudo)
sudo apt-get install -y golang-go

# Option B: manual download (no sudo needed)
curl -sL https://golang.google.cn/dl/go1.22.5.linux-amd64.tar.gz | tar -xz
export PATH=$HOME/go/bin:$PATH
```

## Build from Source
```bash
git clone https://github.com/yjwong/lark-cli.git ~/lark-cli
cd ~/lark-cli
go build -o ~/.local/bin/lark ./cmd/lark/
lark version  # verify: should show "lark dev"
```

## Path Notes
- Binary: `~/.local/bin/lark` (user-level, no sudo needed)
- Config: `~/.lark/config.yaml`
- Tokens: `~/.lark/tokens.json`
- Mail cache: `~/.lark/mail_cache.db` (SQLite)

## Dependencies (auto-fetched by go mod tidy)
- cobra, viper (CLI framework)
- emersion/go-imap/v2 (mail)
- modernc.org/sqlite (local cache)
