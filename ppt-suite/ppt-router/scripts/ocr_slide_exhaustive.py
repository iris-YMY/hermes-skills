#!/usr/bin/env python3
"""图片页元素全量盘点 OCR：超分 + 网格化 + 多阈值 + 反色 四手段并集，防止漏元素。

为什么需要：整页一次 tesseract 会漏掉小字号标签、图例、坐标轴、第二个图表。
（2026-08-13 JD 1+1 任务教训：P5 只 OCR 出韦恩图+1表，漏了年龄分布柱状图、2标签、2结论、第2表）

用法:
  python ocr_slide_exhaustive.py <image.png> [--grid 3] [--lang chi_sim+eng]

输出: 逐网格 × 多手段的 OCR 文本，供 agent 建「元素清单」用。
"""
import sys, subprocess, os, tempfile
from PIL import Image, ImageEnhance, ImageOps


def ocr(img, lang, psm=6):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name)
        p = f.name
    r = subprocess.run(
        ['tesseract', p, 'stdout', '-l', lang, '--psm', str(psm)],
        capture_output=True, text=True)
    os.unlink(p)
    return r.stdout.strip()


def main(path, grid=3, lang='chi_sim+eng'):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    # 超分：小图（<1500px）放大 + 锐化 + 增强对比
    if w < 1500:
        im = im.resize((w * 4, h * 4), Image.LANCZOS)
        im = ImageEnhance.Sharpness(im).enhance(2.0)
        im = ImageEnhance.Contrast(im).enhance(1.5)
        w, h = im.size
    print(f'[尺寸] {w}x{h}  grid={grid}x{grid}')
    # 网格化逐格 OCR（整页 OCR 会漏小字）
    for gy in range(grid):
        for gx in range(grid):
            x0, y0 = w * gx // grid, h * gy // grid
            x1, y1 = w * (gx + 1) // grid, h * (gy + 1) // grid
            cell = im.crop((x0, y0, x1, y1))
            print(f'\n===== 网格[{gy}][{gx}] =====')
            # 手段1: 灰度 + 增强对比
            g = ImageEnhance.Contrast(cell.convert('L')).enhance(2.0)
            out = ocr(g, lang)
            if out:
                print('[灰度增强]')
                print(out)
            # 手段2: 多阈值二值化
            g2 = cell.convert('L')
            for th in (100, 140, 180):
                b = g2.point(lambda x, t=th: 0 if x < t else 255, '1')
                out = ocr(b, lang)
                if out:
                    print(f'[二值化 th={th}]')
                    print(out)
            # 手段3: 反色
            inv = ImageEnhance.Contrast(ImageOps.invert(cell.convert('L'))).enhance(2.0)
            out = ocr(inv, lang)
            if out:
                print('[反色]')
                print(out)


if __name__ == '__main__':
    argv = sys.argv[1:]
    args = [a for a in argv if not a.startswith('--')]
    grid, lang = 3, 'chi_sim+eng'
    for i, a in enumerate(argv):
        if a in ('--grid', '-g') and i + 1 < len(argv):
            grid = int(argv[i + 1])
        elif a.startswith('--grid='):
            grid = int(a.split('=')[1])
        if a in ('--lang', '-l') and i + 1 < len(argv):
            lang = argv[i + 1]
        elif a.startswith('--lang='):
            lang = a.split('=')[1]
    if not args:
        print(__doc__)
        sys.exit(1)
    main(args[0], grid, lang)
