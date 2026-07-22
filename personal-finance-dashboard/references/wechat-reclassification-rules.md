# WeChat 日常消费 Reclassification Rules

WeChat lumps most merchant transactions into "日常消费". This multi-pass system reclassifies them into proper categories.

## When to Run

After any monthly WeChat import, before reporting. The rules apply ONLY to records where:
- `收支类型` = 支出
- `分类` = 日常消费
- `来源` does NOT contain "退款"

## Pass 1: High-Confidence Keywords

| Target | Keywords (case-insensitive match in 备注) | Extra Condition |
|--------|------------------------------------------|-----------------|
| 转账 | 收款方备注:二维码收款, 已转账 | amount >= ¥500 |
| 充值缴费 | 交费, 联通, 移动, 电信 | — |
| 酒店旅行 | 酒店, 签证, 列车, 旅游, 中銀訂單, MOP | — |
| 爱车 | 岚图, ADS, 汽车 | — |
| 穿搭美容 | lululemon, 直值, 肤丽泽, QualityFirst | — |
| 休闲玩乐 | 音乐, 演唱会, 盛世全集, 王力宏, 道观, 香篆 | — |
| 餐饮 | 大众点评, 团购, 烤肉, 烧肉, 牛排, 寿司, 寿喜, 龙虾, 食堂, MAKI, 济州, 席小鲜, 隐山酌, 眉州东坡, 大馥, 东发道, 茉莉奶白, 外卖, 西塔老太太, 爱牧牛, 郭子, 咖啡, 1788广场, HZ108, 冷饮, 小酒馆, 寿司郎 | — |
| 生活日用 | 联华, 奥乐齐, 超市, 先用后付 | — |

## Pass 2: Broader Pattern Matching

| Target | Keywords |
|--------|----------|
| 餐饮 | 堂食, 打包, POS, Coffee, 茶, 果汁, 果切, 水果, 酸奶, 麻辣烫, 馄饨, 拉面, 冰淇淋, Gelato, 爆肉, 饺子, 包子, 香香鸡, 糖葫芦, 串串, 火锅, 柠檬向右, LINLEE, 茉酸奶, BlueBottle, cococean, BOSS CAFE, 马记永, 陈香贵, 四海游龙, 金拱门, 麦当劳, 喜识, 严胜利, 食亭, trova, HUA TING, 三出山, 三立方, 零食小铺, Cappuccino, SBX-Tall, 宝尊项目点, CHAPANDA, 上海CP静安, 上海大宁店, 上海美罗城, 上海商城, 上海静安大融城, 上海大华第一坊, 上海合生汇, 上海兴业太古汇, 上海苏河湾, 上海真如环宇城, 上海长寿路, 上海世纪承乾, 上海Y丽园路, 淳安明珠, 乾元南街, 千岛龙郡, 明申商务, 市北数智, 新万荣门市, 湖州德清, 怡宝, 矿泉水, NEOMAS, VICUNAS, 上海明捷置业, 上海永华影城 |
| 交通 | 缴费离场, 缴费通, 先乘后付, 高速, 停车, 沪ABZ, 苏州奥体中心管理 |
| 医疗保健 | 挂号, 处方, 门诊, 姚梦寅, 4818FU |
| 充值缴费 | apple.com, 连续包年, 腾讯云, 84405140, ID1538527202 |
| 休闲玩乐 | 泡泡玛特, PSN-, 洛克公园, 场地预订 |
| 穿搭美容 | 冠靓芸, 服饰, 回力, COS会员, CHIC, 彩棠, TIMAGE, 遮瑕 |
| 生活日用 | 名创优品, 先购后付 |
| 酒店旅行 | 千岛湖, 阅树, 千岛庄园, CDFG MACAU, NY8 NEW YAOHAN |
| 生活服务 | 闪送, 海马体, 照相馆 |
| 购物 | 京东-订单, 小红书订单, 订单编号, 订单号 |

## Pass 3: Default Rules for Unidentifiable Patterns

| Pattern | Target | Rationale |
|---------|--------|-----------|
| 备注 starts with "商户单号XP" or starts with "4" + len > 10 | 餐饮 | 美团/大众点评 order IDs |
| 备注 contains "请在" + "前付款" | 餐饮 | 外卖 delivery |
| 备注 contains "收款方备注:二维码收款" (amount < ¥500) | 餐饮 | Small vendor QR payments |
| Everything else | Keep as 日常消费 | Truly unidentifiable |

## Post-Classification Corrections (User-Confirmed 2026-07-03)

These specific records were manually corrected. Watch for these patterns in future imports:

| Note Pattern | Wrong Category | Correct Category |
|-------------|---------------|-----------------|
| 老凤祥, 银楼, 珠宝, 金饰 | 餐饮 | 穿搭美容 |
| SPA, 水疗, 足浴, 按摩, 怡心阁, 养芳集 | 餐饮 | 休闲玩乐 |
| 白玉貔貅, 吊坠, 手串, 星月玉化 | 生活日用 | 休闲玩乐 (文玩) |
| 掼蛋, 发牌机, 扑克 | 运动 | 休闲玩乐 |
| 阿里云 | 其他 | AI |
| 切果NOW | 其他 | 餐饮 |
| 热风 | 其他 | 穿搭美容 |
| 百度网盘 | 其他 | 充值缴费 |
| 出入境 | 其他 | 酒店旅行 |
| 闲鱼 | 其他 | 生活服务 |

## Category Merge Map

After reclassification, merge these duplicate categories into canonical ones:

```python
merge_map = {
    '餐饮美食': '餐饮',
    '日用百货': '生活日用',
    '服饰装扮': '穿搭美容',
    '美容美发': '穿搭美容',
    '医疗健康': '医疗保健',
    '交通出行': '交通',
    '文化休闲': '休闲玩乐',
    '保险': '金融保险',
    '亲友代付': '转账',
}
```

These duplicates appear when Alipay's finer categories and WeChat's mapped categories produce slightly different names.

## Validation

After reclassification, check:
- 日常消费 should be < 10% of total expense (target: ~6%)
- If 日常消费 > ¥30K for a single month, investigate — likely a large unclassified transaction
- Total 退款 records caught should match source file refund count
