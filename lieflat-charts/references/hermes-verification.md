# Lieflat Charts 浏览器验证要点（Hermes 环境）

> 安装来源：GitHub larashero3-dotcom/lieflat-charts（2026-09-03 升级至 main 最新版，63 图型 + 12 报告模板 + 地图）。
> 位置：`~/.hermes/skills/lieflat-charts/`（完整仓库 124 文件）。

## 安装/升级
- 完整仓库含 templates/（gallery + color + reports + maps）+ catalog.md + report-catalog.md + mono-tokens.js + color-presets.js + examples/，**必须整包复制**，不能只装 SKILL.md。
- 中国服务器下载 GitHub：git clone / codeload tarball 均超时；**ghfast.top 镜像可用**：
  `curl -sL -o lieflat.tar.gz "https://ghfast.top/https://github.com/larashero3-dotcom/lieflat-charts/archive/refs/heads/main.tar.gz"`（18MB 秒下）。
- 升级后保留 `references/`（Hermes 适配），SKILL.md 两处 Hermes 段落（顶部引用 + 第九节验证陷阱）需手工 merge 回上游版。

## 渲染验证（关键坑）
页面图表用 IntersectionObserver 懒加载（滚入视野 ~30% 才渲染）：
- **快速滚动/一次性 scrollTo 底部不触发回调** → 截图大片空白，SVG innerHTML 长度为 0。
- 排查：`Array.from(document.querySelectorAll('svg')).map(s => s.innerHTML.length)`，出现 0 = 未渲染。
- 触发：页面注册了 click 重播，**模拟点击最可靠**：
  ```js
  document.querySelectorAll('svg').forEach(s =>
    s.dispatchEvent(new MouseEvent('click', {bubbles: true})))
  ```
- 确认全部渲染（无 0）后再截图汇报，避免把半成品当效果图。

## 使用要点（2026-09 新版规则，与旧版差异）
- **默认输出是图表不是报告**：只有用户明确说"报告/年报/月报/白皮书/海报/brief"才读 report-catalog.md 用 R01–R12 整页模板。
- **彩色自动选择**：不再是"用户没提就强制 Mono"。按第六点五节：用户指定色/数据语义适配时可用 porcelain/palm/wire；类目多或关系不明退回 Mono。同一交付只能一种色彩系统。
- **custom 色板**：用户给品牌色/色值时建立 CUSTOM 角色对象（BG/TXT/MUT/GRID/DATA/HERO/RAMP/CAT），PPT 品牌 deck 用。
- **地图 M1/M2 已支持**（旧版写"地图做不了"已过时）：仅用户明确要地图/地域分布时召回，ECharts+在线 GeoJSON 需联网；中国地图不做（合规）。
- 选型顺序：Lupi Editorial（L1–L19）→ Lupi Basics（F1–F17）→ Glance（G3–G22 降级）；主力 L1–L15/F1–F13，后备 L16–L20/F14–F17/G19–G22。
- 数据形状是选图主键，先看数据再选图型编号（catalog.md）。断轴柱状图拒绝。

## 与 PPT 工作流配合（Hermes 融合，2026-09 落地）
- 商务 consulting deck 走 ppt-master 路线时，图表生产规范在 `pptx-production-playbook` skill（"图表选型 SOP" 节）。
- 融合公式：lieflat 视觉语法（灰阶/明度即数据/单位分解/全大写注记）× 手写静态 SVG × svg_to_pptx 导出可编辑 PPTX。
- 图型取用：catalog 锁编号 → 打开对应 gallery html → 读 `// ════ 图型名 ════` 代码块 → 翻译成 Python 静态 SVG（去掉 obsReveal/动画，保留视觉语法）。
- 色板取用：品牌 deck 用品牌色 custom；无品牌要求用 Mono 或内置预设。最小字号、明度即数据等硬规则照旧。
- 渲染验收：`rsvg-convert -w 1280 in.svg -o out.png` 自查 → svg_to_pptx 导出 → LibreOffice 渲染 PDF → pdftoppm PNG → vision 逐项核对。
