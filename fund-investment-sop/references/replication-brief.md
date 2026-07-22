# 基金分析系统复刻 Brief

供另一个 agent 复刻整套基金分析系统。

## 数据源

### 核心 API（已验证可用）

```
# 实时估值（盘中数据，最重要）
GET http://fundgz.1234567.com.cn/js/{基金代码}.js
Headers: User-Agent: Mozilla/5.0
返回: JSONP jsonpgz({fundcode,name,jzrq,dwjz,gsz,gszzl,gztime});
解析: resp[8:-2] → json.loads
字段: dwjz(昨日净值), gsz(今日估值), gszzl(估算涨跌%), gztime(估值时间)
免费，无需认证，8/8基金已验证（2026-06-29）

# 基金净值历史（T+1）
GET http://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize={size}
Headers: Referer: http://fund.eastmoney.com/  ← 必须带，否则403
返回: Data.LSJZList[] → FSRQ(日期), DWJZ(单位净值), LJJZ(累计净值), JZZZL(日增长率%)

# 基金持仓/基本信息
GET http://fund.eastmoney.com/pingzhongdata/{code}.js
Headers: User-Agent: Mozilla/5.0
返回JS变量: fS_name, stockCodes, Data_netWorthTrend

# ETF K线（场内）
AKShare: fund_etf_hist_em(symbol, period="daily", adjust="qfq")

# 新浪财经K线（含预计算均线，仅ETF）
GET https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh510300&scale=240&ma=5,10,20,60&datalen=1023
```

### Python 依赖
- `akshare`（已安装）
- `pandas_ta`（已安装）
- 标准库 `urllib`（零依赖备用方案）

## 实现步骤

1. 读取持仓 → `portfolio.json`（不硬编码持仓）
2. 获取实时估值 → 天天基金JSONP API（盘中数据）
3. 获取历史净值 → 东方财富API（60日）
4. 计算技术指标 → pandas_ta（MA/MACD/RSI/KDJ/BOLL）
5. 五维评估打分 → 见 `references/decision-model.md`
6. 生成加减仓建议 → 触发规则见同文件
7. 定时推送 → cron配置（必须包含具体可执行的操作建议）

## 数据架构

持仓数据存 `portfolio.json`，不存 memory：
- 路径: `/home/ubuntu/.hermes/profiles/finance-master/portfolio.json`
- 更新: 用户发截图或告知操作时
- Cron Job: 从JSON文件读取，不硬编码
- 详见 `references/portfolio-json-schema.md`

## 定时任务模板

| 任务 | Cron | 说明 |
|------|------|------|
| 每日分析 | `30 14 * * 1-5` | 交易日14:30推送 |
| 每周周报 | `0 16 * * 5` | 周五16:00汇总 |
| 每月推荐 | `0 10 1 * *` | 1号10:00新基金 |

## 用户参数（小艾）

| 参数 | 值 |
|------|-----|
| 风险偏好 | 平衡型（最大回撤15%） |
| 月定投 | ¥2,000 |
| 年收益目标 | 20% |

## 已知局限

- 无免费PE/PB百分位API → 需用户每周提供估值截图
- 技术分析是概率工具 → 多维度交叉验证
- 东方财富API需Referer头 → 忘记会403
- 实时估值API偶有超时 → 降级到T-1净值，必须明确标注

## 数据诚信铁律

- 数据无法获得时标注"暂无数据"，写明"无投资建议"
- 严禁编造和伪造
- 实时估值不可用时标注"⚠️ 基于T-1净值提供建议"
- 每条数据标注来源和时间
