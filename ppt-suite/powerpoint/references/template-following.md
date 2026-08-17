# 模板跟随模式（Template-Following Mode）

> 来源：OpenAI `presentations` skill 的 template-following.md 方法论，经 Hermes 适配（实现层改为 python-pptx / OOXML 操作，不依赖 Codex artifact-tool）。

## 何时使用

用户提供了现有 PPTX、要求跟随某份演示文稿、或附带的 PPTX 明确/暗示是模板时。

## 核心原则

**只做源幻灯片盘点（source slide inventory）**：检查每一张源幻灯片，为输出挑选源幻灯片，复制这些源幻灯片，然后就地编辑复制来的元素。不要：
- 从配色、字体、截图或"感觉"重建全新 deck
- 构建/消费可复用模板注册表
- 运行模板代码生成

**保留源 deck 的 master → layout → slide 层级**。一次性编辑改 slide，重复性修改改 layout，只有刻意的全局变更才改 master。不要把继承的 master/layout 压平成 slide 本地覆盖。

## 精确克隆/编辑契约

1. 复制/导入源 PPTX。
2. 渲染并检查每一张源幻灯片（用 `scripts/thumbnail.py` 或 soffice 转图）。
3. 创建 `template-frame-map.json`：把每个输出 slide 映射到一个源 slide。
4. 通过复制映射的源幻灯片构建 `template-starter.pptx`。
5. 应用所需编辑，同时保留源 deck 的结构和样式。
6. **精确保留源模板的排版**：字体族、字号、字重、行距、段距、文本内边距、对齐、垂直锚点，除非用户明确要求重排/改尺寸。新文案放不下时：缩短文案、选更合适的源版式、或拆分到另一张克隆页——**不要悄悄缩小字号来硬塞**。
7. **审计继承的占位符**：包括 `sldNum`、`dt`、`ftr`；要么有意填充，要么删除。把可见的默认提示文本（`Slide Number`、`Date`、`Footer`、`Click to add title`、`Name goes here` 等）视为空的继承占位符；**最终 deck 中绝不留下空的 PowerPoint 占位符**，即使 PNG 渲染看不出来。
8. 导出 PNG 与 PPTX 供 QA。
9. 为外部来源素材与非平凡主张在演讲者备注中保留/添加 `[Sources]` 块。

## 实现方式（Hermes 环境）

### 源幻灯片盘点

```bash
# 1. 转图查看每一页
python scripts/office/soffice.py --headless --convert-to pdf <source.pptx>
pdftoppm -jpeg -r 150 <source>.pdf src-slide

# 2. 提取结构信息
python -m markitdown <source.pptx>          # 文本内容
python scripts/office/unpack.py <source.pptx> unpacked/   # 原始 XML，检查占位符 <p:ph>
```

审查所有源幻灯片 PNG、占位符 XML 和文本，不要只看一两张代表页。

### 构建 frame map

创建 `template-frame-map.json`（放工作目录）：

```json
{
  "outputSlides": [
    {
      "outputSlide": 1,
      "sourceSlide": 3,
      "narrativeRole": "opening thesis",
      "reuseMode": "duplicate-slide",
      "editTargets": []
    }
  ],
  "omittedSourceSlides": [
    { "sourceSlide": 4, "reason": "appendix pattern not needed" }
  ]
}
```

每个输出 slide 都必须有 `sourceSlide`。源 slide 可被多次复用。被省略的源 slide 要在 audit 或 frame map 中记录原因。

### 构建 starter deck

用 python-pptx 复制映射的源幻灯片：

```python
from pptx import Presentation
import copy

src = Presentation("source.pptx")
dst = Presentation("source.pptx")  # 或新建空 deck 后逐页复制

# 复制指定页：python-pptx 复制 slide 需要 XML 级操作
# 参考 scripts/add_slide.py 的思路；保留母版/版式继承
```

> 提示：python-pptx 原生不支持复制 slide，需要操作 XML。简单场景可以直接基于源文件编辑（就地修改文本/图片），复杂场景用 `scripts/office/unpack.py` 解包后复制 slide XML。

### 编辑规则

- `editTargets: []` 表示仅保留（preserve-only）。不向该页添加叙事文本、图表、表格、图片、面板、callout 或方框，除非验证过的 frame map 明确允许新元素且给出有界区域与理由。
- 品牌页、logo、bumper、divider、separator、chrome、section 和空白页是 preserve-only 模式，除非源幻灯片含有明确填充/删除的继承内容槽位。不要把 bumper 大空白品牌侧当画布用。
- **默认每个继承对象（形状/图片/表格/图表/版式元素/master 元素/文本对象）为 `keep`**。只有被明确分类为 `rewrite`/`replace`/`delete` 时才改写、清空或删除。
- **结构性占位符**（带 OOXML `<p:ph>` 元数据或解析后占位符元数据的元素）：必须处理——`rewrite`、`rewrite-and-reposition`、`replace`、`delete` 或 `fill-placeholder` 之一。`keep` 和 `add` 不算处理，因为 PowerPoint 在编辑模式下会显示 "Click to add title" 等默认提示。
- **不要用宽泛文本启发式清空**：绝不运行等价于 `if (text.trim()) shape.text = ""` 的逻辑，绝不清空复制页上每个带文本的形状。OpenAI/品牌 wordmark、品牌文本、页脚、来源栏、章节标记、master/layout 装饰可能是可编辑文本对象——除非编辑计划明确要求改/删该对象，否则保留。

### 数据编辑

- **先计算，后设计**。
- 有用时在备注或附录中展示公式/计算定义。
- 基于计算结果排序和得出结论，而非视觉直觉。
- 尽可能把结果插入继承的表格/图表/指标框架中。

## QA（模板跟随额外检查）

1. 渲染每张最终 slide（soffice → PDF → pdftoppm）。
2. 逐张全尺寸检查，不只看拼贴图。
3. 修复意外重叠、裁剪、换行、断裂的连接线、未解决的占位符、不一致的页脚/页码、图表/数据不匹配。
4. 用 `python scripts/slides_test.py <output.pptx>` 检测内容溢出画布（若脚本已随 skill 提供）。
5. 确认 deck 满足用户需求且叙事连贯。
6. 验证研究性主张与来源素材可追溯。
