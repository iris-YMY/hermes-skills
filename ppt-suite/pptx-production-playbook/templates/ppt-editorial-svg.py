#!/usr/bin/env python3
"""lieflat 编辑风单页 SVG 生成器模板（PPT 融合用，CONFIRMED 2026-09-03）

用途：生成 1280×720 单页 SVG → svg_to_pptx 导出可编辑 PPTX。
视觉正本 = lieflat mono-tokens.js；本模板 = 可复制改造的已知良好起点。

改造步骤：
1. 换数据：从 /home/ubuntu/.hermes/jd_rawdata_parsed.json 挖真实故事（禁编造）
2. 换标题/眉行/来源（结论式标题 + 全大写注记 + letter-spacing）
3. 需要新图型时，去 lieflat templates/basics-gallery.html 按 ════ 注释块找
   手写 SVG 骨架，翻译成静态 SVG（去掉动画/obsReveal/rnd 抖动逻辑）
4. 自检：rsvg-convert -w 1280 x.svg -o x.png → vision_analyze
5. 导出：svg_quality_checker --quick-generate --stage final → svg_to_pptx
   （详见 pptx-production-playbook references/lieflat-visual-into-ppt.md）

输出：/tmp/lieflat_ppt_demo/lieflat_burberry_demo.svg（示例路径）
"""
import os

INK = "#1C1C1A"; PAPER = "#F0EFEB"; MUTED = "#8F8E88"; FAINT = "#C6C5BF"
GRID = "#DEDDD6"
LAD = ["#1C1C1A", "#4A4944", "#8F8E88", "#B0AFA9", "#C6C5BF", "#D8D7D1"]

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

svg = []
S = svg.append
S('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" data-pptx-page-role="content">')
S(f'<rect x="0" y="0" width="1280" height="720" fill="{PAPER}"/>')

# ---- 眉行（全大写、字距）----
S(f'<text x="64" y="58" font-size="12" font-weight="600" font-family="Arial, Helvetica, sans-serif" fill="{MUTED}" letter-spacing="2.2">JD LUXURY WATCH · BURBERRY APPAREL · SHARE OF GMV · MAR–AUG 2026</text>')
S(f'<text x="1216" y="58" font-size="12" font-weight="600" font-family="Arial, Helvetica, sans-serif" text-anchor="end" fill="{MUTED}" letter-spacing="2.2">01</text>')

# ---- 结论式主标题（不写图型名）----
S(f'<text x="64" y="128" font-size="44" font-weight="700" font-family="Georgia, \'Times New Roman\', serif" fill="{INK}">Where Burberry lost the season</text>')
S(f'<text x="66" y="164" font-size="17" font-family="Georgia, \'Times New Roman\', serif" fill="{MUTED}">A two-house race in apparel hot-seller GMV — Burberry 25.3% → 8.2%, PRL 19.8% → 45.1%</text>')

# ═══════════════ LEFT · hairline twin-line ═══════════════
MONTHS = ["MAR", "APR", "MAY", "JUN", "JUL", "AUG"]
BB = [25.3, 21.6, 23.5, 16.6, 13.1, 8.2]     # 主角：最黑 INK
PRL = [19.8, 48.6, 46.9, 64.2, 46.3, 45.1]   # 对手：灰阶较浅

gx0, gy0, gw, gh = 64, 216, 700, 330
plot_x0, plot_y0, plot_w, plot_h = gx0 + 8, gy0 + 30, gw - 90, gh - 80
vmin, vmax = 0, 70
px = [plot_x0 + i * (plot_w - 40) / 5 + 20 for i in range(6)]
def py(v): return plot_y0 + plot_h - (v - vmin) / (vmax - vmin) * plot_h

for gv in range(0, 71, 10):
    y = py(gv)
    S(f'<line x1="{plot_x0}" y1="{y:.1f}" x2="{plot_x0 + plot_w:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.7"/>')
    S(f'<text x="{plot_x0 - 10:.1f}" y="{y + 3:.1f}" font-size="10" font-weight="600" font-family="Arial, Helvetica, sans-serif" text-anchor="end" fill="{MUTED}">{gv}%</text>')

pts = " ".join(f"{px[i]:.1f},{py(BB[i]):.1f}" for i in range(6))
S(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>')
for i in range(6):
    S(f'<circle cx="{px[i]:.1f}" cy="{py(BB[i]):.1f}" r="3" fill="{INK}"/>')
pts2 = " ".join(f"{px[i]:.1f},{py(PRL[i]):.1f}" for i in range(6))
S(f'<polyline points="{pts2}" fill="none" stroke="{LAD[3]}" stroke-width="1.2" stroke-dasharray="2 4" stroke-linejoin="round" stroke-linecap="round"/>')
for i in range(6):
    S(f'<circle cx="{px[i]:.1f}" cy="{py(PRL[i]):.1f}" r="2.4" fill="{PAPER}" stroke="{LAD[3]}" stroke-width="1.1"/>')

anno = [(0, BB[0], "25.3%", "start"), (5, BB[5], "8.2%", "end"), (0, PRL[0], "19.8%", "start"), (5, PRL[5], "45.1%", "end")]
for i, v, lab, side in anno:
    x, y = px[i], py(v)
    col = INK if lab in ("25.3%", "8.2%") else LAD[3]
    if side == "start":
        lx, anchor = x - 12, "end"
    else:
        lx, anchor = x + 12, "start"
    S(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + (12 if side=="end" else -12):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="0.8"/>')
    S(f'<text x="{lx:.1f}" y="{y + 4:.1f}" font-size="13" font-weight="800" font-family="Arial, Helvetica, sans-serif" text-anchor="{anchor}" fill="{col}">{lab}</text>')

for i, m in enumerate(MONTHS):
    S(f'<text x="{px[i]:.1f}" y="{plot_y0 + plot_h + 22:.1f}" font-size="10.5" font-weight="700" font-family="Arial, Helvetica, sans-serif" text-anchor="middle" fill="{MUTED}" letter-spacing="1">{m}</text>')
S(f'<text x="{plot_x0 + 8:.1f}" y="{plot_y0 + plot_h + 44:.1f}" font-size="9.5" font-weight="600" font-family="Arial, Helvetica, sans-serif" fill="{FAINT}" letter-spacing="1.6">SHARE OF CATEGORY GMV · SOLID = BURBERRY · DASHED = PRL · ONE POINT = ONE MONTH</text>')

S(f'<text x="{plot_x0 + plot_w:.1f}" y="{plot_y0 + 4:.1f}" font-size="11.5" font-weight="800" font-family="Arial, Helvetica, sans-serif" text-anchor="end" fill="{INK}">BURBERRY</text>')
S(f'<text x="{plot_x0 + plot_w:.1f}" y="{plot_y0 + 22:.1f}" font-size="11.5" font-weight="600" font-family="Arial, Helvetica, sans-serif" text-anchor="end" fill="{LAD[3]}">PRL</text>')

# ═══════════════ RIGHT · hundred field（1 dot = 1%）═══════════════
MIX = [("POLO", 37), ("TRENCH", 23), ("OUTER", 17), ("OTHER", 14), ("COAT", 5), ("TEE", 4)]
rx0, ry0, rw = 812, 216, 404
S(f'<text x="{rx0}" y="{ry0 + 16}" font-size="15" font-weight="700" font-family="Georgia, \'Times New Roman\', serif" fill="{INK}">What Burberry actually sells</text>')
S(f'<text x="{rx0}" y="{ry0 + 36}" font-size="11.5" font-family="Georgia, \'Times New Roman\', serif" fill="{MUTED}">category mix of apparel GMV · one dot = one percent · darkest = largest</text>')

dot_r, gap_x, gap_y = 4.6, 18.5, 15.5
dx0, dy0 = rx0 + 8, ry0 + 64
col = 0
for name, cnt in MIX:
    shade = LAD[len(MIX) - 1 - [n for n, _ in MIX].index(name)]  # 按排名从黑到浅
    for k in range(cnt):
        cx_ = dx0 + (col % 20) * gap_x
        cy_ = dy0 + (col // 20) * gap_y
        S(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="{dot_r}" fill="{shade}"/>')
        col += 1

# 图例 6 类拆两行（3+3），防横向溢出（实测首轮 bug）
SHADE_OF = {name: LAD[len(MIX) - 1 - i] for i, (name, _) in enumerate(MIX)}
ly = dy0 + 5 * gap_y + 30
for row in range(2):
    lxx = dx0
    for i in range(3):
        idx = row * 3 + i
        if idx >= len(MIX):
            break
        name, cnt = MIX[idx]
        shade = SHADE_OF[name]
        S(f'<circle cx="{lxx + 5:.1f}" cy="{ly + row * 22 - 3:.1f}" r="3.6" fill="{shade}"/>')
        S(f'<text x="{lxx + 14:.1f}" y="{ly + row * 22:.1f}" font-size="10.5" font-weight="700" font-family="Arial, Helvetica, sans-serif" fill="{INK}">{name} {cnt}%</text>')
        lxx += 108 + len(name) * 2.5
S(f'<text x="{rx0}" y="{ly + 56}" font-size="9.5" font-weight="600" font-family="Arial, Helvetica, sans-serif" fill="{FAINT}" letter-spacing="1.6">MAR–AUG TOTAL · ROUNDED TO 100 · POLO SHIRTS ARE THE ENGINE</text>')

# ---- 底注来源行 ----
S(f'<line x1="64" y1="668" x2="1216" y2="668" stroke="{GRID}" stroke-width="1"/>')
S(f'<text x="64" y="692" font-size="10.5" font-weight="600" font-family="Arial, Helvetica, sans-serif" fill="{MUTED}" letter-spacing="1.1">SOURCE: JD BUSINESS INTELLIGENCE (SHANGZHI) HOT-SELLER RANKING, MAR–AUG 2026 · MIDPOINT OF REPORTED RANGES · AI TREND ANALYSIS</text>')
S('</svg>')

out_dir = os.environ.get("LIEflat_OUT", "/tmp/lieflat_ppt_demo")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "lieflat_burberry_demo.svg")
open(out, "w", encoding="utf-8").write("\n".join(svg))
print("saved", out)
