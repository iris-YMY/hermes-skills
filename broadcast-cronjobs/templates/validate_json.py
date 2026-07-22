"""Quick JSON validator for news card data."""
import json, sys

try:
    with open('/tmp/news_card_data.json', 'r') as f:
        data = json.load(f)
    sections = len(data.get('sections', []))
    items = sum(len(s.get('items', [])) for s in data['sections'])
    print(f"✅ JSON valid: {sections} sections, {items} total items")
except json.JSONDecodeError as e:
    print(f"❌ JSON Error at line {e.lineno}, col {e.colno}: {e.msg}")
    # Show the problematic line
    with open('/tmp/news_card_data.json', 'r') as f:
        lines = f.readlines()
    if e.lineno <= len(lines):
        print(f"   Line {e.lineno}: {lines[e.lineno-1].rstrip()}")
    sys.exit(1)
except FileNotFoundError:
    print("❌ File not found: /tmp/news_card_data.json")
    sys.exit(1)
