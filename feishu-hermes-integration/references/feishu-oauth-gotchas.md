# Feishu OAuth Gotchas

## 1. Refresh Token 只能使用一次 ⚠️ CRITICAL

飞书 OAuth 的 `refresh_token` **只能使用一次**。即使刷新失败（如网络问题、code 被抢消耗），该 refresh_token 也会立即失效。

**症状：** 调用 `/authen/v2/oauth/token` 刷新时返回：
```json
{"error": "invalid_grant", "error_description": "The refresh token has been revoked. Please note that a refresh token can only be used once.", "code": 20064}
```

**根因：**
- `lark auth login` 后台进程可能自动尝试交换 code 并消耗 refresh_token
- 手动 curl 刷新与后台进程产生竞争
- 任何一次刷新尝试（即使失败）都会使 token 失效

**修复方案：**
- 如果 refresh_token 失效，**必须重新走完整的 OAuth 授权流程**（生成新授权链接 → 用户同意 → 交换新 code）
- 在手动交换 code 前，务必先 `fuser -k 9999/tcp` 杀掉所有 `lark auth login` 后台进程

## 2. App ID 与 Secret 不匹配

`~/.lark/config.yaml` 中的 `app_id` 必须与 `LARK_APP_SECRET` 环境变量对应同一个飞书应用。

**常见坑位（Hermes multi-profile 环境）：**
- `~/.lark/config.yaml` 可能写的是 hr-assistant 的 app_id（`cli_aa9ebcbfc6e35cba`）
- 但 `~/.bashrc` 中的 `LARK_APP_SECRET` 是 default profile 的 secret（对应 `cli_aa9970856879dcd8`）
- 两者不匹配时，tenant token 和 OAuth 均会返回 `app secret invalid` (code 10014)

**排查方法：**
```bash
# 验证哪个 secret 匹配哪个 app_id
curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"<APP_ID>","app_secret":"<SECRET>"}'
# 返回 {"code":0} 表示匹配，{"code":10014} 表示不匹配
```

## 3. OAuth Code 一次性消耗

授权码 `code` 只能用一次。`lark auth login` 后台进程、手动 curl 任何一方先消耗了 code，另一方就会收到 `20065 invalid_grant`。

**安全流程：**
1. `fuser -k 9999/tcp` 杀掉所有后台 auth 进程
2. 从日志提取授权链接
3. 用户授权后拿到 code
4. 立即用 curl 手动交换（不要依赖 `lark auth login` 自动回调）
5. 直接写入 `tokens.json`
