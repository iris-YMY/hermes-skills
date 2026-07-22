# China Mutual Fund Data APIs (东方财富/天天基金)

Tested 2026-06-24 from cloud server. All APIs accessible without auth.

## API 1: Fund NAV History (净值历史)

**Endpoint**: `http://api.fund.eastmoney.com/f10/lsjz`

```
GET http://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=30
Headers: Referer: http://fund.eastmoney.com/
```

**Response** (JSON):
```json
{
  "TotalCount": 1450,
  "Data": {
    "LSJZList": [
      {
        "FSRQ": "2026-06-23",     // 净值日期
        "DWJZ": "1.8267",         // 单位净值
        "LJJZ": "1.8267",         // 累计净值 (含分红再投资)
        "JZZZL": "-3.54"          // 日增长率 (%)
      }
    ]
  }
}
```

- **Rate limit**: No apparent limit, 8 funds fetched in ~7s
- **History depth**: 996–4451 records depending on fund age
- **Required header**: `Referer: http://fund.eastmoney.com/` (without it returns empty)

## API 2: Fund Basic Info (基金基本信息)

**Endpoint**: `http://fund.eastmoney.com/pingzhongdata/{code}.js`

Returns JavaScript with embedded data (not JSON). Parse with regex:

```python
import re, json, urllib.request

url = f"http://fund.eastmoney.com/pingzhongdata/{code}.js"
js = urllib.request.urlopen(req).read().decode("utf-8")

# Fund name
name = re.search(r'fS_name\s*=\s*"([^"]+)"', js).group(1)

# Fund code
code = re.search(r'fS_code\s*=\s*"([^"]+)"', js).group(1)

# Holding stock codes (top 10)
stocks = re.search(r'stockCodes\s*=\s*\[([^\]]+)\]', js).group(1).replace('"','').split(',')

# NAV trend (for charts) — JSON array of {x: timestamp_ms, y: nav, equityReturn, unitMoney}
nav_trend = re.search(r'Data_netWorthTrend\s*=\s*(\[[^\]]+\])', js).group(1)
```

**Available fields** (parsed via regex):
| Variable | Content |
|----------|---------|
| `fS_name` | Fund name |
| `fS_code` | Fund code |
| `fS_inceptionDate` | 成立日期 |
| `fS_fundType` | 基金类型 |
| `stockCodes` | 持仓股票代码 (top 10) |
| `Data_netWorthTrend` | 净值走势 JSON array |
| `Data_ACWorthTrend` | 累计净值走势 |
| `Data_grandTotal` | 累计收益对比 |
| `Data_rateInSimilarType` | 同类排名走势 |
| `stockCodesNew` | 持仓股票代码 (新格式) |
| `fund_sourceRate` | 原费率 |
| `fund_Rate` | 现费率 |
| `fund_minsg` | 最小申购金额 |

## API 3: Real-time Intraday Valuation (盘中估值)

⚠️ **BLOCKED from cloud server** (2026-06-24): `fundgz.1234567.com.cn` times out.

**Endpoint** (when accessible): `http://fundgz.1234567.com.cn/js/{code}.js`
Returns JSONP with estimated NAV based on holding stocks' real-time prices.

**Workaround for real-time estimates**: Calculate from holding stocks:
1. Get holding stocks from API 2 (`stockCodes`)
2. Fetch real-time stock prices via Tencent API (`qt.gtimg.cn`)
3. Weighted sum = estimated fund NAV

## Fund vs Stock Data Differences

| Dimension | Stock | Fund |
|-----------|-------|------|
| Price data | OHLCV (K-line) | NAV only (no open/high/low) |
| Update frequency | Real-time | T+1 (after market close) |
| Volume | ✅ | ❌ |
| Holdings info | ❌ | ✅ (top 10 stocks) |
| Manager info | ❌ | ✅ (fund manager) |
| Analysis focus | Entry/exit points | Hold/add/reduce |
| Key metrics | RSI, MACD, Bollinger | Sharpe ratio, max drawdown, volatility |

## Tested Fund Types (confirmed working)

| Type | Examples | Notes |
|------|----------|-------|
| 指数型 (Index) | 015599, 013180, 008586, 007817 | ETF联接基金 |
| 商品型 (Commodity) | 000218 | 黄金ETF联接 |
| 混合型 (Hybrid) | 004814 | 灵活配置 |
| 债券型 (Bond) | 002794, 110017 | 固收+ |

## AkShare Installation on Ubuntu

⚠️ `pip install akshare` fails with PEP 668 error (externally-managed-environment).
**Solutions**:
1. Use `--break-system-packages` flag (not recommended)
2. Use venv: `python3 -m venv ~/venv && source ~/venv/bin/activate && pip install akshare`
3. **Skip AkShare entirely** — call East Money APIs directly via `urllib.request` (recommended for cron jobs)
