# Alipay Category System (支付宝记账本分类)

Categories observed from Alipay 记账本 export (1,695 records, 2025-06 ~ 2026-06).

## Full category list

| 分类 | Annual Amount | % of Alipay Expense |
|---|---|---|
| 穿搭美容 | ¥22,542 | 22.7% |
| 人情社交 | ¥17,374 | 17.5% |
| 餐饮 | ¥15,572 | 15.6% |
| 生活日用 | ¥15,372 | 15.4% |
| 休闲玩乐 | ¥8,584 | 8.6% |
| 交通 | ¥7,410 | 7.4% |
| 转账 | ¥6,695 | 6.7% |
| 宠物 | ¥3,082 | 3.1% |
| 其他 | ¥866 | 0.9% |
| 运动 | ¥488 | 0.5% |
| 购物 | ¥468 | 0.5% |
| 医疗保健 | ¥371 | 0.4% |
| 金融保险 | ¥265 | 0.3% |
| 生活服务 | ¥201 | 0.2% |
| 学习 | ¥142 | 0.1% |
| 爱车 | ¥59 | 0.1% |
| 酒店旅行 | ¥28 | 0.0% |

## Notes

- Alipay's categories are **user-maintained** in the 记账本 (cashbook). They're reliable because the user manually assigned them.
- `投资理财` type transactions show as `不计收支` (neutral) — fund purchases, Yu'ebao earnings, etc.
- `退款` entries also appear as `不计收支` — not counted as income or expense.
- Account sources: 余额宝, 招商银行, 平安银行 (auto-synced via 账单同步).
- The 人情社交 category includes 亲情卡 (family card) payments to Kimy.

## Unified category mapping (Alipay ↔ WeChat)

| Unified Category | Alipay 分类 | WeChat 分类 (mapped) |
|---|---|---|
| 日常消费 | 生活日用 + 购物 | 日常消费 (商户消费/二维码) |
| 餐饮 | 餐饮 | (within 日常消费) |
| 穿搭美容 | 穿搭美容 | (within 日常消费) |
| 人情社交 | 人情社交 | 亲属卡 + 红包 + 群收款 |
| 转账 | 转账 | 转账 |
| 交通 | 交通 | (within 日常消费) |
| 休闲玩乐 | 休闲玩乐 | (within 日常消费) |
| 宠物 | 宠物 | (within 日常消费) |
| 投资理财 | (不计收支) | 零钱提现/信用卡还款 |

**Key issue**: WeChat's coarse "日常消费" lumps together what Alipay splits into 5+ categories. When merging, keep platform-specific breakdowns separate for accuracy.
