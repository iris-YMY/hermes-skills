---
name: event-scheduling
description: Event/festival schedule scraping, parsing, and personalized itinerary planning — extracting data from official sources, applying user constraints, and generating calendar outputs.
---

# Event Scheduling & Itinerary Planning

## Overview
Extract event schedules from official websites (Excel/HTML/JSON), parse structured data, and generate personalized calendar recommendations based on user constraints (time windows, location, genre preferences). Common use cases: film festivals (SIFF), conferences, trip itineraries.

## When to Use
- User provides screenshots/images of event listings and wants a personalized plan
- User asks to "扒官网排片" or find a festival/event timetable
- Need to recommend sessions based on user constraints (work hours, weekends, travel time, genre)
- Building structured itineraries from images, lists, or event data

---

## 1. Data Extraction

### Identify the Data Source
- Check the event's official website for a schedule/排片表 page
- **Look for Excel/CSV export links** — many sites provide downloadable spreadsheets
- If no download link, scrape the schedule page HTML (table rows, list items)
- Fallback: use the event's official app or mini-program

### Scraping via Browser
1. `browser_navigate` to the known URL
2. `browser_snapshot` to understand DOM layout
3. Use `browser_console` to extract data via JS queries
4. Handle pagination/lazy load with `browser_scroll` then re-query

### Console JS Patterns
```js
// ✅ Use 'var' — 'let'/'const' persist across evaluations and cause redeclaration errors
var rows = document.querySelectorAll('table tr');
var data = [];
rows.forEach(function(row) {
  var cells = row.querySelectorAll('td');
  if (cells.length >= 4) {
    data.push({
      title: cells[0].innerText.trim(),
      info: cells[1].innerText.trim(),
      dates: cells[2].innerText.trim(),
      cinemas: cells[3].innerText.trim()
    });
  }
});
JSON.stringify(data);
```

### Parsing Excel (.xlsx) Without openpyxl
Chinese festival sites often use **Inline Strings (`<is>` tags)**, not Shared Strings:
```python
import zipfile, xml.etree.ElementTree as ET
zf = zipfile.ZipFile('/tmp/schedule.xlsx')
sheet_xml = zf.read('xl/worksheets/sheet1.xml')
root = ET.fromstring(sheet_xml)
# inlineStr cells have <is><t>TEXT</t></is>, not <v>ref</v>
```

---

## 2. Constraint Application & Scheduling

### Classify Items
- **Mandatory** — explicitly marked (red boxes, "必须", user says required)
- **Optional** — fill-ins based on user preferences

### Apply Constraints
- **Time windows**: e.g., "Mon-Fri only after 19:00", "weekends OK but avoid Saturday mornings"
- **Content preference**: genre, documentary vs story film, niche
- **Spatial/logistical**: 30-45 min travel between venues within central Shanghai; 60+ min cross-district
- **Work constraints**: avoid 09:00-18:00 on weekdays
- **Meal breaks**: at least 1 hour lunch, 45 min dinner between sessions

### Deduplication Rules
- Each film/event appears **at most once** in final schedule
- Don't just transcribe screenshots — user wants recommendations
- Accept iterative constraint updates mid-conversation

---

## 3. Calendar Output Format

```
📅 [Event Name] 行程

🔑 抢票时间：[time]

▎[Date] [Day]

① [Item Name] 【标记】
- 时间：HH:MM–HH:MM
- 场地：Venue · Hall
- 类型：Genre · Duration

🍽️ [Meal/Travel note if gap > 2h]
```

### Feishu Rendering Rules
- **NO markdown tables** — Feishu silently drops them
- Use plain text lists with bold headings
- Use `block_type: 2` (paragraph) + `bold: true` for headings via API
- Batch ≤20 children per API call

### Confirmation Step
After presenting the itinerary, **always ask**:
- Whether items need adjustment (swap, remove, add)
- Whether the user wants this generated as a document
- **Do NOT auto-generate documents** — wait for explicit confirmation

---

## 4. Feishu Document Generation

### Using User Access Token (OAuth)
```bash
# Create docx in Skills folder
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"folder_token":"PdkOfBF0nlUKlkdVABZcYuKFneh","title":"Doc Title"}'

# Append content (block_type 2 = paragraph, bold for headings)
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/<doc_id>/blocks/<doc_id>/children" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"children":[{"block_type":2,"text":{"elements":[{"text_run":{"content":"Heading","style":{"bold":true}}}]}}]}'
```

### ⚠️ Critical Notes
- `text_run` uses `"content"` key, NOT `"text"` — using `"text"` returns error 99992402
- OAuth tokens expire in 2 hours; refresh_token is single-use
- Before re-authorization: `fuser -k 9999/tcp` to kill `lark auth login` background processes

---

## 5. Known Site Quirks

- **Damai.cn**: Good for concerts/theater/sports, does NOT host film festival schedules
- **SIFF official** (siff.com): Full schedule with Excel download, links to Damai for purchasing
- **Ticketing vs Content separation**: In China, ticketing platforms handle sales while event official sites host detailed schedules
- **Console `let`/`const` persistence**: Use `var` in browser console — `let`/`const` persist across evaluations

---

## 6. Pitfalls Checklist
- ❌ Don't just transcribe screenshots — user wants recommendations
- ❌ Don't schedule the same film twice
- ❌ Don't use markdown tables in Feishu
- ❌ Don't assume openpyxl is available — use XML parsing fallback
- ❌ Don't underestimate travel time — budget 30-45 min minimum
- ❌ Don't skip meal breaks
- ❌ Don't auto-generate documents without confirmation
- ⚠️ Chinese festival sites often use `inlineStr` in Excel exports
- ⚠️ Always verify cinema addresses and calculate realistic travel time
- ⚠️ Verify Feishu doc exists before writing (error 1770003 = deleted)
