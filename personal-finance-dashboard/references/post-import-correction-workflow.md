# Post-Import Correction Workflow (2026-07-01 Session)

## Context
During June 2026 import, user requested tiered expense review (>¥999, then >¥500). Multiple corrections needed:
- 杰尼亚 ¥8580: User confirmed refund → mark as 不计支出
- 家属消费 ¥680: User reclassified to 餐饮美食

## Correction Patterns

### Pattern 1: Refund Marking
User says: "8580已经退款了，要标记不计支出"

Action:
```python
resp = api_call('POST', batch_update_url, {'records': [{
    'record_id': target_id,
    'fields': {
        '收支类型': '不计收支',
        '是否退款': True
    }
}])
```

### Pattern 2: Category Reclassification
User says: "家属消费应该改成餐饮"

Action:
```python
resp = api_call('POST', batch_update_url, {'records': [{
    'record_id': target_id,
    'fields': {'分类': '餐饮美食'}
}])
```

### Pattern 3: Bulk Corrections
When multiple corrections needed, collect all record_ids first, then batch_update in one call (max 500 per batch).

## Critical: Post-Correction Cascade

After ANY correction to Bitable records:

1. **Re-sync spreadsheet** — rewrite entire month's row block
   - Reason: Row positions shift after deletions, can't do surgical updates
   - Method: Fetch corrected Bitable records, convert to sheet format, PUT to spreadsheet

2. **Re-run update_summary()** — refresh monthly summary table
   - Reason: Summary aggregates are now stale
   - Method: Call `update_summary(token)` which recalculates all months

3. **Re-query and report** — verify final numbers
   - Reason: User needs confirmed corrected totals
   - Method: Fetch all records, recalculate income/expense/neutral per platform

## Example Workflow (from 2026-07-01)

```
User: "8580已经退款了，要标记不计支出"
Agent: 
  1. Find record via (date, amount, platform, note)
  2. batch_update: 收支类型→不计支出, 是否退款→True
  3. Report: "✅ 已修正"

User: "家属消费改成餐饮"
Agent:
  1. Find record
  2. batch_update: 分类→餐饮美食
  3. Report: "✅ 已改好"

User: "dashboard里面所有表格都应该更新"
Agent:
  1. Re-sync spreadsheet (rewrite month block)
  2. Re-run update_summary()
  3. Report: "全部表格已同步完成"
```

## Key Insight
User expects the correction cascade to happen automatically. Don't just apply the correction and stop — always follow through with re-sync and re-calculate.