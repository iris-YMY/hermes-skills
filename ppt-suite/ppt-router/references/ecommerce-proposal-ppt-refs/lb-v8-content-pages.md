# LB Operation Traffic v8 — P3/P4/P5/P7 内容与版式定稿（2026-08-08）

背景：用户提供最新版飞书文档《Love Bonito 品牌定位》（wiki U1q3wm1nWi6yIlkvYtgcZvSZn0e → obj_token=OwSddXsrmognZyxUPJPcZJa8nff，docx，全文 10091 字），要求按文档天猫章节（三、3.1–3.8；四、渠道6–9；五、5.2/5.4）优化 LB_Operation_Traffic_v7 的 P3/P4/P5/P7，交付可对外 present 完整版。生成脚本：`/tmp/lb_files/gen_lb_ppt_v8.py`。

## 用户明确的内容裁剪指令（必须遵守，不得加回）
1. 不留 [IMG] 占位框 → 正常生成完整版（配真实品牌图）
2. P7 外部数据（2024 店播 GMV 64%/份额 69.5% 等）→ 替换成文档天猫策略内容
3. P3 去掉"站内付费与搜索"内容 + 去掉截图占位
4. P4 不要 KPI 内容
5. P5 不要"货盘四层承接"
6. 配图必须用 LB 品牌图（tpl_imgs/），不用 orig_imgs 截图

## 每页版式定稿
- **P3 OPERATIONAL SEARCH TRAFFIC**：左竖图（image19）+ 右三卡 = SEARCH KEYWORD SYSTEM（四组词：品牌/品类/问题/场景词）/ SHELF CATCHMENT 货架承接（按问题/生命阶段/场景/功能/身高体型 5 种购物方式）/ SELLING POINTS + PDP OPTIMIZATION；底部条"SHELF = 承接搜索 → 稳定自然成交"。
- **P4 OPERATIONAL CONTENT TRAFFIC**：左侧 2×2 卡（GUANG GUANG/SHORT VIDEOS、STORE LIVESTREAMING、KOC/KOS CULTIVATION、BUYER SHOW/Q&A）+ 右侧大图（image21）；底部条=内容语言一致性案例「LB松弛腰腹显比例通勤裤｜久坐饭后不勒腰｜Petite/Regular｜真口袋」（文档 5.2）。
- **P5 PDP SHORT VIDEO STRATEGY**：左竖图（image23）+ 右区 = 覆盖率大数字（80–100% TOP100，Progressive 63%→81%→100%）/ FUNCTION MAPPING 条（Bloat Friendly→久坐不勒腰、BraFree→免内衣、Crease-Ease→出差免熨、Petite→小个子版型）/ 3×2 素材卡；底部条=PDP 自证六要素（解决什么问题→结构/版型/面料→多身材试穿→坐立行走测试→中国尺码→洗护售后）。
- **P7 LB LIVESTREAM STRATEGY 店播+中腰部达播**：推荐条（店播 base + 中腰部达播 amplifier）+ 左 2 卡（STORE STREAM = TMALL CONTENT CORE、SIX FIXED COLUMNS 六档栏目：梨形裤装/小个子裤长/BraFree 胸型/一衣三穿/南方通勤/孕期重返职场）+ 右 2 卡（DABO AMPLIFIER RULES：不依赖纯低价头部达播、新客导入会员体系；DABO × HERO SKU 匹配表：职场穿搭→RuchedReady西装(春装)/品质女装→BraFree(618)/小个子梨形→Leggy/母婴→Bump·Nursing/生活方式→Multi-Way(11.11)）；底部条=直播联动（小红书种草→店播转化→达播大促爆发→新客入会员）。

## 图片素材盘点（/tmp/lb_files/tpl_imgs/，25 张）
- image19-25（572×800×7张）：LB 产品/模特图 → 卡片配图首选
- image13.jpeg（3128×4692）：高清品牌大图（深色）
- image15.png（2000×2800）：章节页大图（P1 在用）
- image11.jpeg（1916×1881）、image3/4/5（792×1108）、image16/17/18（500×700）：更多产品图
- orig_imgs/（1044 张）：原文档拆图（含 1080×2520 竖屏截图），用户明确不要截图，默认不用

## 版式规范（LB TEMPLATE）
- 16:9（12192000×6858000），Century Gothic，LB_RED #C42E2E / DARK #0A0A06 / LIGHT #F0F0EE / PINK #FDF3F3
- 卡片标题英文大写 + 要点中文（中文标题在 Century Gothic 下渲染可疑，避免）
- 底部结论条 = PINK 底 + LB_RED 粗体
- 渲染自查：soffice → PDF → pymupdf dpi=110 → PNG → tesseract OCR 检查文字完整性
