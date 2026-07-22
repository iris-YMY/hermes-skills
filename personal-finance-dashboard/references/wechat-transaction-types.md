# WeChat Transaction Type → Category Mapping

Observed `交易类型` values from a 2,526-record WeChat export (2025-06 ~ 2026-06).

## Primary types (non-refund)

| 交易类型 | → Category | Notes |
|---|---|---|
| 商户消费 | 日常消费 | Most common, includes online + offline |
| 二维码收款 | 日常消费 | QR code payments |
| 扫二维码付款 | 日常消费 | Scanning merchant QR |
| 亲属卡交易 | 人情社交 | Family card (Kimy) |
| 微信红包 | 人情社交 | 1-on-1 red packets |
| 微信红包（群红包） | 人情社交 | Group red packets |
| 企业微信红包 | 人情社交 | Corporate WeChat red packets |
| 转账 | 转账 | Direct transfers |
| 群收款 | 人情社交 | Group bill splitting |
| 信用卡还款 | 不计收支 | Financial operation, not spending |
| 零钱提现 | 不计收支 | Cash withdrawal from wallet |

## Refund types

Any `交易类型` ending in `-退款` is a refund. Observed variants:
- 商户消费 → `xxx店-退款` (various merchant names)
- 亲属卡交易-退款
- 微信红包-退款
- 企业微信红包-退款
- 转账-退款
- 闪送-退款

**Pattern**: If `交易类型` ends with `-退款`, classify as `退款` regardless of prefix.

## Mapping logic (pseudocode)

```python
trans_type = str(row['交易类型'])
if trans_type.endswith('-退款'):
    category = '退款'
elif '商户消费' in trans_type or '二维码' in trans_type:
    category = '日常消费'
elif '亲属卡' in trans_type:
    category = '人情社交'
elif '红包' in trans_type:
    category = '人情社交'
elif '转账' in trans_type:
    category = '转账'
elif '零钱' in trans_type or '提现' in trans_type or '信用卡还款' in trans_type:
    category = '不计收支'
elif '群收款' in trans_type:
    category = '人情社交'
else:
    category = '其他'
```

## Account sources observed

- 招商银行信用卡(7100)
- 平安银行储蓄卡(4284)
- 零钱 (wallet balance)
- 零钱通 (savings wallet)
