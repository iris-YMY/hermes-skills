# 东方财富基金 API 直接调用（零依赖方案）

## 背景
AkShare 在云服务器上安装困难（PEP 668 系统包限制），且部分数据源需要中国网络。
东方财富公开 API 可以直接用 Python 标准库 `urllib` 调用，零依赖。

## API 1: 基金净值历史

```
GET http://api.fund.eastmoney.com/f10/lsjz
参数:
  fundCode = 基金代码（如 008586）
  pageIndex = 页码（从 1 开始）
  pageSize = 每页条数

Headers:
  Referer: http://fund.eastmoney.com/  ← 必须带，否则 403
```

**返回字段**（Data.LSJZList[]）：
- `FSRQ` — 日期
- `DWJZ` — 单位净值
- `LJJZ` — 累计净值（含分红再投资）
- `JZZZL` — 日增长率（%）
- `TotalCount` — 总记录数

**已验证可用（2026-06-24）**：8 只基金全部成功
- 015599 航天军工（996条）
- 013180 新能源车电池（1173条）
- 008586 人工智能（1450条）
- 007817 通信设备（1648条）
- 000218 黄金（2482条）
- 004814 红利优享（1975条）
- 002794 永利债券（2463条）
- 110017 增强回报（4451条）

## API 2: 基金持仓信息（JS 接口）

```
GET http://fund.eastmoney.com/pingzhongdata/{fundCode}.js
Headers: User-Agent: Mozilla/5.0
```

**返回 JS 变量**（用正则提取）：
- `fS_name` — 基金名称
- `fS_code` — 基金代码
- `stockCodes` — 持仓股票代码数组（前10大重仓）
- `Data_netWorthTrend` — 完整净值走势（JSON 数组）
- `fS_inceptionDate` — 成立日期

## API 3: 基金实时估值（已验证不通）

以下接口从云服务器（海外/大陆）访问超时：
- `fundgz.1234567.com.cn` — 天天基金实时估值
- `fundmobapi.eastmoney.com` — 东方财富移动端

**结论**：实时估值数据在云服务器上不可用，接受 T+1 净值数据。

## 示例代码

```python
import json, urllib.request

def fetch_fund_nav(code, page_size=30):
    url = f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize={page_size}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://fund.eastmoney.com/"
    })
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp.get('Data', {}).get('LSJZList', [])

# 计算区间收益率
navs = fetch_fund_nav("008586", 30)
latest = float(navs[0]['DWJZ'])
old = float(navs[min(7, len(navs)-1)]['DWJZ'])
return_7d = ((latest - old) / old) * 100
```

## 与股票数据的差异

| 维度 | 基金 | 股票 |
|------|------|------|
| 价格数据 | 净值（每日1个） | K线（开高低收） |
| 更新频率 | T+1 | 实时 |
| 成交量 | 无 | 有 |
| 持仓信息 | 有（前10大重仓股） | 无 |
| 适合分析 | 趋势、波动率、夏普比率 | 技术面、日内交易 |
