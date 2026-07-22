# XHS Viral Copy Flow (Hermes Adapted)

Adapted from the original viral copy flow for use with Hermes browser tools and gpt-image-2.

## Data Extraction Methods

### Method 1: Browser Extraction (Preferred)
1. `browser_navigate` to source URL
2. `browser_snapshot` to capture page state
3. `browser_console` to run DOM queries for text/image extraction
4. `vision_analyze` for cover image analysis

### Method 2: Tavily API (Fallback/Supplement)
```bash
# Direct URL extraction
curl -X POST "https://api.tavily.com/extract" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "<KEY>", "urls": ["<source_url>"]}'

# Related content search
curl -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "<KEY>", "query": "xiaohongshu <topic>", "search_depth": "advanced", "max_results": 10}'
```

## Cover Image Extraction Selectors

```javascript
// Priority - active non-duplicate slide
document.querySelector('.swiper-slide-active:not(.swiper-slide-duplicate) .img-container img')

// Fallback - active slide
document.querySelector('.swiper-slide-active .img-container img')

// Extract URL
const img = /* selector result */;
const url = img.currentSrc || img.src;
```

## Image Generation

Use gpt-image-2 for cover and supporting image generation. Include:
- Vertical 3:4 ratio specification
- Style keywords from source analysis
- Text overlay requirements
- Explicit exclusions for style-only mode

## Hermes Browser Tool Reference

| Action | Tool |
|--------|------|
| Open URL | `browser_navigate` |
| View page | `browser_snapshot` |
| Run JS | `browser_console` |
| Click element | `browser_click` |
| Type text | `browser_type` |
| Analyze image | `vision_analyze` |
| Generate image | gpt-image-2 (image gen skill) |
| Extract web data | Tavily API |
