# python-pptx 从零画页面 — 工具函数库（2026-08-08 v8 沉淀，LB 提案实测可用）

适用：任何"按品牌模版视觉从零生成 PPTX"任务（不依赖模版文件，新建空 Presentation()）。
完整示例脚本：`/tmp/lb_files/gen_lb_ppt_v8.py`。

## 视觉常量（LB TEMPLATE，换品牌时改这里）
```python
FONT = 'Century Gothic'          # 模版字体
DARK = RGBColor(0x0A, 0x0A, 0x06)  # 深色文字/背景
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LB_RED = RGBColor(0xC4, 0x2E, 0x2E)  # 主色（红条/卡片标题/结论条）
GRAY = RGBColor(0x8A, 0x8A, 0x86)    # 次要说明
BODY = RGBColor(0x33, 0x33, 0x30)    # 正文
LIGHT = RGBColor(0xF0, 0xF0, 0xEE)   # 卡片底
PINK = RGBColor(0xFD, 0xF3, 0xF3)    # 底部结论条底
```
```python
prs = Presentation()                      # 空文件，绝不打开模版删页
prs.slide_width = Emu(12192000)           # 16:9
prs.slide_height = Emu(6858000)
blank = prs.slide_layouts[6]              # BLANK layout
```

## 核心工具函数
```python
def new_slide():
    return prs.slides.add_slide(blank)

def add_rect(slide, left, top, width, height, color, line_color=None):
    """纯色矩形；line_color=None 时无边框。所有卡片的底。"""
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    if line_color:
        sh.line.color.rgb = line_color; sh.line.width = Pt(0.75)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh

def add_textbox(slide, left, top, width, height, text, size, bold=False,
                color=DARK, align=PP_ALIGN.LEFT, font=FONT, spacing=None):
    """多行文本框（\n 分行）。word_wrap=True 防溢出。"""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing: p.space_after = Pt(spacing)
        r = p.add_run(); r.text = line
        r.font.name = font; r.font.size = Pt(size)
        r.font.bold = bold; r.font.color.rgb = color
    return tb

def add_pic_fit(slide, img_path, left, top, max_w, max_h):
    """图片等比缩放放进 max_w×max_h 框内并居中——不变形。
    不用 add_picture 直接传宽高（会拉伸）。"""
    from PIL import Image
    im = Image.open(img_path); w, h = im.size
    scale = min(max_w / w, max_h / h)
    w2, h2 = int(w * scale), int(h * scale)
    x = left + (max_w - w2) // 2; y = top + (max_h - h2) // 2
    return slide.shapes.add_picture(img_path, x, y, w2, h2)

def add_card(slide, left, top, width, height, title, points,
             title_size=12, pt_size=10, title_color=LB_RED):
    """浅灰卡片 = 底 + 左红竖条 + 红字标题 + 圆点要点。"""
    add_rect(slide, left, top, width, height, LIGHT)
    add_rect(slide, left, top, Emu(40000), height, title_color)   # 左竖条
    add_textbox(slide, left + Emu(180000), top + Emu(80000), width - Emu(300000), Emu(300000),
                title, title_size, bold=True, color=title_color)
    tb = slide.shapes.add_textbox(left + Emu(180000), top + Emu(420000),
                                  width - Emu(320000), height - Emu(500000))
    tf = tb.text_frame; tf.word_wrap = True
    for i, pt in enumerate(points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(4)
        r = p.add_run(); r.text = "• " + pt
        r.font.name = FONT; r.font.size = Pt(pt_size); r.font.color.rgb = BODY
    return tb

def add_top_bar(slide, title, subtitle=None):
    """顶部细红条 + 标题（20pt 粗）+ 可选红色副标题。"""
    add_rect(slide, 0, 0, SW, Emu(45000), LB_RED)
    add_textbox(slide, Emu(700000), Emu(240000), Emu(10000000), Emu(600000),
                title, 20, bold=True)
    if subtitle:
        add_textbox(slide, Emu(700000), Emu(820000), Emu(10000000), Emu(400000),
                    subtitle, 13, color=LB_RED)

def add_bottom_strip(slide, text, size=12):
    """底部浅红结论条 = PINK 底 + LB_RED 粗体一句话结论。"""
    add_rect(slide, Emu(700000), Emu(6100000), Emu(10800000), Emu(500000), PINK)
    add_textbox(slide, Emu(900000), Emu(6180000), Emu(10400000), Emu(380000),
                text, size, bold=True, color=LB_RED)

def add_original_page(slide, png, title):
    """整页嵌原图 + 底部 LB 红页脚条（'内容不动'页用）。"""
    add_pic_fit(slide, png, 0, 0, SW, SH)
    add_rect(slide, 0, SH - Emu(80000), SW, Emu(80000), LB_RED)
    add_textbox(slide, Emu(300000), SH - Emu(78000), Emu(9000000), Emu(60000),
                f'LOVE, BONITO  |  {title}', 9, color=WHITE)
```

## 布局注意
- 卡片标题**英文大写** + 要点中文（Century Gothic 下中文标题渲染可疑）
- 右侧配图用 `add_pic_fit`（等比居中），左侧竖图宽约 3700000 EMU、高约 4500000 EMU
- 底部结论条 y=6100000，正文区控制在 1450000–6000000 之间，别和结论条重叠
- 卡片要点过多时降 pt_size（10→8/9）或拆行，宁小勿溢出

## 素材盘点方法论（判断图片是什么，无 vision 时）
用 PIL 读每张图：尺寸 + 平均亮度 + 色彩丰富度，判断用途：
```python
from PIL import Image
im = Image.open(p).convert('RGB')
small = im.resize((60, 140))
pixels = list(small.getdata())
avg = sum(sum(px) for px in pixels) / (len(pixels)*3)          # 亮度
colorful = sum(1 for px in pixels if abs(px[0]-px[1])>30 or abs(px[1]-px[2])>30) / len(pixels)
```
- 亮图（avg>150）+ 低彩 → 产品白底图/截图
- 深图（avg<100）+ 低彩 → 品牌氛围图/深色图表
- 统一尺寸多张（如 572×800×7）→ 产品图系列，卡片配图首选
- 竖屏长图（1080×2520）→ 手机 app 截图（小红书/天猫），用户说"不要截图"时排除

## 批量上传云空间（review 图/交付文件）
```python
import json, urllib.request, uuid
tok = json.load(open('/home/ubuntu/.lark/tokens.json'))['access_token']
parent = 'nodcnnkM2lJvS2xjFQBBBRT4Eeg'   # 根目录，无效报 1061044
def upload(path, name, ctype='application/octet-stream'):
    boundary = uuid.uuid4().hex
    content = open(path, 'rb').read()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file_name"\r\n\r\n{name}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="parent_type"\r\n\r\nexplorer\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="parent_node"\r\n\r\n{parent}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="size"\r\n\r\n{len(content)}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f'Content-Type: {ctype}\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request('https://open.feishu.cn/open-apis/drive/v1/files/upload_all',
        data=body, method='POST',
        headers={'Authorization': f'Bearer {tok}', 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())
# 返回 data.file_token → 链接 https://e1kg6bc4dl9.feishu.cn/file/{token}
```
review 图用 image/png，交付文件用 application/octet-stream。
