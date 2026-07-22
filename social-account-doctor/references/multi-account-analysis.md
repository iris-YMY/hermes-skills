# 多账号对比分析方法论

> 适用于：用户给一批竞品账号（Instagram/TikTok/小红书），要求批量分析并输出 Excel 对比。

## 内容分类体系（内容类型 vs 媒体类型）

### 内容类型（帖子讲的是"什么"）

根据文案关键词分类，与媒体形式无关：

| 内容大类 | 触发关键词 | 子类 |
|---|---|---|
| 每周菜单 | weekly rotating menu, this week, weekly menu, weekly flavors | Weekly Menu / Fan Favorites Week / Theme Week |
| 新品发布 | (new), just dropped, introducing, now available, new flavor | New Product Launch |
| 经典回归 | fan favorite, back by popular, back on menu | Fan Favorite Return |
| 互动投票 | which one, vote, tell us, tag a friend, what's your | Which One? / Comment Prompt / Interactive Game |
| 节日/纪念日 | happy, national, holiday, christmas, valentine, 4th of july | National Day / Holiday / Birthday |
| 幕后制作 | behind the scenes, how we make, day in my life, making of, BTS | Behind the Scenes |
| 配方教程 | recipe, how to, tutorial, step by step, ingredients | Recipe/How-to |
| 联名合作 | collab, partnership, x , ft., feat | Brand Collab |
| 门店/活动 | open, location, visit us, order now, store | Store/Event |
| UGC/转发 | repost, regram, featured, customer, you guys | UGC/Repost |
| 限时催单 | last day, last chance, limited, hurry, don't miss | Last Day/Urgency |
| 产品展示 | （默认兜底，不匹配以上任何类型时） | Product Showcase |

### 媒体类型（帖子"怎么呈现"）

| 媒体类型 | Instagram media_type | 说明 |
|---|---|---|
| 视频/Reel | 2 | 含 Reels、普通视频 |
| 图片 | 1 (且无 carousel_media) | 单张图片 |
| 轮播图 | 8 (或有 carousel_media) | 多图轮播 |

**铁律**：视频/Reels 是媒体类型，不是内容类型。一条视频帖的内容类型取决于文案内容（幕后制作/产品展示/互动投票等）。

## Excel 模板结构

### Sheet 1: 账号总览
按粉丝数排序，每账号一行：
- 账号、品牌名、粉丝数、帖子总数、认证、品类
- 采样帖子数、平均点赞/评论/播放
- 互动率(赞+评/粉丝)、视频/轮播/图片占比
- CTA覆盖率、Top 3 内容类型、主页链接

### Sheet 2: 全部内容明细
所有帖子按点赞数排序，每条标注：
- 账号、发布时间、内容大类、内容子类、媒体类型
- 文案、点赞、评论、播放、互动率(赞+评/粉丝)
- 有CTA、有Emoji、链接

### Sheet 3: 内容类型分布-按账号 ⭐
每个账号双行展示：
- 第1行：各内容类型的帖子数量
- 第2行（↳ 占比）：各内容类型的占比百分比
- 最后一行：全部合计

### Sheet 4: 媒体类型分布-按账号 ⭐
每账号一行，展示：
- 视频数/占比/均赞/均评/均播放
- 图片数/占比/均赞/均评
- 轮播数/占比/均赞/均评
- 最后一行：全部合计

**number_format 列号精确对应**（以 15 列为例）：
- Col 4 (视频占比): `"0%"`
- Col 9 (图片占比): `"0%"`
- Col 13 (轮播占比): `"0%"`
- 其他数值列: `"#,##0"`

### Sheet 5: 账号内容矩阵
21×N 交叉表：每行=账号，每列=内容类型，值为帖子数。用颜色底色区分类型。

### Sheet 6: 综合洞察
- 账号规模分布（头部/腰部/成长）
- 内容策略对比（视频优先/图片为主/均衡混合）
- 互动率排名
- 关键发现
- 数据概览

## 互动率计算

**唯一公式**：`engagement_rate = (likes + comments) / followers`

- ✅ 适用于所有帖子类型（视频、图片、轮播）
- ❌ 不要用 plays 做分母（图片帖 plays=0，导致除零或 >100%）
- 账号级互动率 = 所有帖子的平均(赞+评) / 粉丝数

## Instagram 翻页取数

每页返回 12 条，需翻 3 页取 ~36 条：

```python
# Page 1
r1 = requests.get(f"{API}?user_id={uid}&count=12")
items_p1 = r1["data"]["items"]
next_id = r1["data"]["next_max_id"]

# Page 2
r2 = requests.get(f"{API}?user_id={uid}&count=12&max_id={next_id}")
items_p2 = r2["data"]["items"]
next_id2 = r2["data"]["next_max_id"]

# Page 3
r3 = requests.get(f"{API}?user_id={uid}&count=12&max_id={next_id2}")
items_p3 = r3["data"]["items"]

# Merge + deduplicate by pk
all_items = deduplicate(items_p1 + items_p2 + items_p3)
```

## CTA 检测关键词

```python
cta_words = ["order now", "link in bio", "visit", "come try", "grab", 
             "shop", "swipe", "comment", "tag", "head to", "see you at"]
has_cta = any(w in caption_lower for w in cta_words)
```

## openpyxl 颜色方案

```python
cat_colors = {
    "每周菜单": "E2EFDA",   # 绿
    "新品发布": "FFF2CC",   # 黄
    "经典回归": "FCE4D6",   # 橙
    "互动投票": "D9E2F3",   # 蓝
    "节日/纪念日": "E4DFEC", # 紫
    "限时催单": "F4CCCC",   # 红
    "产品展示": "D0E0E3",   # 青
    "幕后制作": "CFE2F3",   # 浅蓝
    "配方教程": "D5A6BD",   # 粉
    "门店/活动": "B6D7A8",   # 浅绿
    "联名合作": "F9CB9C",   # 浅橙
    "UGC/转发": "D9D2E9",   # 浅紫
}
```

## 用户偏好备忘

- ❌ 不需要 Hashtag 分析 Sheet（用户明确说不需要）
- ✅ 内容类型和媒体类型都要 BY ACCOUNT 拆分
- ✅ 用 emoji 分段 + 短列表呈现分析结果（用户可能在手机端看）
- ✅ 视频链接必须可在 PC 浏览器打开
