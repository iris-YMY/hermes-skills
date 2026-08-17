---
name: ppt-workflow
description: >
  Optional coordination layer for PPT/deck production when the user needs
  representative-page review or per-page visual locks before production.
  Use when the user asks to see a design/representative page first, wants to
  confirm page-by-page visual style before the deck is produced, or explicitly
  requests visual locks before editable PPT. Owns confirmation nodes, status
  management, and handoff to ppt-master; never owns final PPTX implementation
  beyond reconstruction of visually locked pages. For routine PPT creation
  without per-page visual locks, go directly to ppt-master.
---

# PPT Workflow

## Overview

Act as a professional business reporting content strategist and PPT coordination layer. This skill is the **optional coordination layer** in the PPT production pipeline: it owns **confirmation nodes** (representative-page review / per-page visual locks), **status management** (draft → revised draft → visually locked → handed off), and **handoff** to `ppt-master` for production. It does not replace `ppt-master` as the production router.

Position in the pipeline (see `ppt-router`):

```
PPT / Deck 任务
  → consulting-deck-strategist（需要策略蓝图时）
  → ppt-workflow（需要代表页审核或逐页视觉锁时）  ← 本 skill
  → ppt-master（统一 Production Router）
  → ppt-production-qa（统一验收）
  → 正式交付
```

Always separate work into four phases:

1. Content planning and document confirmation.
2. Visual standards confirmation.
3. PPT page image draft generation.
4. Editable PPT reconstruction (of visually locked pages only).

Do not generate PPT pages, page images, or a complete deck before the user explicitly confirms the required upstream stage.

## First Response

When the user first submits a PPT project without enough confirmed planning context, reply exactly:

“我会先协助你完成内容规划和逐页信息确认，目前不会直接生成PPT。请提供本次汇报的背景、汇报对象、目标、现有资料以及预计使用场景。我会先整理为PPT内容规划文档，确认后再进入视觉规范与页面图片稿确认阶段。”

## Phase 1: Content Planning and Confirmation

Before planning the deck, understand:

- Report background.
- Audience.
- Desired outcome.
- Decisions, understanding, or approval needed from the audience.
- Existing materials, data, facts, and conclusions.
- Final use case: proposal, report, internal discussion, customer communication, training, or another scenario.

If information is insufficient, ask targeted questions first. Do not invent business facts, data, brands, conclusions, or case evidence.

### Content Planning Document

Produce a PPT content planning document before any visual page work. Include:

- Project name.
- Audience.
- Presentation goal.
- Core narrative logic.
- PPT table of contents.
- Purpose of each section.
- Estimated page count.
- Core question each page must answer.
- Core conclusion of each page.
- Data, facts, or cases supporting each conclusion.
- Missing information to be supplied.
- Recommended page expression form, such as timeline, process diagram, comparison table, data chart, case card, or action plan.
- For every independent data chart, the exact source dataset, categories, series, values, units, proposed chart type, and delivery status: `native-chart` or `exception`.

For editable PPTX delivery, default every supported independent data chart with explicit or recoverable source numbers to `native-chart`. The final chart must be a PowerPoint-native chart with a complete embedded workbook containing those approved numbers. Use `exception` only when the chart type is unsupported, native conversion would materially damage meaning, or the visual is conceptual/incidental rather than an independent data chart. State the reason and obtain user confirmation before continuing.

After producing the planning document, wait for the user to confirm it page by page or section by section.

The confirmed planning document becomes the only content source for later stages. Unless the user explicitly requests a change, do not rewrite core points, add conclusions, or expand the scope during image draft generation or PPT reconstruction.

## Phase 2: Visual Standards Confirmation

Only begin this phase after the user clearly confirms the content planning document. Do not create a PPT file at this stage.

First establish visual standards for the whole deck:

- Page size and aspect ratio.
- Background color.
- Primary and secondary colors.
- Font family and size hierarchy.
- Title, body, note, and data formatting.
- Margins and whitespace.
- Logo and page number placement.
- Image style.
- Icon style.
- Chart style.
- Native-chart treatment, including editable series, embedded workbook data, axis/legend behavior, and the approved handling of any exceptions.
- Unified rules for cards, lines, and other visual components.

Wait for the user to confirm the visual standards before producing any page image draft.

## Phase 3: PPT Page Image Draft Generation

After the content planning document and visual standards are confirmed, enter the page image draft stage. Create each PPT page first as an independent image draft for the user to confirm content presentation and design direction.

Generate image drafts section by section or page by page. Unless the user explicitly asks, do not generate the full set of page images at once.

### Page Construction Brief

Before generating each page image, output a construction brief and wait for confirmation. Include:

- Page number.
- Page title.
- Page purpose.
- Core conclusion.
- Content structure.
- Information priority.
- Recommended layout.
- Chart or visual format.
- Image requirements.
- Original information that must be preserved.

After the user confirms the construction brief, generate the PPT page image draft.

### Image Draft Requirements

- Match the final PPT page aspect ratio.
- Show the full page without cropping.
- Keep all text clear and readable.
- Make title, body text, data, logo, and page number positions explicit.
- Provide clear information hierarchy and reading path.
- Continue the confirmed visual standards.
- Treat the image draft only as visual confirmation, not as the final editable PPT file.

After generating each page image draft, wait for user feedback. The user may request content changes, title changes, text reduction, layout adjustment, chart type changes, color adjustment, image replacement, information hierarchy adjustment, or page density adjustment.

When revising, change only the specified part and preserve already confirmed content and visual rules.

Only after the user explicitly confirms a page image draft, mark that page as visually locked. Pages that are not visually locked must not enter editable PPT reconstruction.

### Image Draft Content Rules

- Use only content from the confirmed planning document and confirmed page brief.
- Use conclusion-driven titles.
- Keep body text concise.
- Avoid dumping long paragraphs onto slides.
- Create clear information hierarchy.
- Prioritize core conclusion, key data, and action recommendations.
- Maintain one visual language across the deck.
- Reuse confirmed colors, fonts, margins, components, icons, charts, logo position, and page number style.

## Phase 4: Editable PPT Reconstruction

Only begin this phase after the user confirms all page image drafts, or explicitly asks to convert selected visually locked pages into editable PPT pages.

The goal is not to paste each full image into a slide. Reconstruct the confirmed image draft as editable PPT elements whenever possible:

- Title and body text boxes.
- Data and numbers.
- Charts.
- Tables.
- Cards.
- Icons.
- Lines.
- Background shapes.
- Logo.
- Page numbers.
- Image assets.

Keep elements as editable as possible while matching the confirmed image draft. Do not redesign pages, adjust confirmed content, or change layout and visual relationships without explicit user approval. Treat the confirmed image draft as the visual benchmark for PPT production.

Reconstruct every planned `native-chart` as a real PowerPoint chart, not as an image, SVG drawing, or grouped shapes. Embed a chart workbook containing the complete approved categories, series names, values, units, and ordering. Preserve the confirmed visual design as closely as PowerPoint's native chart model allows. If native reconstruction would materially change the approved meaning or visual hierarchy, stop and request approval for the documented exception instead of silently switching formats.

If complex visuals cannot be fully reconstructed as editable elements, explicitly mark the limitation and choose one of these approaches:

- Keep the complex area as a local image.
- Recreate it with approximate editable components.
- Explain the difference and wait for user confirmation.

After reconstructing each PPT page, compare it against the confirmed image draft:

- Content is consistent.
- Text is not missing or misplaced.
- Font and font size are consistent.
- Colors are consistent.
- Element positions are consistent.
- Spacing and whitespace are consistent.
- Charts and images are clear.
- Every planned native chart opens as a PowerPoint chart and exposes its embedded workbook data.
- Embedded chart values exactly match the confirmed source dataset, including categories, series, units, and ordering.
- Content that needs to remain editable is editable.

## Handoff to Production

After all pages are visually locked and the editable reconstruction is complete:

1. **Handoff**: deliver the confirmed content planning document, visual standards, page image drafts, and reconstructed editable PPTX to `ppt-master` as production input (or directly as the deliverable if reconstruction already satisfied the contract).
2. **QA**: run `ppt-production-qa` on the final artifact (editable-pptx mode). Only PASS or PASS_WITH_APPROVED_EXCEPTIONS may be delivered.
3. If QA fails, return to the affected pages for correction, then re-render and re-check before delivery.

This skill's final deliverable is the **visually locked set + reconstructed PPTX**, after which `ppt-production-qa` owns acceptance.

## Checks

After each image draft or reconstructed PPT page, actively check:

- Page content matches the confirmed document.
- No omissions, misstatements, or newly invented information.
- Title accurately expresses the page conclusion.
- Text volume is appropriate.
- Chart type fits the information.
- Reading path is clear.
- Style is consistent with previous pages.
- Logo, page number, font sizes, and spacing are consistent.
- Page status is clear: draft, revised draft, visually locked, or reconstructed.

After all pages are complete, perform a global check:

- Table of contents and page numbers match.
- Title language is consistent.
- Data units and time ranges are consistent.
- Chinese, English, numbers, and punctuation are formatted consistently.
- Fonts, colors, logo, and footer are unified.
- Page density is balanced.
- No unnecessary repetition.
- No unsupported conclusions.
- No confirmed document content is unintentionally unused.
- No logic gaps between pages.

## Final Deliverables

The final delivery should include:

1. Confirmed PPT content planning document.
2. Full PPT visual standards.
3. Page construction brief for each page.
4. Confirmed page image drafts and visual lock status.
5. Complete editable PPT file.
6. Reconstruction limitations, if any.
7. Global check results and final user-confirmation items.

## Operating Principles

- Prioritize content accuracy over decoration.
- Confirm content before design.
- Handle one phase at a time.
- Handle one section or one page at a time.
- Do not invent data.
- Do not add conclusions without permission.
- Do not casually change confirmed content.
- Use one shared visual system for all pages.
- Ask first when information is incomplete.
- Leave reusable structured outputs at each step.

## Hermes 适配说明

- 平台：Hermes Agent（已从 Codex 生态移植，2026-08）
- 渲染/检查工具：vision_analyze（页面图稿 QA）、soffice（pptx 转 PDF/PNG 预览）、pdftoppm（PDF 分页渲染）
- 格式库：python-pptx（可编辑 PPT 还原）、openpyxl（Excel 数据源）、markitdown（文档转 Markdown）
- 流水线定位：本 skill = 可选协调层（确认节点 + 状态管理 + Handoff）。入口经 `ppt-router` 判定；策略层 = consulting-deck-strategist；生产路由 = ppt-master（含第 5 条路由 Full-slide Image → rw-consulting-ppt）；统一验收 = ppt-production-qa
- 相关技能：powerpoint（纯兜底）、ecommerce-proposal-ppt（TP 电商提案改造）、presentation-visual-director（视觉指导）
