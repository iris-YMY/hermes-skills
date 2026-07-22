# OpenClaw → Hermes Agent 适配指南

> 从 OpenClaw 生态的 skill 移植到 Hermes Agent 时使用的工具映射表。

## 浏览器工具映射

| OpenClaw 工具/模式 | Hermes Agent 等效 | 备注 |
|---|---|---|
| `browser.start --profile openclaw` | `browser_navigate(url)` | Hermes 无 profile 概念 |
| `evaluate` (JS执行) | `browser_console(js_code)` | 直接等效 |
| `snapshot` (页面DOM) | `browser_snapshot()` | 直接等效 |
| `browser.upload` | `browser_click` 上传按钮 + 文件对话框 | 需测试 |
| `type` (逐字输入) | `browser_type(selector, text)` | 直接等效 |
| `fill` (表单填充) | `browser_type` 或 `browser_click` + type | 视实现而定 |
| `navigate` | `browser_navigate(url)` | 直接等效 |
| `click` | `browser_click(selector)` | 直接等效 |

## 路径替换

| OpenClaw 路径 | Hermes 路径 |
|---|---|
| `/tmp/openclaw/uploads` | `/tmp/hermes-uploads/` 或 tempdir |

## 需删除的内容

- 所有 `profile="openclaw"` 引用（~18处）
- `clawhub` 包管理器引用
- `openclaw-manager` 能力检查
- `https://docs.openclaw.ai/tools/browser` 链接
- 整个 `Openclaw一键安装.md` 文件

## 图片生成替换

| OpenClaw 工具 | Hermes 替代 |
|---|---|
| Nano Banana / nano-banana-pro | gpt-image-2 或 vision_analyze |

## 适配检查清单

1. `grep -r "openclaw\|clawhub\|profile=\"openclaw\"" <skill-dir>/` → 应为 0
2. 所有浏览器操作使用 `browser_navigate/snapshot/console/click/type`
3. 图片生成使用 gpt-image-2 或 Hermes 内置 vision 能力
4. 文件路径不使用 `/tmp/openclaw/`
