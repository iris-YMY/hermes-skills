# WeChat "日常消费" Reclassification Rules

WeChat lumps ~40% of all expenses into a single "日常消费" category. This multi-pass keyword methodology reclassifies them into proper categories.

## Methodology: Multi-Pass Keyword Classification

### Pass 1 — High-confidence keywords (priority order, first match wins)

```python
rules_pass1 = [
    # (target_category, keywords_in_note, extra_condition)
    ("转账", ["收款方备注:二维码收款", "已转账"], lambda r: r['amt'] >= 500),
    ("充值缴费", ["交费", "联通", "移动", "电信"], None),
    ("酒店旅行", ["酒店", "签证", "列车", "旅游", "中銀訂單", "MOP"], None),
    ("爱车", ["岚图", "ADS", "汽车", "车"], None),
    ("穿搭美容", ["lululemon", "直值", "肤丽泽", "QualityFirst"], None),
    ("休闲玩乐", ["音乐", "演唱会", "盛世全集", "王力宏", "道观", "香篆"], None),
    ("餐饮", ["大众点评", "团购", "烤肉", "烧肉", "牛排", "寿司", "寿喜", "龙虾",
              "食堂", "MAKI", "济州", "席小鲜", "隐山酌", "眉州东坡",
              "大馥", "东发道", "茉莉奶白", "外卖", "西塔老太太", "爱牧牛",
              "郭子", "1788广场", "1788国际", "HZ108", "冷饮", "小酒馆", "寿司郎"], None),
    ("生活日用", ["联华", "奥乐齐", "超市", "先用后付"], None),
]
```

### Pass 2 — Broader patterns (catch medium-confidence matches)

```python
rules_pass2 = [
    # 餐饮 — broader
    ("餐饮", ["堂食", "打包", "POS", "咖啡", "Coffee", "茶", "果汁", "果切",
              "水果", "酸奶", "麻辣烫", "馄饨", "面馆", "冰淇淋", "Gelato",
              "爆肉", "香香鸡", "糖葫芦", "LINLEE", "茉酸奶", "BlueBottle",
              "cococean", "BOSS CAFE", "马记永", "陈香贵", "四海游龙",
              "金拱门", "喜识", "严胜利", "食亭", "trova", "HUA TING",
              "三出山", "三立方", "零食小铺", "宝尊项目点", "CHAPANDA",
              "上海CP静安", "上海大宁店", "上海美罗城", "上海无限极",
              "上海商城", "上海静安大融城", "上海大华第一坊", "上海静安",
              "上海合生汇", "上海兴业太古汇", "上海苏河湾", "上海真如环宇城",
              "上海长寿路", "淳安明珠", "乾元南街", "千岛龙郡", "新万荣门市",
              "湖州德清", "怡宝", "矿泉水", "NEOMAS", "VICUNAS",
              "上海明捷置业"]),
    ("交通", ["缴费离场", "缴费通", "先乘后付", "高速", "停车", "沪ABZ"]),
    ("医疗保健", ["挂号", "处方", "门诊", "姚梦寅", "4818FU"]),
    ("充值缴费", ["apple.com", "连续包年", "腾讯云", "84405140", "ID1538527202"]),
    ("休闲玩乐", ["泡泡玛特", "PSN-", "洛克公园", "场地预订", "上海永华影城"]),
    ("穿搭美容", ["冠靓芸", "服饰", "回力", "COS会员", "CHIC", "彩棠", "TIMAGE", "遮瑕"]),
    ("生活日用", ["名创优品", "先购后付"]),
    ("酒店旅行", ["千岛湖", "阅树", "千岛庄园", "CDFG MACAU", "NY8 NEW YAOHAN"]),
    ("生活服务", ["闪送", "海马体", "照相馆"]),
    ("购物", ["京东-订单", "小红书订单"]),
]
```

### Pass 3 — Pattern-based grouping (for remaining items)

| Pattern | Default Classification | Rationale |
|---------|----------------------|-----------|
| 商户单号XP开头 | → 餐饮 | 美团/大众点评订单号格式 |
| 二维码收款 + ¥<500 | → 餐饮 | 街边小店扫码支付 |
| "请在...前付款" | → 餐饮 | 外卖平台催付格式 |
| 统一刷卡/前台码/扫码支付 | → 保留日常消费 | 无法识别商户 |
| 无备注 + ¥>200 | → 保留日常消费 | 需用户确认 |
| 无备注 + ¥<50 | → 保留日常消费 | 小额零碎，影响小 |

## Expected Results (based on 2025-06 ~ 2026-06 data)

| Step | Records Classified | Amount | Remaining |
|------|-------------------|--------|-----------|
| Original "日常消费" | 520笔 | ¥227,176 | — |
| Minus 43笔退款 | — | ~¥100K | 477笔 |
| Pass 1 | ~180笔 | ~¥76K | ~297笔 |
| Pass 2 | ~175笔 | ~¥19K | ~116笔 |
| Pass 3 (auto) | ~30笔 | ~¥4K | ~86笔 |
| Final (user review) | ~86笔 | ~¥28K | → 保留日常消费 |

## Key Lessons

- **退款 must be handled first** — 43笔 "已全额退款" records still marked as 支出 inflate the category by ~¥100K. Fix these to 不计收支 before reclassification.
- **Two-pass approach is critical** — Pass 1 with strict keywords catches ~60% of classifiable items. Pass 2 with broader patterns catches another ~35%. Don't try to do everything in one pass.
- **Some items genuinely need user input** — "统一刷卡支付" (¥2,831 + ¥1,434), large no-note transactions (>¥500), and ambiguous merchants require user confirmation.
- **Keep "日常消费" as fallback** — Items that can't be classified should stay as "日常消费" rather than being force-assigned to wrong categories.
