# 原地改色技术（改色型套模版任务）

场景：用户给一个已有 PPTX + 目标品牌模版，要求「保留原 PPT 内容样式，只把颜色改成目标模版」。此时**不要从零重绘**，直接在原文件上改色。

## 核心原则
1. **copy 原文件改**（`shutil.copy`），不新建 Presentation（保留所有 layout/master/动画/占位符）。
2. **递归 walk 所有形状**（含 GROUP），对 fill / line / font 三处做颜色映射。
3. **跳过 PICTURE**（图片像素改不了色）。
4. **layout / master 层的装饰形状也要处理**（页眉装饰条、logo 图形常在 layout 层，不在 slide 层——slide 改完顶部仍残留红色，多半是 layout 层）。
5. **品牌 logo 色保留**：logo 是品牌标识不是装饰色，改掉破坏识别（如京东 logo 红 #C81623 应保留；装饰红 C00000/FF0000 才改成主色）。

## ⚠️「去掉红色」= 三种不同处理，别一刀切（2026-08-13 用户纠正）
用户说「去掉所有红色内容」时，同一「红色」按元素类型有三种不同改法，一刀切红→主色会被驳回：
1. **红色填充的文本框/形状** → **无色**（`shape.fill.background()`），不是改深蓝（用户原话「文本框不能有颜色」）。
2. **红色文字（run）** → 改目标主色（如深蓝 #000F9F）。文字是内容不能删，只能改色。
3. **红色 logo / 页眉装饰（master/layout 层的品牌标识图、装饰条）** → **删除**（`sh._element.getparent().remove(sh._element)`），不是改色也不是无色。

对应代码要点：
```python
# 1. 文本框无色（用户明确要「文本框不能有颜色」时）
def recolor_fill_none(sh):
    if sh.fill.type is not None and get_rgb_hex(sh.fill.fore_color) in REDS:
        sh.fill.background()          # 无填充，不是 solid+深蓝

# 3. 删除 master/layout 层 logo 与装饰条（遍历用 list() 包裹避免边删边遍历丢元素）
for sh in list(master.shapes):
    if sh.shape_type == MSO_SHAPE_TYPE.PICTURE and Emu(sh.width).inches > 2.0:  # 大 logo 图
        sh._element.getparent().remove(sh._element)
for sh in list(layout.shapes):
    if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and get_rgb_hex(sh.fill.fore_color) in REDS:
        sh._element.getparent().remove(sh._element)   # 红色页眉装饰条删除
```

判断属于哪类：红**文字**→改色；红**填充块**且是信息标签/文本框→无色（用户会说「文本框不能有颜色」）；红**logo/页眉/装饰条**（master/layout 层、非内容）→删除。拿不准时按用户措辞判断，别默认「红→主色」。

## 颜色映射：先分析原 PPT 用了哪些色
用 Counter 统计原 PPT 目标页 shape 的 fill/line/font 色（遍历 fill.fore_color.rgb / line.color.rgb / run.font.color.rgb），得到「原色 → 目标色」映射表。例（JD 1+1 → Burberry）：
- 红系 C00000/B60000/FF0000/DF2625 → 深蓝 #000F9F
- 金棕 C1A56A → 卡其 #A6A183
- 黑 #000000 / 白 #FFFFFF → 保留
- 京东 logo 红 #C81623 → 保留（品牌标识）

⛔ **必须扫描【全部】品牌色，不是只扫红色**（2026-08-13 v4 教训）：JD 1+1 原 PPT 里大量标签块的填充/边框不是京东红，而是**京东自有深蓝 #156082 + 边框 #042433**（如 P9-P12 的「新建pop店铺」「Stock management」「单独货盘」等标签块，白字深蓝底）。用户要「改成 burberry」时，这京东深蓝也得映射到 burberry 深蓝 #000F9F，否则整批标签块颜色没变、被批「最后四张没改成 burberry 板式」。改色前先 Counter 原 PPT **所有** fill/line/font 色，任何「非黑非白非目标色的品牌色」（红、金、深蓝、橙、紫…）都列进映射表，一个都不能漏。

⛔ **三层都要改：fill + line(边框) + font**（2026-08-13 v3→v4 教训）：只改 fill 会漏两处——①红色**边框线** `line.color.rgb=C00000`（连接符 Connector、文本框描边）原样残留，页面仍有红色；②「红底白字」标签框去掉填充后，**白字在白底上直接看不见**（fill 变无色了但 font 还是 FFFFFF）。apply() 里 line 也要映射，且「白字 + 原填充是品牌色」的 run 要改成深色（深蓝或黑），否则去填充后文字消失。fill/line/font 三处共用同一份 REDS/GOLDS/JD_NAVY 集合。

⛔ **渐变线（gradFill）用 line.color.rgb 读不到色，会漏删（2026-08-14 教训）**：layout 层的「区分线」常是**渐变填充**（如红→白横贯全宽的分隔线，`<a:gradFill>` 含多段 `srgbClr`）。此时 `sh.line.color.rgb` 返回 None（gradFill 不是纯色 solidFill），用 `get_rgb_hex` 判「读不到色」就跳过了，导致这条红线漏删、被用户批「还有红色区分线」。正解：
```python
import re
# 渐变线颜色读不到时，读底层 XML 正则提取真实颜色
xml = sh._element.xml
colors = re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', xml)  # 渐变线会列出多段色
# 若 colors 含任何 REDS → 删除该线（或改色）
if any(c.upper() in REDS for c in colors):
    sh._element.getparent().remove(sh._element)
```
排查技巧：去红验证时若渲染图仍有红像素，先看红像素**位置分布**——「贯穿整行（如 10 列全有）」= 一条横线（多半是 layout 层渐变区分线），「集中在左上/右上角」= logo/页眉装饰。位置反推元素类型，比盲目再扫一遍 slide 层高效。

## 改色脚本骨架
```python
import shutil
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.shapes import MSO_SHAPE

shutil.copy(SRC, DST)  # 在原文件基础上改

NAVY = RGBColor(0x00, 0x0F, 0x9F)
REDS = {'C00000','B60000','FF0000','DF2625'}   # 装饰红，要改
GOLDS = {'C1A56A'}                              # 金棕，要改

def get_rgb_hex(color):
    if color.type is None: return None
    if 'RGB' in str(color.type).upper(): return str(color.rgb).upper()
    return None  # scheme 色跳过

def map_color(h):
    h = h.upper()
    if h in REDS: return NAVY
    if h in GOLDS: return RGBColor(0xA6,0xA1,0x83)
    return None

def apply(shape, force_white=False):
    try:
        if shape.fill.type is not None:
            c = get_rgb_hex(shape.fill.fore_color)
            m = map_color(c) if c else None
            if m: shape.fill.solid(); shape.fill.fore_color.rgb = m
    except Exception: pass
    try:
        if shape.line.fill.type is not None:
            c = get_rgb_hex(shape.line.color)
            m = map_color(c) if c else None
            if m: shape.line.color.rgb = m
    except Exception: pass
    if shape.has_text_frame:
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if force_white: r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF); continue
                c = get_rgb_hex(r.font.color)
                m = map_color(c) if c else None
                if m: r.font.color.rgb = m

def walk(shapes, force_white=False):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP: walk(sh.shapes, force_white); continue
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE: continue  # 图片不动
        apply(sh, force_white)

# 逐页应用（如 P2/P3/P4）
for idx in [1,2,3]:
    walk(prs.slides[idx].shapes)
```

## 封面改深蓝全幅（在已有 slide 上加背景矩形并移到底层）
```python
bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background(); bg.shadow.inherit = False
spTree = slide.shapes._spTree
spTree.remove(bg._element); spTree.insert(2, bg._element)  # 移到底层
walk(slide.shapes, force_white=True)  # 封面文字改白
```

## layout/master 层装饰形状改色
slide 层改完若顶部仍有残留色，多半是 layout/master 里的装饰条：
```python
master = prs.slide_masters[1]
layout = master.slide_layouts[11]  # 先确认目标页用的哪个 layout（slide.slide_layout.name）
for sh in layout.shapes:
    if sh.shape_type in (1, 9):  # AUTO_SHAPE / LINE
        c = get_rgb_hex(sh.fill.fore_color)  # 或 line.color
        m = map_color(c) if c else None
        if m: sh.fill.solid(); sh.fill.fore_color.rgb = m
```

## 验证
1. soffice 转 PDF → pymupdf 渲染 PNG。
2. PIL 采样每页像素 `Counter`，确认「原红色 → 深蓝」生效、残留红只在 logo 处。
3. OCR 抽查文字完整（区分渲染问题 vs OCR 中文误读，如「双店」→「双语」是误读不是 bug；用 pymupdf `get_text('dict')` 看 span 兜底）。
4. 服务器无 Arial/微软雅黑时，LibreOffice 用 WenQuanYi Zen Hei + LiberationSans 替代渲染——**PPTX 里字体元数据是对的，用户电脑装了字体即正常**，别在 review 时误报字体错。

## 中文字体设置（python-pptx 必须设 east asian font）
```python
from pptx.oxml.ns import qn
def set_font(run, size, bold, color, en='Arial', cn='微软雅黑'):
    run.font.name = en; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', cn)
```
