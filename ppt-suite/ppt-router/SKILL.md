---
name: ppt-router
description: PPT/Deck 生产流水线统一入口与路由（曾分拆为 ppt-workflow / ppt-production-qa / ppt-delivery / consulting-deck-strategist / presentation-visual-director / ecommerce-proposal-ppt，已并入本 skill 的 references/）。任何 PPT/Deck 相关请求（制作、创建、生成、改造、优化、模板、图片稿、咨询 deck、提案 PPT、视觉锁、代表页审核、验收、交付）都先经本 skill 判定流向，再交给对应生产/策略路径。决策链：①商业问题/证据/结论/故事线是否明确 → 策略层（consulting blueprint）；②是否需要代表页审核或逐页视觉锁 → 协调层（visual-lock workflow）；③其余直达 ppt-master 统一 Production Router。美学导向 deck（品牌发布/产品发布/营销创意/杂志感/视觉冲击）分流至 huashu-design（HTML 原生设计路线），商务 consulting deck 仍走 ppt-master（PPTX 原生路线）。策略、协调、视觉指导、QA 验收、交付规范、TP 提案改造的完整 SOP 见 references/。
---

# PPT / Deck 任务顶层路由

PPT 任务全流程的唯一入口。任何 PPT/Deck 请求先经本路由判定，再激活对应 skill。禁止绕过本路由直接选择生产路径（除非请求已明确匹配某生产 skill 的独占触发条件且用户显式指定）。

## 路由决策链

```
PPT / Deck 任务
  │
  ▼
【决策0】美学属性判断（consulting-deck-strategist 的风格确认关口）
  ├─ 美学导向 deck（品牌发布/产品发布/营销创意/杂志感/视觉冲击）
  │     → huashu-design（HTML 原生设计路线，blueprint 逻辑层成果作为输入）
  └─ 商务 consulting deck（咨询/战略/商业计划/数据分析）→ 继续走 PPTX 原生路线
  │
  ▼
【决策1】商业问题、证据、结论与故事线是否明确？
  ├─ 是 → 直接进入【决策2】
  └─ 否 → consulting-deck-strategist
  │             产出：商业逻辑 • Storyline • 页面 Blueprint
  │                   Proof Object • Visual Mother Concept
  │              ▼
【决策2】是否需要代表页审核或逐页视觉锁？
  ├─ 需要 → ppt-workflow（协调层，视觉锁必经关卡）
  │          确认节点 • 状态管理 • Handoff → 交给 ppt-master
  └─ 不需要 / 已有成熟模板 → 直接进入 ppt-master
  │
  ▼
  ppt-master（统一 Production Router）
    ├─ 新建可编辑 PPTX → Generate Editable PPTX
    ├─ 创建品牌模板 → Create Native Template
    ├─ 填充现有模板 → Fill Native PPTX
    ├─ 优化现有 PPTX → Enhance Native PPTX
    └─ 整页图片交付 → Full-slide Image（rw-consulting-ppt + image_gen）
  │
  ▼
  ppt-production-qa（统一验收）
    ├─ 通过 → 正式交付（ppt-delivery：命名/归档/上传确认/版本管理）
    └─ 未通过 → 返回 ppt-master 修正对应 Production Format
```

### 小改快速通道（改动 ≤3 页）

改动 ≤3 页、内容级编辑（数据/文案/换图/版式微调）且视觉权威已批准时，代表页审核压缩为一次确认：出稿 → 确认 → 锁定。确认返回修改意见则退出快速通道，转完整审核。快速通道是审核循环的压缩，不是豁免——不出稿、不确认、不锁定，小改永远不会自动跳过关卡。

## 判定细则

### 决策0：美学属性判断（consulting-deck-strategist 风格确认关口）

| 条件 | 流向 |
|---|---|
| 美学导向 deck：品牌发布/产品发布/营销创意/杂志感/视觉冲击/HTML 原生设计 | huashu-design（HTML 原生设计路线） |
| 商务 consulting deck：咨询/战略/商业计划/数据分析/汇报材料 | 继续走 PPTX 原生路线（ppt-master） |
| 跨层美学引用：商务路线美学判断阶段可引用 huashu-design 的美学层（design-styles/typography）做方向探索 | 色板→主题色、字体→字体栈、布局→版式；HTML 专属特效不进 PPTX |

### 决策1：策略层是否需要介入

| 条件 | 流向 |
|---|---|
| 任务涉及战略/市场/增长/投资/运营模式/管理分析，需要证据支撑的故事线、issue tree、claim-evidence map、页面 blueprint | consulting-deck-strategist |
| 商业问题、证据、结论与故事线已经明确（用户给出现成大纲/文案/结构） | 跳过策略层，直接决策2 |
| 纯制作类：已有完整内容只要排版/套模板/填充 | 跳过策略层，直接决策2 |

### 决策2：协调层是否需要介入

| 条件 | 流向 |
|---|---|
| 需要代表页审核（先出代表页确认风格再批量）或逐页视觉锁（每页都要视觉确认） | ppt-workflow（视觉锁是商务路线必经关卡，即使有成熟模板也须执行，模板仅作 style authority） |
| 不需要审核 / 已有成熟模板 / 用户要求快速出稿 | 直接 ppt-master |

### Production Format 判定（进入 ppt-master 后）

| 请求形态 | 路由 |
|---|---|
| 新建演示文稿；用素材/主题重做视觉 | Generate PPTX |
| 可复用品牌/风格/布局/deck 模板 | Create Template |
| 用现有 PPTX 的原生页壳替换/填充内容 | Fill Native PPTX |
| 已完成 PPTX 保持可见页稳定，加备注/音频/计时/转场 | Enhance Native PPTX |
| 整页图片交付（无对象级可编辑要求，AI 生成 16:9 整页 PNG） | Full-slide Image → rw-consulting-ppt |

## Handoff 契约

- 策略层产出 Blueprint 后：需要视觉锁 → handoff 给 ppt-workflow；不需要 → 直接 handoff 给 ppt-master
- 协调层确认通过后：handoff 给 ppt-master（含已确认的代表页/视觉锁作为生产输入）
- 生产产出后：一律进 ppt-production-qa 验收，PASS / PASS_WITH_APPROVED_EXCEPTIONS 才允许正式交付
- 验收未通过：返回 ppt-master 对应 Production Format 修正，修正后重新渲染并复检

## 兜底

- 无任何 skill 匹配时使用 powerpoint（纯兜底，简单 PPTX 操作）
- ecommerce-proposal-ppt 是 TP 品牌提案专用改造流程（触发词：PPT review / 把XX提案改成XX品牌），命中时优先走它
- huashu-design：美学导向 deck 的 HTML 原生设计路线（触发词：品牌发布/产品发布/营销创意/杂志感/视觉冲击/HTML deck）。本环境已安装，见 `skill_view(name='huashu-design')`。
- guizang-pptx-skill 与 rw-consulting-ppt 属于历史兼容路线，不作为核心路由；不得从 consulting-deck-strategist 绕过 ppt-master 直接进入它们。

## 生产执行笔记（必经必读）

- 进入 ppt-master 的 Visual Construction / 导出 / 图表生成阶段前，**必读 `pptx-production-playbook`**（agent 自有生产经验：spec_lock 契约、质量门顺序、LibreOffice 渲染验收、品牌模板复刻、压字防间距标准）。
- **PPT 内任何数据图表默认实现 = lieflat 法典**（§7.3 选型 SOP）：判数据形状 → 翻 lieflat catalog 锁图型 → 读 gallery 真模板 → 静态 SVG → svg_to_pptx。禁止临场自由发挥画图。lieflat-charts 已升级上游最新版（63 图型 + R01–R12 报告模板），用法见 playbook references/lieflat-visual-into-ppt.md。

---

## 已并入的流水线层（原独立 skill → 现为 references/ 章节）

以下六层曾作为独立 skill 存在，现合并为本路由的 references/ 子文档。触发对应场景时读取对应文件：

### 1. 策略层 — consulting-deck-strategist
**触发**：任务涉及战略/市场/增长/投资/运营模式/管理分析，需要证据支撑的故事线、issue tree、claim-evidence map、页面 blueprint。
**读取**：`references/consulting-deck-strategist.md`（SOP）+ `references/consulting-deck-strategist-refs/consulting-blueprint.md`（蓝图模板）。
**要点**：先定决策问题与假设 → MECE issue tree → claim 分类（fact/calculation/hypothesis/...）→ claim-evidence map → 页面 blueprint（每页一个 action title + narrative job + proof object）。**本层不碰 PPTX 实现**，产出 blueprint 后 handoff 给生产路径（需要视觉锁 → 协调层；否则 → ppt-master）。

### 2. 协调层 — ppt-workflow
**触发**：需要代表页审核（先出代表页确认风格再批量）或逐页视觉锁（每页视觉确认）。
**读取**：`references/ppt-workflow.md`（含 agents/ 子目录的协调 agent 配置）。
**要点**：确认节点、状态管理、Handoff 契约；确认通过后把已确认的代表页/视觉锁作为生产输入交给 ppt-master。本层为可选协调层，纯制作任务可跳过。

### 3. 视觉指导 — presentation-visual-director
**触发**：需要视觉方向、构图约束、图片 prompt 指导、代表页/逐页视觉审核。
**读取**：`references/presentation-visual-director.md` + `references/presentation-visual-director-refs/`（visual-system / review-rubric / ppt-production-qa / feishu-deck-optimization-workflow / ppt-skill-routing）。
**要点**：视觉方向先于生产；图片由 image_gen 生成（本 skill 不是 PPTX 生成器）；视觉审核产出一致性/构图/间距问题清单回灌生产。

### 4. QA 验收 — ppt-production-qa
**触发**：任何 PPT/Deck 制品交付前的统一验收。
**读取**：`references/ppt-production-qa.md`。
**要点**：验收标准分 Production Format（editable / image-only 等）；结果 PASS / PASS_WITH_APPROVED_EXCEPTIONS 才允许进入交付；FAIL 返回生产修正后复检。

### 5. 交付规范 — ppt-delivery
**触发**：交付、上传、归档、发文件、deliver（前置：已通过 QA 验收）。
**读取**：`references/ppt-delivery.md`。
**要点**：命名规范 `项目-任务-YYYYMMDD-versionN`；归档到飞书云空间固定文件夹（token: R4IHfas5VlWqpOdQzMbc5Kxvngh）；上传接口 `POST /drive/v1/files/upload_all`；上传后必须回贴文件链接；视觉批准 ≠ 上传确认，须用户明确指令。

### 6. TP 品牌提案改造 — ecommerce-proposal-ppt
**触发**：PPT review / 把 XX 提案改成 XX 品牌（TP 公司品牌提案场景，如 LB/JACQUEMUS）。
**读取**：`references/ecommerce-proposal-ppt.md` + `references/ecommerce-proposal-ppt-refs/`（pptx-drawing-utils / lb-channel-objective-example / lb-v8-content-pages / lb-assets-inventory）。
**要点**：品牌提案的 review → 改造流程，含画图工具、渠道目标示例、内容页结构、资产清单。

