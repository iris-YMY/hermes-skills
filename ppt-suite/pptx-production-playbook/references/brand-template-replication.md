# 品牌模板复刻流程 + 压字防间距标准（2026-08 京东奢品 deck 实战）

## 场景
用户点名品牌模板（提供源文件 .pptx）且要求根治文字重叠（压字）。
本会话事实：free design 仿 BURBERRY 版被用户打回（"还是有压字"），随后用户发来真实模板
JD_1plus1_Burberry_EN_20260818.pptx，要求"用 burberry 的品牌模版 + 调整压字一起改"。

## 完整流程
1. **提取模板视觉语言（源文件为唯一权威）**
   - soffice 渲染模板各页 → pdftoppm PNG → vision_analyze 逐页问清单：
     顶部标题条样式（颜色/形状/文字位置）、页眉页脚/页码、卡片/面板样式
     （边框/圆角/填充/标题栏）、具体用色（问出近似 HEX）、有无格纹/线条/装饰
   - 别凭品牌刻板印象脑补：BURBERRY 模板实际是白底 + 深蓝横幅 + 极简，**无格纹**
2. **写 spec_lock**（契约见 SKILL.md §1）：colors / typography / layout_rules
   （layout_rules 登记 banner 横幅样式、card_border、value_gap ≥20、desc_gap ≥60）
3. **重写 SVG**：横幅/卡片/分区标题按提取规范；间距按下表
4. **质量门**：first-page → 全页 final（0 errors）→ 导出
5. **150dpi 渲染验收**：坐标数学为真值，vision 只抓真实重叠/遮挡
6. **抽查修复**：vision 报的真实 bug 必修（案例见下）；夸大报告（实际 24px 报 2px）忽略

## 压字防间距表（真机最坏情况，用户要求根治）
| 场景 | 最小间距 |
|------|---------|
| 数值 ↔ 条形/图形右缘 | 24px（早期 12–16px 被用户打回） |
| 条内数值 ↔ 条尾 | 10px 内边距 |
| 折线标注 ↔ 数据点 | 30px（点上方）；点下方标注 16px+ |
| 卡片描述 ↔ hero 数字 | 60px 起，实测余量做到 100px+ |
| 横幅主/副标题 | 10px+ |
| 行内多层（label+desc+双track） | 层间 9px+ |
| 卡片 desc ↔ 卡底 | 11px+ |
| 中栏 4 层结构 | 行高 76 |

## 文本宽度估算（保守，按最宽 fallback 字体）
- CJK ≈ 1.0em；拉丁/数字 ≈ 0.6em（DejaVu/真机替代比 0.5em 更宽）；符号 ≈ 0.5em
- 混合 CJK+拉丁：**精确数清字母数**再算，+10% 安全垫
- **案例（真 bug）**：'BURBERRY 黄金甲' = 8 字母 + 空格 ≈ 9×0.6em + 3 汉字，估算少算 1 字母 →
  标签右缘 174 顶进条起点 168，标签被灰色条形遮挡（vision 抓到）。修复：跌侧条形整体右移
  +27px（起点 168→195）让位。标签与图形起点间距按 10px+ 兜底

## 字体栈
- 标题 `Burberry House, Georgia, 微软雅黑`：导出主路径不校验系统字体，字体名原样写入 PPTX；
  用户机器装有品牌字体 → 原生渲染；否则回退 Office 自带 Georgia 衬线
- 正文微软雅黑（Office 自带，真机稳定）
- 注意：svg_to_pptx 的 text_outline.py 有 installed-font 解析（fontconfig），但只在描边转换
  场景触发；常规导出不因系统缺字体失败

## 命令
```bash
/usr/bin/python3 scripts/svg_quality_checker.py <project> --stage final --json
/usr/bin/python3 scripts/svg_to_pptx.py <project> -o <project>/out/xxx.pptx -f ppt169 --pptx-structure flat
soffice --headless --convert-to pdf --outdir preview out/xxx.pptx
pdftoppm -png -r 150 preview/xxx.pdf preview/slide
```

## 视觉验证注意
- vision 在 150dpi 系统性夸大"间距过小"（实际 24px 报 2–8px）——以坐标计算为真
- checker bounds 溢出 advisory（如 '+103%' horizontal overflow 1.3%）：扩大模块
  data-pptx-bounds 即可消除（advisory 非 blocking）
- 提交前两页都过 vision 复查 + gate 0 blocking
