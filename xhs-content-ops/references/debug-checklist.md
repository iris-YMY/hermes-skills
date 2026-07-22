# 小红书全链路 SOP — 调试清单

> 最后更新: 2026-07-15

## 🔴 P0 — 基础依赖（阻塞后续所有步骤）

| # | 调试项 | Skill | 问题 | 修复命令 |
|---|--------|-------|------|---------|
| 1 | 安装 Pillow | xhs-writer | ❌ 未安装 | `pip install Pillow` |
| 2 | 修正路径硬编码 | xhs-writer | SKILL.md 写死 `~/.claude/skills/` | sed 替换为 hermes 路径 |
| 3 | social-account-doctor 依赖 | social-account-doctor | requirements.txt 未装 | `pip install -r requirements.txt` |

## 🟡 P1 — 核心功能（直接影响日常使用）

| # | 调试项 | Skill | 问题 | 验证方法 |
|---|--------|-------|------|---------|
| 4 | Tavily 抓小红书 | 数据获取 | 未测试效果 | 用笔记URL测试 Tavily extract |
| 5 | 浏览器抓小红书 | 数据获取 | 反爬+DOM提取 | browser_navigate → browser_console |
| 6 | yt-dlp 下载抖音 | viral-video-studio | 可能需cookies | 测试裸连 vs cookies |
| 7 | yt-dlp 下载B站 | viral-video-studio | CC字幕提取 | 测试字幕获取 |
| 8 | 小红书视频下载 | viral-video-studio | yt-dlp不支持 | 浏览器兜底方案 |
| 9 | lark-cli→飞书API | viral-video-studio | skill用lark-cli | 替换为REST API+User Token |
| 10 | Vision AI帧分析 | viral-video-studio | 未端到端测试 | vision_analyze分析关键帧 |
| 11 | TikHub CLI测试 | social-account-doctor | ✅ REST API可用，MCP不稳定 | 优先用REST API降级 |
| 12 | analyze_image.py | social-account-doctor | 封面视觉分析 | 用小红书封面测试 |
| 13 | xhs-viral-copy端到端 | xhs-viral-copy | 图文拆解→复刻 | 用爆款URL跑全流程 |

## 🟢 P2 — 增强功能

| # | 调试项 | Skill | 问题 | 验证方法 |
|---|--------|-------|------|---------|
| 14 | OpenAI API Key | xhs-writer | 图生图需要 | 用户提供或找替代 |
| 15 | 飞书多维表格写入 | viral-video-studio | API未测试 | 创建Base→写入→验证 |
| 16 | 知识库初始化写入 | xhs-knowledge-base | 目录空 | 首次写入测试 |
| 17 | 小红书登录+Cookie | xhs-publish | 需QR扫码 | 浏览器登录→保存cookie |
| 18 | 发布自动化 | xhs-publish | 反爬+风控 | 测试创作后台操作 |
| 19 | 评论互动 | xhs-publish | 通知→回复→风控 | 限速+随机延迟 |
| 20 | PDF报告生成 | social-account-doctor | render脚本 | 需装weasyprint |

## 执行顺序

```
P0 #1~#3（5min）→ P1 #4~#5（20min）→ P1 #6~#8（15min）
→ P1 #9~#10（15min）→ P1 #11~#13（15min）→ P2 按需
```
