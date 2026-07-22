---
name: xhs-content-ops
description: >-
  小红书全链路内容运营 SOP：数据获取 → 图文/视频拆解 → 账号诊断 → 笔记生成 → 知识沉淀 → 发布。
  包含爆款拆解、知识管理、笔记写作、发布评论等子流程的详细 SOP。
  当用户说"小红书运营"、"爆款拆解"、"对标产出"、"内容流水线"、"写小红书"、"小红书发布"时加载。
metadata:
  hermes:
    tags: [xiaohongshu, content-ops, pipeline, orchestration, publishing, knowledge-base, note-writing]
    related_skills: [viral-video-studio, social-account-doctor, humanizer]
---

# 小红书全链路内容运营 SOP

## SOP 7 步流水线

```
① 数据获取 → ② 图文拆解 → ③ 视频拆解 → ④ 账号诊断 → ⑤ 知识沉淀 → ⑥ 笔记生成 → ⑦ 发布
  Tavily+浏览器  viral-copy-pipeline  viral-video-studio  social-account-doctor  knowledge-base  note-writer  publish-comments
```

| SOP 环节 | 详细流程 | 核心能力 |
|---|---|---|
| ① 数据获取 | Tavily API + browser_navigate | 笔记URL→正文/互动数据 |
| ② 图文拆解 | `references/viral-copy-pipeline.md` | 爆款结构提取 + 封面分析 + 复刻模板 |
| ③ 视频拆解 | `viral-video-studio` skill | 6维度拆解 + ffmpeg抽帧 + 字幕 + 飞书资产库 |
| ④ 账号诊断 | `social-account-doctor` skill | 找对标→拆爆款→套自己 + 诊断模式 |
| ⑤ 知识沉淀 | `references/knowledge-base-structure.md` | 5类记录(account/topic/pattern/action/review) |
| ⑥ 笔记生成 | `references/note-writer.md` | 5种标题公式 + 卡片组 + 图生图 + 去AI味 |
| ⑦ 发布SOP | `references/publish-and-comments.md` | 发布流程 + 评论互动 + 风控 |

## 典型工作流

### 爆款拆解→对标产出（最常见）
1. 用户给爆款URL → ① Tavily/browser 提取内容
2. 判断图文还是视频 → ② references/viral-copy-pipeline.md 或 ③ viral-video-studio 拆解
3. 拆解结果 → ⑤ references/knowledge-base-structure.md 沉淀
4. 结合用户产品 → ⑥ references/note-writer.md 生成对标笔记
5. 去AI味（humanizer 已内置于 note-writer Step 4）

### 账号诊断→内容规划
1. 用户给账号信息 → ④ social-account-doctor 找对标+诊断
2. 诊断结果 → 确定内容方向
3. ⑤ references/knowledge-base-structure.md 记录诊断结论
4. ⑥ references/note-writer.md 产出下一条笔记初稿

## Skill 结构

本 skill 是小红书全链路运营的 umbrella，包含以下子流程的详细内容：

| 子流程 | 文件 | 说明 |
|---|---|---|
| 爆款拆解 | `references/viral-copy-pipeline.md` | URL输入→分析→复刻模板 |
| 知识沉淀 | `references/knowledge-base-structure.md` | 5类记录结构+搜索方法 |
| 笔记生成 | `references/note-writer.md` | 图文卡片/视频脚本生成 |
| 发布评论 | `references/publish-and-comments.md` | 发布流程+评论互动+风控 |
| 去AI味 | `references/humanizer-zh.md` | 中文文本人性化 |
| 爆款方法论 | `references/xiaohongshu-viral-methodology.md` | 5大核心原则+卖点分析 |
| 素材处理 | `references/material-intake.md` | 素材清点与分类 |
| 封面配图 | `references/image-sourcing.md` | 封面图获取策略 |
| curl提取 | `references/xhs-content-extraction-via-curl.md` | Tavily不可用时，curl+移动端UA提取帖子内容和图片 |

跨平台技能（独立 skill，不在本 umbrella 内）：
- `viral-video-studio` — 多平台视频拆解 + 飞书资产库
- `social-account-doctor` — 多平台账号诊断 + 对标分析

## 环境依赖状态

| 依赖 | 状态 | 用途 |
|---|---|---|
| yt-dlp | ✅ 已安装 v2026.06.09 | 视频下载（抖音/B站/快手） |
| ffmpeg | ✅ 已安装 v6.1.1 | 关键帧提取 + 字幕转换 |
| Tavily API Key | ⚠️ 未确认 | 网页内容提取（1000次/月免费）— 2026-07 session 中 env 未检测到，需确认配置 |
| Pillow | ❌ 未安装 | xhs-writer 卡片生成必需 |
| OpenAI API Key | ❌ 未配置 | xhs-writer 图生图（可选） |
| TikHub CLI | ✅ 已安装 | social-account-doctor 数据获取（CLI 走 MCP，经常超时；优先用 REST API） |
| TikHub API Key | ✅ 已配置 ~/.env | REST API (`api.tikhub.io`) 稳定可用；MCP (`mcp.tikhub.io`) 经常超时 |

### TikHub API 快速指南
详见 `references/tikhub-api-endpoints.md`

**优先用 REST API + curl，不用 CLI（CLI 走 MCP 不稳定）：**
- 视频搜索: `GET /api/v1/tiktok/app/v3/fetch_video_search_result?keyword=XXX&count=20&sort_type=0&region=US`
- 用户搜索: `GET /api/v1/tiktok/app/v3/fetch_user_search_result?keyword=XXX&count=5`
- 用户帖子: `GET /api/v1/tiktok/app/v3/fetch_user_post_videos_v3?sec_user_id=XXX&count=20&cursor=0` (仅首页) / `GET /api/v1/tiktok/app/v3/fetch_user_post_videos?sec_user_id=XXX&max_cursor=0` (翻页用v1)
- OpenAPI spec: `GET /openapi.json` (带 auth header)
- Auth: `Authorization: Bearer <key from ~/.env TIKHUB_API_KEY>`

**响应结构:** `data.search_item_list[].aweme_info` → `statistics.{digg_count, comment_count, share_count, play_count, collect_count}`, `author.{unique_id, nickname, custom_verify, sec_uid}`

## 已知问题 & 调试项

详见 `references/debug-checklist.md`。

## Pitfalls

- **TikHub CLI 需要先 refresh:** 首次使用或工具列表不存在时，必须运行 `python3 ~/.hermes/skills/social-media/social-account-doctor/tikhub/scripts/refresh_tools.py <platform>` 缓存工具目录
- **TikHub CLI 走 MCP 经常超时:** 优先用 REST API + curl，不要依赖 CLI
- **TikHub hashtag search 端点无效:** `/api/v1/tiktok/app/v3/fetch_hashtag_search_result` 返回 0 结果。替代方案：用视频搜索端点 + hashtag 作为关键词（如 `keyword=crumbl+asmr`）
- **TikHub web search 端点不稳定:** `tiktok_web_fetch_search_video` 经常 RetryError，改用 `app/v3/fetch_video_search_result`
- **多词关键词需 URL encode:** `crumbl cookies` → `crumbl+cookies` 或 `%20` 编码
- **中文关键词在 TikTok 搜索效果差:** 中文搜索返回大量不相关内容，建议用英文关键词（如"chocolate chip cookie"而非"美式大曲奇"）
- **note-writer 路径**：原 xhs-writer-skill 中写死 `~/.claude/skills/xhs-writer-skill/`，已合并入本 skill 的 `references/note-writer.md`，脚本路径需使用 `~/.hermes/skills/social-media/xhs-content-ops/scripts/`
- **lark-cli vs 飞书 API**：viral-video-studio 用 lark-cli 操作多维表格，我们环境用飞书 REST API + User Access Token
- **小红书反爬**：yt-dlp 不支持小红书视频下载，必须浏览器兜底
- **Cloudflare Turnstile**：无头浏览器无法通过注册验证，Tavily等需要手动注册后配置 API Key
