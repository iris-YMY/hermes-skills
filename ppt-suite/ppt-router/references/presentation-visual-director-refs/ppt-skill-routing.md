# PPT Skill 路由与冲突地图（2026-08-08 全库 review）

来源：小艾要求 review 全局 PPT skill 后整理。8 个相关 skill 逐一加载比对。

## 一、统一路由表（推荐分工）

| 用户请求形态 | 首选 skill | 理由 |
|---|---|---|
| 可编辑原生 PPTX（默认/绝大多数） | `ppt-master` | 完整路由：Generate/Create Template/Fill Native/Enhance Native；支持 quick-generate；native-chart + embedded workbook |
| 需要逐页严格确认的汇报 | `ppt-workflow` | 四阶段确认制（内容→视觉→图稿→还原），无快速路径，慢但稳 |
| 咨询级/图片稿（image-only，不需要可编辑） | `rw-consulting-ppt` | 自带路由锁：要可编辑图表就切 ppt-master，不削弱自身 |
| TP 品牌提案改造/审查（LB/JACQUEMUS 等） | `ecommerce-proposal-ppt` | 专属铁律：先 review → 用户 OK → 出 PPT |
| 通用轻量 .pptx 处理（读/改/渲染） | `powerpoint` | 全格式操作 + QA 脚本（slides_test/render_slides） |
| 策略蓝图先行（hypothesis-led 咨询） | `consulting-deck-strategist` | 只做论证结构，生产交给生成层 |

## 二、已识别的冲突（review 结论，2026-08-08）

### 🔴 C1：consulting-deck-strategist 与 ppt-master 矛盾
- 它写死 "Do not invoke ppt-master, ppt-workflow, or rw-consulting-ppt as production owners"，并把蓝图交给 `presentations:Presentations`
- **Hermes 环境没有 Presentations 插件**（全库搜索 0 结果）→ 蓝图无人接手，还禁止用主力生产
- 待修：把 `presentations:Presentations` 改为 `ppt-master`，删除禁止条款

### 🔴 C2：触发条件重叠（入口混乱，最严重）
- `ppt-master` / `ppt-workflow` / `powerpoint` 的 description 都覆盖 "create/produce a PPT/deck/slides"
- 用户一句"帮我做个 PPT"会同时命中 3 个 skill，agent 不知道该听谁的
- 待修：各 skill description 加互斥路由声明（见上表）

### 🟡 C3：流程门禁节奏不一致
- `ppt-workflow`：强制四阶段每阶段等确认，无快速路径
- `ppt-master`：有 BLOCKING gate，但 quick-generate 可跳过确认
- 同一句"快点出一版"，两 skill 行为完全不同

### 🟡 C4：ecommerce-proposal-ppt 与 presentation-visual-director 方法论相反
- `ecommerce-proposal-ppt`（用户纠正定案）：新建空 Presentation() 从零画，避免模版页残留（30 页事件教训）
- `presentation-visual-director`：保留模版全部 slide + add_slide 追加（会产出 21+9=30 页）
- ⚠️ 追加方案正是小艾明确否过的 30 页方案。TP 场景标准 = 从零画。

### 🟡 C5：ppt-master 与 ppt-workflow 功能重叠
- 两者都做可编辑 PPT + native-chart + embedded workbook
- 区别仅在确认节奏；长期可考虑合并或明确场景分工

## 三、做得好的（保持）
- `rw-consulting-ppt` 自带路由锁（image-only ↔ 切 ppt-master），边界清晰
- `artifact-review-director` 边界干净，不碰 PPTX 视觉方向
- `presentation-visual-director` 有生态章节，但不含新三件套（本次已补）

## 四、安装信息速查（2026-08-08）
- `ppt-master`：hugohe3/ppt-master v4.4.0 完整版，装到 productivity/ppt-master（427 文件 28MB）；attribution_guard.py 校验通过；templates/icons（11,883 文件）与 ai-image-comparison PNG 未下载（按需补）
- `ppt-workflow`：productivity/ppt-workflow（SKILL.md + agents/openai.yaml）
- `rw-consulting-ppt`：productivity/rw-consulting-ppt（含 9 references + 2 examples + 打包脚本）
- 三者均做 Hermes 轻适配（Codex→agent 字样替换）
