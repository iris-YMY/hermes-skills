# PPT Suite — Hermes Agent 演示文稿生产全家桶

一套完整的 PPT/Deck 生产流水线 skill 集合，覆盖从商业策略、视觉设计、生产制作到 QA 验收、交付归档的全流程。任何 PPT/Deck 相关请求（制作、创建、生成、改造、优化、模板、图片稿、咨询 deck、提案 PPT、视觉锁、代表页审核、验收、交付）都由统一入口 `SKILL.md`（ppt-router）路由调度。

## 目录结构

```
ppt-suite/
├── SKILL.md                   ← 统一入口：路由判定（继承 ppt-router）
├── README.md                  ← 本文件
├── ppt-router/                ← 🧭 路由层：策略 / 协调 / QA / 交付 / 视觉指导 / TP 提案改造
├── ppt-master/                ← ⚙️ 生产引擎：可编辑 PPTX 生成、模板、增强
├── powerpoint/                ← 🛟 兜底层：python-pptx 读写 / 渲染 / 简单操作
├── pptx-visual-analysis/      ← 🔍 视觉分析：提取模板视觉规范、字体、主题色
└── rw-consulting-ppt/         ← 🖼️ 图片稿：整页 PNG / image-only PPTX 交付
```

## 快速安装

```bash
# 方式一：直接复制（推荐）
cp -r ppt-suite ~/.hermes/skills/productivity/ppt-suite

# 方式二：只装路由入口（其余按需）
cp -r ppt-suite/ppt-router ~/.hermes/skills/productivity/ppt-router
cp -r ppt-suite/ppt-master ~/.hermes/skills/productivity/ppt-master
```

安装后 agent 即可识别 `ppt-suite`（统一入口）或各子 skill。

## 使用示例

对 agent 说：

- 「做一个 XX 品牌的提案 PPT」→ 路由到策略层 + ppt-master
- 「把这个 PPTX 优化一下，文字太多没重点」→ ppt-master Enhance
- 「按这个模板套一份新内容」→ ppt-master Fill Native Template
- 「把这几页做成整页图片的咨询 deck」→ rw-consulting-ppt
- 「分析这个 PPT 用了什么字体和颜色」→ pptx-visual-analysis

## 路由决策链（统一入口）

```
PPT / Deck 任务
  ├─ 商业问题/证据/结论/故事线不明确 → 策略层（consulting blueprint）
  ├─ 需要代表页审核/逐页视觉锁 → 协调层（visual-lock workflow）
  └─ 其余 → ppt-master Production Router
              ├─ 可编辑 PPTX → Generate / Fill / Enhance
              └─ 整页图片 → rw-consulting-ppt
        → ppt-production-qa 验收 PASS → ppt-delivery 交付（命名/归档/上传确认/版本管理）
```

详见 `ppt-router/SKILL.md`。

## 依赖

| Skill | 依赖 |
|-------|------|
| ppt-master | python-pptx、LibreOffice、Poppler、pptxgenjs（可选）、Pillow |
| powerpoint | python-pptx、markitdown[pptx]、Pillow、pdf2image、LibreOffice |
| rw-consulting-ppt | image_gen（AI 生图）、Pillow |
| pptx-visual-analysis | python-pptx、Pillow |

## 说明

- `ppt-router/references/` 内含完整的策略（consulting-deck-strategist）、协调（ppt-workflow）、视觉指导（presentation-visual-director）、QA 验收（ppt-production-qa）、交付规范（ppt-delivery）、TP 提案改造（ecommerce-proposal-ppt）SOP。
- `ppt-master/references/ai-image-comparison/` 的完整参考图集（约 19MB）已裁剪，仓库仅保留说明。
- `rw-consulting-ppt/examples/` 示例图已压缩，完整示例见历史版本。
