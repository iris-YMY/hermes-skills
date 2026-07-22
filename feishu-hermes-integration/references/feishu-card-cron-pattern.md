# Feishu Card Cron Reports — Gateway :::CARD Pattern

> Absorbed from `feishu-card-cron-reports` skill (2026-07-06 consolidation)

## Overview

Two architectures for sending Feishu Interactive Cards from cron jobs:

1. **脚本模式**（黑执事/data-master）：`deliver: local` + `send_xxx_card.py` 脚本直接调 API
2. **网关模式**（理财大师）：`deliver: feishu` + Agent 输出 `:::CARD...:::ENDCARD` 标记 → 网关自动提取并以 interactive 类型发送

## 网关代码修改（:::CARD 标记识别）

文件：`/home/ubuntu/.hermes/hermes-agent/gateway/platforms/feishu.py`

### 正则定义（~line 161）
```python
_CARD_CONTENT_RE = re.compile(r"^:::CARD\s*\n(.*?)\n:::ENDCARD\s*\n?", re.DOTALL)
```

### send() 方法修改
在 `send()` 方法的 chunking 之前：
- 用 `_CARD_CONTENT_RE.match()` 检测卡片内容
- 提取卡片 JSON → 以 `msg_type="interactive"` 发送
- 剩余内容正常 chunk → 以 `msg_type="post"` 发送

### 容错
- 卡片 JSON 无效 → 跳过卡片，照常发送详细内容
- 卡片发送失败 → 不阻塞详细内容发送

## Agent 输出格式

```
:::CARD
{"config":{"wide_screen_mode":true},"header":{"title":{"content":"标题","tag":"plain_text"},"template":"blue"},"elements":[{"tag":"markdown","content":"摘要内容用\\n换行"},{"tag":"hr"},{"tag":"markdown","content":"更多摘要"}]}
:::ENDCARD

# 详细报告标题
（正常 markdown 内容）
```

## 卡片 JSON 规范

### 必填字段
- `config.wide_screen_mode: true`
- `header.title.content`: 报告标题
- `header.template`: 颜色（blue/green/red/orange）
- `elements`: 数组，每个元素是 markdown/hr/action

### 卡片颜色规则
| 颜色 | 使用场景 |
|------|---------| 
| blue | 正常/中性 |
| green | 盈利/正向 |
| red | 亏损/警告 |
| orange | 需注意 |

### 元素类型
- `{"tag": "markdown", "content": "**文字**\\n换行用\\\\n"}` — 文本块
- `{"tag": "hr"}` — 分割线
- `{"tag": "action", "actions": [...]}` — 按钮

### 注意事项
- JSON 必须合法（双引号、无尾逗号）
- markdown content 中换行用 `\\n`，不要用真换行符
- 单个 markdown 元素上限 ~4000 字符
- 整张卡片最多 30 个 elements

## 核心设计原则：卡片与 MD 严禁重复

**用户明确要求**：卡片中出现的内容不要在后文 MD 中重复。卡片是摘要，MD 是详细分析，两者职责不同。

- 卡片放**结论/必做项**（用户 3 秒内能决定是否展开看详情）
- MD 放**推理过程/完整数据**（给想了解"为什么"的用户）
- 判定规则、阈值表等放在 prompt 中仅供生成卡片用，不要出现在 MD 输出里

## 已配置的网关模式 Cron Jobs

| Job | ID | 卡片颜色规则 |
|-----|-----|------------| 
| 每日基金投资建议 | ccb47d15762b | blue/red/green 按盈亏 |
| 每周基金周报 | 3cced79a54e0 | blue/red/green 按周盈亏 |
| 每月新基金推荐 | 68653430510f | blue/red/green 按月盈亏 |

## Pitfalls
- **git pull 会覆盖修改**：网关代码修改在 hermes-agent 源码中，更新后需重新 patch
- **卡片 JSON 错误不致命**：解析失败会跳过卡片，详细内容仍会发送
- **gateway 重启**：修改 feishu.py 后需 `hermes --profile finance-master gateway restart`
