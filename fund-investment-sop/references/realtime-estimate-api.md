# 天天基金实时估值 API

## 接口

```
GET http://fundgz.1234567.com.cn/js/{基金代码}.js
Headers: User-Agent: Mozilla/5.0
```

**免费，无需认证**，8/8基金已验证可用（2026-06-29）。

## 返回格式

JSONP（非标准JSON）：
```javascript
jsonpgz({"fundcode":"008586","name":"华夏人工智能ETF联接C","jzrq":"2026-06-26","dwjz":"1.8500","gsz":"1.8774","gszzl":"1.48","gztime":"2026-06-29 15:00"});
```

## 字段说明

| 字段 | 含义 | 示例 |
|------|------|------|
| fundcode | 基金代码 | 008586 |
| name | 基金名称 | 华夏人工智能ETF联接C |
| jzrq | 昨日净值日期 | 2026-06-26 |
| dwjz | 昨日单位净值 | 1.8500 |
| gsz | 今日估算净值 | 1.8774 |
| gszzl | 估算涨跌幅(%) | 1.48 |
| gztime | 估值时间 | 2026-06-29 15:00 |

## JSONP 解析代码

```python
import json, urllib.request

def get_realtime_estimate(code):
    url = f"http://fundgz.1234567.com.cn/js/{code}.js"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    # 去掉 jsonpgz( 和 );
    json_str = resp[8:-2]
    return json.loads(json_str)

# 用法
data = get_realtime_estimate("008586")
print(f"今日估值: {data['gsz']}, 涨跌: {data['gszzl']}%")
```

## 精度与延迟

- 基于持仓股票的实时价格计算
- 延迟约15分钟
- 与最终净值误差通常 < 1%
- 交易日 9:30-15:00 更新

## 降级方案

如 API 不可用（超时/返回异常）：
- 标注 "⚠️ 实时估值不可用，以下基于T-1净值数据提供投资建议"
- 改用东方财富 API 获取最近净值
- 不猜测估值数据
