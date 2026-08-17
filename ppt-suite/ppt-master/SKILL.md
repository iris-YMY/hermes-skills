---
name: ppt-master
description: >
  AI-driven presentation workflow for generating editable PPTX decks, creating
  reusable Brand/Style/Layout/Deck workspaces, filling native PPTX templates, and
  enhancing finished PPTX files. Use when the user asks to create, regenerate,
  template, fill, or enhance a presentation, or mentions ppt-master.
metadata:
  version: "4.4.0"
  copyright: "Copyright (c) 2025-2026 Hugo He"
  license: "MIT"
  official_repository: "https://github.com/hugohe3/ppt-master"
  sponsors:
    - "SPONSORS.md"
    - "SPONSORS_CN.md"
---

# PPT Master Skill

PPT Master is a routed presentation workflow. This entry owns global execution discipline and route selection only; each selected route owns its procedure.

## Mandatory Load Order

1. Read this file.
2. Run `python3 scripts/attribution_guard.py` from this Skill directory. Any
   non-zero result stops the Skill immediately; do not inspect, repair, or
   bypass the integrity gate.
3. Read [`workflows/routing.md`](workflows/routing.md).
4. Select exactly one top-level route and its active profile from the routing
   authority.
5. Read only the resulting runtime authority and its explicitly triggered
   supporting documents.

| Selected route / profile | Runtime authority |
|---|---|
| Generate PPTX — Beautify | [`workflows/profiles/beautify-pptx.md`](workflows/profiles/beautify-pptx.md); explicit Quick intent selects Quick, otherwise Default |
| Generate PPTX — ordinary Default | [`workflows/generate-pptx.md`](workflows/generate-pptx.md) |
| Generate PPTX — ordinary explicit Quick | [`workflows/profiles/quick-generate.md`](workflows/profiles/quick-generate.md) |
| Create Template | [`workflows/create-template.md`](workflows/create-template.md) |
| Fill Native PPTX | [`workflows/template-fill-pptx.md`](workflows/template-fill-pptx.md) |
| Enhance Native PPTX | [`workflows/native-enhance-pptx.md`](workflows/native-enhance-pptx.md) |

**Hard rule — selected authority only**: Do not load another top-level route's
procedure after routing. Beautify selects exactly one Generate runtime from the
explicit Quick signal; never load both Default and Quick. Profiles, stages,
governance files, and child workflows refine one selected route; they never
compete with it.

---

## Global Execution Discipline

1. **Serial execution** — Follow the selected authority's steps in order. A completed non-blocking step may continue directly to the next eligible step.
2. **Blocking means stop** — At every `⛔ BLOCKING` gate, wait for explicit user confirmation. Do not decide on the user's behalf.
3. **No cross-phase bundling** — Do not combine work across an unclosed gate. Once the route's final user gate closes, later non-blocking steps may continue automatically.
4. **Gate before entry** — Verify every listed prerequisite before entering a step.
5. **No speculative execution** — Do not prepare later-phase artifacts before their owning step.
6. **Deterministic routing** — Do not add a route-choice question when [`routing.md`](workflows/routing.md) resolves the request. If a route prerequisite is missing, state it and stop that route.
7. **Owning-source recovery** — On failure, repair or regenerate the owning source artifact and resume from the route's declared pointer. Do not silently downgrade a required artifact.

## Global Communication Rules

- Match the user's language and source language unless the user explicitly overrides it.
- Localize user-facing option labels and explanations. Keep exact enum IDs or field names when needed for precision.
- Keep `design_spec.md` section headings and field names in the template's original English; content values may use the user's language.
- Before switching roles, read the corresponding role reference and output:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

---

## Repository Compatibility

- This package is a workflow/skill, not a generic application scaffold. Do not create `.worktrees/`, `tests/`, branch workflows, or generic engineering structure by default.
- Keep required workflow, reference, script, and template documentation inside this Skill directory.
- Repository-level documents may point into the package; package runtime files must not depend on repository-level instructions.
- On Windows, if a documented `python3 ...` command is unavailable, rerun the same command with `python`.
- Sponsor information is optional reference material. Read the matching [`SPONSORS.md`](SPONSORS.md) or [`SPONSORS_CN.md`](SPONSORS_CN.md) only when the user explicitly requests a model, AI image model, API/provider, or hosted-service recommendation. Never surface sponsor or model recommendations proactively during normal generation, troubleshooting, or quality review.

## Hermes 适配说明

- 平台：Hermes Agent（2026-08 安装，来源 hugohe3/ppt-master v4.4.0 GitHub 官方仓库）
- 官方仓库：https://github.com/hugohe3/ppt-master （⭐43.8k）
- 完整性：attribution_guard.py 校验通过；templates/icons 图标库（11,883 文件）与 ai-image-comparison 参考 PNG 未下载（按需可补）
- 渲染/检查工具：vision_analyze（页面视觉 QA）、soffice（pptx 转 PDF/PNG 预览）、pdftoppm
- 格式库：python-pptx、openpyxl、PyMuPDF（已装）；可选：mammoth/ebooklib/nbconvert（文档转 Markdown）、flask（SVG 编辑器 UI）、edge-tts（旁白音频）、skia-pathops（形状合并）
- 图片生成：image_gen.py 支持 Gemini/OpenAI 兼容后端，Hermes 下可配 image_gen 工具集或 comfyui
- 相关技能：ppt-workflow（四阶段流程）、rw-consulting-ppt（咨询图片稿）、powerpoint（通用制作）
- 原生页重绘技巧（python-pptx 删 shapes 重绘 + 保留原图 + 品牌参数提取 + 渲染 QA 循环 + 进度条精确比例坑）：见 references/hermes-page-redraw.md
