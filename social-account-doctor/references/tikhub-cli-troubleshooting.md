# TikHub CLI Troubleshooting Reference

> 实测日期：2026-07-15 | 环境：腾讯云服务器 (Ubuntu 22.04)

## 1. Tool Catalog 过期问题

### 症状
```bash
$ tikhub xiaohongshu xiaohongshu_app_search_notes --keyword 咖啡 --page:int=1
Unknown tool: xiaohongshu_app_search_notes
```

### 原因
本地 `references/tools-xiaohongshu.json` 缓存的是旧工具目录。TikHub MCP 端点已下线 V1 工具（无 `_v2` 后缀的版本），只保留 V2 + Web V2/V3。

### 修复
```bash
cd ~/.hermes/skills/social-media/social-account-doctor/tikhub
export TIKHUB_API_KEY="your-key"
python3 scripts/refresh_tools.py xiaohongshu
# [xiaohongshu] wrote 43 tool(s) → references/tools-xiaohongshu.json
```

## 2. V1 → V2 工具名映射

| 旧名（V1，已下线） | 新名（V2，当前可用） |
|---|---|
| `xiaohongshu_app_search_notes` | `xiaohongshu_app_v2_search_notes` |
| `xiaohongshu_app_search_users` | `xiaohongshu_app_v2_search_users` |
| `xiaohongshu_app_get_note_info` | `xiaohongshu_web_v3_fetch_note_detail` 或 `xiaohongshu_app_v2_get_image_note_detail` |
| `xiaohongshu_app_get_note_comments` | `xiaohongshu_app_v2_get_note_comments` |
| `xiaohongshu_app_get_user_info` | `xiaohongshu_web_v3_fetch_user_info` 或 `xiaohongshu_app_v2_get_user_info` |
| `xiaohongshu_app_get_user_notes` | `xiaohongshu_web_v2_fetch_home_notes_app` 或 `xiaohongshu_app_v2_get_user_posted_notes` |
| `xiaohongshu_web_search_notes` | `xiaohongshu_app_v2_search_notes` |

## 3. API Key 验证

### 成功（health check）
```bash
$ tikhub --health
{"status":"healthy","version":"2.0.0","platforms":17,"total_endpoints":1017}
```

### Key 无效/过期 → Cloudflare 403
```
HTTP Error: 403
Body: {"type":"...error-1010/","title":"Error 1010: Access denied",
"detail":"The site owner has blocked access based on your browser's signature."}
```

### Key 配置后工具仍报 RetryError
```bash
$ tikhub xiaohongshu xiaohongshu_app_v2_search_notes --keyword 咖啡 --page:int=1
{"error": "RetryError[<Future ... raised HTTPStatusError>]"}
```
可能原因：
- **API Token 权限不足**（最常见！403 "lacks required permissions"）→ 用 REST API 确认：`curl -s "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes?keyword=test&page=1" -H "Authorization: Bearer $KEY"` → 如果返回403+权限提示，去 https://user.tikhub.io/dashboard/api 编辑 token scopes
- Key 额度用完（免费档有限额）
- 服务端限流（RPS 上限 10/s）
- 云服务器 IP 被风控

### MCP 端点超时（initialize 挂起 60s+）
```bash
$ tikhub xiaohongshu xiaohongshu_app_v2_search_notes --keyword 咖啡 --page:int=1
[tikhub] POST https://mcp.tikhub.io/xiaohongshu/mcp method=initialize session=None
[Command timed out after 60s]
```
**原因**: MCP 端点 (`mcp.tikhub.io`) 的 SSE streaming 连接被卡住（0 bytes received）。这是 MCP 网关问题，不是 key 问题。

**修复**: 改用 REST API (`api.tikhub.io`) 直接调用（见 tikhub-troubleshooting.md §Fallback 1）：
```bash
curl -s --max-time 30 \
  "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes?keyword=咖啡&page=1" \
  -H "Authorization: Bearer $TIKHUB_API_KEY"
```

## 4. 降级策略

TikHub 不可用时的替代方案：

| 任务 | 降级方案 |
|---|---|
| 搜索笔记 | Tavily 搜索第三方分析报告 + 用户手动提供 |
| 笔记详情 | 用户截图/复制内容 |
| 用户信息 | 用户手动提供账号链接 + 截图 |
| 评论分析 | 用户截图 |

## 5. 环境配置速查

```bash
# ~/.claude/.env
TIKHUB_API_KEY=your-key-here

# symlink
ln -sf ~/.hermes/skills/social-media/social-account-doctor/tikhub/bin/tikhub ~/.local/bin/tikhub

# PATH
export PATH="$HOME/.local/bin:$PATH"

# 验证
tikhub --health
tikhub list xiaohongshu  # 应显示 43 个工具
```

## 6. 费用预估

| 诊断类型 | 预估调用次数 | 费用 |
|---|---|---|
| 单品牌完整诊断 | 30-50 次 | ~$0.3-0.5 |
| 5品牌对比诊断 | 100-200 次 | ~$1-2 |
| 10品牌大规模诊断 | 200-500 次 | ~$2-5 |

免费额度用完后按次计费 $0.01/次。
