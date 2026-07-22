# Z.ai / Zhipu AI Documentation Access

## The Problem
Zhipu AI's main websites are all JavaScript SPAs — curl returns only a loading page, and browser navigation fails to render content (stays blank even after 8s+ wait):
- `zhipuai.cn` — Next.js SPA, keywords visible in HTML `<meta>` but no content
- `open.bigmodel.cn` — Vue SPA, returns "doesn't work properly without JavaScript"
- `www.bigmodel.cn` — same Vue SPA
- `open.bigmodel.cn/cn/guide/models/text/glm-5.2` — page loads but content area stays empty

Search engines (Google, Bing, DuckDuckGo) also returned empty results from the server, likely blocked.

## The Solution: docs.z.ai (Mintlify)
`docs.z.ai` is a Mintlify-based documentation platform that serves raw markdown.

### Step 1: Get the Sitemap
```bash
curl -sL "https://docs.z.ai/llms.txt" -H "User-Agent: Mozilla/5.0"
```
Returns a full index of all documentation pages with URLs and descriptions.

### Step 2: Fetch Any Page as Markdown
Append `.md` to any docs URL:
```bash
curl -sL "https://docs.z.ai/guides/llm/glm-5.2.md"
```

### Key Documentation Pages (as of 2026-06)

**Language Models:**
| Model | URL |
|-------|-----|
| GLM-5.2 | `https://docs.z.ai/guides/llm/glm-5.2.md` |
| GLM-5.1 | `https://docs.z.ai/guides/llm/glm-5.1.md` |
| GLM-5 | `https://docs.z.ai/guides/llm/glm-5.md` |
| GLM-5-Turbo | `https://docs.z.ai/guides/llm/glm-5-turbo.md` |
| GLM-4.7 | `https://docs.z.ai/guides/llm/glm-4.7.md` |
| GLM-4.6 | `https://docs.z.ai/guides/llm/glm-4.6.md` |
| GLM-4.5 | `https://docs.z.ai/guides/llm/glm-4.5.md` |

**Vision Models:** `glm-5v-turbo`, `glm-4.6v`, `glm-ocr`, `autoglm-phone-multilingual`
**Image:** `glm-image`, `cogview-4`
**Video:** `cogvideox-3`, `vidu-q1`, `vidu2`
**Audio:** `glm-asr-2512`

**Capabilities:**
- Thinking Mode: `https://docs.z.ai/guides/capabilities/thinking-mode.md`
- Deep Thinking: `https://docs.z.ai/guides/capabilities/thinking.md`
- Function Calling: `https://docs.z.ai/guides/capabilities/function-calling.md`
- Context Caching: `https://docs.z.ai/guides/capabilities/cache.md`
- Structured Output: `https://docs.z.ai/guides/capabilities/struct-output.md`
- Streaming: `https://docs.z.ai/guides/capabilities/streaming.md`

**Other useful pages:**
- Pricing: `https://docs.z.ai/guides/overview/pricing.md`
- Migration to GLM-5.2: `https://docs.z.ai/guides/overview/migrate-to-glm-new.md`
- API Reference (Chat): `https://docs.z.ai/api-reference/llm/chat-completion.md`
- Release Notes: `https://docs.z.ai/release-notes/new-released.md`

## GLM-5.2 Quick Facts (from docs)
- Flagship foundation model, text-only input/output
- 1M token context window, 128K max output
- Strongest open-source coding model (Terminal-Bench 2.1: 81.0, SWE-bench Pro: 62.1)
- Supports: thinking mode, streaming, function calling, context caching, structured output, MCP
- New parameter: `reasoning_effort` (controls reasoning depth, e.g. "max")
- Thinking parameter: `{"type": "enabled"}` or `{"type": "disabled"}`

## General Mintlify Pattern
This `.md` suffix + `/llms.txt` pattern works for ANY Mintlify-hosted docs site.
If a docs site looks like Mintlify (search bar, sidebar nav, "Powered by Mintlify" footer),
try the same approach.
