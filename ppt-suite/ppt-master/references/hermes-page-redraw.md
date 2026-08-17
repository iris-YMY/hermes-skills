# 原生 PPTX 页面重绘（Page Redraw）技术

场景：已有 PPTX 个别页面文字密集、重点不突出，需保持品牌风格重排（内容不变、视觉升级）。
本方法不走 ppt-master 的 native-enhance 脚本，直接 python-pptx 删除目标页 shapes 后重绘，保留原图。适合"改 2-4 页"的场景，比整套 enhance 流程轻量。

## 工作流

1. **结构分析**：遍历每页 shapes，打印 `type/name/pos/size/文本前40字`。区分文字页（AUTO_SHAPE+TEXT_BOX）与整页大图页（全尺寸 PICTURE，通常不用动）。
2. **品牌参数提取**：从现有 AUTO_SHAPE 读 `fill.fore_color.rgb`（例：LB 品牌 红#C42E2E / 灰卡#F0F0EE / 粉条#FDF3F3），从标题 textbox 读 `font.name/size/bold/color`（例：Century Gothic 20pt bold）——用原值保证风格统一，不要自己发明配色。
3. **提取原图**：删除 shapes 前先遍历 picture shape 存 `shape.image.blob`，重绘时用 `add_picture(BytesIO(blob), ...)` 恢复。
4. **重绘**：封装 `add_rect` / `add_text` 辅助函数：
   - 形状：`fill.solid(); fill.fore_color.rgb = ...`；去边框 `line.fill.background()`；关阴影 `shadow.inherit = False`
   - 文本：`word_wrap=True`、`vertical_anchor`、`margin_* = Emu(0)`、`line_spacing`
   - LB 卡片公式：灰底矩形 + 左侧 0.06in 红竖条 + 红 bold 标题 + 深色正文
5. **渲染 QA 循环**：`soffice --headless --convert-to pdf` → `pdftoppm -png -r 100` → 拼接对比图 → `vision_analyze` 提审 → 修 → 重渲染，直到通过。

## 关键坑

- ⚠️ `add_picture` 只收 file-like，不收 bytes：报 `AttributeError: 'bytes' object has no attribute 'seek'` → 必须 `BytesIO(blob)` 包装。
- ⚠️ 删除 shape 用 XML 层：`sh._element.getparent().remove(sh._element)`（python-pptx 无顶层 remove API）。
- ⚠️ 数据可视化必须精确比例：进度条 63% 就画 63% 长度。三段"各自独立"的进度条（每段占满再填充比例）易被误读为三组并列达成率 → 改**连续一段**，0-63 浅 / 63-81 中 / 81-100 深，分界点下方标注百分比。
- ⚠️ 底部总结条一行 70+ 字符必换行：拆两行或降字号（10pt + line_spacing 1.1）。
- ⚠️ 版心 13.33in 宽：边距 0.8in；左侧卡片区与右侧图片区要平衡，避免大面积留白（可加宽卡片/缩小图片底衬）。

## vision_analyze QA 提问模板

- 文字是否溢出卡片边界或被截断？布局是否对齐？元素是否重叠？
- 每页是否有一个清晰视觉焦点（主角）？其余内容是否降级？
- 数据可视化（进度条/比例）是否与数值精确对应？

## 展示给用户

- 先发**纵向拼接 PNG**（单页竖排，宽 ~1334px，手机可读），用户确认后才交付 pptx 文件。
- 用户偏好：业务 PPT 优先**原生形状**而非 AI 生图（保证文字准确 + 可编辑）；原图（模特图等）保留不动。
