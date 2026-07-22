---
name: xhs-viral-copy
description: |
  Xiaohongshu (XHS/小红书) viral copy pipeline: input a viral note URL, analyze its viral factors,
  generate a new publish-ready note (cover image, title, body, hashtags) using structural replication
  methodology. Supports style-only, tight, and medium copy modes with AI-generated cover images.
metadata:
  hermes:
    tags:
      - social-media
      - xiaohongshu
      - content-creation
      - viral-analysis
      - image-generation
---

# XHS Viral Copy Pipeline (URL Input)

**Goal:** Input a viral note URL → output a high-fit publishable new note (cover/title/body/hashtags).

## Standard Four-Step Flow (Default)

1. Input viral note URL
2. Analyze viral factors (title/cover/body/engagement)
3. Generate new cover image using gpt-image-2 (default style-only mode)
4. Publish (upload images, fill title/body, confirm before publishing)

## 1) Input Parameters

- `source_url`: Viral note link
- `copy_mode`: `style-only` (default) | `tight` (high consistency) | `medium` (moderate fit)

Default uses `style-only`: preserves original topic and engagement mechanism, but cover only references style/color palette/information hierarchy — does not reuse specific elements.
Only switch to `tight` when user explicitly requests "high-fidelity replication".

## 2) Source Note Analysis (Mandatory)

Extract and record:
- **Title template**: year/action words/emotion words/sentence patterns (e.g., "Please press the confirm button")
- **Cover template**: main text, information hierarchy, large-text poster style, color palette
- **Body template**: opening hook, number of opinion sections, closing CTA
- **Engagement template**: comment section action words (e.g., "type confirm"), participation threshold
- **Hashtag template**: core topics and long-tail topics

### Cover Image Extraction Rules (Carousel Pages - Mandatory)

When extracting cover images from carousel/swiper pages, use browser tools:

```
// Priority selector - use browser_console to execute:
document.querySelector('.swiper-slide-active:not(.swiper-slide-duplicate) .img-container img')

// Fallback selector:
document.querySelector('.swiper-slide-active .img-container img')
```

- Extract `currentSrc || src` from the matched element
- Save the image URL for use as image generation reference input
- Use `vision_analyze` to analyze the cover's visual structure, color palette, and text layout

### Browser Extraction Workflow

1. Use `browser_navigate` to open the source URL
2. Use `browser_snapshot` to capture the page state
3. Use `browser_console` to execute DOM queries for image extraction
4. Use `vision_analyze` on extracted images to understand visual structure

**Key lessons learned:**
- Taking the first `.img-container` often captures the wrong cover (previous slide or duplicate)
- Always use `swiper-slide-active` and exclude `.swiper-slide-duplicate`
- Verify the image URL key matches the expected active slide

Output: `Source Template` (brief structured summary)

## 3) Viral Copy Rewrite Rules

### Tight Mode

Goal: produce a "second viral post on the same topic", not a cross-topic remix.

- **Preserve:**
  - Same topic (don't change the main subject)
  - Same engagement mechanism (e.g., "type confirm in comments")
  - Same content structure (title style, body rhythm, cover hierarchy)
- **Replace:**
  - Specific wording, case details, expression order
  - Account persona tone (light injection, don't change topic)
- **Prohibited:**
  - Sentence-by-sentence copying
  - Reusing original images
  - Migrating original author's personal/private information

### Cover Consistency Control (Key Experience)

When image-to-image results have "too-high element consistency", immediately switch to "style-only" prompts:
- Only reference style, color palette, information layering, and vertical composition
- Explicitly prohibit reusing: character poses, icon combinations, text box shapes and positions
- Use "preserve topic + redesign elements" strategy, don't require identical elements

### Style-Only Mode (Default)

- Analyze the source cover's: color palette, text hierarchy, visual density, mood
- Generate a completely new cover that captures the same *feel* but with different visual elements
- Use gpt-image-2 with detailed style prompts

## 4) Output Format (Deliver All at Once)

1. **Title:** 3 options (at least 1 with ≤20 characters)
2. **Body:** 1 version ready to publish
3. **Cover:**
   - Main text + subtitle text
   - 1 image generation prompt (high text readability)
4. **Supporting images:** 3-6 infographic text descriptions + corresponding prompts
5. **Hashtags:** 5-8 topics

## 5) Data Extraction via Tavily API (Primary Data Source)

When browser access to XHS is restricted or unreliable, use Tavily API as the primary data extraction method:

### Tavily Search for Viral Note Analysis

```bash
# Search for the specific note or related content
curl -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "<TAVILY_API_KEY>",
    "query": "xiaohongshu <topic keywords>",
    "search_depth": "advanced",
    "include_answer": true,
    "include_raw_content": true,
    "max_results": 10
  }'
```

### Tavily Extract for Direct URL Parsing

```bash
# Extract content directly from the note URL
curl -X POST "https://api.tavily.com/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "<TAVILY_API_KEY>",
    "urls": ["<source_url>"]
  }'
```

### When to Use Tavily vs Browser

| Scenario | Method |
|----------|--------|
| Note URL is accessible in browser | Browser extraction (preferred) |
| Browser blocked / login required | Tavily Extract API |
| Need trending/related content analysis | Tavily Search API |
| Need visual cover analysis | Browser + vision_analyze |
| Supplementing browser data with context | Tavily Search (combined) |

### Tavily Workflow Integration

1. **First attempt:** Try `browser_navigate` to the source URL
2. **If blocked:** Fall back to `Tavily Extract` for text content
3. **Always:** Use `Tavily Search` to find related viral content in the same topic area
4. **For covers:** Use browser when possible; if not, describe expected cover style based on Tavily text data

## 6) Image Generation with gpt-image-2

### Cover Image Generation

Use gpt-image-2 (via image generation tools) to create new cover images:

1. **Analyze source cover** with `vision_analyze` to extract:
   - Color palette (hex values if possible)
   - Text placement zones
   - Visual density and mood
   - Information hierarchy

2. **Construct generation prompt** including:
   - Vertical format (3:4 ratio for XHS)
   - Style keywords derived from analysis
   - Main text overlay specifications
   - Explicit exclusions (for style-only mode)

3. **Post-generation check:**
   - Use `vision_analyze` to verify the generated image matches the intended style
   - If user reports "too similar to original", regenerate with more divergent prompts

### Supporting Images

For infographic/educational slides:
- Generate each slide with consistent style parameters
- Include text content specifications in each prompt
- Maintain color palette consistency across all slides

## 7) Publish Integration

Call the publish flow (see `xhs-publish` skill):

- Upload images via browser tools
- Fill title and body using `browser_type`
- Stop at publish button for user confirmation
- Use `browser_snapshot` to verify all fields before confirming

## 8) Risk & Compliance

- Do not promise "guaranteed viral/guaranteed follower growth"
- Do not output content violating medical claims, exaggerated promises, or inflammatory material
- Use "structural-level replication", avoid "text-level plagiarism"
- Always maintain creative distance from the source material
- Respect original creators' intellectual property

## 9) Persona Integration

When generating body text, follow the XHS persona guidelines:
- Short sentences + line breaks
- Conversational, slightly tsundere tone
- Point out key insights without over-explaining
- Use platform-native expressions
- Keep emoji usage minimal (max 1 per post)

## Quick Reference: Hermes Browser Toolset

| Action | Tool |
|--------|------|
| Open URL / Navigate | `browser_navigate` |
| Capture page state | `browser_snapshot` |
| Execute JavaScript | `browser_console` |
| Click elements | `browser_click` |
| Input text | `browser_type` |
| Analyze images | `vision_analyze` |
| Generate images | gpt-image-2 (image generation) |
| Web data extraction | Tavily API (search/extract) |
