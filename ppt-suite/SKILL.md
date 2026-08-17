---
name: ppt-suite
description: PPT/Deck 生产流水线全家桶统一入口。整合 ppt-router（路由/策略/QA/交付）、ppt-master（生产引擎）、powerpoint（兜底操作）、pptx-visual-analysis（视觉分析）、rw-consulting-ppt（图片稿）为一套完整流水线。任何 PPT/Deck 相关请求（制作、创建、生成、改造、优化、模板、图片稿、咨询 deck、提案 PPT、视觉锁、代表页审核、验收、交付）都先经本入口判定流向，再激活对应子 skill。决策链：①商业问题/证据/结论/故事线是否明确 → 策略层；②是否需要代表页审核或逐页视觉锁 → 协调层；③其余直达 ppt-master 统一 Production Router。完整 SOP 见子 skill 目录。
---

# PPT Suite — 统一入口

本 skill 是 PPT/Deck 生产流水线全家桶的**统一入口**（路由层）。所有 PPT 相关请求先经本入口判定流向，再激活对应子 skill。

## 子 skill 结构

| 子 skill | 职责 | 触发场景 |
|----------|------|----------|
| `ppt-router/` | 路由 + 策略/协调/QA/交付/视觉/TP提案完整 SOP | 任何 PPT/Deck 请求的判定与全流程规范 |
| `ppt-master/` | 可编辑 PPTX 生产引擎 | 新建/模板/填充/增强演示文稿 |
| `powerpoint/` | 兜底 PPTX 操作 | 简单读写、渲染、转换、脚本操作 |
| `pptx-visual-analysis/` | 视觉规范提取 | 分析模板字体/颜色/版式 |
| `rw-consulting-ppt/` | 整页图片稿交付 | image-only deck、全页 PNG |

## 路由决策链

```
PPT / Deck 任务
  │
  ▼
【决策1】商业问题、证据、结论与故事线是否明确？
  ├─ 是 → 直接进入【决策2】
  └─ 否 → 策略层（consulting-deck-strategist，见 ppt-router/references/）
              │  产出：商业逻辑 • Storyline • 页面 Blueprint
              ▼
【决策2】是否需要代表页审核或逐页视觉锁？
  ├─ 需要 → 协调层（ppt-workflow，见 ppt-router/references/）
  └─ 不需要 / 已有成熟模板 → 直接进入生产层
              ▼
  生产层（Production Router）
    ├─ 可编辑 PPTX → ppt-master（Generate / Fill / Enhance）
    └─ 整页图片稿 → rw-consulting-ppt（Full-slide Image）
              ▼
  QA 验收（ppt-production-qa，见 ppt-router/references/）
    ├─ 通过 → 正式交付（ppt-delivery：命名/归档/上传确认/版本管理）
    └─ 未通过 → 返回生产层修正
```

## 使用指引

1. **读取本 skill（ppt-suite）** 判定请求流向
2. **按流向激活对应子 skill**：读取 `ppt-router/SKILL.md` 获取完整路由规则与 SOP 索引；读取 `ppt-master/SKILL.md`、`powerpoint/SKILL.md`、`pptx-visual-analysis/SKILL.md`、`rw-consulting-ppt/SKILL.md` 获取生产细节
3. **生产完成后**：按 `ppt-router/references/ppt-production-qa.md` 验收，PASS 后按 `ppt-router/references/ppt-delivery.md` 交付

## 子 skill 入口文件

- `ppt-router/SKILL.md` — 路由判定细则 + 全部 SOP 索引（策略/协调/QA/交付/视觉/TP提案）
- `ppt-master/SKILL.md` — 生产引擎使用（生成/模板/填充/增强）
- `powerpoint/SKILL.md` — 兜底操作（python-pptx 读写、渲染、编辑）
- `pptx-visual-analysis/SKILL.md` — 视觉规范提取分析
- `rw-consulting-ppt/SKILL.md` — 图片稿生产与打包
