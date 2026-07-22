#!/usr/bin/env python3
"""China province heatmap generator — grayscale choropleth with labeled provinces.

Usage: Modify the `data` dict below, then run with /usr/bin/python3.
Output: PNG file at the path specified in plt.savefig().

Dependencies: geopandas, matplotlib, numpy (install via pip --break-system-packages)
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# ── Config ──────────────────────────────────────────────────────────
OUTPUT_PATH = '/home/ubuntu/china_heatmap.png'
GEOJSON_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
GEOJSON_PATH = '/tmp/china_provinces.json'
DPI = 200
FIGSIZE = (16, 12)
LABEL_FONTSIZE = 7
COLORMAP = 'Greys'

# ── Province data (modify as needed) ───────────────────────────────
data = {
    '上海': 178, '浙江': 134, '北京': 118, '广东': 86, '江苏': 122,
    '四川': 47, '辽宁': 40, '山东': 43, '湖北': 26, '福建': 22,
    '天津': 23, '河北': 28, '安徽': 23, '河南': 18, '湖南': 22,
    '重庆': 24, '吉林': 37, '黑龙江': 17, '山西': 11, '陕西': 18,
    '广西': 6, '云南': 15, '新疆': 6, '内蒙古': 11, '江西': 10,
    '青海': 0, '宁夏': 1, '贵州': 6, '西藏': 1, '甘肃': 3, '海南': 2
}

# ── Label offsets for small/overlapping provinces ───────────────────
LABEL_OFFSETS = {
    '北京': (0.8, 0.3), '天津': (0.8, -0.3),
    '上海': (0.6, 0), '香港': (0.5, -0.5),
    '澳门': (-0.8, -0.5), '海南': (0, -0.3),
    '台湾': (0.3, 0),
}

NAME_SUFFIXES = ['壮族', '回族', '维吾尔', '特别行政区', '自治区', '省', '市']

# ── Font setup ──────────────────────────────────────────────────────
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


def shorten_name(name):
    """Remove administrative suffixes for clean labels."""
    short = name
    for suffix in NAME_SUFFIXES:
        short = short.replace(suffix, '')
    return short


def get_value(name):
    """Match short province name from data dict against full GeoJSON name."""
    for key, val in data.items():
        if key in name:
            return val
    return -1  # sentinel for missing (e.g., 台湾, 香港, 澳门)


def main():
    # Load GeoJSON (download first if not present)
    import os
    if not os.path.exists(GEOJSON_PATH):
        import subprocess
        subprocess.run(['curl', '-sL', GEOJSON_URL, '-o', GEOJSON_PATH], check=True)

    gdf = gpd.read_file(GEOJSON_PATH)
    gdf['value'] = gdf['name'].apply(get_value)

    # Split into data/no-data for separate plotting (missing_color deprecated)
    has_data = gdf[gdf['value'] >= 0]
    no_data = gdf[gdf['value'] < 0]

    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)
    fig.patch.set_facecolor('white')

    # Plot no-data regions as light gray
    no_data.plot(ax=ax, color='#e8e8e8', linewidth=0.8, edgecolor='0.4')

    # Plot data regions with grayscale colormap
    vmin, vmax = 0, max(data.values())
    has_data.plot(
        column='value', ax=ax, cmap=COLORMAP,
        vmin=vmin, vmax=vmax, linewidth=0.8, edgecolor='0.4',
        legend=True,
        legend_kwds={'label': '数值', 'orientation': 'vertical', 'shrink': 0.6, 'pad': 0.02}
    )

    # Add province labels
    for _, row in gdf.iterrows():
        name = row['name']
        if not name:
            continue

        short_name = shorten_name(name)

        # Get centroid
        try:
            centroid_str = row.get('centroid', None)
            if centroid_str and isinstance(centroid_str, str) and ',' in centroid_str:
                parts = centroid_str.strip('[]').split(',')
                x, y = float(parts[0]), float(parts[1])
            else:
                c = row.geometry.centroid
                x, y = c.x, c.y
        except Exception:
            c = row.geometry.centroid
            x, y = c.x, c.y

        # Apply manual offset
        ox, oy = LABEL_OFFSETS.get(short_name, (0, 0))
        ax.annotate(
            short_name, xy=(x + ox, y + oy),
            ha='center', va='center',
            fontsize=LABEL_FONTSIZE, fontweight='bold', color='#1a1a1a'
        )

    ax.set_axis_off()
    ax.set_title('全国省市数据热力分布图', fontsize=18, fontweight='bold', pad=20, color='#2a2a2a')

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=DPI, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
