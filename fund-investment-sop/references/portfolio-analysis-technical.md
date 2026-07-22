# Fund Portfolio Analysis — Technical Execution Layer

> Absorbed from `fund-portfolio-analysis` skill (2026-07-06 consolidation)

## 分析代码（零依赖，Python urllib）

```python
import json, urllib.request

def analyze_fund(code, name, category):
    url = f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=30"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://fund.eastmoney.com/"
    })
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    nav_list = resp.get('Data', {}).get('LSJZList', [])
    if not nav_list:
        return None
    latest = float(nav_list[0]['DWJZ'])
    nav_7d = float(nav_list[min(6, len(nav_list)-1)]['DWJZ'])
    nav_30d = float(nav_list[min(29, len(nav_list)-1)]['DWJZ'])
    return_7d = ((latest - nav_7d) / nav_7d) * 100
    return_30d = ((latest - nav_30d) / nav_30d) * 100
    # 波动率（日收益率标准差）
    returns = []
    for i in range(min(29, len(nav_list)-1)):
        r = (float(nav_list[i]['DWJZ']) - float(nav_list[i+1]['DWJZ'])) / float(nav_list[i+1]['DWJZ']) * 100
        returns.append(r)
    volatility = (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)) ** 0.5 if returns else 0
    # 最大回撤
    navs = [float(nav_list[i]['DWJZ']) for i in range(min(30, len(nav_list)))]
    peak, max_dd = navs[0], 0
    for n in navs:
        if n > peak: peak = n
        dd = (peak - n) / peak * 100
        if dd > max_dd: max_dd = dd
    return {
        'code': code, 'name': name, 'category': category,
        'nav': latest, 'date': nav_list[0]['FSRQ'],
        'return_7d': round(return_7d, 2), 'return_30d': round(return_30d, 2),
        'volatility': round(volatility, 2), 'max_drawdown_30d': round(max_dd, 2)
    }
```

## 双维度诊断规则

### 维度A：动量信号减仓（看近期表现）
| 信号 | 操作建议 |
|------|---------|
| 30日涨幅 > 8% 且回撤 > 12% | 减仓 30-40%（涨太多+波动大） |
| 30日涨幅 > 5% 且回撤 > 10% | 减仓 20-30%（锁利润） |
| 30日跌幅 > 8% 且商品/避险类 | 减仓 20-30% 锁利（高位回撤） |
| 小幅回调 < 5% 且板块长期看好 | 持有，可小额定投加仓 |
| 跌幅 > 5% 且基本面不明 | 谨慎，别急着抄底 |
| 债券型基金 | 持有不动（压舱石） |

### 维度B：绝对收益止盈（看持仓盈亏，需portfolio.json）
| 信号 | 操作建议 |
|------|---------| 
| 持仓盈利 > 30% | 减仓 20-30%（锁定利润） |
| 持仓盈利 > 50% | 减仓 30-40%（落袋为安） |
| 达用户设定目标收益率 | 按目标减仓 |

**两个维度同时触发时，取更保守的操作**（减更多的）

## 组合健康度检查

- **权益类占比**：不超过 60%，否则波动过大
- **板块集中度**：同板块不超过 3 只，否则关联风险高
- **债券配比**：至少 20% 作为压舱石
- **黄金/商品**：建议 10-15%

## 输出格式

1. 逐只基金诊断表（净值/收益/波动/回撤/建议）
2. 资产配置饼图（权益/债券/商品/混合占比）
3. 操作建议汇总表（按优先级排序）
4. ⚠️ 风险提示（不构成投资建议）

## 数据源与 Pitfalls

- API 必须带 `Referer: http://fund.eastmoney.com/`，否则 403
- **实时估值**：`http://fundgz.1234567.com.cn/js/{code}.js`（JSONP格式，解析时用 `resp[8:-2]` 截取）
- 持仓数据从 `/home/ubuntu/.hermes/profiles/finance-master/portfolio.json` 读取
- 数据诚信铁律：数据无法获得时如实报告"该数据暂无"，严禁编造
