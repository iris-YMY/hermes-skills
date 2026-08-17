---
name: powerpoint
description: "Create, read, edit .pptx decks, slides, notes, templates. Fallback skill: use ONLY when no more specialized PPT skill matches (ppt-master for editable production, rw-consulting-ppt for image-only decks, ppt-workflow for visual-lock coordination, ecommerce-proposal-ppt for TP brand proposals, ppt-router for routing). Simple one-off pptx operations (read text, edit a slide, convert, render) are fine here; full deck production goes to ppt-master."
license: Proprietary. LICENSE.txt has complete terms
---

# Powerpoint Skill

## When to use

Use this skill for simple .pptx operations that do not match a more specialized PPT skill: reading, parsing, or extracting text from a .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); small edits to existing presentations; combining or splitting slide files; template/layout/notes inspection; rendering or QA of an existing pptx.

**Fallback positioning (2026-08-08)**: This skill is the *pure fallback* in the PPT skill ecosystem. For full deck production — new decks, visual redesign, template creation, native-chart decks — prefer `ppt-master`. For AI-generated full-slide image decks prefer `rw-consulting-ppt`. For per-page visual-lock review loops prefer `ppt-workflow`. For TP brand proposal transformation prefer `ecommerce-proposal-ppt`. When in doubt about which skill applies, load `ppt-router` first. If a .pptx file needs to be opened, created, or touched and no specialized skill applies, use this skill.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Follow a user-provided PPTX as template | Read [references/template-following.md](references/template-following.md) |
| Narrative/story structure & style | Read [references/narrative-style.md](references/narrative-style.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |
| Detect content overflow | `python scripts/slides_test.py output.pptx` |
| Build montage/contact sheet | `python scripts/create_montage.py --input_dir <dir> --output_file montage.png` |
| Render slides to images | `python scripts/render_slides.py output.pptx` |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.**

Use when no template or reference presentation is available.

---

## Narrative & Communication Framework

**Read [references/narrative-style.md](references/narrative-style.md) for the full guide before planning any deck.**

Core rules:
- **Define the communication job first**: By the end, **[audience]** should **[outcome]** because **[takeaway]**.
- **Choose a narrative arc** (context→stakes→evidence→implications→action, question→analysis→answer, etc.). An agenda is not a narrative.
- **Every slide has one narrative job + one primary claim**; use takeaway-style titles that communicate the point, not just name the topic.
- **Turn evidence into meaning** — don't list facts as an inventory; show what each means and why it matters to this audience.
- **Open and close deliberately** — open with context/tension, close with recommendation/action/implications. Never end on a generic "Thank you" slide.
- **Write natural, audience-facing copy** — concrete claims, active verbs, plain language. Rewrite any title that sounds like a prompt, slogan generator, or mechanical template.
- **Never invent** people, quotes, facts, data, or outcomes.

## Typography Minimums (HARD REQUIREMENT)

When no template or explicit style guidance is provided, use at least:

| Element | Size |
|---------|------|
| Deck title | **50 pt** |
| Slide title | **35 pt** |
| Subheadings / callout headers / text-box titles | **24 pt** |
| Body text | **16 pt** |

Inspect for unexpected wrapping — **never allow a one-line title/banner to wrap to two lines**. If narrative copy doesn't fit, shorten it or change layout; do NOT shrink type below minimums.

## Layout: One Composition, Not a UI Panel Collection

Avoid card grids, pills, badges, button-like text boxes, tab/navigation patterns, dense dashboard layouts, and other component-library styling that implies interactivity. Use stylized text boxes sparingly; favor a flat structure on the canvas.

## Diagram Rules

- **DO NOT use Python to draw images** or programmatic vector shapes for visuals. Use image search or image_gen instead.
- Minimize diagrams; add them only when requested or when one diagram materially clarifies a complex concept.
- Simple diagrams: native PowerPoint shapes. Complex relational/topological/network diagrams: Graphviz. Highly aesthetic/illustrative/scientific infographics: image_gen.
- When using native shapes with connectors: **create connectors (arrows/edges) BEFORE entity nodes** so edges appear behind nodes and never cross through node shapes or labels.
- Don't reuse the same image more than once (unless background). Inspect final crops at full-slide size; replace blurry/distorted assets.

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Automated Overflow Detection

```bash
python scripts/slides_test.py output.pptx
```

Checks for content overflowing the original slide canvas (renders with padding and inspects margins). Run this after every render cycle — catch overflow that visual inspection might miss.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `pip install Pillow` - thumbnail grids
- `pip install python-pptx pdf2image numpy` - overflow detection (slides_test.py), render_slides.py
- `npm install -g pptxgenjs` - creating from scratch
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images
