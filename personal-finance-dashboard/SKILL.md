---
name: personal-finance-dashboard
description: Merge Alipay + WeChat + Tencent Docs financial exports into unified data source and generate interactive HTML dashboard with charts.
tags: [finance, data-merging, dashboard, alipay, wechat, csv, excel]
triggers:
  - 整理财务
  - 账单合并
  - 财务看板
  - 支付宝账单
  - 微信账单
  - 记账汇总
  - 年度收支
---

# Personal Finance Dashboard

Merge financial exports from Alipay (支付宝) and WeChat (微信) into a unified dataset, then generate an interactive dark-themed HTML dashboard with Chart.js visualizations.

## Supported Data Sources

### 1. Alipay CSV (支付宝记账本导出)

**File format**: CSV, **GBK encoding** (NOT UTF-8)

**Old format (≤2024)**: First 10 rows disclaimers. Header at row 10. Data from row 11.
**Columns**: `记录时间, 分类, 收支类型, 金额, 备注, 账户, 来源, 标签, (empty)`

**New format (2025+)**: Metadata rows vary. Header detected by finding row with `交易时间`. Data starts next row.
**Columns (13)**: `交易时间, 交易分类, 交易对方, 对方账号, 商品说明, 收/支, 金额, 收/付款方式, 交易状态, 交易订单号, 商家订单号, 备注, (empty)`

Auto-detection: Script checks column count ≥12 and presence of `交易对方` to distinguish formats.

Key fields (new format mapping):
- `交易分类` → 分类
- `收/支` → 收支类型 (`支出` / `收入` / `不计收支`)
- `金额` (col 6) → 金额
- `商品说明` → 备注
- `收/付款方式` → 账户
- `交易对方` → 来源

### 2. WeChat Excel (微信支付账单导出)

**File format**: .xlsx, single sheet
**Header**: Rows 1-17 are metadata (nickname, date range, summary stats, notes). Row 17 is the column header row. Data starts row 18 (0-indexed).
**Columns**: `交易时间, 交易类型, 交易对方, 商品, 收/支, 金额(元), 支付方式, 当前状态, 交易单号, 商户单号, 备注`

Key quirks:
- `金额(元)` has `¥` prefix — must strip before float conversion
- `收/支` values: `支出`, `收入`, `/` (neutral)
- `交易类型` is verbose: `商户消费`, `亲属卡交易`, `微信红包`, `转账`, `扫二维码付款`, plus many `-退款` suffixed variants
- Coarse categories — most merchant transactions lumped into "日常消费"
- **Refund detection**: Check `当前状态` for `已全额退款` or `交易类型` ending in `-退款`

### 3. Tencent Docs (腾讯文档记账) — placeholder

User exports this separately. Format TBD — add parsing logic when received.

## Workflow

1. **Ingest**: Read each file with correct encoding and header offset (use pure Python — no pandas)
2. **Normalize**: Map to unified schema:
   ```
   { date, category, type (收入/支出/不计收支), amount, note, account, source, platform (alipay/wechat) }
   ```
3. **WeChat categorization**: Map `交易类型` to categories:
   - `商户消费` / `二维码` → 日常消费
   - `亲属卡` → 人情社交
   - `红包` → 人情社交
   - `转账` → 转账
   - `退款` suffix → 退款
   - `零钱` / `提现` → 投资理财
4. **Combine & aggregate**: Monthly totals, category breakdown, platform comparison
5. **Split into batches**: Header + 499 rows per batch file (batch_0.json ... batch_N.json), max 500 rows each
6. **Create Feishu Spreadsheet**: Use user OAuth token → places in user's My Folder
7. **Batch write data**: 500 rows/batch via PUT, write payload to temp file to avoid shell escaping
8. **Build & send interactive card**: Via tenant token (bot identity), with Unicode charts and button linking to spreadsheet
9. **Confirm with user**: Share spreadsheet link, highlight data quality issues (refunds, coarse categories)

## Feishu Delivery Workflow (PRIMARY — use this, not HTML)

When the user is in a Feishu chat context, **HTML dashboards are invisible**. Always deliver via Feishu-native content:

### Step A: Create Feishu Spreadsheet (Data Source)
```bash
# Create spreadsheet in user's My Folder (requires user OAuth token with drive:drive scope)
curl -s -X POST "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"艾酱年度财务数据源_YYYY-YYYY（合并版）"}'
```

### Step B: Batch Write Data (500 rows per batch)
1. Query `sheet_id` via `GET /sheets/v3/spreadsheets/{token}/sheets/query`
2. Split data into batches of 500 rows (first batch includes header row)
3. Write each batch with PUT to `/sheets/v2/spreadsheets/{token}/values`
4. Range format: `{sheet_id}!A{start_row}:H{end_row}`
5. **Write payload to temp file** (`/tmp/batch_payload_N.json`) then use `-d @file` to avoid shell escaping issues with Chinese characters
6. Add `time.sleep(0.5)` between batches to avoid rate limiting

### Step C: Send Interactive Card (Dashboard)
Use Feishu interactive card (msg_type: `interactive`) with:
- **column_set** for side-by-side comparisons (platform, income/expense)
- **lark_md** for rich text with bold, headers (## for sections)
- **Unicode bar charts** (████░░░░) for monthly trends and category breakdowns
- **button** action linking to the spreadsheet
- **note** element for metadata footer
- **hr** dividers between sections

Card structure:
```
Header: 💰 title (template: blue)
Elements:
  - 数据范围 + 数据来源 summary
  - 年度财务总览 (4 cards via 2x column_set)
  - 平台对比 (column_set: Alipay vs WeChat)
  - 月度支出趋势 (Unicode bars: YYYY-MM ¥amount ████░░░░)
  - 消费分类 Top 8 (Unicode bars with percentages)
  - 年度大额支出 Top 5 (numbered list with refund tags)
  - 数据洞察 (bullet points)
  - note: metadata footer
  - action: button linking to spreadsheet
```

### Step D: Send Card via Tenant Token
⚠️ **User OAuth token lacks `im:message.send_as_user` scope** — cannot send messages.
Must use **tenant_access_token** (bot identity) for `POST /im/v1/messages`:
```bash
TENANT_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$APP_ID\",\"app_secret\":\"$LARK_APP_SECRET\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/card_payload.json
```

### Step E: Create Bitable BI Dashboard (PREFERRED — user explicitly wants this)

When user asks for "BI看板" or "数据看板", create a **Feishu Bitable** (多维表格), NOT just a spreadsheet or card.

```bash
# 1. Create Bitable app (requires bitable:app scope, NOT just bitable:app:readonly)
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"艾酱年度财务BI看板_YYYY-YYYY","folder_token":""}'
# Returns: app_token + default_table_id

# 2. Create fields ONE BY ONE (batch_create endpoint returns 404)
# Types: 1=Text, 2=Number, 3=SingleSelect, 5=DateTime, 20=Formula
# For DateTime: use millisecond timestamps (int(dt.timestamp() * 1000))
# For SingleSelect: include "property":{"options":[{"name":"X","color":N}]}

# 3. Batch insert records: POST /bitable/v1/apps/{token}/tables/{table}/records/batch_create
# ⚠️ Payload MUST be wrapped: {"records": [{"fields": {...}}, ...]}
# Without the wrapper → code 9499 "Bad Request"
# Max 500 records per batch, write to temp file, use -d @file

# 4. Add formula field for month grouping:
curl -s -X POST ".../fields" -d '{
  "field_name": "月份", "type": 20,
  "property": {"formula_expression": "DATETIME_FORMAT(CurrentValue.[交易时间], \"yyyy-MM\")"}
}'

# 5. Create additional table for monthly summary:
# POST /bitable/v1/apps/{token}/tables with "table":{"name":"月度汇总","fields":[...]}'

# 6. Create filtered grid views for dashboard data sources:
# POST /bitable/v1/apps/{token}/tables/{table}/views
# Supported view_type: grid, kanban, gallery, gantt, form
# ⚠️ "chart" is NOT a supported view_type via API — returns 99992402

# 7. Dashboard charts CANNOT be created via API
# Must provide user with a manual config guide (send as interactive card)
# Guide should specify: chart type, data table, X/Y axis, filters, colors
```

**Recommended dashboard charts** (user creates manually in Bitable dashboard tab):
1. KPI指标卡 ×3 (总收入/总支出/净额) — filter by 收支类型
2. 折线图 — 月度收支趋势 (X=月份, Y=金额, 颜色=收支类型)
3. 饼图 — 消费分类分布 (筛选支出)
4. 堆叠柱状图 — 平台月度对比 (X=月份, Y=金额, 颜色=平台)
5. 环形图 — 支付宝分类细分
6. 横向柱状图 — 月度支出排行Top 10
+ 4 filters: 平台, 月份, 收支类型, 分类

### HTML Dashboard (SECONDARY — only if explicitly requested)
Generate single HTML file with embedded Chart.js (CDN), dark theme (#0f172a base). Send as file attachment only if user asks for it. Do NOT assume user can view HTML.

## Dashboard Components (Feishu Card)

- 4 summary cards: 总收入 / 总支出 / 净额 / 不计收支
- Monthly trend (Unicode bar chart, one bar per month)
- Category breakdown Top 8 (Unicode bars with percentages)
- Platform comparison (column_set: Alipay vs WeChat with top-3 categories each)
- Monthly detail table (in spreadsheet, not card — card is for overview only)
- Top 5 expenses (numbered list with ⚠️退款 tags)
- Data insights (bullet points)
- Button linking to full spreadsheet

## Pitfalls

- **GBK encoding**: Alipay CSV is GBK, not UTF-8. Using default encoding will garble Chinese text.
- **Header offsets**: Both files have multi-row metadata before actual data. Hard-coding `skiprows` or `min_row` is fragile — detect by finding the header row.
- **Refund inflation**: WeChat shows both payment and refund as separate rows. Large purchases with "已全额退款" status inflate total expense. Always flag refund transactions and offer to recalculate excluding them.
- **No pandas**: This server uses externally-managed Python — `pip install` fails or times out. Use pure Python (`csv` + `openpyxl`) as standard approach. Do NOT attempt `pip install pandas`.
- **Heredoc timeout**: Large Python scripts via heredoc can timeout on this server. Keep scripts focused, split data prep from API calls, or use `write_file` + execute.
- **WeChat category coarseness**: WeChat lumps most spending into "日常消费". Note this limitation to user — Alipay's categories are much more granular and reliable.
- **理财 transactions**: Both platforms mark investment purchases/redemptions as neutral (不计收支). Keep them separate from income/expense analysis.
- **HTML invisible in Feishu**: User cannot view HTML dashboards in Feishu chat. Always deliver as Feishu native content (spreadsheet + interactive card). Only generate HTML if explicitly requested for local browser use.
- **Feishu Sheets batch size**: Max 500 rows per API call. Write payload to temp file to avoid shell escaping with Chinese text.
- **Message sending token**: User OAuth token cannot send messages (`im:message.send_as_user` not granted). Use tenant_access_token (bot identity) for `POST /im/v1/messages`.
- **Bitable batch_create requires wrapper**: Payload must be `{"records": [...]}`. Sending a bare array returns `9499 Bad Request`.
- **Bitable field creation is sequential**: The `fields/batch_create` endpoint returns 404. Must create fields one at a time via `POST /fields`.
- **Bitable date fields use millisecond timestamps**: `int(dt.timestamp() * 1000)`, not seconds.
- **Bitable formula fields for date grouping**: `DATETIME_FORMAT(CurrentValue.[交易时间], "yyyy-MM")` creates a month-extraction formula field (type 20).
- **Bitable cannot create dashboard charts via API**: View types supported: grid, kanban, gallery, gantt, form. No "chart" or "dashboard" type. Must send manual config guide to user.
- **Bitable requires `bitable:app` scope**: Default lark-cli only has `bitable:app:readonly`. Must add `bitable:app` to scopes.go and re-authorize.
- **Default table has dummy fields**: New Bitable creates a default table with fields (文本, 单选, 日期, 附件). Must delete them and add proper fields.
- **HOME env in Hermes**: `~` resolves to profile home (e.g. `~/.hermes/profiles/hr-assistant/home/`), not system home. Token paths should use `~/.lark/tokens.json` (relative to HOME).
- **Alipay new format (2025+)**: 13 columns instead of 9. Script auto-detects by checking for `交易对方` column. Column indices shift: 金额 is col[6], 收支类型 is col[5].
- **Dedup via /records**: The `/fields/{field_id}` endpoint does NOT support paginated value listing (returns 404). Must use `/records` endpoint and extract timestamps from record fields.
- **tmp variable scope**: In `api_call()`, always initialize `tmp = None` before the `if payload:` block to avoid `UnboundLocalError` on GET requests.
- **Amount type from API**: Bitable may return amounts as strings. Always `float()` cast before arithmetic in aggregation functions.
- **Formula fields return list of dicts**: Formula fields (e.g. 月份, 年份) return as `[{"text": "2026-06", "type": "text"}]`, not plain strings. Extract with: `val[0].get('text', '') if isinstance(val, list) else str(val)`. Same pattern applies to SingleSelect fields in some API responses.
- **Category overlap (2026-06+)**: Data quality script produces subcategories that overlap with old coarse categories. Apply merge_map after import: 服饰装扮→穿搭美容, 餐饮美食→餐饮, 日用百货→生活日用, 交通出行→交通, 文化休闲→休闲玩乐, 医疗健康→医疗保健, 美容美发→穿搭美容, 保险→金融保险, 亲友代付→转账. The "日常消费" catch-all (was 41%, now ~6.4% after reclassification) is decomposed via 3-round keyword matching — see `references/daily-expense-reclassification.md`.
- **Spreadsheet_creation token**: Use **user OAuth token** for creating spreadsheets (places in user's My Folder). Tenant token creates in App Shared Space (user can't find it).
- **WeChat partial refunds misclassified as expense**: Records with `当前状态` = `已退款(¥X)` or `已全额退款` are still marked `支出` in the source file. The refund comes in as a separate `收入` row with `-退款` suffix in `交易类型`. data_quality.py must detect these by checking `来源` field (which stores `当前状态`) for patterns `已退款` and `已全额退款`, then reclassify the original payment from `支出` to `不计收支`.
- **Alipay metadata shows NET expense, data rows show GROSS**: Header summary (e.g., "支出：140笔 13255.84元") is after deducting refund amounts. But data rows still show the original purchase as `支出` and the refund as a separate `不计收支` row with `分类=退款`. So summing `支出` rows from data gives GROSS, which is always higher than the metadata number. The difference equals the refund total. Always explain this to user when they question the numbers.
- **Cross-import date overlap**: Monthly export files frequently include 1-5 records from adjacent months (especially when exported on the boundary day). Dedup must filter Bitable records to target month before comparing against source file keys, otherwise boundary records from prior imports appear as "extras".
- **Refunds escaping automated detection**: Some refunded transactions have NO corresponding refund row in the source file (e.g., offline refund, refund processed after export date). These remain as `支出` and are invisible to data_quality.py. User review of large expenses (>¥999) catches these — always present the list proactively.
- **Spreadsheet re-sync after Bitable corrections**: When records are modified or deleted post-import, the spreadsheet must be rewritten for that month's entire row block. Row positions shift after deletions — cannot update individual rows. Rewrite from known start row.
- **Source-file internal dedup key must use (timestamp, amount), not (timestamp, amount, note)**: Multiple legitimate transactions can share the same timestamp (e.g., batch purchases on 618). The `note` field is needed to distinguish them, but for dedup purposes `(timestamp, amount)` with a Counter is more robust — it correctly handles N records with the same ts+amt.

## References
- `references/alipay-categories.md` — Full list of Alipay spending categories and their meanings
- `references/wechat-transaction-types.md` — WeChat transaction type → category mapping table
- `references/wechat-reclassification-rules.md` — Multi-pass rules to reclassify 日常消费 catch-all + category merge map + user-confirmed corrections
- `references/elasticity-analysis-framework.md` — Three-tier elasticity classification (user-confirmed mapping), calculation method, Bitable schema, report structure
- `references/feishu-sheets-batch-write.md` — Python pattern for batch writing to Feishu Sheets (500 rows/batch)
- `references/feishu-card-template.md` — Interactive card template for finance dashboard (column_set, Unicode bars, button)
- `references/post-import-correction-workflow.md` — Correction patterns and mandatory cascade (refund marking, category changes, re-sync)
- `references/daily-expense-reclassification.md` — Multi-pass keyword rules for reclassifying WeChat "日常消费" catch-all category

## Verification

- Total record count should match file metadata (WeChat header shows exact counts)
- Income + expense + neutral amounts should reconcile with file headers
- Monthly totals should sum to annual totals
- Spot-check top-10 expenses against raw data

---

## Monthly Import SOP

### Trigger
User provides monthly Alipay CSV + WeChat Excel export files for incremental Bitable update.

### Core Resources
- **飞书多维表格**: `TcxxbfP05adgltsZpJEcGKi9nme`
- **交易明细表**: `tbln6KDEsF2QXyKB`
- **月度汇总表**: `tblHqZiC0ZoW1K7o`
- **飞书电子表格**: `V9s7sWj8JhFpRwtIon0cm79Anoc` (sheet `28d56d`)

### Field Mapping (Transaction Detail Table)
| Field | Type | Alipay (new format 2025+) | Alipay (old ≤2024) | WeChat Source |
|-------|------|---------------------------|---------------------|---------------|
| 交易时间 | DateTime(5) | row[0] → ts*1000 | row[0] → ts*1000 | row[0].timestamp()*1000 |
| 分类 | Text(1) | row[1] 交易分类 | row[1] 分类 | Mapped from 交易类型 |
| 收支类型 | SingleSelect(3) | row[5] 收/支 | row[2] 收支类型 | row[4] 收/支 mapped |
| 金额 | Number(2) | float(row[6]) | float(row[3]) | Strip ¥ then float(row[5]) |
| 备注 | Text(1) | row[4] 商品说明 | row[4] | row[3] 商品 |
| 账户 | Text(1) | row[7] 收/付款方式 | row[5] | row[6] 支付方式 |
| 来源 | Text(1) | row[2] 交易对方 | row[6] | row[7] 当前状态 |
| 平台 | SingleSelect(3) | "支付宝" | "支付宝" | "微信" |
| 支出弹性 | SingleSelect(3) | — | — | Auto-tagged post-import (刚性/半弹性/高弹性) |

### WeChat Category Mapping
```
商户消费/二维码 → 日常消费
亲属卡 → 人情社交
红包/企业微信红包 → 人情社交
转账 → 转账
退款 → 退款
零钱/提现 → 投资理财
其他 → 其他
```

### Workflow Phases
1. **Data Receive**: Confirm files (Alipay CSV GBK + WeChat Excel), confirm time range and metadata record counts
2. **Incremental Write**: Run `scripts/update_bitable.py` — dedup by (time+amount+platform) against Bitable, batch_create 500/batch
3. **Sync Spreadsheet**: PUT values to electronic spreadsheet (append mode)
4. **Data Quality**: Run `scripts/data_quality.py --mode all --wechat_source <file>` (refund marking, category refinement, family card alignment)
5. **Post-Import Verification** (CRITICAL — do NOT skip):
   - Build source-file key set: `Counter((ts, amt))` per platform from raw files
   - Fetch Bitable records for target month, build bitable key set
   - Delete extras where `bitable_count > source_count` (cross-import duplicates from prior month overlap)
   - Fix WeChat refund records: change `支出` → `不计收支` for records with partial/full refund status in `来源` field
   - Compare final totals: Bitable expense sum vs source-file expense sum per platform
   - Report any remaining discrepancy to user
6. **User Review** (proactively present, don't wait):
   - Run `scripts/post_import_qa.py --month YYYY-MM --threshold 999` — list large expenses
   - Present as numbered table; then offer >¥500 tier
   - Apply user corrections (refund marking, category changes) via batch_update
### Step 8: Update Summary
Refresh monthly summary table — **only monthly rows, NO 年度合计/月均 rows**
10. **Notify**: Send summary card with verified final numbers

### Dedup Strategy (Source-File Cross-Reference — CRITICAL)
Simple Bitable-internal dedup (comparing new records against existing) is **insufficient** — previous month's import may have already included some records from the overlap period (e.g., June file exported on July 1 may contain July 1 records that were also in May's file).

**Correct approach:**
1. Build key set from SOURCE FILE: `Counter((timestamp_ms, amount))` per platform
2. After import, fetch ALL Bitable records for the target month
3. Build key set from BITABLE: `Counter((timestamp_ms, amount))` per platform, filtered to target month
4. For each key: `extras = bitable_count - source_count`. If extras > 0, delete `extras` records (keep first `source_count`)
5. For each key in Bitable but NOT in source at all: investigate (likely from prior import overlap)

**Key format**: `(int(timestamp_ms), float(amount))` — must match across platforms separately
**Cross-month boundary**: Files often include 1-2 records from adjacent months. Filter Bitable records to target month only before comparing.

### Data Quality Optimization (Post-Import)
Script: `scripts/data_quality.py`
- **Step 1 — Refund marking**: Flag transactions with refund keywords in source/category/note (Checkbox field)
- **Step 2 — WeChat category refinement**: Split "日常消费" by keyword matching (餐饮/交通/穿搭/生活/运动/休闲/宠物/医疗/爱车)
- **Step 3 — Family card alignment**: Unify 亲属卡/亲情卡 → "家属消费" across both platforms (timestamp matching for WeChat)

### Monthly Update Checklist
- [ ] Confirm Alipay/WeChat file time ranges and record counts from metadata
- [ ] Verify OAuth token valid
- [ ] Run update_bitable.py incremental write (Bitable + Spreadsheet sync)
- [ ] Run data_quality.py --mode all --wechat_source new file
- [ ] **Post-import cross-reference verification**: Compare Bitable vs source file per platform, delete extras, fix WeChat refunds
- [ ] **Scan for missed refunds**: Query all 日常消费 records, check 来源 for "退款" keywords, reclassify to 不计收支
- [ ] **Reclassify 日常消费**: Run multi-pass reclassification rules (see `references/wechat-reclassification-rules.md`), then apply merge_map for duplicate categories
- [ ] **Update elasticity tags**: For any new categories from reclassification, assign elasticity tier per `references/elasticity-analysis-framework.md` (ask user for new categories)
- [ ] **User review**: Present large expenses (>¥999, then >¥500) for user confirmation; apply corrections
- [ ] **Re-sync spreadsheet**: Rewrite month's row block after all corrections
- [ ] **Recalculate monthly summary**: Aggregate all Bitable records by month+tier, batch_update summary table (including 刚性/半弹性/高弹性/弹性系数 fields)
- [ ] Run post-import classification (余额宝/AI/基金)
- [ ] Update monthly summary table (only monthly rows, NO 年度合计/月均)
- [ ] Send notification card with verified final numbers
- [ ] Verify record count + reasonable category distribution

### Token Expiry Monitoring
Script: `scripts/check_token_expiry.py`
- Daily check at 9AM, alerts when refresh_token < 3 days remaining
- Cron job ID: `8a3bb5b61fb0`

### Post-Import Classification Rules (Based on 备注 Field)

Apply **after** data import, before dashboard review. Match in priority order — first rule wins.

**Priority 1 → 余额宝收益**
- `余额宝-收益发放`

**Priority 2 → AI**
- 备注含 AI 相关投资产品关键词：`AI.*节省计划`, `AI.*基金`, `AI.*ETF`, `人工智能.*ETF`, `算力.*ETF`, `芯片.*ETF`, `半导体.*ETF`, `机器人.*ETF`
- 不含纯消费类智能设备（如智能饮水机、智能大白车等归入日常消费）

**Priority 3 → 基金/股票类**
- `蚂蚁财富-.*买入` / `蚂蚁财富-.*卖出` / `蚂蚁财富-.*赎回`
- `余额宝-自动转入`, `转账收款到余额宝`
- `.*ETF.*` (包括通信设备ETF — 虽是AI基建但归入基金)
- 基金公司名 + `买入/卖出/定投` (易方达/天弘/中欧/国泰/永赢/招商国证等)
- `.*股票.*`, `.*证券.*买入/卖出`

**Excluded from fund/stock (keep original category):**
- 含"混合猫砂"等商品名中的"混合" — 这是商品不是基金
- 退款类（已有退款分类处理流程）

**Batch Update API:**
```bash
# Build payload: {"records": [{"record_id": "recXXX", "fields": {"分类": "基金/股票类"}}, ...]}
# Max 500 per batch, write to temp file, POST to batch_update endpoint
curl -s -X POST ".../records/batch_update" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch_update_payload.json
```

### Post-Import User Review (MANDATORY — user always requests this)

After automated import + quality checks, **proactively** offer large-expense review without waiting for user to ask:

1. Run `scripts/post_import_qa.py --month YYYY-MM --threshold 999` — list all expenses above threshold
2. Present as numbered table with: date, amount, platform, category, note
3. Flag any items with `是否退款` already set
4. User typically reviews in descending tiers: >¥999, then >¥500, sometimes >¥200
5. For each correction user requests:
   - **Refund marking**: Update `收支类型→不计收支` + `是否退款→True`
   - **Category change**: Update `分类` field
   - Apply immediately via `batch_update` API
6. **After ALL corrections**: Re-sync spreadsheet (rewrite entire month's block from Bitable) + re-run `update_summary()`
7. Re-query and report final corrected totals

### Spreadsheet Re-Sync After Corrections

When Bitable records are corrected post-import (deletions, type changes, category changes), the spreadsheet becomes stale. **Must rewrite the month's data block:**

1. Fetch all Bitable records for the target month, sort by date
2. Convert to sheet format: `[time_str, category, direction, amount, note, account, source, platform]`
3. Overwrite starting from the known start row (first row after previous month's data)
4. Clear any extra rows beyond the new data count
5. This is the same logic as initial sync but targets a specific row range

⚠️ Do NOT try to update individual spreadsheet rows — row positions shift after Bitable deletions. Always rewrite the full month block.

### Key Lessons
- **Data sync completeness**: Must sync ALL targets (Bitable + Spreadsheet) — never skip one
- **Category mapping priority**: Rules match first-hit in order: refund → family → keyword → default
- **Classification priority**: 余额宝收益 → AI → 基金/股票类 → keep original
- **通信设备ETF**: AI infrastructure fund but classified as 基金/股票类 (not AI)
- **Batch operations**: 500/batch, 0.5s pause between, single-batch failure doesn't affect others
- **Source-file cross-reference is mandatory**: Never trust Bitable-internal dedup alone. Always compare Bitable records against raw source file to catch cross-import duplicates.
- **WeChat refund reclassification**: After import, scan for WeChat records with `来源` containing `已退款`/`已全额退款` that still have `收支类型=支出`. These must be changed to `不计收支`. The refund income rows (with `-退款` in `交易类型`) are already classified correctly as `收入`.
- **Alipay gross ≠ metadata net**: Always use data-row sums for Bitable, and explain to user that metadata summary shows net-after-refunds while data rows show gross. The delta = refund total in `不计收支`.
- **Report verified numbers to user**: After all fixes, re-query Bitable and report actual totals per platform per direction. Never report pre-fix numbers.
- **Monthly summary table — no aggregates**: Only write individual monthly rows (2025-01, 2025-02, ...). Never write 年度合计 or 月均 rows. User finds them redundant.
- **Large expense review is proactive**: Always present >¥999 tier first, then offer >¥500 tier. Don't wait for user to ask. Some refunds escape automated detection (offline refunds, post-export refunds) — user review catches these.
- **Post-correction cascade is mandatory**: After ANY user-requested correction (refund marking, category change), automatically re-sync spreadsheet + re-run summary + re-report totals. Don't wait for user to say "update the dashboard" — this is an implicit requirement of every correction. See `references/post-import-correction-workflow.md` for the full cascade pattern.
- **Post-correction spreadsheet rewrite**: After ANY Bitable correction (delete/update), rewrite the entire month's row block in spreadsheet. Don't try surgical row updates — positions shift.
- **Reclassification before reporting**: ALWAYS run WeChat 日常消费 reclassification BEFORE any expense analysis or elasticity report. The catch-all category distorts all downstream calculations.
- **Elasticity report = mandatory post-reclassification step**: After reclassification + merge, recalculate all elasticity tags (batch_update), then recalculate monthly summary (刚性/半弹性/高弹性/弹性系数 fields), then sync spreadsheet.
- **Bitable field IDs for elasticity**: `支出弹性` field_id = `fld51xwACE` on detail table. Summary table fields: `刚性支出`/`半弹性支出`/`高弹性支出` (Number type 2), `弹性系数` (Text type 1).
- **curl -o pattern for large responses**: Always write Bitable API responses to temp files (`curl -o /tmp/file.json`) then read with Python. Direct pipe output gets truncated at ~20KB causing JSON parse errors.
- **Monthly summary table — no aggregates**: Only write individual monthly rows (2025-01, 2025-02, ...). Never write 年度合计 or 月均 rows. User finds them redundant.
- **Large expense review is proactive**: Always present >¥999 tier first, then offer >¥500 tier. Don't wait for user to ask. Some refunds escape automated detection (offline refunds, post-export refunds) — user review catches these.
- **Post-correction cascade is mandatory**: After ANY user-requested correction (refund marking, category change), automatically re-sync spreadsheet + re-run summary + re-report totals. Don't wait for user to say "update the dashboard" — this is an implicit requirement of every correction. See `references/post-import-correction-workflow.md` for the full cascade pattern.
- **Post-correction spreadsheet rewrite**: After ANY Bitable correction (delete/update), rewrite the entire month's row block in spreadsheet. Don't try surgical row updates — positions shift.
- **WeChat 日常消费 catch-all**: WeChat classifies ~90% of transactions as 日常消费. MUST run multi-pass reclassification (see `references/wechat-reclassification-rules.md`) after every import. Without reclassification, the category breakdown is useless. Target: 日常消费 < 10% of total expense.
- **Category duplicates from dual-platform imports**: Alipay and WeChat produce overlapping category names (餐饮美食 vs 餐饮, 日用百货 vs 生活日用, etc.). MUST apply merge_map after reclassification. See `references/wechat-reclassification-rules.md` for the canonical merge map.
- **Refund records inflating expense totals**: WeChat refunds with 来源="已全额退款" remain as 支出 unless explicitly caught. The automated data_quality.py sometimes misses partial refunds. After every import, scan ALL 日常消费 records for "退款" in 来源 field and reclassify to 不计收支.
- **Bitable field type mismatch on re-fetch**: Formula fields (月份, 年份) return as `[{"text": "2026-06", "type": "text"}]` not plain strings. SingleSelect fields may return as strings or lists. Always handle both types when reading records back.
- **curl output truncation with large JSON**: When fetching 500+ records, terminal output gets truncated and json.loads fails. Always `curl -o /tmp/file.json` then read the file, never pipe curl output directly.
- **Elasticity tier mapping is user-defined**: Do NOT infer or change tier assignments without explicit user confirmation. See `references/elasticity-analysis-framework.md` for the confirmed mapping. If a new category appears, ask user before assigning a tier.
- **月度汇总表 update after reclassification**: After ANY category change or elasticity reassignment, recalculate monthly totals from scratch (iterate all Bitable records, aggregate by month+tier) and batch_update the summary table. Don't try incremental updates.
- **充值缴费 "移动支付" mystery records**: 7 WeChat records from Alipay have 备注="移动支付" with no merchant info. Keep as 充值缴费 but flag to user in reports.
- **Re-fetch after batch_update may miss new fields**: If you create a new field (e.g. 支出弹性) and then batch_update records to populate it, a subsequent re-fetch of ALL records may not include the new field in older records' responses. For aggregation that depends on the new field, recompute from known category mappings instead of relying on the re-fetched data.
- **Refund count underestimation**: Scanning a sample (e.g., first 100 records) undercounts refunds. Always scan ALL records — the actual refund count can be 2x the sample estimate (observed: 43 in sample → 77 in full scan).
- **Multi-round classification required for 日常消费**: Single-pass keyword matching misses ~60% of reclassifiable records. Must use 3-round strategy: Round 1 (high-confidence brand/store names) → Round 2 (broader generic terms like 堂食/打包/POS) → Round 3 (pattern fallbacks like 商户单号XP→餐饮, 二维码收款<¥500→餐饮). After 3 rounds, ~6% of 日常消费 remains unidentifiable (no merchant info at all).

---

## Elastic Expense Analysis Framework (弹性支出分析)

Three-tier classification for expense flexibility and budget optimization.
Full methodology: `references/elasticity-framework.md`
Reclassification rules: `references/daily-expense-reclassification.md`

### Tier Mapping (updated 2026-07-03, user-confirmed)

| Tier | Chinese | Categories |
|------|---------|------------|
| 刚性 | Fixed | 金融保险, 充值缴费, AI, 学习, 数码电器, 宠物, 医疗保健, 运动 |
| 半弹性 | Semi-flexible | 家属消费, 餐饮, 生活日用, 交通, 转账 |
| 高弹性 | Highly flexible | 穿搭美容, 休闲玩乐, 购物, 酒店旅行, 人情社交, 日常消费(未识别), 其他, 生活服务 |

### Bitable Implementation
- `支出弹性` SingleSelect field (fld51xwACE) on transaction detail table — auto-tagged for all 3,635 expense records
- Monthly summary table has 4 new fields: `刚性支出`, `半弹性支出`, `高弹性支出`, `弹性系数`
- After each import: tag new expense records with elasticity tier based on category, then update summary table

### Calculation (applied per monthly analysis)
```
baseline = median of monthly spending per category (non-zero months, 13-month window)
recent_excess = sum over last 3 months of max(0, actual - baseline)
elasticity_ratio = 高弹性支出 / 总支出 × 100%
throttle_priority = sort categories by recent_excess descending
```

### User Preferences (confirmed 2026-07-03)
- **家属消费 = 半弹性** (mostly food + gaming for family member Kimy/李昊龙)
- Large WeChat transfers (≥¥1K) within 家属消费 may be reclassified as fixed if user confirms monthly allowances
- **日常消费 must be reclassified first** before elastic analysis (see `references/daily-expense-reclassification.md`)
- **宠物/医疗保健/运动 = 刚性** (moved from 半弹性/高弹性 per user request)

### User-Confirmed Category Corrections (2026-07-03)
Apply these after every import when scanning for misclassified records.
Full correction rules: `references/elasticity-analysis-framework.md` § User-Confirmed Category Corrections

## Monthly Elasticity Report (Cron Job)

### Schedule
Monthly on the 8th at 10:00 AM (`0 10 8 * *`) — runs after the typical monthly import window (1st-7th).
**Cron Job ID**: `00dc5d3c14c2`
**Script**: `scripts/monthly_elasticity_report.py` (data collection, stdout injected as context)
**Card Script**: `scripts/send_elasticity_card.py` (reads `/tmp/elasticity_report_data.json`, builds & sends Feishu card)
**Deliver**: `local` (card sent by script, NOT by cron delivery)
**Provider**: MUST be `"qwen"` (not `"custom"`) — config.yaml key is `qwen`

### ⚠️ Cron Job Creation Pitfalls (confirmed 2026-07-03)
### Cron Job Configuration
- **Job ID**: `00dc5d3c14c2`
- **Schedule**: `0 10 8 * *` (8th of each month, 10:00 AM — after typical import window 1st-7th)
- **Model**: `qwen3.7-max` / provider `qwen`
- **Deliver**: `local` (card sent by script, NOT by cron delivery)
- **Enabled toolsets**: `["terminal"]` (agent only needs to call the sender script)

### Architecture: File-Based Data Handoff (CRITICAL)
```
┌──────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│ monthly_elasticity_      │     │ /tmp/elasticity_         │     │ send_elasticity_         │
│ report.py (script field) │────▶│ report_data.json         │────▶│ card.py (called by agent)│
│ fetches Bitable, writes  │     │ (full report JSON)       │     │ builds card, sends via   │
│ JSON to /tmp file        │     │                          │     │ tenant token             │
└──────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

⚠️ **Do NOT inject large JSON via stdout into prompt** — the Bitable data (4600+ records) produces ~50KB JSON which causes agent timeout/hallucination when injected. The script writes to `/tmp/elasticity_report_data.json` and the card sender reads from that file.

**Scripts**:
- `scripts/monthly_elasticity_report.py` — data collection (cron `script` field, runs before prompt)
- `scripts/send_elasticity_card.py` — card builder + sender (agent calls via terminal)

### Agent Prompt (minimal — only calls sender script)
```
你是凛子。数据已自动写入 /tmp/elasticity_report_data.json。
运行卡片发送脚本：
python3 /home/ubuntu/.hermes/profiles/hr-assistant/scripts/send_elasticity_card.py
检查输出是否包含 "✅ Card sent successfully"。
```

### Card Structure (built by send_elasticity_card.py)
```
Header: 📊 家庭弹性支出分析报告 | {last_3_months[-1]} (template: blue)
---
📋 总览 KPI (column_set 2x2): 总支出 | 基准线 | 近期月均 | 弹性系数
---
🟢 刚性 — table of categories with amounts
🟡 半弹性 — table of categories with amounts + excess
🔴 高弹性 — table of categories with amounts + excess
---
🎯 节流建议 (per-category when excess > ¥500):
  - Pattern detection (季节性飙升 / 持续超支 / 单次大额 / 频率增加)
  - Top 3 transactions
  - 6-month Unicode trend bar
  - Specific suggestion + estimated monthly savings
---
📈 弹性系数月度趋势 (13-month bars with 🔴/⚠️/✅ flags)
---
note: 数据来源 + timestamp
action: button → Bitable
```

### Analysis Scope (confirmed 2026-07-03)
- Rolling 13-month window (all complete months, exclude current incomplete month)
- Recent focus: last 3 months
- Baseline: median of monthly spending per category (non-zero months)
- NOT a pure single-month report — user confirmed rolling analysis is preferred

## Family Expense Bitable (Specialized Tracking Tables)

### Overview
Separate Bitable (`ElxDbS7vwaA66uso5wQcfrRknpe`) with 8 independent tables for specialized expense tracking. Data source: Tencent Docs "家庭支出记录.xlsx" (7 sheets). Entry URL: https://e1kg6bc4dl9.feishu.cn/base/ElxDbS7vwaA66uso5wQcfrRknpe

### Table Index
| Table | table_id | Records | Source Sheet |
|-------|----------|---------|--------------|
| 礼金记录 | tblAs8CUrEPlPg4X | 49 | Sheet1 |
| 外债记录 | tblbA998K3HEdWAI | 4 | Sheet2(left) |
| 车辆费用 | tblUyEe74qhO5TWZ | 14 | Sheet2(right) |
| 出差及报销记录 | tblaolrGEVFIPNmV | 135 | Sheet3 |
| 医美记录 | tblCsChziO7go7x7 | 1 | Sheet4 |
| Navy | tblnghMqDLgkx9Se | 4 | Sheet5 |
| 生活账号类 | tbljq50VYJzIMUFm | 15 | Sheet6 |
| 演唱会 | tblUhdkG3neKgv5E | 5 | Sheet7 |

### User Input Format
User provides 3 items in natural language: `table name, field name, amount`
Example: `车辆费用，ADS高阶功能包，12000`
- Item 1 → matches table_id
- Item 2 → Text field value (fills ★ primary field)
- Item 3 → Number field value (amount)

### Write Rules
- **Must use User OAuth Token** (from tokens.json), Tenant Token returns 91403 Forbidden
- Token valid 2h, refresh with refresh_token when expired
- Single write: `POST /bitable/v1/apps/ElxDbS7vwaA66uso5wQcfrRknpe/tables/{table_id}/records`
- Batch write: `POST .../records/batch_create` (max 500)
- Number fields: pass int/float; DateTime: millisecond Unix timestamp

### Field ID Mapping
- `references/family-expense-field-ids.md` — Complete field_id/type mapping per table
- `references/flexible-expense-framework.md` — 弹性支出三层分类模型 + 计算公式 + 拆解规则

### Pitfalls
- 出差记录「已回报销」is Number (amount), not boolean
- 车辆费用 includes loan (100000), deposit (-5000) — not just direct expenses
- 医美记录 restructured as top-up/deduction model (differs from original Excel)
- 生活账号类 expiry dates are DateTime — use millisecond timestamps
- 8 tables are completely independent, no shared data

### Cumulative Data (as of 2026-06-12)
- Gifts: given ¥15,654 / received ~¥52,475
- Debt: lent ¥85,263 / interest ¥10,000
- Vehicle: total ¥298,234.8
- Travel: 135 entries, 2024-2026
- Concerts: 5 shows, ¥17,246
