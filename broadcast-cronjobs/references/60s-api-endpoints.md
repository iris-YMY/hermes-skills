# 60s API Endpoint Reference

Base URL: `https://60s.viki.moe`
Docs: https://docs.60s-api.viki.moe
GitHub: https://github.com/vikiboss/60s

⚠️ All endpoints require `/v2/` prefix (v1 deprecated).
⚠️ Cloudflare Workers hosted — concurrent request limit applies (~3 safe).
⚠️ Free, no API key required.

## News & Information
| Endpoint | Description | Data Format |
|----------|-------------|-------------|
| `/v2/60s` | 每日60秒新闻摘要 | `{date, news[], tip, image}` |
| `/v2/ai-news` | AI 新闻 | `{date, news[{title, detail, link, source}]}` |
| `/v2/it-news` | IT/科技新闻 | `[{title, description, link}]` |
| `/v2/it-news/rank` | IT 新闻排行 | `[{title, link}]` |
| `/v2/hacker-news/top` | Hacker News Top | `[{id, title, link}]` |
| `/v2/hacker-news/best` | HN Best | same |
| `/v2/hacker-news/new` | HN New | same |
| `/v2/bing` | Bing 每日 | `{title, headline, description, main_text}` |

## Hot Lists
| Endpoint | Description | Data Format |
|----------|-------------|-------------|
| `/v2/baidu/hot` | 百度热搜 | `[{rank, title, desc}]` |
| `/v2/baidu/realtime` | 百度实时 | same |
| `/v2/baidu/teleplay` | 百度电视剧 | `[{rank, title, desc, score}]` |
| `/v2/baidu/tieba` | 百度贴吧 | `[{rank, title, desc}]` |
| `/v2/toutiao` | 头条热榜 | `[{title, hot_value}]` |
| `/v2/weibo` | 微博热搜 | `[{title, hot_value, link}]` |
| `/v2/zhihu` | 知乎热榜 | `[{title, detail}]` |
| `/v2/rednote` | 小红书 | `[{rank, title, score}]` |
| `/v2/douyin` | 抖音热榜 | `[{title, hot_value}]` |
| `/v2/quark` | 夸克热搜 | ⚠️ Returns raw HTML, not clean JSON |

## Entertainment
| Endpoint | Description | Data Format |
|----------|-------------|-------------|
| `/v2/douban/weekly/movie` | 豆瓣口碑电影 | `[{rank, title, rating}]` |
| `/v2/douban/weekly/tv_chinese` | 豆瓣国产剧 | same |
| `/v2/douban/weekly/tv_global` | 豆瓣全球剧 | same |
| `/v2/douban/weekly/show_chinese` | 豆瓣国产综艺 | same |
| `/v2/douban/weekly/show_global` | 豆瓣全球综艺 | same |
| `/v2/maoyan/realtime/movie` | 猫眼实时票房 | `{list[{movie_name, box_office_desc, ...}]}` |
| `/v2/maoyan/realtime/tv` | 猫眼全网热度 | `{list[{programme_name, channel_name, attention_rate_desc}]}` |
| `/v2/maoyan` | 影史票房总榜 | `{list[{movie_name, box_office_desc}]}` |
| `/v2/dongchedi` | 懂车帝热榜 | `[{rank, title}]` |

## Finance
| Endpoint | Description | Data Format |
|----------|-------------|-------------|
| `/v2/fuel-price` | 油价 | `{region, trend, items[]}` |
| `/v2/exchange-rate` | 汇率 | `{base_code, rates{}}` |
| `/v2/gold-price` | 金价 | `{date, metals[{name, today_price, high_price, low_price, unit}], stores, banks}` |

## Fun / Utility
| Endpoint | Description | Data Format |
|----------|-------------|-------------|
| `/v2/moyu` | 摸鱼日历 | `{date{gregorian, lunar}, progress{week, month, year}, currentHoliday{name, countdown}}` |
| `/v2/hitokoto` | 一言 | string |
| `/v2/dad-joke` | 冷笑话 | string |
| `/v2/luck` | 每日运势 | object |
| `/v2/ip` | IP 信息 | object |
| `/v2/weather/realtime` | 实时天气 | object |
| `/v2/weather/forecast` | 天气预报 | object |

## Known Pitfalls
- `/v2/bili` returns 500 (B站 API blocked)
- `/v2/quark` returns HTML, not clean JSON
- `/v2/maoyan/realtime/web` returns empty dict
- All endpoints return `{code: 200, data: ...}` wrapper
