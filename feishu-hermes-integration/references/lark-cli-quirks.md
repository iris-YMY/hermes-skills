# lark-cli & Feishu Drive API Quirks

## lark-cli 完整命令速查 (2026-06-12 更新)

### 顶级命令
`auth`, `bitable`, `cal`, `chat`, `contact`, `doc`, `mail`, `msg`, `sheet`, `minutes`, `version`

⚠️ **命名陷阱**: `cal`（不是 `calendar`）、`msg`（不是 `im`）、`chat`（不是 `im chat`）

### 按模块命令

| 模块 | 命令 | 用法示例 | 说明 |
|------|------|----------|------|
| **contact** | `contact search <name>` | `lark contact search "小艾"` | 位置参数，**不是** `--query` |
| **contact** | `contact get <id>` | `lark contact get ou_xxx` | 按 ID 获取用户信息 |
| **contact** | `contact list-dept` | `lark contact list-dept` | 列出部门成员 |
| **contact** | `contact search-dept` | `lark contact search-dept "技术"` | 搜索部门 |
| **chat** | `chat search [query] [--limit N]` | `lark chat search --limit 10` | 搜索/列出群聊（无 query 则返回全部） |
| **msg** | `msg history` | `lark msg history` | 获取聊天消息历史 |
| **msg** | `msg send` | `lark msg send` | 发送消息 |
| **msg** | `msg recall` | `lark msg recall` | 撤回消息 |
| **msg** | `msg react` | `lark msg react` | 添加消息表情回复 |
| **msg** | `msg resource` | `lark msg resource` | 下载消息中的资源文件 |
| **cal** | `cal list` | `lark cal list` | 列出日历事件 |
| **cal** | `cal search "关键词"` | `lark cal search "会议" --from 2026-06-01` | 搜索事件（位置参数，不是 `--query`） |
| **doc** | `doc get <id>` | `lark doc get <document_id>` | 获取文档内容 (Markdown) |
| **doc** | `doc list <folder_token>` | `lark doc list <token>` | 列出文件夹内容 |
| **doc** | `doc search <keyword>` | `lark doc search "周报"` | 搜索文档 |
| **doc** | `doc create` | `lark doc create --title "X" --folder <token>` | 创建文档 |
| **doc** | `doc append` | `lark doc append <id> --text "内容"` | 追加内容 |
| **doc** | `doc blocks` | `lark doc blocks <id>` | 获取文档 block 结构 |
| **doc** | `doc update-block` | `lark doc update-block` | 更新文档 block |
| **doc** | `doc comments` | `lark doc comments <id>` | 获取文档评论 |
| **doc** | `doc download` | `lark doc download` | 从 Drive 下载文件 |
| **doc** | `doc image` | `lark doc image` | 下载文档中的图片 |
| **doc** | `doc wiki` | `lark doc wiki` | 解析 wiki 节点到 document token |
| **doc** | `doc wiki-children` | `lark doc wiki-children` | 列出 wiki 子节点 |
| **doc** | `doc wiki-search` | `lark doc wiki-search "关键词"` | 搜索 wiki 节点 |
| **mail** | `mail list` | `lark mail list` | 列出邮箱文件夹 |
| **mail** | `mail search` | `lark mail search` | 搜索本地缓存邮件 |
| **mail** | `mail sync` | `lark mail sync` | 同步邮件到本地 |
| **mail** | `mail show` | `lark mail show` | 显示邮件内容 |
| **mail** | `mail fetch` | `lark mail fetch` | 下载邮件为 .eml |

### 不存在的命令
- ❌ `lark im` → 用 `lark msg`
- ❌ `lark calendar` → 用 `lark cal`
- ❌ `lark doc delete` → 用 Drive API 直接调用
- ❌ `lark drive list` → 用 `lark doc list`
- ❌ `lark chat list` → 用 `lark chat search`（无参数 = 全部）

### SCOPE_ERROR 排查模式

当调用 API 返回 `SCOPE_ERROR` 时，响应中会包含：
1. **Required scopes**: 完整列出缺失的 scope 列表
2. **Remediation command**: `lark auth login --add --scopes <group>`

常见 scope group 名: `documents`, `messages`, `calendar`, `contacts`, `bitable`, `mail`, `minutes`

#### ⚠️ `lark auth status` scope_groups 不可靠（2026-06-12 确认）

`lark auth status` 的 `scope_groups` 使用"全有或全无"逻辑：如果某个 group 内**任何一个** scope 缺失，整个 group 显示 `false`。同时 `refresh_token_expires_at` 可能显示零值（`0001-01-01T00:00:00Z`）。

**`tokens.json` 是唯一的可靠数据源**：
```bash
# 直接读取 tokens.json 获取真实 scope 列表和过期时间
cat $LARK_CONFIG_DIR/tokens.json | python3 -c "
import json,sys
t=json.load(sys.stdin)
scopes=set(t['scope'].split())
print('Granted scopes:', len(scopes))
print('refresh_token expires:', t.get('refresh_token_expires_at','N/A'))
# 对比 SCOPE_ERROR 中的 required scopes
required = set('docx:document:readonly wiki:wiki:readonly ...'.split())
missing = required - scopes
if missing: print('MISSING:', missing)
"
```

#### 排查流程（更新版）
1. **运行命令获取 SCOPE_ERROR** → 记下 Required scopes 列表
2. **读取 `tokens.json`** → 提取 `scope` 字段（空格分隔的 scope 列表）
3. **对比差异** → 找出真正缺失的 scope（通常是 1-2 个，不是整个 group）
4. **飞书开发者后台** → 启用缺失的权限 → **必须发布新版本**
5. **重新授权** → 优先使用 `lark auth login`（全量重新授权），比 `--add --scopes` 更可靠
   - `lark auth login --add --scopes documents` 在无头服务器上可能挂起超时

#### 常见缺失 Scope 与 Group 对应
| Group | 关键 Scope（缺任何一个整个 group 显示 false） |
|-------|------|
| documents | `wiki:wiki:readonly`（容易遗漏） |
| messages | `im:message`（区别于 `im:message:readonly`，需要完整读写权限） |

## ⚠️ `lark doc append` multiple `--text` flags partial content drop

When chaining multiple `--text` flags in a single `lark doc append` call, only the **last** `--text` block may appear in the document. Earlier text blocks are silently dropped.

**Workaround**: Split into individual `lark doc append` calls, one per content block:
```bash
# BAD — only last --text survives
lark doc append <id> --text "Line 1" --text "Line 2" --text "Line 3"

# GOOD — each call writes one block
lark doc append <id> --text "Line 1"
lark doc append <id> --text "Line 2"
lark doc append <id> --text "Line 3"
```

Combine `--text` with `--bullet`/`--code`/`--divider` in the **same** call works fine — the issue is specifically multiple `--text` flags. Use a Python loop for bulk writes.

## 关键字段名

- `lark doc create` 返回 **`document_id`**，不是 `doc_token`
- `lark doc list` items 中返回 **`token`**（即 document_id）
- `lark doc get` 返回 **`document_id`**
- 三者格式相同（字母数字串），但字段名不同，不要混用

## Drive API 删除文档

lark-cli 无删除命令，需直接调 API：

```
DELETE https://open.feishu.cn/open-apis/drive/v1/files/{file_token}?type={type}
Authorization: Bearer {tenant_access_token}
```

**注意**：
- `type` 参数**必填**，值来自 `lark doc list` 的 `type` 字段（`docx`/`sheet`/`bitable`/`file`）
- 不带 `type` 返回 400 `field validation failed`
- 需要应用开通 `drive:drive` 或 `drive:drive:delete` 权限
- hr-assistant 应用**当前无删除权限**，返回 403 `operate node no permission`
- 无权限时只能手动在飞书 UI 删除

## 获取 tenant_access_token

```python
import json, urllib.request
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
data = json.dumps({"app_id": "<app_id>", "app_secret": "<secret>"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["tenant_access_token"]
```

## 内容对比陷阱

`lark doc get` 返回的 Markdown 含飞书转义：
- `"` → `&#34;`
- `_` → `\_`
- `#` → `\#`

对比时需 normalize 后再判断是否需要更新。

## ⚠️ OAuth Token Expiry (2026-06-09 发现)

**lark-cli 依赖 OAuth User Access Token（非 Tenant Token）才能访问用户文件夹。**

### Token 存储位置
| 位置 | 说明 |
|------|------|
| `~/.lark/tokens.json` | 全局 OAuth tokens |
| `~/.hermes/profiles/<name>/home/.lark/tokens.json` | 按 Profile 存储（hr-assistant 有，default 通常没有） |

### 过期时间
- **access_token**: ~2 小时
- **refresh_token**: ~7 天
- 过期后 `lark` 命令返回 `AUTH_ERROR` 或 `failed to refresh token`

### 症状
```
$ lark doc list <folder_token>
{"code": "AUTH_ERROR", "message": "Not authenticated. Run: lark auth login"}
# 或
{"code": "API_ERROR", "message": "failed to refresh token: token request failed (code 20026)"}
```

### 重新授权流程
1. **需要桌面浏览器**（飞书内嵌浏览器不行）
2. 打开授权链接获取 `code`
3. 将 code 交给 agent，agent 通过 `lark auth login` 完成授权
4. Token 自动写入 `~/.lark/tokens.json`

### 跨 Profile 问题
Default Profile 的 `~/.hermes/profiles/default/home/.lark/` 目录通常**没有 tokens.json**，只有 `app_secret` 和 `config.yaml`。需要从 `~/.lark/` 或其他 Profile 复制，但 refresh token 有有效期，过期后必须重新授权。

### 排查步骤
```bash
# 1. 检查 token 是否存在
ls -la ~/.lark/tokens.json
# 2. 检查过期时间
python3 -c "import json; t=json.load(open('~/.lark/tokens.json')); print(t['expires_at'])"
# 3. 测试认证
lark auth status
```

## ⚠️ 应用可见范围限制（2026-06-04 确认）

**lark-cli 以应用身份（App）运行，只能看到应用有权限的文件夹。**

当用 `lark doc list ""`（空 token = 根目录）时，只能看到以下 4 个文件夹：
- `Skills` (PdkOfBF0nlUKlkdVABZcYuKFneh)
- `数据大师` (SpYKfg5t0l9s4qdQbh0cgqFdnXe)
- `凛子小姐` (IdI2f33ZCljdE6dIAgBcomQonNe)
- `黑执事` (OSJtfkVXrl8q0SdzU24c6LsMnNf)

**应用看不到的内容：**
- 用户在飞书个人空间创建的文件夹和文档
- 其他应用创建的内容
- 用户通过飞书 UI 手动创建的"用户小艾"等文件夹（除非明确分享给了应用）

**排查"文档找不到"问题时：**
1. 先用 `lark doc list ""` 查看应用根目录下所有文件夹
2. 逐个 `lark doc list <folder_token>` 遍历
3. 如果应用空间确实没有，说明文档可能在用户个人空间，需要用户提供链接或手动分享
