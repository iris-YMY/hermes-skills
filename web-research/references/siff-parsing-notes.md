# SIFF 上海国际电影节排片表解析

## 数据源
- 官网: https://www.siff.com
- 排片表页面: https://www.siff.com/page/paipian
- **Excel 下载**: https://www.siff.com/schedule/paipianexportcn
- 下载命令: `curl -s -L -o /tmp/siff_schedule.xlsx "https://www.siff.com/schedule/paipianexportcn"`

## Excel 格式特征
- 使用 `inlineStr` 格式（非 sharedStrings）
- 所有文本直接嵌入单元格 XML 中
- 列结构: A=单元, B=中文片名, C=英文片名, D=导演, E=制片国/地区, F=时长, G=日期, H=放映时间, I=影院, J=影厅, K=影院地址, L=见面会

## 解析脚本（XML方式）
```python
import zipfile, xml.etree.ElementTree as ET, re

zf = zipfile.ZipFile('/tmp/siff_schedule.xlsx')
sheet_xml = zf.read('xl/worksheets/sheet1.xml')
root = ET.fromstring(sheet_xml)
ns = {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

data = []
for row in root.findall('.//ss:row', ns):
    cells = {}
    for cell in row.findall('ss:c', ns):
        ref = cell.get('r', '')
        col = re.match(r'([A-Z]+)', ref)
        if col:
            is_elem = cell.find('ss:is', ns)
            if is_elem is not None:
                t = is_elem.find('.//ss:t', ns)
                cells[col.group(1)] = t.text if t is not None else ''
    if cells.get('A', '').strip():
        data.append({
            'unit': cells.get('A', '').strip(),
            'name_cn': cells.get('B', '').strip(),
            'name_en': cells.get('C', '').strip(),
            'director': cells.get('D', '').strip(),
            'country': cells.get('E', '').strip(),
            'duration': cells.get('F', '').strip(),
            'date': cells.get('G', '').strip(),
            'time': cells.get('H', '').strip(),
            'cinema': cells.get('I', '').strip(),
            'hall': cells.get('J', '').strip(),
            'address': cells.get('K', '').strip(),
        })
```

## 2026 SIFF 单元分布（369部影片）
- 向大师致敬: 256场次
- 官方推荐: 191场次
- 多元视角: 159场次
- 世界万象: 147场次
- 金爵奖参赛片: 132场次
- SIFF经典: 121场次
- 特别策划: 83场次
- "一带一路"电影周: 62场次
- 新视野: 57场次
- SIFF纪录: 49场次
- 今日亚洲: 37场次

## 2026 SIFF 排片周期
- 展映日期：6月12日 – 6月21日
- 抢票时间：通常为展映开始前1天（如6月5日12:00开售）
- ⚠️ 6月21日之后无官方排片。如果用户询问节后日期，直接告知电影节已结束
