# 易变数据管理模式（Volatile Data Pattern）

## 问题场景
某些数据**频繁变化**（如持仓、价格、库存、任务列表），如果存入 memory：
- 占用大量 token 空间
- 每次更新都要触发确认流程
- memory 很快达到上限

## 解决方案：JSON 文件 + 指针

### 架构
```
Memory（稳定层）
└── 存储：文件路径 + 核心规则
    └── 示例："持仓明细存于 /path/to/portfolio.json，每周五校准"

JSON 文件（易变层）
└── 存储：完整数据结构
    ├── meta: {last_updated, source, total}
    ├── holdings: [{code, name, amount, cost, gain}, ...]
    └── allocation: {equity: [...], bond: [...], ...}

Cron Job / 其他工具
└── 读取：JSON 文件路径
    └── 动态获取最新数据
```

### 实现步骤

#### 1. 创建 JSON 文件
```json
{
  "meta": {
    "last_updated": "2026-06-29",
    "source": "蚂蚁财富平台截图",
    "total_assets": 61384.09
  },
  "holdings": [
    {
      "code": "008586",
      "name": "华夏人工智能ETF联接C",
      "amount": 11682.86,
      "cost": 11495.79,
      "gain": 187.07,
      "gain_pct": 1.63
    }
  ],
  "allocation": {
    "equity": ["008586", "007817"],
    "bond": ["002794", "110017"]
  }
}
```

#### 2. Memory 只存指针
```
基金投资：持仓明细存于 portfolio.json（每周五截图校准更新）。核心偏好：平衡型风险（最大回撤15%），年收益目标20%。
```

#### 3. Cron Job 读取文件
```python
import json
with open('/path/to/portfolio.json') as f:
    portfolio = json.load(f)
    holdings = portfolio['holdings']
```

#### 4. 用户更新流程
```
用户发截图 → Agent 识别数据 → 更新 JSON 文件 → 下次 Cron 自动用新数据
```

## 适用场景

| 数据类型 | 更新频率 | 示例 |
|---------|---------|------|
| 基金持仓 | 每周 | portfolio.json |
| 任务列表 | 每天 | tasks.json |
| 库存记录 | 实时 | inventory.json |
| 配置参数 | 偶尔 | config.json |
| 日志摘要 | 每天 | daily_summary.json |

## 优势

| 对比项 | 存 Memory | 存 JSON 文件 |
|--------|----------|-------------|
| Token 占用 | 高（每次注入） | 低（仅路径） |
| 更新成本 | 高（需确认流程） | 低（直接写文件） |
| 数据结构 | 扁平文本 | 结构化 JSON |
| 工具读取 | 需解析文本 | 直接 `json.load()` |
| 版本追踪 | 无 | 可加 `last_updated` |

## 反模式（避免）

❌ **把持仓明细写入 memory**：
```
基金持仓（2026-06-29）：008586 ¥11,683(+1.63%) | 007817 ¥6,691(+56.84%) | ...
```
问题：占 300+ chars，每周更新一次，很快爆 memory。

✅ **memory 存指针 + JSON 存数据**：
```
基金投资：持仓明细存于 portfolio.json（每周五截图校准更新）。
```

## 文件路径规范

建议放在 profile 目录下：
```
~/.hermes/profiles/<profile-name>/
├── portfolio.json      # 持仓数据
├── tasks.json          # 任务列表
└── config.json         # 配置参数
```

或通过软链接共享：
```
~/.hermes/shared-data/
├── portfolio.json
└── tasks.json
```

## 实际案例：finance-master 的基金持仓

**Memory 内容**（~80 chars）：
```
基金投资：持仓明细存于 portfolio.json（每周五截图校准更新）。核心偏好：平衡型风险（最大回撤15%），年收益目标20%。
```

**portfolio.json 内容**（~2000 chars）：
- 8 只基金完整持仓
- 成本价、盈亏、占比
- 配置分类（权益/债券/商品）
- 月投分配计划

**Cron Job 读取**：
```python
import json
portfolio = json.load(open('/home/ubuntu/.hermes/profiles/finance-master/portfolio.json'))
for fund in portfolio['holdings']:
    # 分析每只基金
```

**节省效果**：Memory 从 56% → 28%，释放 500+ chars 空间。
