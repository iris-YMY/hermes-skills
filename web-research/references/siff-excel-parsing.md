# SIFF Schedule Excel Parsing Guide

## The Challenge
The SIFF schedule Excel file (`xl/worksheets/sheet1.xml`) often uses **Inline Strings** (`<is>` tags) instead of the standard **Shared Strings** (`<si>` tags) or direct numeric values. Standard parsing libraries (like `openpyxl` in some modes) might miss these or return empty values if not configured to handle inline strings correctly.

## Technical Solution (Python)
Use `zipfile` to access the internal XML structure and `xml.etree.ElementTree` to parse cell content directly.

### 1. Extract XML
```python
import zipfile
import xml.etree.ElementTree as ET

zf = zipfile.ZipFile('schedule.xlsx')
sheet_xml = zf.read('xl/worksheets/sheet1.xml')
root = ET.fromstring(sheet_xml)
ns = {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
```

### 2. Parse Inline Strings
Iterate through rows and cells. Look for the `<ss:is>` tag. If present, extract the text from the nested `<ss:t>` tag.

```python
for row in root.findall('.//ss:row', ns):
    cells = []
    for cell in row.findall('ss:c', ns):
        # Check for inline string
        is_elem = cell.find('ss:is', ns)
        if is_elem is not None:
            t_elem = is_elem.find('.//ss:t', ns)
            if t_elem is not None and t_elem.text:
                cells.append(t_elem.text.strip())
            else:
                cells.append('')
        else:
            # Check for shared string reference (type="s")
            cell_type = cell.get('t')
            v_elem = cell.find('ss:v', ns)
            if v_elem is not None:
                if cell_type == 's':
                    # Handle shared string index lookup here if needed
                    pass 
                else:
                    cells.append(v_elem.text)
            else:
                cells.append('')
    # Process cells...
```

### 3. Key Tags
- `<ss:c>`: Cell
- `<ss:is>`: Inline String (contains text directly)
- `<ss:v>`: Value (used for numbers or shared string indices)
- `<ss:t>`: Text element (nested inside `<is>` or `<v>`)
