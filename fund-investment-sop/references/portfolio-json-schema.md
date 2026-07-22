# portfolio.json 结构与更新流程

## 路径

`/home/ubuntu/.hermes/profiles/finance-master/portfolio.json`

## 设计原则

- **volatile数据不存memory**：持仓明细、盈亏等频繁变化的内容存JSON文件
- memory只存稳定的用户偏好（风险偏好、年目标）
- Cron Job 读取 portfolio.json 获取最新持仓，不硬编码

## Schema

```json
{
  "meta": {
    "last_updated": "2026-06-29",
    "source": "蚂蚁财富平台截图",
    "total_assets": 61384.09,
    "total_gain": 1833.65,
    "note": "通信设备6/29减仓40%后数据"
  },
  "holdings": [
    {
      "code": "008586",
      "name": "华夏人工智能ETF联接C",
      "category": "指数型-AI",
      "amount": 11682.86,
      "cost": 11495.79,
      "gain": 187.07,
      "gain_pct": 1.63,
      "note": ""
    }
  ],
  "allocation": {
    "equity_index": ["008586", "007817", "015599", "013180"],
    "mixed": ["004814"],
    "commodity": ["000218"],
    "bond": ["002794", "110017"]
  },
  "monthly_plan": {
    "total": 2000,
    "loss_fund_cost_averaging": 500,
    "bond_accumulation": 600,
    "dip_buying_reserve": 500,
    "new_fund_position": 400
  }
}
```

## 更新触发条件

| 触发 | 操作 |
|------|------|
| 用户发持仓截图 | 识别截图 → 全量更新 holdings |
| 用户告知操作 | 局部更新对应基金（amount/cost/gain） |
| 每周五周报后 | 提醒用户发截图校准 |

## 更新字段计算

### 加仓后
```python
new_amount = old_amount + add_amount
new_cost = (old_cost * old_amount + add_amount) / new_amount  # 加权平均
```

### 减仓后
```python
recovered = old_amount * reduce_pct
new_amount = old_amount * (1 - reduce_pct)
new_gain = (current_nav / cost - 1) * new_amount  # 重算
```

## Cron Job 读取示例

```python
import json
with open('/home/ubuntu/.hermes/profiles/finance-master/portfolio.json') as f:
    portfolio = json.load(f)
for h in portfolio['holdings']:
    print(f"{h['code']} {h['name']}: ¥{h['amount']}")
```
