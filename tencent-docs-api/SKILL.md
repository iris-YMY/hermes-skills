---
name: tencent-docs-api
description: Tencent Docs Drive v2 API — file/folder management (create, rename, delete, list). Core Rules, patterns, error codes, Python template. Credentials in ~/.env.
version: 3.0.0
author: 凛子 (Rinko)
license: MIT
metadata:
  hermes:
    tags: [tencent, docs, drive, api, automation, productivity]
    related_skills: [tencent-docs-oauth]
---

# Tencent Docs Drive v2 API

## Overview

腾讯文档 Drive v2 API 提供文档/表格/智能表/文件夹的文件级管理（创建、重命名、删除、复制、查询列表）。采用三元组 Header 认证，所有请求从后端发起。

存储于 `~/.env`：
```
TENCENT_DOCS_CLIENT_ID=<应用ID>
TENCENT_DOCS_OPEN_ID=<用户唯一标识>
TENCENT_DOCS_ACCESS_TOKEN=<访问令牌>
```

读取：`source ~/.env` 或 python 读文件解析。Token 有效期 30 天。

## Core Rules

1. **API Base**: `https://docs.qq.com/openapi`
2. **三元组 Header**（缺一不可，名称大小写敏感）：
   ```
   Access-Token: $TENCENT_DOCS_ACCESS_TOKEN
   Client-Id: $TENCENT_DOCS_CLIENT_ID
   Open-Id: $TENCENT_DOCS_OPEN_ID
   ```
3. **POST 请求**: `Content-Type: application/x-www-form-urlencoded`，用 `--data-urlencode`
4. **根目录**: folderID = `/`，URL 中编码为 `%2F`
5. **curl 必须加 `-L`**：API 对 `/folders/%2F` 返回 301 重定向，不加 `-L` 会得到空响应
6. **响应键名**: 文件夹内容数组在 `data.list`（不是 `data.files`）

## Quick Reference — 文件管理 `/drive/v2`

| 操作 | Method | Path |
|------|--------|------|
| 新建文档 | POST | `/files` |
| 查询文档 | GET | `/files/{fileID}/metadata` |
| 重命名 | PATCH | `/files/{fileID}` |
| 删除 | DELETE | `/files/{fileID}` |
| 复制 | POST | `/files/{fileID}/copy` |
| 收藏 | PATCH | `/files/{fileID}/star` |
| 获取文件夹内容 | GET | `/folders/{folderID}` |
| 创建文件夹 | POST | `/folders` |
| 删除文件夹 | DELETE | `/folders/{folderID}` |

type 枚举：`doc`(默认) / `sheet` / `form` / `slide` / `mind` / `flowchart` / `smartsheet`

其他模块（需额外权限）：在线表格 `/sheet/v2` · 智能表 `/smartsheet/v2` · 文档内容 `/doc/v2` · 收集表 `/form/v2`

## Common Patterns

### 新建文档
```bash
source ~/.env
curl -s -X POST "https://docs.qq.com/openapi/drive/v2/files" \
  -H "Access-Token: $TENCENT_DOCS_ACCESS_TOKEN" \
  -H "Client-Id: $TENCENT_DOCS_CLIENT_ID" \
  -H "Open-Id: $TENCENT_DOCS_OPEN_ID" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "type=doc&title=文档标题"
```
可选：`&folderID=FOLDER_ID` 指定目录。

### 获取文件夹列表（含分页）
```bash
# 根目录：必须加 -L 跟随 301 重定向
curl -sL "https://docs.qq.com/openapi/drive/v2/folders/%2F" \
  -H "Access-Token: $TENCENT_DOCS_ACCESS_TOKEN" \
  -H "Client-Id: $TENCENT_DOCS_CLIENT_ID" \
  -H "Open-Id: $TENCENT_DOCS_OPEN_ID"

# 指定文件夹 + 分页（?next=光标）
curl -sL "https://docs.qq.com/openapi/drive/v2/folders/FOLDER_ID?next=0" \
  -H "Access-Token: $TENCENT_DOCS_ACCESS_TOKEN" \
  -H "Client-Id: $TENCENT_DOCS_CLIENT_ID" \
  -H "Open-Id: $TENCENT_DOCS_OPEN_ID"
```
响应结构：`{ "ret": 0, "data": { "list": [...], "next": 0 } }`
- 文件数组键名为 **`list`**（不是 `files`）
- `next > 0` 表示还有更多，用 `?next=N` 继续请求

### 查询文档元数据
```bash
curl -s "https://docs.qq.com/openapi/drive/v2/files/{fileID}/metadata" \
  -H "Access-Token: $TENCENT_DOCS_ACCESS_TOKEN" \
  -H "Client-Id: $TENCENT_DOCS_CLIENT_ID" \
  -H "Open-Id: $TENCENT_DOCS_OPEN_ID"
```

### 重命名
```bash
curl -s -X PATCH "https://docs.qq.com/openapi/drive/v2/files/{fileID}" \
  -H "Access-Token: $TENCENT_DOCS_ACCESS_TOKEN" \
  -H "Client-Id: $TENCENT_DOCS_CLIENT_ID" \
  -H "Open-Id: $TENCENT_DOCS_OPEN_ID" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "title=新标题"
```

### 删除
```bash
curl -s -X DELETE "https://docs.qq.com/openapi/drive/v2/files/{fileID}" \
  -H "Access-Token: $TENCENT_DOCS_ACCESS_TOKEN" \
  -H "Client-Id: $TENCENT_DOCS_CLIENT_ID" \
  -H "Open-Id: $TENCENT_DOCS_OPEN_ID"
```

### Python 调用模板
```python
import subprocess, os, json

ENV_PATH = "/home/ubuntu/.env"

def load_creds():
    c = {}
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith("TENCENT_DOCS_") and "=" in line:
                k, v = line.strip().split("=", 1)
                c[k] = v
    return c

def api(method, path, data=None):
    c = load_creds()
    cmd = ["curl", "-s", "-L", "-X", method, f"https://docs.qq.com/openapi{path}",
           "-H", f"Access-Token: {c['TENCENT_DOCS_ACCESS_TOKEN']}",
           "-H", f"Client-Id: {c['TENCENT_DOCS_CLIENT_ID']}",
           "-H", f"Open-Id: {c['TENCENT_DOCS_OPEN_ID']}"]
    if data:
        cmd += ["-H", "Content-Type: application/x-www-form-urlencoded"]
        for k, v in data.items():
            cmd += ["--data-urlencode", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)
```

## Error Codes

| ret | 含义 | 解决 |
|-----|------|------|
| 0 | 成功 | — |
| 10313 | Access-Token 为空 | 检查 Header 名称必须为 `Access-Token` |
| 10303 | Open-Id 错误 | 检查 Open-Id 非空且与 Token 匹配 |
| 10302 | Client-Id 错误 | 检查 Client-Id 非空且与 Token 匹配 |
| 37019 | Token 过期/错误 | 从后台重新获取 |
| 10202 | 文件夹不存在 | 根目录用 `/`（URL 编码 `%2F`）|

## Pitfalls

1. **Header 名称**：必须 `Access-Token` / `Client-Id` / `Open-Id`。不可用 `Authorization: Bearer` 或 `X-` 前缀
2. **Content-Type**：POST/PATCH 用 `application/x-www-form-urlencoded`，不是 JSON
3. **根目录路径**：`/` 不是 `root`，URL 中编码为 `%2F`。curl 需加 `-L` 跟随 301 重定向
4. **fileID 格式**：类似 `300000000$FsRRKfqPzhXT`（`$` 需 URL 编码为 `%24`），不是 URL 短码
5. **Token 30 天有效**：过期从腾讯文档后台重新获取
6. **后端发起**：Open API 请求必须由后端服务发起，浏览器直接调用可能失败
7. **响应结构**：文件夹内容在 `data.list` 数组中，分页游标在 `data.next`（`next=0` 表示已到底）
8. **`execute_code` 沙箱 `.env` 路径**：沙箱中 `HOME` 环境变量被覆盖，必须使用绝对路径 `/home/ubuntu/.env`
9. **搜索/共享端点不可用**：`GET /drive/v2/search` 返回 10002，`POST /drive/v2/search` 返回 405。`/folders/shared`、`/drive/v2/shared` 等端点均 404
10. **共享文档标记**：文件夹列表响应中 `isCollaborated: true` 表示该文档是协作文档

---

## HR Assistant Profile Configuration

### 当前状态（2026-06-01）
- **SaaS 访问权限**：⏳ 审批中
- **凭据配置**：`~/.env` 中尚无腾讯文档凭据

### Authentication
- **Auth Type**: 三元组 Header 认证（`Access-Token` + `Client-Id` + `Open-Id`）
- **Client ID**: `8b94874c4dd24469a7f9f01e6251a9a7`（HR 自动化应用）
- **Client Secret**：❌ 尚未获取（SaaS 审批通过后从开放平台后台获取）
- **Access Token / Open ID**：❌ 尚未获取

### 审批通过后的操作步骤
1. 确认应用主体为**企业**（个人主体 SaaS 权限大概率被拒）
2. 从腾讯开放平台后台获取 **Client Secret**
3. 配置 `~/.env`（含 `TENCENT_DOCS_CLIENT_ID`、`TENCENT_DOCS_CLIENT_SECRET`、`TENCENT_DOCS_ACCESS_TOKEN`、`TENCENT_DOCS_OPEN_ID`）
4. 验证 Drive API 连通性：列出根目录文件夹

---

## OAuth2 User Authorization Flow

### Current Status: ⏸️ PENDING
- SaaS 访问权限: ❌ 无法通过（需企业资质）
- Client Secret: ❌ 无法获取
- **搁置原因**: 腾讯文档开放平台 SaaS 权限仅对企业主体开放

### OAuth2 Flow (4 Steps)
1. **构造授权链接**: `https://docs.qq.com/oauth/v2/authorize?client_id=...&redirect_uri=...&response_type=code&scope=all`
2. **用户扫码授权**: 微信扫码 → 同意 → 回调 URL 带 `code`
3. **换取 access_token**: `curl -X GET 'https://docs.qq.com/oauth/v2/token'` with client_secret
4. **调用 Open API**: 使用 User Access Token 代替应用级 Token

### Account Isolation
| Dimension | App-Level | User-Level (OAuth) |
|-----------|-----------|-------------------|
| Can see "My Docs" | App-created only | All user docs ✅ |
| Can see "Shared with me" | ❌ | ✅ |
| Needs client_secret | ✅ | ✅ (token exchange) |
| Token validity | 30 days | 30 days (refresh 1 year) |

### SaaS Permission Status
- Sheet/Doc content APIs (`/sheet/v2/`, `/doc/v2/`) return 404 — need SaaS approval
- Search/shared endpoints also 404/10002
- **Developer entity requirement**: SaaS permissions require enterprise entity (企业主体), not individual (个人)