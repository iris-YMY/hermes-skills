# 飞书多维表格 API 替换指南（替代 lark-cli）

> viral-video-studio 原用 `lark-cli` 操作多维表格，现改为直接调用飞书 REST API。

## 认证

```bash
# 获取 tenant_access_token
source ~/.env 2>/dev/null
TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")
```

## API 对照表

| 原 lark-cli 命令 | 飞书 REST API |
|---|---|
| `lark-cli base +base-create --name "X"` | `POST /open-apis/bitable/v1/apps` body: `{"name":"X"}` |
| `lark-cli base +field-create --base-token T --table-id TID --name N --type 1` | `POST /open-apis/bitable/v1/apps/{T}/tables/{TID}/fields` body: `{"field_name":"N","type":1}` |
| `lark-cli base +field-list --base-token T --table-id TID` | `GET /open-apis/bitable/v1/apps/{T}/tables/{TID}/fields` |
| `lark-cli base +record-upsert --base-token T --table-id TID --json '{...}'` | `POST /open-apis/bitable/v1/apps/{T}/tables/{TID}/records` body: `{"fields":{...}}` |
| `lark-cli base +record-search --base-token T --table-id TID --query "X"` | `POST /open-apis/bitable/v1/apps/{T}/tables/{TID}/records/search` with filter |
| `lark-cli base +base-get --base-token T` | `GET /open-apis/bitable/v1/apps/{T}` |

## 日期字段注意

Bitable 日期字段值为 **Unix 毫秒时间戳**，不是字符串：
```json
{"fields": {"拆解时间": 1720857600000}}
```

## 字段类型编号

| type | 含义 |
|------|------|
| 1 | 文本 |
| 2 | 数字 |
| 3 | 单选 |
| 4 | 多选 |
| 5 | 日期 |
| 7 | 复选框 |
| 11 | 人员 |
| 13 | 电话 |
| 15 | 超链接 |
| 17 | 附件 |
| 18 | 单向关联 |
| 20 | 公式 |
| 21 | 双向关联 |

## ⚠️ 权限前置条件

飞书应用需要开通以下权限之一：
- `bitable:app` — 多维表格完整读写
- `base:app:create` — 创建多维表格

授权链接（替换 APP_ID）：
```
https://open.feishu.cn/app/{APP_ID}/auth?q=bitable:app
```
