# Feishu Docx Markdown Escaping Bug

## Symptom
When `lark doc append --text "..."` receives Markdown-formatted text (e.g., `### Title`, `**bold**`), Feishu renders it as escaped literal text: `\# \# \# Title`, `\* \* bold \* \*`. The content becomes unreadable.

## Root Cause
`lark doc append --text` sends content as a plain text block. Feishu's docx engine escapes Markdown syntax characters rather than parsing them as formatting.

## Confirmed Behavior (2026-06-03)
- `lark doc append NWMsdzBXcoJpjOxzD0bcXGsanxg --text "# 标题"` → renders as `\# 标题`
- `lark doc get` returns content with `\\#`, `\\*`, `&#34;` etc.
- The normalize() function in sync_feishu_docs.py strips these for comparison, but the actual doc display is mangled.

## Fix Applied
`sync_feishu_docs.py` now has a `to_plain_text()` function that:
1. Strips `# ` header prefixes
2. Removes `**`, `*`, `_` emphasis markers
3. Removes `- ` and `* ` list markers
4. Strips code blocks and links
5. Outputs clean plain text

## Recommendation
For any Feishu doc sync, always convert Markdown to plain text before `lark doc append --text`. If rich formatting is needed, use `lark doc create` with proper block structure (not implemented yet).
