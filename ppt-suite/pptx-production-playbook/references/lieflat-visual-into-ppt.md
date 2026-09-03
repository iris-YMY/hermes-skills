# lieflat 编辑风视觉 → PPT 图表融合配方（CONFIRMED 2026-09-03 实弹验证）

用户（小艾）明确喜欢 lieflat-charts（GitHub: larashero3-dotcom/lieflat-charts）的编辑级视觉，
主要想用在 **PPT 图表制作**里（HTML/PNG 直出需求很低）。融合链路 =
**lieflat 视觉语法 → 静态 SVG（Python 生成）→ 本管线 svg_to_pptx 导出可编辑 PPTX**（原生 DrawingML 形状，非图片）。
实测成品：BURBERRY 服饰 GMV 份额单页 1280×720，quality_gate=passed，LibreOffice 渲染验收通过。

## 为什么静态 SVG 而不是 gallery 的 HTML

lieflat 手写 SVG 图型（rung bars / hairline line / hundred field / dot cascade 等）在 gallery 里由 JS 动态渲染 + 动画。
PPT 不需要动画：把图型代码骨架翻译成**静态 SVG**，视觉语法完整保留
（灰阶 ladder、单位分解、全大写注记、结论式标题、发丝网格）。禁止退回图表库默认样式。

## 五步流水线

1. **挖真实数据故事**（禁止编造；本地现成源 `/home/ubuntu/.hermes/jd_rawdata_parsed.json`，
   京东商智导热销 7110 条 / 6 品类 / 2026-03~08，amount、unit_price 区间取 midpoint）。
   示例故事：BURBERRY 服饰 GMV 份额 25.3%(Mar)→8.2%(Aug)，PRL 19.8%→45.1%，Polo 占品类 37%。
2. **Python 生成单页 SVG**（1280×720 `viewBox`；root `data-pptx-page-role="content"`）：
   - 颜色取 lieflat `mono-tokens.js`：PAPER `#F0EFEB` 底 / INK `#1C1C1A` 墨 / MUTED `#8F8E88` /
     FAINT `#C6C5BF` / GRID `#DEDDD6`；灰阶 ladder `['#1C1C1A','#4A4944','#8F8E88','#B0AFA9','#C6C5BF','#D8D7D1']`；
     **明度即数据**：主角最黑，对手/次类沿 ladder 变浅。
   - **字体必须 PPT-safe**：标题 Georgia（衬线编辑感）、正文/注记 Arial。
     ⚠️ Inter 是 lieflat gallery 的 Web 字体，PPT 环境不存在 → 回退难看；直接用 Arial/Georgia。
   - 卡片要素：结论式标题（写判断不写图型名）+ 全大写眉行/来源行（letter-spacing ≥2px）+
     副标题写图例口径（"one dot = one percent"）+ 来源行全大写。
   - 诚实单位分解：hundred field 1 点 = 1%（100 点取整到整百分点，注明 ROUNDED）；发丝线 0.7–1.6px；
     对手系列虚线（stroke-dasharray "2 4"）、主角实线；关键点发丝引线 + 数值（font-weight 800）。
3. **自检 PNG**：`rsvg-convert -w 1280 x.svg -o x.png` → vision_analyze 查溢出/截断/重叠，改完重渲再看一轮
   （实测首轮抓到：图例横向排溢出画布 → 改两行 3+3；注记过长 → 精简）。
4. **质量门 + 导出（顺序不能反）**：
   ```bash
   mkdir -p project/svg_output && cp x.svg project/svg_output/
   python3 <ppt-master>/scripts/svg_quality_checker.py project --quick-generate --stage final --json
   python3 <ppt-master>/scripts/svg_to_pptx.py project --quick-generate -f ppt169 --pptx-structure flat -o project/out/x.pptx
   ```
   ⚠️ `--quick-generate` 要求先有**通过**的 final SVG quality report，否则报 `found not-provided`。
5. **渲染验收**：`soffice --headless --convert-to pdf --outdir preview out/x.pptx` →
   `pdftoppm -png -r 150 preview/x.pdf preview/slide` → vision_analyze 对比 PPTX 与原始 SVG
   （文字丢失/乱码/元素移位）。通过后交付 .pptx（可编辑矢量，用户可点选线/点）。

## 踩坑清单（全部实测）

- `--quick-generate` 免 spec_lock/design_spec；与 spec_lock 正式模式互斥。
- SVG 文本 XML 转义：`&`→`&amp;`、`<`→`&lt;`、`>`→`&gt;`（动态文案统一 esc()）。
- 静态 SVG 头号 bug = 图例/注记溢出画布：先算坐标再渲染；图例类多拆两行。
- 彩色走 custom 时整份交付只锁一套色彩系统（Mono / 单一 preset / custom），不混用；
  品牌色（如 BURBERRY）也走 CUSTOM 角色对象，不散落 hex。
- 融合页图表仍守 lieflat 全部数据契约（数值∝视觉、面积用 sqrt、不断轴、不编单位、类目>6 退回灰阶）。

## 彩色预设 PPT 用色速查（color-presets.js 核心值，2026-09-03 实测可用）

§7.3 色板决策允许 porcelain/palm/wire/custom；PPT 静态 SVG 直接用以下 hex（不必每次重开
`~/.hermes/skills/lieflat-charts/color-presets.js`）。同一交付只锁一套，混用即返工。

- **porcelain 青瓷蓝**（有序/单序列/排名）：BG `#F7F2EB` · TXT/INK `#081F5C` · MUT `rgba(8,31,92,.60)`
  · GRID `rgba(8,31,92,.16)` · DATA `#334EAC` · DATA2 `#7096D1` · FAINTDATA `#BAD6EB`
  · 明度梯（深→浅）`['#081F5C','#334EAC','#7096D1','#9EB3CD','#BAD6EB','#D0E3FF']`
- **palm 椰林绿**（无序类目 ≤6）：BG `#F0EFEB` · TXT/INK `#58402E` · MUT `rgba(88,64,46,.60)`
  · GRID `rgba(88,64,46,.16)` · DATA `#43593B` · HERO 琥珀 `#D4A017`（只给一个主角）· FAINTDATA `#ACAD79`
  · 类目色 `['#43593B','#77835A','#ACAD79','#F2D17E']`（⚠️ DATA 与 HERO 语义相反，勿当平等类目）
- **wire 编辑部红**（灰阶 + 一个荧光橙主角）：BG `#F0F0EE` · TXT/INK `#1F1E1C` · DATA `#22211F`
  · DATA2 `#8F8E86` · **HERO `#F5572F` 只给一个元素** · 类目色 `['#F5572F','#22211F','#8F8E86','#C0BFB7']`
- **custom**（品牌色）：定义 CUSTOM 角色对象 BG/TXT/MUT/GRID/DATA(+HERO/RAMP/CAT)，从角色取色不散落 hex。

彩色通用规则（也进 PPT）：线宽 ×1.8、透明度地板 .85（发丝线换淡色会消失）；每图 ≥3 色阶或色位；
颜色必须连接真实维度并在底注写清；类目 >6 退回 Mono 灰阶。

## 上游版本差（本地已升级 2026-09-03，此节为历史记录）

- ⚠️ 本地 lieflat-charts 已于 **2026-09-03 升级到上游 main 最新版**（用户批准，方案 B）：
  63 图型（L1–L19 / F1–F17 / G3–G22 / M1–M2）+ 报告模式 R01–R12（中英整页 HTML）+ custom 色板 + 彩色自动选择。
  Hermes 适配保留：references/hermes-verification.md + SKILL.md 两处适配段（顶部引用 + 第九节验证陷阱）。
- 历史快照（2026-08-06 版 48 图）已备份 `/tmp/lieflat-charts-backup-20260903.tar.gz`。
- 选型规则以升级后 SKILL.md 为准（见 §7.3 SOP）。升级方法（ghfast.top 镜像）见 hermes-verification.md。

## 上游核查/同步方法（CN 网络实测，2026-09）

✅ 本地 lieflat-charts（~/.hermes/skills/lieflat-charts）**已于 2026-09-03 升级到上游 main 最新版**
（用户批准方案 B 后执行，含 Hermes 适配保留）。后续上游再更新时，用下方方法核查后决定是否再升级；
升级动作需用户批准，升级后更新本文件 + SKILL.md §7.1 标注 + references/hermes-verification.md 同步版本。

**CN 网络下载加速（实测有效）：ghfast.top 镜像秒下**
```bash
curl -sL -o lieflat.tar.gz "https://ghfast.top/https://github.com/larashero3-dotcom/lieflat-charts/archive/refs/heads/main.tar.gz"
# 18MB 秒下；git clone / codeload 直连 180s+ 超时勿用
```
仓库：`larashero3-dotcom/lieflat-charts`（main 分支，★4100+，2026-09 仍活跃）。
上次盘点（2026-09-03）：本地 8-06 快照 = 48 图 → **已升级至上游 main 最新** = 63 图 + 报告模式
R01–R12（中英整页 HTML `templates/reports/`）+ 地图 M1/M2 + 主力/后备图分级 + custom 色板规则
+ 彩色自动选择（porcelain 青瓷蓝 / palm 椰林绿 / wire 编辑部红，按数据形状自动选，不再默认禁彩）。
升级核对方法：文件清单 + blob sha（git blob 格式 sha1）对比本地是否过期。
