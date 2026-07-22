# Instagram API via TikHub REST (实测 2026-07-16)

## 可用端点

| 任务 | REST 端点 | 必填参数 | 可选参数 |
|---|---|---|---|
| **用户信息** | `/instagram/v1/fetch_user_info_by_username` | `username` | — |
| **用户帖子(首页)** | `/instagram/v1/fetch_user_posts` | `user_id` | `count`(默认12), `max_id`(翻页) |
| **用户 Reels** | `/instagram/v1/fetch_user_reels` | `user_id` | `count`, `max_id` |
| **帖子详情** | `/instagram/v1/fetch_post_by_url` | `url` | — |
| **帖子评论** | `/instagram/v1/fetch_post_comments_v2` | `shortcode` | — |
| **Hashtag 帖子** | `/instagram/v1/fetch_hashtag_posts` | `hashtag` | — |
| **搜索** | `/instagram/v1/fetch_search` | `keyword` | — |

## ⚠️ 端点版本陷阱

- ✅ **V1 端点可用**：`/instagram/v1/fetch_user_info_by_username`、`/instagram/v1/fetch_user_posts`
- ❌ **V3 端点返回 400**：`/instagram/v3/get_user_profile`、`/instagram/v3/get_user_posts` — 不要用
- V2 端点部分可用但未充分测试

## 用户信息数据结构

```json
{
  "data": {
    "data": {
      "user": {
        "id": "273020258",
        "full_name": "Crumbl",
        "biography": "...",
        "external_url": "http://www.crumbl.com/order",
        "is_verified": true,
        "is_business_account": true,
        "category_name": "Dessert Shop",
        "edge_followed_by": {"count": 6342454},
        "edge_follow": {"count": 5},
        "edge_owner_to_timeline_media": {"count": 3144, "edges": [...]},
        "edge_felix_video_timeline": {"count": ..., "edges": [...]},
        "highlight_reel_count": 10,
        "has_clips": true
      }
    }
  }
}
```

**关键字段提取**：
- `edge_followed_by.count` → 粉丝数
- `edge_follow.count` → 关注数
- `edge_owner_to_timeline_media.count` → 帖子总数
- `category_name` → 品类标签
- `is_verified` → 认证状态

## 帖子数据结构

帖子通过 `data.items[]` 返回（非 `edges/node` 结构）：

```json
{
  "data": {
    "more_available": true,
    "items": [
      {
        "pk": 3939907970260004656,
        "code": "DatXWynE-8w",
        "caption": {"text": "..."},
        "like_count": 23632,
        "comment_count": 1827,
        "play_count": 1148553,
        "ig_play_count": 1148553,
        "taken_at": 1783900853,
        "media_type": 2,
        "product_type": "clips",
        "carousel_media": null,
        "user": {"id": "273020258"}
      }
    ],
    "next_max_id": "..."
  }
}
```

**关键字段**：
- `code` → 帖子 shortcode，URL 格式：`https://www.instagram.com/p/{code}/`
- `caption.text` → 文案正文
- `like_count` → 点赞数
- `comment_count` → 评论数
- `play_count` / `ig_play_count` → 播放数（仅视频/Reels）
- `taken_at` → Unix 时间戳
- `media_type`：1=图片, 2=视频, 8=轮播
- `product_type`："clips" = Reels, "feed" = 普通帖子
- `carousel_media` → 非 null 时为轮播图

## 批量分析流程（21 账号实测）

```bash
AUTH="Authorization: Bearer $TIKHUB_API_KEY"
API="https://api.tikhub.io/api/v1/instagram/v1"

# Step 1: 批量获取用户信息
for username in crumbl levainbakery milkbarstore; do
  curl -s "$API/fetch_user_info_by_username?username=$username" \
    -H "$AUTH" -o "/tmp/ig_profile_${username}.json"
done

# Step 2: 从 profile 提取 user_id
python3 -c "
import json
with open('/tmp/ig_profile_crumbl.json') as f:
    d = json.load(f)
uid = d['data']['data']['user']['id']
print(uid)
"

# Step 3: 批量获取帖子（每账号 12-24 条）
for uid_info in "crumbl:273020258" "levainbakery:221402837"; do
  username=$(echo $uid_info | cut -d: -f1)
  uid=$(echo $uid_info | cut -d: -f2)
  curl -s "$API/fetch_user_posts?user_id=$uid&count=24" \
    -H "$AUTH" -o "/tmp/ig_posts_${username}.json"
done
```

## 内容分类框架（品牌账号分析用）

| 内容大类 | 识别关键词 | 英文子类 |
|---|---|---|
| 每周菜单 | weekly rotating menu, this week, weekly menu | Weekly Menu |
| 新品发布 | (new), just dropped, introducing, now available | New Product Launch |
| 经典回归 | fan favorite, back by popular, return | Fan Favorite Return |
| 配方教程 | recipe, how to, tutorial, step by step | Recipe/Tutorial |
| 幕后制作 | behind the scenes, BTS, how we make | Behind the Scenes |
| 互动投票 | which one, vote, comment below, tell us | Interactive/Voting |
| 节日营销 | happy, national, holiday, celebrate | Holiday/Event |
| 联名合作 | collab, partnership, x , ft. | Collaboration |
| 限时催单 | last day, last chance, limited, hurry | Limited/Urgency |
| 产品展示 | (默认分类) | Product Showcase |
| 视频/Reels | media_type==2 | Video/Reels |
| UGC/转发 | repost, regram, featured | UGC/Repost |

## Excel 输出规范（openpyxl）

**⚠️ 必须用 `/usr/bin/python3`**（系统 Python 3.12），hermes venv 无 pip 无法装 openpyxl。

标准 7 Sheet 结构：
1. **账号总览** — 按粉丝数排序，含互动率、媒体占比、CTA覆盖率
2. **全部内容明细** — 按点赞数排序，每条标注分类/媒体类型/互动数据
3. **内容类型分布** — 全品类内容统计
4. **媒体类型分析** — 视频 vs 图片 vs 轮播对比
5. **账号内容矩阵** — 账号 × 内容类型交叉表
6. **Hashtag 分析** — Top 30 标签 + 使用账号
7. **综合洞察** — 规模分布、策略对比、关键发现
