# Lark CLI 部署进度与续办清单

## ✅ 已完成
- [x] `lark-cli` 二进制安装于 `~/.local/bin/lark`（Go 源码位于 `~/lark-cli/`）
- [x] 配置文件 `~/.lark/config.yaml` 已指向应用 `cli_aa9970856879dcd8`，region: `feishu`
- [x] App Secret `rMt3nn8T1bv4Ze2j9h5ahfGZ3KkhSS88` 已写入 `~/.bashrc`
- [x] 回调地址源码已修改：`~/lark-cli/internal/auth/server.go` 中 `GetRedirectURI()` 返回 `http://106.54.37.126:%d/callback`（公网 IP）
- [x] 已重新编译并安装：`cd ~/lark-cli && go build -o ~/.local/bin/lark ./cmd/lark/`
- [x] 环境变量 `LARK_CONFIG_DIR` 和 `LARK_APP_SECRET` 已加入 `~/.bashrc`

## ⏳ 待完成（续办步骤）

### 1. 飞书开放平台配置
1. 登录飞书开放平台 → 选择应用 `cli_aa9970856879dcd8`
2. 进入 **应用功能 → 安全设置**
3. 在 **重定向 URL** 中添加：`http://106.54.37.126:9999/callback`
4. ⚠️ **必须创建新版本并发布**，否则配置不会生效！

### 2. 云服务器安全组
1. 登录云服务器控制台（腾讯云/阿里云等）
2. 在安全组添加入站规则：TCP 端口 `9999`，来源 `0.0.0.0/0`
3. 确认防火墙未拦截：`sudo iptables -L -n | grep 9999` 应为空（不拦截）

### 3. 完成 OAuth 授权
```bash
source ~/.bashrc
fuser -k 9999/tcp 2>/dev/null || true
lark auth login
```
运行后会输出一个长 URL，复制后用浏览器打开，完成飞书登录授权。

### 4. 验证
```bash
lark auth status
```
应显示 `authenticated: true` 及过期时间。

## ⚠️ 注意事项
- 每次修改 `server.go` 中的回调地址后，都需要重新编译
- `LARK_APP_SECRET` 是敏感信息，仅存于 `~/.bashrc` 和全局 `.env` 中
- 如果重启服务器，确保 `source ~/.bashrc` 后再运行 lark 命令
