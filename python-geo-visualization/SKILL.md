---
name: python-geo-visualization
description: "Python choropleth/heatmap generation with matplotlib + geopandas. China province maps, geographic data visualization."
tags: [python, matplotlib, geopandas, choropleth, heatmap, visualization, china-map]
---

# Python Geographic Data Visualization

Generate choropleth maps and heatmaps using matplotlib + geopandas.

## Environment Setup

```bash
# Install on system Python (hermes venv may not have geopandas)
pip install geopandas matplotlib numpy --break-system-packages
# Or use: /usr/bin/python3 (system Python with geopandas installed)
```

**Pitfall**: The hermes-agent venv python3 (`~/.hermes/hermes-agent/venv/bin/python3`) may lack geopandas. Use `/usr/bin/python3` or `pip install --break-system-packages`.

## China Province Map Workflow

### 1. Get GeoJSON Data

```bash
# Aliyun DataV — reliable source for China province boundaries
curl -sL "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json" -o /tmp/china_provinces.json
```

### 2. Key Implementation Notes

**Chinese font support:**
```python
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
```

**Province name matching** — GeoJSON uses full names ("北京市", "浙江省", "内蒙古自治区"):
```python
def get_value(name):
    for key, val in data.items():  # data keys are short names like "北京", "浙江"
        if key in name:
            return val
    return -1  # sentinel for missing data
```

**Pitfall — `missing_color` parameter removed** in newer matplotlib/geopandas:
```python
# DON'T: gdf.plot(..., missing_color='#f0f0f0')  # raises AttributeError
# DO: Plot missing and valid data separately
no_data = gdf[gdf['value'] < 0]
has_data = gdf[gdf['value'] >= 0]
no_data.plot(ax=ax, color='#e8e8e8', linewidth=0.8, edgecolor='0.4')
has_data.plot(column='value', ax=ax, cmap='Greys', vmin=0, vmax=max_val, ...)
```

**Label positioning** — small provinces need manual offsets:
```python
offsets = {
    '北京': (0.8, 0.3), '天津': (0.8, -0.3),
    '上海': (0.6, 0), '香港': (0.5, -0.5),
    '澳门': (-0.8, -0.5), '海南': (0, -0.3),
    '台湾': (0.3, 0)
}
```

**Name shortening** for labels:
```python
short_name = name
for suffix in ['壮族', '回族', '维吾尔', '特别行政区', '自治区', '省', '市']:
    short_name = short_name.replace(suffix, '')
```

### 3. Grayscale Color Scheme

For black/white/gray heatmaps:
- `cmap='Greys'` — white (low) to black (high)
- Set `vmin=0, vmax=max(data.values())` for consistent scaling
- Edge color `'0.4'` (medium gray) for province borders

### 4. Output

```python
plt.savefig('output.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
```

## Templates

- `scripts/china_heatmap.py` — Complete working template for China province heatmap (grayscale, labeled, with all pitfalls addressed)
