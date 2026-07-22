# Feishu Pure Text Sync Format

## Problem
`lark doc append --text` sends Markdown source as raw text. Feishu's API escapes `#`, `*`, `-` etc., producing `\\# 标题` garbage visible to the user.

## Solution: `to_plain_text()` filter
Located in `scripts/sync_feishu_docs.py`. Converts Markdown to plain text before sending:

```python
def to_plain_text(md_text: str) -> str:
    # Remove headers (# Title -> Title)
    text = re.sub(r'^#+\s+', '', md_text, flags=re.MULTILINE)
    # Remove bold/italic (**text** -> text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove list markers (- Item -> Item)
    text = re.sub(r'^(\s*)[-*]\s+', r'\1', text, flags=re.MULTILINE)
    # Remove code blocks, links
    text = re.sub(r'```.+?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text.strip()
```

## Output format example
Instead of:
```markdown
### MEMORY.md
管家工作原则：1)透明度...
```

Send:
```
MEMORY.md：
管家工作原则：1)透明度...
```

Sections separated by `\n\n---\n\n` (visible horizontal rule text, not markdown).
