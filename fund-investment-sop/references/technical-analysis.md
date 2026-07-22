# 基金技术分析实现指南

## 依赖

- `pandas_ta`（已安装）：130+ 技术指标
- `akshare`（已安装）：基金净值/ETF K线数据
- 东方财富 API（零依赖，urllib）

## 技术指标计算

```python
import pandas as pd
import pandas_ta as ta

def calc_indicators(nav_series):
    """nav_series: pd.Series of fund NAV values (chronological order)"""
    result = pd.DataFrame({'nav': nav_series})
    nav = result['nav']

    # 均线系统
    result['MA5'] = ta.sma(nav, length=5)
    result['MA20'] = ta.sma(nav, length=20)
    result['MA60'] = ta.sma(nav, length=60)

    # MACD (12,26,9)
    macd = ta.macd(nav, fast=12, slow=26, signal=9)
    result = pd.concat([result, macd], axis=1)
    # Columns: MACD_12_26_9, MACDh_12_26_9 (histogram), MACDs_12_26_9 (signal)

    # RSI
    result['RSI6'] = ta.rsi(nav, length=6)
    result['RSI14'] = ta.rsi(nav, length=14)

    # KDJ (Stochastic)
    stoch = ta.stoch(nav, nav, nav)
    result = pd.concat([result, stoch], axis=1)

    # 布林带
    bb = ta.bbands(nav, length=20, std=2)
    result = pd.concat([result, bb], axis=1)

    return result
```

## 信号判读规则

### 均线
- **多头排列**: MA5 > MA20 > MA60 → 趋势向上，持有/加仓
- **空头排列**: MA5 < MA20 < MA60 → 趋势向下，观望/减仓
- **粘合后发散**: 启动信号

### MACD
- **金叉** (DIF 上穿 DEA): 买入信号
- **死叉** (DIF 下穿 DEA): 卖出信号
- 零轴上方金叉 = 强势买入；零轴下方死叉 = 强势卖出

### RSI
- RSI > 70: 超买区，可能回调
- RSI < 30: 超卖区，可能反弹
- 40-60: 正常区间

## 新浪财经 K线 API（含预计算均线）

```
GET https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
参数: symbol=sh510300&scale=240&ma=5,10,20,60&datalen=1023
```
直接返回 `ma_price5`, `ma_price10`, `ma_price20`, `ma_price60`，无需本地计算。仅适用于 ETF/场内基金。

## 波动率与最大回撤计算

```python
def calc_risk_metrics(nav_list):
    """nav_list: list of dicts with 'DWJZ' field"""
    navs = [float(n['DWJZ']) for n in nav_list]
    # 波动率
    returns = [(navs[i] - navs[i+1]) / navs[i+1] * 100 for i in range(len(navs)-1)]
    avg_r = sum(returns) / len(returns)
    volatility = (sum((r - avg_r)**2 for r in returns) / len(returns)) ** 0.5
    # 最大回撤
    peak = navs[0]
    max_dd = 0
    for n in navs:
        if n > peak: peak = n
        dd = (peak - n) / peak * 100
        if dd > max_dd: max_dd = dd
    return {'volatility': round(volatility, 2), 'max_drawdown': round(max_dd, 2)}
```
