---
name: presentation-visual-director
description: Provide visual direction, composition constraints, image-sizing rules, render-based visual QA, and attachment-free draft review for presentations. Use together with the installed Presentations skill when the user explicitly asks for better-looking slides, visual/art direction, improved typography or image proportions, visual QA, inline or browser-based review, or to avoid receiving a new PPTX attachment on every review round. Do not use as a second PPTX generator.
---

# Presentation Visual Director

Act as the visual strategy and QA layer around the installed Presentations skill. Let Presentations remain the sole owner of PPTX creation, editing, rendering, and final export.

## Boundaries

- Do not create or edit PPTX independently of Presentations.
- Do not use `python-pptx`, a separate SVG-to-PPTX pipeline, or another presentation engine.
- Do not modify the installed Presentations skill.
- Do not create competing draft PPTX deliverables.
- Keep working decks, renders, contracts, and QA reports in the task's temporary workspace.
- A generated working PPTX is an internal implementation artifact, not a user-facing attachment.
- Deliver, cite, link, copy to a delivery location, or upload a PPTX only after the user has reviewed the rendered preview and explicitly approves export or delivery.
- Do not infer approval from task wording such as “调整”“优化”“做一版” or from the agent considering the requested task complete.
- If Presentations has a harder technical or delivery requirement, follow it. This skill refines visual choices; it does not override the implementation contract.

## Load the Required Guidance

- Read [visual-system.md](references/visual-system.md) before planning a new deck or materially restyling one.
- Read [review-rubric.md](references/review-rubric.md) before inspecting rendered slides or processing review feedback.
- Read [ppt-production-qa.md](references/ppt-production-qa.md) before final delivery QA — production QC acceptance gates (editable-pptx / image-only modes, 12pt minimums, noAutofit, data-ledger consistency, native-chart & embedded-workbook checks, pilot-gate, blocker contract, QA report template). Review must use this standard as the acceptance contract.
- Read [feishu-deck-optimization-workflow.md](references/feishu-deck-optimization-workflow.md) when user provides a Feishu PPT link (`feishu.cn/file/<token>`) and asks for optimization — end-to-end recipe (download via files API, render, text-overflow check, montage, parallel vision diagnosis, tiered A/B/C report, confirm-then-build).
- Read both for a complete create-review-export workflow.

## Workflow

### 1. Establish the visual contract

Translate the brief into a compact internal `visual-contract.txt` in the temporary workspace. Define:

- audience, communication job, and desired impression;
- visual style and tone;
- typography scale and density tier;
- grid, margins, and alignment anchors;
- preferred slide archetypes;
- image roles, target prominence, aspect-ratio and crop policy;
- chart treatment and emphasis hierarchy;
- draft review mode: inline renders or persistent local preview.

Make reasonable defaults when the user has not specified these. Ask only when a missing choice would materially change the design.

### 2. Hand implementation to Presentations

Use Presentations to plan and build the deck. Treat `visual-contract.txt` as binding design guidance while respecting user-provided templates and references. Favor a small set of coherent compositions over free placement. Shorten or split content before shrinking type.

### 3. Run internal visual QA before user review

Render every slide. Inspect individual slides at full size and the whole deck as a montage. Apply [review-rubric.md](references/review-rubric.md). Fix hard failures and clear aesthetic failures before showing a draft to the user.

Keep a concise internal `visual-qa.txt` containing slide number, finding, evidence, and action. Do not attach this file unless requested. Do not expose or link the working PPTX at this stage.

### 4. Present the QA result for review without PPTX attachments

Default to one continuous production task:

1. Keep the working PPTX internal and do not provide a clickable file link.
2. Complete internal QA first; fix hard failures before asking the user to review.
3. Report the review findings and material design changes in the conversation.
4. Show representative or changed slide renders inline. For a small deck, show all slides; for a large deck, show a montage plus slides needing a decision.
5. Explicitly ask whether the visual direction is approved before producing a user-facing attachment.
6. If the user requests changes, apply them to the same internal working deck and re-render affected slides plus any neighboring slides needed to judge flow.
7. Repeat the render-review loop without delivering versioned PPTX attachments.

If a persistent local preview is practical, offer or start it when the user asks for browser-based review. Do not introduce an SVG editing pipeline solely for preview. Use rendered slide images as the source of truth unless the active presentation implementation already exposes a faithful interactive preview.

### 5. Finalize only after explicit approval

Treat clear statements such as “可以生成附件”“确认导出”“这版OK” or an explicit upload request as approval. Only then run the complete Presentations validation workflow, render all slides once more, and deliver one final PPTX. Preserve the working source internally only as required by the host workflow.

If the user asks for external delivery such as Feishu upload, complete the applicable delivery preflight and confirmation flow after visual approval. Visual approval does not replace upload confirmation.

## Feishu/TP-company Review Loop (小艾的 PPT review 工作流, CONFIRMED 2026-08-07)

For 小艾 (TP公司电商运营) reviewing a modified deck, the loop has hard rules learned from iteration (LB OPERATION TRAFFIC v4→v7):

**交付物形态 = 图片版 review，不是文件**
- 飞书环境 `MEDIA:/path` 内联图片**不渲染**（仅 tg/discord 有效）。图片 review 的正确姿势：
  1. 渲染每页 PNG（soffice → PDF → pymupdf 或 pdftoppm）
  2. 拼成 3×3 总览图（PIL，白底 padding 20px，按 P1..P9 顺序）
  3. `drive/v1/files/upload_all`（user OAuth + `drive:drive` scope）上传 → 发飞书链接
- 上传 parent_node 用根目录 token `nodcnnkM2lJvS2xjFQBBBRT4Eeg`（parent_type=explorer），空/无效报 1061044

**"内容不动" = 原始文案 + 图片 100% 保留**
- 用户说"内容不动/文案图片都要留下来"时：**禁止改写、重排、摘录原文案**。正确做法是整页嵌入原始渲染图（pymupdf 150dpi 渲染原 PDF 页面）作为 slide 底图 + LB 页脚红条。
- 在飞书文档里直接编辑时同理：保留原始 block 文本，只在指定位置插入新内容。

**用户圈页 = 只改圈出的页，其他页保持上一版不动**
- 用户会发批注图（红框圈出要改的页码）。只重做被圈的页，其余页完全复用上一版代码。
- 每次迭代基于上一个已确认版本（如 v4），而非从零重写：`gen_lb_ppt_vN.py` 复制上版 + 只改目标页函数。

**版式偏好（用户明确要求）**
- ❌ 大段文字堆叠（"不要大段文字输出"）
- ✅ 分点卡片排版：卡片模块（浅灰底 + 左侧红条 + 标题 + bullet 要点）、2×2/3×2 网格、大数字突出（如覆盖率 80–100% 用 20pt 大字）
- ✅ 需要贴图的位置留**灰色虚线占位块**（浅灰填充 + 灰边框 + 居中标注 `[ IMG ] xxx` + 小字注明"(等待小艾提供截图)"）
- ✅ 顶部 LB 风格红条 + 标题（20pt bold）+ 可选红色副标题

**Vision 不可用时的批注图解读**（vision provider 是纯文本模型报 400 时）：
- 红色像素分析：numpy 取 `(r>150)&(g<100)&(b<100)` → 按 3×3 格子统计 red pixel count → 圈中的页 >400px
- tesseract OCR（`-l chi_sim+eng`）确认版本和页面标题
- 不要依赖 vision_analyze（该环境必失败）

**PPTX 生成细节**
- 不要用"模版 21 页 + 追加 9 页"= 30 页（用户明确说"为什么生成 30 页，我需要只有 9 页"）。删模版页会导致 zip 损坏（duplicate name warning），正确做法：`Presentation()` 新建 16:9 空白文件（`slide_width=Emu(12192000)`, `slide_height=Emu(6858000)`），BLANK layout（index 6），从零构建目标页。
- 封面/章节页大图从模版提取：`zipfile` 解 `ppt/media/`，按 md5 匹配章节页图片。
- 交付前用 `soffice --headless --convert-to pdf` 验证无损坏 + pymupdf 检查文本是否溢出画布。

## PPT Skill Ecosystem (2026-08-08)

The global PPT-related skills form one ecosystem — 10 skills (6 production + 2 strategy + 1 router + 1 QA). Know the routing map when a deck task starts; full detail in `references/ppt-skill-routing.md`:

- `ppt-router` — **顶层路由入口**：任何 PPT/Deck 任务先经它判定（决策1 策略层是否介入 → 决策2 协调层是否介入 → Production Format），再流向对应 skill
- `ppt-master` — 主力生产：可编辑原生 PPTX，完整路由（Generate / Create Template / Fill Native / Enhance Native / **Full-slide Image → rw-consulting-ppt**），支持 quick-generate；来源 hugohe3/ppt-master v4.4.0（⭐43.8k）
- `ppt-workflow` — 可选协调层：代表页审核/逐页视觉锁（内容规划→视觉规范→图片稿→可编辑还原），确认通过后 Handoff 给 ppt-master；强制 native-chart + embedded workbook；无快速路径
- `rw-consulting-ppt` — 咨询级图片稿（image-only），即 ppt-master 第 5 条路由 Full-slide Image 的实现者；自带路由锁：要可编辑图表切 ppt-master
- `ecommerce-proposal-ppt` — TP 品牌提案改造（LB/JACQUEMUS），先 review → 确认 → 出 PPT
- `powerpoint` — 通用轻量 pptx 处理（创建/编辑/渲染/QA 脚本），**纯兜底**（无更专业 skill 命中时使用）
- `consulting-deck-strategist` — 策略蓝图（issue tree / claim-evidence map / page blueprint），产出后 handoff 给 ppt-master / rw-consulting-ppt
- `presentation-visual-director` (this skill) — 视觉方向、render QA、无附件审稿循环、approval gate
- `artifact-review-director` — 通用制品 QA 编排
- `ppt-production-qa` — **独立 skill**（全流程统一验收点，2026-08-08 从 references 提升）：editable-pptx / image-only modes, 12pt minimums, noAutofit, data-ledger consistency, native-chart + embedded-workbook checks, pilot gate, blocker contract, QA report template。本 skill 的 references/ppt-production-qa.md 与其内容一致，任何生产路径（ppt-master / rw-consulting-ppt / powerpoint / ecommerce-proposal-ppt）交付前都须过它
- `ppt-delivery` — **正式交付规范**（2026-08-08 新建）：命名（项目-任务-日期-versionN）、归档（飞书云空间指定文件夹 R4IHfas5VlWqpOdQzMbc5Kxvngh）、交付格式（pptx）、上传确认（视觉批准 ≠ 上传确认，须用户明确上传指令）、版本管理（新版本不覆盖历史版本）

Standard chain: **ppt-router 路由 → 策略规划（consulting-deck-strategist）→ 协调确认（ppt-workflow，可选）→ 生产（ppt-master / rw-consulting-ppt）→ 视觉 QA + 用户审稿（presentation-visual-director / artifact-review-director）→ 生产 QC 验收（ppt-production-qa）→ 正式交付（ppt-delivery）**. For "PPT skill 文字版/总览" requests, generate text-only output (no markdown tables — Feishu drops them), structured with emoji headers + short lists.

## Feedback Translation

Convert subjective feedback into measurable actions without flattening the user's taste:

- “文字太挤” → reduce copy, increase line spacing, enlarge the text area, or split the slide; do not default to smaller type.
- “图片太小” → promote it to hero or split-image status and rebalance the composition.
- “不够高级” → reduce decorative vocabulary, strengthen hierarchy, improve image quality, and increase intentional whitespace.
- “每页都一样” → vary adjacent silhouettes while preserving the same grid and visual system.
- “太像网页/UI” → remove card grids, pills, tabs, and repeated panels; return to flat editorial composition.
- "重点不明显" → ensure one dominant visual element and demote competing elements.
- "大段文字" / "要学会分点排版论述，不要大段文字输出" (TP/宝尊电商提案场景，2026-08-07) → convert long paragraphs into "小节标题 + • 要点" bullet structure (section titles bolded in brand accent color, items as bullet lists); never leave a slide as one wall of text. Content-bearing images become gray dashed placeholder boxes labeled with what image goes there (e.g. "[IMG] STORE TRAFFIC STRUCTURE CHART") until the real asset is available.

## Output Discipline

- During review, communicate what changed and show renders; do not cite, link, attach, copy, or upload the working PPTX as a deliverable.
- A local PPTX path rendered as a clickable link counts as an attachment and is prohibited before approval.
- Never attach scratch plans, visual contracts, QA ledgers, or preview assets unless requested.
- On final delivery, follow the Presentations skill's required citation and handoff format.

## Hermes 适配说明（Environment Adaptation）

This skill was adapted from the Codex skill collection for Hermes. Replacements:

- **Owning generator**（Hermes 无 Codex 的 Presentations skill）：用系统 python3 + python-pptx 创建/编辑 PPTX（`powerpoint` skill 亦可用）。本 skill 只管视觉方向与 review 流程，生成归 python-pptx。
- **Render & review**：`soffice --headless --convert-to pdf` 转 PDF → `pymupdf`（`import pymupdf`，fitz 已弃用）`get_pixmap(dpi=110)` 逐页渲染 PNG → 对话里用 `MEDIA:/path.png` 内联展示。
- **QA 检查**：渲染后逐页用 pymupdf `get_text("blocks")` 检查文本是否溢出页面边缘（x1 > W-5 或 y1 > H-5）。**vision_analyze 2026-08-08 实测可用**（deepseek-v4-flash 成功返回逐页详细诊断，质量高）——逐页视觉诊断优先用 vision_analyze（多页可并行调用），仅当报 400 deserialize（vision provider 不支持 image_url）时 fallback 到文本块检查 + 直接把截图 MEDIA: 发给用户。

## 视觉元素决策（图表/图片/留白判断）

每页一个主视觉元素，从四类中选一：**陈述句 / 大数字 / 图片 / 图表**。其余元素降级为配角（communication hierarchy）。

**用图表（Chart）**：页面有需要比较/看趋势/看占比/看分布的数据
- 增长趋势 → 折线图；结构占比 → 饼/条形图；多项对比 → 柱状/雷达图；相关性 → 散点图
- 铁律：图表是证据不是装饰 → 必须配一句 explicit takeaway（"chart + one explicit takeaway" 标准版式）；数据真实可追溯（data-ledger）；原生可编辑 + 嵌入数据源（native-chart + embedded workbook）
- 只有 2-3 个数字时不做图表 → 大数字排版（32-52pt）更震撼

**用图片（Image）**：按角色分配（详见 references/visual-system.md §4）
- Hero（45-70%）情绪锚点 / Split（40-60%）图文对半 / Background（100%）氛围+安全文字区 / Evidence（30-55%）可检视事实（产品图/截图/实拍，须完整展示）/ Supporting（20-35%）辅助 / Accent（<15%）可不用
- 一页通常一张主图；多图必须有关系（对比/序列/集合）；有意义的图绝不缩成邮票

**什么都不用**：单一结论 → 一句话+强留白（breathing 页）；流程/结构 → 时间轴/流程图示（比图片信息量更高）；过渡 → 章节分隔页

**TP 公司场景（小艾）**：大段文字一律拆"小节标题+bullet"卡片；待贴图位置用灰色虚线占位块 `[IMG] xxx`；大数字突出（20pt+）；**有占比/进度数据优先可视化**（如流量结构堆叠图、覆盖率进度条），这是"用图表"的第一优先触发信号。
- **用户 review 偏好（小艾，2026-08-07 明确纠正）**：先出图片版 review 到对话（MEDIA:），用户确认 OK 后才交付 PPTX 文件；不要把改好的新 PPT 直接当 review 发文件链接。

### python-pptx 模板改造陷阱（CONFIRMED 2026-08-07）

- **❌ 不要用 drop_rel + 从 `_sldIdLst` 删除模版 slide 来"清空模版"**：python-pptx 保存时旧 slide part 仍在包内，产生 `Duplicate name: ppt/slides/slideN.xml` 警告，生成的 PPTX **LibreOffice 无法加载**（"source file could not be loaded"）。
- **✅ 正确做法：保留模版全部 slide，用 `prs.slides.add_slide(blank_layout)` 追加新页**。review 时只渲染追加页区间（如 21-30 页）给用户看，不影响模版原有页。
- 找 BLANK layout：`for l in prs.slide_layouts: if l.name == 'BLANK'`，找不到用 `layouts[-1]`。
- 对齐模版风格先探测：遍历模版各页 shapes 的 position/size/font（`sh.has_text_frame` → runs 的 font.name/size/bold/color）；提取 media 图片供复用（zipfile 读 `ppt/media/*`，用 md5 匹配每页用的图）。
- 渲染验证：`soffice --headless --convert-to pdf --outdir <dir> <file>.pptx`，超时给 120-150s（10MB 级文件，转换慢属正常）。
