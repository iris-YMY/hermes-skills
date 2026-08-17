---
name: pptx-visual-analysis
description: 用 python-pptx 程序化检查/分析 PPTX 文件，提取视觉规范（画布尺寸、字体、主题色、标题格式、版式分类）并渲染抽验。触发词：摘模版 / 提取视觉规范 / 这个PPT用什么字体颜色 / 分析PPT结构 / 拆可复用模版。区别于"套模板改造"（见 ppt-router/ecommerce-proposal-ppt）与纯文本读取（见 powerpoint）。
---

# PPTX 视觉规范分析 / 模版摘取

用 python-pptx 程序化读取 PPTX，提取可复用的视觉常量（画布尺寸、字体表、主题色、标题格式、版式分类），输出一份「模版规范清单」+ 预览图。用户说「把 PPT 的模版摘出来」「这个 deck 用的什么字体/配色」时用本 skill。

## 运行环境（本服务器）
- 用 `/usr/bin/python3`（自带 pptx 1.0.2 + PIL + pymupdf）。shell 默认 `python3` 指向 hermes venv，**无 pptx**（`import pptx` 报 ModuleNotFoundError）。跑 PPT 分析/生成脚本前先确认解释器，别用 venv python。
- 渲染抽验：`soffice --headless --convert-to pdf`。文件名含空格时先 `cp` 成无空格名再转，否则转换失败/产物异常。

## 提取步骤
1. **尺寸/结构**：`prs.slide_width/height`（16:9 = 12192000×6858000 EMU）、`len(prs.slides)`、各 layout 名。
2. **字体（两处分别取，结果不同）**：
   - 主题字体：正则扫 theme XML 里 `typeface="..."`。
   - 实际 run 字体：遍历每个 run 的 `font.name` 做 `Counter`（品牌字体 vs 回退字体混用，如 master 引 Apercu、run 实际用 House）。
3. **主题色**：`master.part.part_related_by('http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme')` 取 theme part → `blob.decode` 后正则 `<a:clrScheme>` 里 dk1/lt1/dk2/lt2/accent1-6 的 `srgbClr val`。
   ⚠️ 直接 `element.find('.//a:clrScheme')` 返回 None，必须走 part + regex。多 master 时逐个取。
   ⛔ **theme accent1 不能当品牌主色直接信**（2026-08-13 教训：一个 PPT 多个 master，accent1 各不相同——Burberry 周报 master[0] accent1=深蓝 #000F9F、master[1] accent1=酒红 #C5112B，光看 scheme 会选错；实际渲染用的主色是**深蓝 #000F9F**，不是酒红）。**必须以实际渲染像素采样为准**：soffice→pdf→pymupdf 渲染 → PIL 对封面/表头/整页采样 `Counter` 像素，取频次最高的才是真主色（Burberry 封面背景 #000F9F、表头 #000F9F 底白字、数据涨绿 #00B050 跌红 #FF0000）。
4. **文字色（鲁棒读法）**：`run.font.color.rgb` 对 scheme 色抛 `AttributeError: no .rgb property on color type '_SchemeColor'` → 先判 `color.type` 字符串是否含 `RGB`，是才取 `.rgb`，否则取 `.theme_color`。
5. **标题格式**：run 级 `font.size` 常为 None（继承自 placeholder/layout），需额外看 paragraph 级 font + `shape.placeholder_format.idx/type`。标题字号/字体藏在 layout/master 占位符，不在具体页 run 上。
6. **逐页分类**：按 shape 类型（TEXT/PIC/GROUP/TABLE/CHART）递归 walk（GROUP 要递归子 shape），归纳页面类型（封面/数据概览/商品表现/竞品/专题报告/内容计划…）。
7. **渲染抽验**：soffice→pdf→pymupdf 渲染 3-4 张代表页 + tesseract OCR 复核文字完整性。

## 坑
- 主题 typefaces ≠ 实际 run 字体名，两条都要报给用户。
- 品牌专有字体（如 Burberry House / Oracle / Styrene）非系统字体，规范里必须标注「需嵌入/安装，否则回退默认字体」。
- soffice 转大文件可能 PDF 页数少于 slide 数（LibreOffice 对部分内容渲染不全，30 页只出 14 页），抽验用代表页即可，不必纠结全量。
- 标题命名常带固定前缀（如 `JD.COM | XXX` 全大写竖线分隔），这是「标题规范」的核心特征，要单列。
- **OCR 误读中文常见**（"双店"→"双语"、"自营"→"A="、"烈儿宝贝⭐"→乱码）。判断文字是否真渲染正确，用 pymupdf `page.get_text('dict')` 看 span.text + span.font，**别只信 tesseract**；tesseract 只做「大概有没有内容」的初筛。
- **红底白字表头 OCR 识别不出**是正常现象（白字在深底上 tesseract 读不出来），读回 `tbl.cell(0,j).text` 确认内容即可，不是渲染 bug。

## 纯图片页识别 + 重构为可编辑 slide（下游高频需求，2026-08）
用户摘完模版常接着要「把源 PPT 套成这个模版，图片页要变可编辑 slide」。分析阶段顺带产出：
- **识别纯图片页**：逐页统计 shape 类型，`pic>=1 且 text==0`（或内容全是空占位符）= 纯图片页，需重构。
- **OCR 提取**：渲染该页 PNG（soffice→pdf→pymupdf dpi≥150）→ `tesseract -l chi_sim+eng` 提文字。
- **分两类**：① 数据/图表页可完整重构（文字→文本框、表格→原生 Table、图表→原生 Chart）；② App 界面截图页不可重构为可编辑，只重构标题+关键数据点、截图保留为图片。
- **保持图表类型不变（用户明确要求）**：把图片页里的图表重构成可编辑时，图表类型要跟原图一致——韦恩图→韦恩图（用 MSO_SHAPE.OVAL 两个半透明圆重叠 + 文字标注重合率）、矩阵表→原生 Table、柱状图→原生 Chart。别把柱状图擅自改成表格、把韦恩图改成文字卡片。
- ⛔ **一张图里的内容块一个都不能少，别擅自缩减**（2026-08-13 用户两连批「第四张原本有很多内容被你缩减了」「第五张有两个表格你只保留了一个」）：图片页重构前先把 OCR 结果**逐块盘清**——标题、结论条、每个图表、**每个表格**、每个数据卡、底部说明，列成清单再逐块落地。一张图里常有**多个表格**（如 P5 同时有「各人群占比表」+「自营与POP PLUS用户分布表」两个表），漏做一个就会被点名。重构语义是「把图片里所有元素 1:1 转成可编辑」，不是「概括成几个要点」。
- **提取图片时 placeholder 也会藏图**：`MSO_SHAPE_TYPE.PICTURE` 之外，整屏截图常藏在 Picture placeholder（`type=PLACEHOLDER`）里——它也能 `sh.image` 访问并 `.blob` 导出，walk 提取时别只认 PICTURE 类型，否则漏掉整页截图。
- 数据密集页 OCR 数字可能不完整 → 让用户选 A（按 OCR 先做、数字后核对）或 B（用户提供原始数据精确填），别自己猜数字。

## 字体替换偏好（用户明确指示，2026-08）
品牌专有字体（Burberry House/Oracle/Styrene、Century Gothic 等）在目标环境无法使用时，**英文→Arial、中文→微软雅黑**，标题加粗保持层级。套模版前主动问目标环境是否有品牌字体，没有就默认 Arial/微软雅黑，别默认能渲染品牌字体（否则回退默认字体、排版走样）。

## ⚠️「套模版」两种含义，别搞混（2026-08-13 用户纠正「太卡片了」）
摘完模版后，「套用某品牌模版」可能是两种完全不同的活，动手前必须先问清/判断：
1. **重绘型**：参考模版视觉常量，python-pptx 从零新建页面，卡片/表格自由重排（如 LB 提案）。产出新卡片式布局。
2. **改色型**：**保留原 PPT 的排版/形状/文字/图片不动，只把颜色替换成目标模版配色**（如 JD 1+1 → Burberry）。用户要这个时绝不能用重绘型的卡片函数，否则被批「太卡片了」。
- 判断信号：用户说「保留我给你的 ppt 内容样式，颜色改成 X 的模版」「剩下的 slide 不用动」= **改色型**；「按模版改造/重新排版/图片页变可编辑」= 重绘型。拿不准先问。
- ⚠️ 别复用上一个品牌的绘图函数库：某品牌的 add_card/add_top_bar（浅灰卡+左红竖条+粉结论条）是该品牌专属视觉，套到别的品牌 = 「又变成上一个品牌」。改色型任务根本不调用绘图函数，是在原文件上原地改色。
- 改色型正确做法见 `references/recolor-in-place.md`（copy 原 pptx → 递归 walk 形状含 group → 映射 fill/line/font 色 → 跳过 PICTURE → 处理 layout/master 层装饰形状 → 品牌 logo 色保留）。

## 交付清单模板
- 画布尺寸（EMU + inch/cm）
- 字体表（用途 / 字体 / 字号 / 字重）
- 主题配色（主色 / 辅助 / 强调 / 中性 + 十六进制）
- 标题规范（固定格式 / 字体 / 字号 / 位置）
- 版式分类（按页面功能分 N 类）
- 视觉元素特征（产品图尺寸 / 图表类型 / 表线颜色 / 分隔线 / 趋势色）
- 预览图若干张（飞书走 drive/v1/files/upload_all 发云空间链接）

## 脚本
`scripts/analyze_pptx.py` — 通用探针：给定 PPTX，打印画布尺寸、主题色 scheme、字体/字号/颜色 Counter。直接 `/usr/bin/python3 scripts/analyze_pptx.py <file.pptx>` 跑，别重新手写。

## 参考
`references/burberry-jd-template-spec.md` — Burberry 京东周报模板规格（配色/字体/标题格式/版式分类/自绘版式常量），摘取后套模版直接复用。
