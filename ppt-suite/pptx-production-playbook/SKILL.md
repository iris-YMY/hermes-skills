---
name: pptx-production-playbook
description: >
  ppt-master 生产执行要点（agent 自有笔记）：spec_lock.md 格式契约、svg_to_pptx.py 导出 CLI、
  质量门顺序（first-page/final）、LibreOffice 渲染验收、中文文本宽度估算与溢出修复、
  品牌模板点名时优先提取真实模板视觉语言（含 JD×BURBERRY 真实配方）、压字防间距标准。走 ppt-master 路线
  （Generate Editable PPTX / Create Template / Fill / Enhance）前先读。因 ppt-master 与
  ppt-router 为外部安装写保护，本 playbook 是 agent 可写的生产经验归属。
---

# PPTX 生产执行 Playbook（ppt-master 路线）

实战验证：2026-08 京东奢品趋势 2 页 deck（1280×720，BURBERRY 视觉语言）。

## 触发

- 用户要求用 ppt-master 生成/改造可编辑 PPTX（尤其 1280×720 商务 consulting deck）
- 进入 Generate Editable PPTX 的 Visual Construction / Export 阶段前

## 1. spec_lock.md 格式契约（写错 = blocking error）

- `## canvas` 节**必须存在**：`- viewBox: 0 0 1280 720`
- `## typography` roles **必须扁平**：`- title: 40` 直接放节下；**禁止**嵌套 `roles:` 列表
  （嵌套报 `spec_lock typography sizes ... found roles: .`）
- `## colors` 值**禁止**用反引号/引号包 HEX：`- background: #F7F3EC`
  （`parse_hex_color("`#F7F3EC`")` 失败 → roles 空 → `theme contract is missing: colors`）
- `## typography` 需含 `font_family` / `title_family` / `body_family`（theme font contract）
- 模板库（templates/scaffolds）缺失时校验契约不变

## 2. 导出 CLI（svg_to_pptx.py）

```bash
/usr/bin/python3 scripts/svg_to_pptx.py <project_path> -o <project_path>/out/xxx.pptx --with-notes
```

- project_path 是**位置参数**；`-o` 输出；`--with-notes` 带备注；**不是** `--project/--spec/--validate`
- 前置依赖：`/usr/bin/python3 -m pip install --break-system-packages python-pptx`
- 默认产出原生 DrawingML（可编辑形状）；flat structure 自带 Master + Blank Layout
- POSTFLIGHT `passed-with-warnings` 常见良性 advisory：contextual 颜色未注册（如 #8A7F6E）、
  latin 角色用微软雅黑

## 3. 质量门顺序

1. 首页画完**必跑**：`python3 scripts/svg_quality_checker.py <project> --stage first-page --json`
   一次看完问题集再修（含 spec_lock 契约错），修完再画后续页
2. 全部页完成：`--stage final --json`，0 errors 才导出
   ⚠️ 导出前置：svg_to_pptx.py 校验 `validation/svg_quality_report.json` 必须**最新且通过**，
   否则报 `found stale`——顺序 = checker `--stage final --json` 成功 → 再导出（2026-08 实测）
3. checker 只是第一层——估算 bounds 抓不到真实重叠/截断，导出后必做渲染验收（见 4）

## 4. 渲染验收（第二层，必做）

```bash
soffice --headless --convert-to pdf --outdir preview out/xxx.pptx
pdftoppm -png -r 150 preview/xxx.pdf preview/slide
```

vision_analyze 逐页看图，重点查：hero 数字与说明文字重叠；结论面板末字截断（如"周"）；
text-anchor=end 标签向左溢出容器左缘；卡片描述与右侧 hero 数字贴太近。
- 渲染分辨率用 `pdftoppm -png -r 150`（72dpi 看不出真实贴边）
- ⚠️ vision 在 150dpi 会夸大"间距过小"（实际 24px 常被报成 2–8px）：以 SVG 坐标数学为真值，
  vision 只用于抓真实重叠/截断/遮挡（本会话靠它抓到 'BURBERRY 黄金甲' 标签被条形盖住的真 bug）
- checker 的 bounds 溢出 advisory（如 '+103%' horizontal overflow 1.3%）：扩大该模块
  data-pptx-bounds 即可消除，非 blocking

## 5. 文本宽度估算与压字防间距（1280×720 实测，2026-08 两轮修正）

宽度估算（保守，按最宽 fallback 字体）：
- CJK ≈ 1.0em；拉丁/数字 ≈ 0.6em（DejaVu/真机替代字体会比 0.5em 更宽）；符号 ≈ 0.5em
- 混合 CJK+拉丁标签：**精确数清字母数**（如 BURBERRY = 8 字母 + 空格 ≈ 9×0.6em），再 +10% 安全垫。
  教训：'BURBERRY 黄金甲' 少算 1 字母 → 标签右缘顶进条形左缘被遮挡

压字防间距标准（真机最坏情况，用户明确要求根治）：
- 数值与条形/图形右缘间距 ≥ 24px（早期 12–16px 被用户打回）
- 条内数值距条尾 ≥ 10px 内边距；折线标注与数据点 ≥ 30px（点下方标注 ≥ 16px）
- 卡片描述与右侧 hero 数字间距 ≥ 60px（实测余量做 100px+）
- 横幅主/副标题间距 ≥ 10px；行内多层（label+desc+双 track）层间 ≥ 9px；desc 距卡底 ≥ 11px
- 中栏 4 层结构行高 ≥ 76
- 拿不准时用 PIL/字体度量实测文本宽，别信估算

## 6. 品牌模板点名：真实模板优先（2026-08 修订）

- 用户提供品牌源文件（.pptx）时，**以源文件为唯一权威**：LibreOffice 渲染各页 →
  vision_analyze 逐项提取真实视觉语言 → 按它重建。这是首选路径
  （查模板索引 → 缺失 → 自创配方 只是无源文件时的降级退路）
- 提取模板页问 vision 的问题清单：顶部标题条样式（颜色/形状/文字位置）、页眉页脚/页码、
  卡片/面板样式（边框/圆角/填充/标题栏）、具体用色、有无格纹/线条装饰
- 真实 JD×BURBERRY 配方（用户源文件 JD_1plus1_Burberry_EN_20260818.pptx，2026-08 验证）：
  background #FFFFFF / banner #000F9F 全宽横幅（白字标题居中，下沿 4px #A6A183 细线）/
  accent #C00000（仅关键数据）/ secondary_accent #A6A183 / grid #E0DCD3 /
  卡片 = 白底圆角 rx8 + 1.5px 描边 + 左侧 6px 深蓝竖条；分区标题 #000F9F bold；
  极简无格纹装饰（别凭品牌刻板印象脑补）
- 字体栈：标题写 `Burberry House, Georgia, 微软雅黑`——导出主路径不校验系统字体，
  字体名原样写入 PPTX；用户机器装有品牌字体则原生渲染，否则回退 Office 自带 Georgia 衬线
- 旧 free design 配方（米白 #F7F3EC + Nova Check 格纹）仅降级用，勿当品牌真身
- 完整复刻流程 + 压字防间距表见 references/brand-template-replication.md

## 7. 单页多栏迷你趋势图（英文 PPT，2026-08 实测）

场景：单页 deck 三栏 × 每栏多图（如 Handbags/Apparel/Footwear 各 3 图）、全英文。原 matplotlib 图中文标题且大图缩进单页必糊 → **用同源数据重绘 SVG 迷你图**（数据 → JSON → Python 生成 SVG → svg_to_pptx 导出），字号完全可控（12-14px 清晰）。

流程：
1. 数据脚本（参考 `~/.hermes/jd_en_chart_data.py`）：复用属性词典 first_match 归因（支持 `[(label,[kw...])]` 与纯词列表两种词典格式）+ price_bands，输出月度占比序列 JSON
2. SVG 生成器（参考 `~/.hermes/jd_en_svg_gen.py`）：折线每图 2-4 条线（BURBERRY 配色 #000F9F/#C00000/#A6A183/#8C8C8C）、标题 12.5px bold、红色高亮 11px、月份标签 9px、卡片 400×124
3. 导出：新项目目录只放单页 SVG + `--quick-generate`（免 spec_lock/design_spec），`-f ppt169 --pptx-structure flat`；SVG gate 同样用 `--quick-generate`

坑（全部实测踩过）：
- ⚠️ **SVG 文本 XML 转义**：`&`→`&amp;`、`<`→`&lt;`、`>`→`&gt;`。中招 3 次：结论文本 `&`、图例 `<1.5K`、结论 `<¥4.5K`/`>¥15K`。生成器统一 `esc()` 函数处理所有动态文本
- ⚠️ **图例放绘图区左上角会遮折线起点**（Mar 数据点穿图例文字）→ 图例放绘图区**右侧**竖排（leg_w≈92px，折线区减宽；行距 14px）
- ⚠️ **红色高亮标注加白色衬底 rect**（宽按 `len(highlight)*6.2`，min 70）——否则与高数值折线（如 67.8% 起点）视觉接触
- ⚠️ **150dpi 渲染裁剪验证的缩放系数 = PNG宽/1280 ≈ 1.5635**（不是 1.875！）。用错系数 → 裁剪区域偏移 → vision 把标题/标签误报为"截断/缺失"
- 用户偏好：英文 PPT 图表必须英文化（拒绝中英混搭）；结论**分点论述**（bullet），每点 = 趋势 + 原因（驱动），不能只报数字（用户 2026-08 打回"结论过于简单"）
- 用户笔误判定：如"包袋放价格，鞋型结构，颜色"——"鞋型结构"是鞋靴属性，判定该句为鞋靴；执行前复述确认，理解错会被打断

## 7.1 lieflat 编辑风视觉 → PPT 图表（2026-09 实测，用户明确喜欢）

用户想用 lieflat-charts 的编辑级视觉做 PPT 图表（HTML/PNG 直出需求低）。链路 =
**lieflat 视觉语法 → 静态 SVG（Python 生成）→ 本管线 svg_to_pptx 导出可编辑 PPTX**。
实测成品：BURBERRY 服饰 GMV 份额单页（发丝双线 + hundred-field 1 点=1%），quality_gate=passed。

要点：
- 颜色取 lieflat mono-tokens.js（PAPER #F0EFEB / INK #1C1C1A / GRID #DEDDD6 / 灰阶 ladder），
  **明度即数据**：主角最黑、对手/次类沿 ladder 变浅；对手系列虚线、主角实线
- **字体 PPT-safe**：标题 Georgia（衬线编辑感）、正文 Arial——⚠️ Inter 是 gallery Web 字体，
  PPT 环境不存在会回退难看
- 结论式标题（写判断不写图型名）+ 全大写眉行/来源行（letter-spacing ≥2px）+ 副标题写图例口径
- 诚实单位分解：hundred field 1 点 = 1%（整百分点，注明 ROUNDED），发丝线 0.7–1.6px
- 图例多类拆两行，防横向溢出画布（实测首轮 bug）
- 自检顺序：rsvg-convert 出 PNG → vision_analyze → 修 → 再渲；再走 §3/§4 质量门 + 渲染验收

完整五步流水线 + 踩坑见 references/lieflat-visual-into-ppt.md；可直接改造的已知良好起点：templates/ppt-editorial-svg.py（BURBERRY 发丝双线 + hundred-field 单页）
⚠️ 2026-09-03 已按用户批准把本地 lieflat-charts 升级到上游 main 最新版（63 图型 + R01–R12 报告模板 + M1/M2 地图 + custom 色板），并保留 Hermes 适配（references/hermes-verification.md + SKILL.md 两处适配段）。升级方法（ghfast.top 镜像秒下 18MB）：见 references/hermes-verification.md。选型规则以新版 SKILL.md 为准（彩色自动选择，不再默认禁彩）。

### 7.2 融合设计原则（用户 2026-09-03 明确，含否决）

- **不做"等用户触发的独立 skill"**——单独 lieflat skill 会像本地 8-06 版一样吃灰一个月。用户明确否决该形态。
- 融合 = **lieflat 成为 PPT 图表生产环节的默认实现**（替换"agent 临场自由发挥画图"），不是提醒/路由纸条。
  图表生成固定走：判数据形状 → 翻 lieflat catalog 锁图型 → 读 gallery 真模板代码骨架 → mono-token 语法
  静态 SVG → 自检清单 → svg_to_pptx。保证执行的机制 = 规范焊死在 playbook（必经必读文档）而非自觉。
- 向用户解释方案用**菜谱类比**（预制菜=预编译图型库会过期；现学现做=每次照活法典画，零维护永不过期）。
  用户问"方案B是不是只加了句路由"时，正确回答 = 澄清"换默认实现"而非"加提醒"，并举出第 1 步锁图型/
  第 2 步取真模板等具体强制环节。
- ✅ **方案 B（最简式）已批准执行（2026-09-03）**：lieflat 已升级上游最新版当"活的规范手册"（零维护永不过期），
  本 playbook 为必经文档焊死选型 SOP（见 §7.3），不建会过期的预编译图型库。
- lieflat 视觉选型判断权在 agent：数据形状 → 图型（少类目比较→阶梯柱？占比→单位点阵？趋势→发丝线？），用户不指定。
- 上游新内容吸收原则：custom 色板 + 新图型（Treemap/Candlestick 等）纳入；报告模式 R01–R12 不融 PPT
  （PPT 有整页体系），留作飞书文档确认稿出口；地图 M1/M2 有合规限制不主动触发。

### 7.3 图表选型 SOP（方案 B 核心钩子：PPT 图表默认实现 = lieflat 法典）

**任何 PPT/deck 需要数据图表时，禁止"临场自由发挥画图"。固定走 lieflat 法典选型：**

1. **判数据形状**（主键）：几个类目比较？占比构成？时间趋势？前后对比？带正负？分布？归因/流向？
2. **翻 lieflat catalog 锁图型**（`~/.hermes/skills/lieflat-charts/catalog.md`，63 张）：
   - 默认顺序 Lupi Editorial → Lupi Basics → Glance（Glance 仅 dashboard/三秒快读/用户明确要）
   - 主力 L1–L15 / F1–F13 优先；后备 L16–L20 / F14–F17 / G19–G22 需写明主力不适配理由
   - 常见映射：少类目比较→F1 Rung Bars/F5 Tick Rows；占比→F4 Tick Donut/L14 Hundred Field（饼图替代）；
     趋势→F2 Hairline Line/F3 Hairline Area；前后对比→F12 Dumbbell Queue/F6 Paired Rungs；
     瀑布→F9；分布→G15/F15；层级份额→F13 Treemap；行情→F17 Candlestick
3. **读 gallery 真模板代码骨架**（`templates/basics-gallery.html` / `lupi-gallery.html` 的 `// ════` 注释块），
   翻译成 Python 静态 SVG（去动画/obsReveal，保留核心几何、数据编码、视觉语法）
4. **色板决策**（lieflat 新版第六点五节）：用户明确色→服从；数据有序→porcelain 或 Mono；
   无序类目≤6→palm；需要视线落点→wire；类目>6/关系不明→Mono。品牌 deck 有品牌色 → custom 色板
   （BG/TXT/MUT/GRID/DATA/HERO 角色对象，不散落 hex）。整份交付只锁一种色彩系统。
   ⚡ porcelain/palm/wire/custom 的 PPT 用 hex 速查见 `references/lieflat-visual-into-ppt.md`（彩色预设节），不必重开 color-presets.js。
5. **视觉硬规则**：明度即数据（最重要=最深）；结论式标题（不写图型名）；全大写注记 letter-spacing；
   最小字号 6.5（半宽）/5.5（通栏）；数值∝视觉、面积 sqrt、柱不断轴；字体 PPT-safe（标题 Georgia/正文 Arial，
   ⚠️ 勿用 Inter）
6. **自检 + 导出**：rsvg-convert → vision_analyze → 修；质量门 `svg_quality_checker --quick-generate --stage final`
   → `svg_to_pptx`；soffice 渲染验收（§3/§4）

## 8. 结论写作规范：for 品牌视角 + 品牌带动（2026-08 用户明确要求）

单页英文 deck 的结论必须：
- **有价格图的先讲价格段变化**；有季节性的点出季节性；**点出由什么品牌带动**
- ⚠️ 季节/趋势句**必须带明确时间节点**（如 "67.8% (Mar) → 5.5% (Jun) → 42.9% (Aug)"），
  不许只写 "seasonal swing"——用户明确打回过只写 seasonal 的英文版，要求中文里的时间节点全翻译进英文
- **分点论述**（bullet），每栏 3 点（每图 1 点），每点 2 行（主行 + 续行缩进）
- 有代表品牌的 → **写品牌 + 代表产品**（如 "PRL tennis polo drives 84.8%"、"COACH City tote"、"Ferragamo ballet leads 61.9%"）
- for 高单价品牌（BURBERRY）→ 结论**重点高价位段**内容（≥¥15K 高端窗口、非促销期高端份额）——品牌单价高是结论视角的前提，先确认品牌定位
- **PPT 结论用英文，中文版结论单独在对话框给用户**（同一内容双语言交付）

**品牌带动分析**（写脚本 cat × price band / attribute × brand 交叉求金额份额）：
- brand 字段归一化映射（COACH/BURBERRY/PRL/Moncler/Ferragamo/Stefano Ricci/McQueen 等，含中文别名）
- 关键查询：高价段品牌 Top4（如服饰 ≥15K：3 月 BURBERRY 35.9% / Moncler 20.1%，8 月 Moncler 47.4%）、品类品牌（Polo→PRL 84.8%、羽绒→Moncler 97.1%）、鞋型品牌（芭蕾→Ferragamo 61.9%）、价格段品牌（鞋靴 <4.5K→McQueen 66%、>15K→Stefano Ricci 41.9%）
- 参考 `~/.hermes/jd_en_brand_analysis.py`

**结论框布局**（三栏 400px 宽）：卡片压缩到 400×112（图区 68px），卡间距 6，3 卡 y=148/266/384；结论框 y=506 高 150（6 行 = 3 bullet × 2 行），行距 19 + bullet 组间 +7（`y + 20 + k*19 + (k//2)*7`），字号 11.5px、每行 ≤55 字符（11.5px Arial ≈ 5.9px/字符，370px 可用）。参考 `~/.hermes/jd_en_svg_gen.py`。
