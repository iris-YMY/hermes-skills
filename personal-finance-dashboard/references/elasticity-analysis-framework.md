# Elasticity Analysis Framework

Three-tier classification for household expense flexibility analysis.

## Tier Mapping (user-confirmed 2026-07-03)

| Tier | Categories |
|------|-----------|
| 刚性 (Fixed) | 金融保险, 充值缴费, AI, 学习, 数码电器, 宠物, 医疗保健, 运动 |
| 半弹性 (Semi-flexible) | 家属消费, 餐饮, 生活日用, 交通, 转账 |
| 高弹性 (Highly flexible) | 穿搭美容, 休闲玩乐, 购物, 酒店旅行, 人情社交, 日常消费(未识别), 其他, 生活服务 |

## Python Mapping Dict

```python
elasticity_map = {
    # 刚性
    '金融保险': '刚性', '充值缴费': '刚性', 'AI': '刚性', '学习': '刚性',
    '数码电器': '刚性', '宠物': '刚性', '医疗保健': '刚性', '运动': '刚性',
    # 半弹性
    '家属消费': '半弹性', '餐饮': '半弹性', '生活日用': '半弹性',
    '交通': '半弹性', '转账': '半弹性',
    # 高弹性
    '穿搭美容': '高弹性', '休闲玩乐': '高弹性', '购物': '高弹性', '酒店旅行': '高弹性',
    '人情社交': '高弹性', '日常消费': '高弹性', '其他': '高弹性', '生活服务': '高弹性',
}
```

## Calculation Method

```
full_months = last 13 complete months (exclude current incomplete month)
baseline = median of monthly spending per category (non-zero months only)
recent_3m = sum over last 3 months of max(0, actual - baseline)
elasticity_ratio = 高弹性月度合计 / 总支出 × 100%
```

## Bitable Fields

### Detail Table (tbln6KDEsF2QXyKB)
- `支出弹性` (SingleSelect, fld51xwACE): 刚性/半弹性/高弹性

### Summary Table (tblHqZiC0ZoW1K7o)
- `刚性支出` (Number)
- `半弹性支出` (Number)
- `高弹性支出` (Number)
- `弹性系数` (Text): percentage string like "25.2%"

## Report Priority Rules

When generating cost-saving suggestions, rank by:
1. **Absolute excess amount** (highest ¥ first)
2. **Pattern type**: seasonal spike (one-off) vs chronic overspend (systemic)
3. **Controllability**: categories with most discretionary spending first

### Deep Analysis Triggers
For each category where `recent_3m_excess > ¥500`:
- List top 5 transactions
- Show 13-month trend bar
- Identify if spike is seasonal or chronic
- Suggest specific action with estimated savings

## Pattern Detection Rules (for cost-saving suggestions)

| Pattern | Condition | Suggestion Type |
|---------|-----------|----------------|
| 季节性飙升 | max_month > median × 3 AND months_above ≤ total_months × 0.3 | 大促前制定购物清单，设月度提醒上限 median × 1.5 |
| 持续超支 | months_above > total_months × 0.5 | 设定月度硬性上限 median |
| 单次大额 | top1_txn > median × 2 | 标记为一次性支出，排除基准线 |
| 频率增加 | (fallback) | 控制消费频率，目标不超过 median/月 |

## User-Confirmed Category Corrections (2026-07-03)
Apply these after every import when scanning for misclassified records:
```python
food_corrections = [("老凤祥", "穿搭美容"), ("怡心阁水疗", "休闲玩乐"), ("养芳集", "休闲玩乐")]
daily_corrections = [("白玉貔貅", "穿搭美容"), ("星月玉化药片", "休闲玩乐"), ("星月玉化大肠", "休闲玩乐"), ("文玩手串收纳盒", "休闲玩乐")]
sport_corrections = [("掼蛋", "休闲玩乐"), ("发牌机", "休闲玩乐")]
other_corrections = [("阿里云", "AI"), ("切果NOW", "餐饮"), ("热风", "穿搭美容"), ("百度网盘", "充值缴费"), ("出入境", "酒店旅行"), ("闲鱼", "生活服务")]
```
