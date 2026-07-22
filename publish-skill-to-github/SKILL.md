---
name: publish-skill-to-github
description: 将 Hermes Skill 发布到 GitHub 仓库（公开/私有），含仓库创建、文档完善、安装脚本和验证。
tags: [github, skill, publish, deploy]
triggers:
  - 发布 skill 到 github
  - skill 上传 github
  - 开源 skill
  - publish skill
---

# 发布 Skill 到 GitHub

## 输入

| 参数 | 说明 | 示例 |
|------|------|------|
| 本地 skill 路径 | 必须 | `~/.hermes/profiles/work-assistant/skills/business/my-skill/` |
| 发布模式 | `collection`（默认）或 `standalone` | `collection` |
| 目标仓库 | collection 模式下指定已有仓库，不填则用默认 | `iris-YMY/hermes-skills` |
| 仓库名称 | standalone 模式下创建新仓库 | `my-skill` |
| 公开/私有 | standalone 模式下有效 | `public` 或 `private` |

## 默认配置

```yaml
# 集合仓库（默认目标）
default_collection_repo: iris-YMY/hermes-skills

# 集合仓库结构
# hermes-skills/
# ├── skill-name-1/
# │   ├── SKILL.md
# │   ├── README.md
# │   └── ...
# └── skill-name-2/
#     └── ...
```

## 两种发布模式

**模式 A — 集合仓库（collection，推荐）**：
- 将 skill 推送到已有仓库的子目录
- 适合：统一管理多个 skill、私有收藏
- 默认仓库：`iris-YMY/hermes-skills`

**模式 B — 独立仓库（standalone）**：
- 为 skill 单独创建 GitHub 仓库
- 适合：开源单个 skill、独立分发
- 需要指定仓库名和公开/私有

## Pre-flight Checks（先做这个）

执行前必须确认：

```bash
# 1. 检查 gh CLI 登录状态
gh auth status

# 2. 如果未登录，检查是否有现成 token
grep -i "GITHUB\|GH_TOKEN\|ghp_" ~/.env ~/.claude/.env ~/.hermes/.env 2>/dev/null

# 3. 检查 git 配置
git config user.name
git config user.email
```

**如果要查看有哪些用户自建 Skill 可以发布**：

```bash
python3 ~/.hermes/skills/github/publish-skill-to-github/scripts/list-user-skills.py
```

这个脚本会对比 `.bundled_manifest`，列出所有用户自建/定制的 Skill（按分类），方便选择发布目标。

**如果 gh auth status 显示未登录：**
- 搜索上述 env 文件中的 `ghp_*` 或 `github_pat_*` 格式的 token
- 如果找不到，需要引导用户去 GitHub 网页创建新 token
- Token 创建路径：Settings → Developer settings → Personal access tokens → Tokens (classic)
- 必须勾选 `repo` 权限

## 执行步骤

### 1. 检查本地 skill 结构

确认目录包含：

- `SKILL.md` — skill 定义（必须）
- `README.md` — 使用说明（必须）
- `references/` — 参考资料（可选）
- `scripts/` — 辅助脚本（可选）
- `templates/` — 模板文件（可选）

### 2. 准备 GitHub 仓库

根据发布模式选择：

---

#### 模式 A — 集合仓库（collection）

将 skill 推送到已有仓库的子目录。

```bash
# 1. 克隆目标仓库（默认 iris-YMY/hermes-skills）
git clone https://<username>:<token>@github.com/<target-repo>.git /tmp/hermes-skills-push

# 2. 复制 skill 到子目录
cp -r <local-skill-path> /tmp/hermes-skills-push/<skill-name>/

# 3. 提交并推送
cd /tmp/hermes-skills-push
git add <skill-name>/
git commit -m "Add skill: <skill-name> v0.1.0"
git push origin main

# 4. 清理临时目录
rm -rf /tmp/hermes-skills-push
```

**如果目标仓库不存在**：提示用户先用 standalone 模式创建，或指定其他仓库。

---

#### 模式 B — 独立仓库（standalone）

为 skill 创建新的 GitHub 仓库。

**方式 B1 — gh CLI 一键创建：**

```bash
gh repo create <repo-name> --<public|private> --source=<local-skill-path> --push
```

**方式 B2 — 手动创建：**

```bash
cd <local-skill-path>
git init
git add .
git commit -m "Initial release: <skill-name> v0.1.0"
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

**无头服务器注意**：HTTPS push 需要 token 嵌入 URL：
```bash
git remote set-url origin https://<username>:<token>@github.com/<username>/<repo-name>.git
```

### 3. 完善仓库文档

确保 `README.md` 包含：

- Skill 定位（一句话说明解决什么问题）
- 安装方式（clone 到哪个目录）
- 使用示例（怎么对 agent 说）
- 依赖说明（API key、系统依赖等）

### 4. 添加安装脚本（推荐）

创建 `install_as_skill.sh`，自动化：

- 复制文件到 `~/.claude/skills/<skill-name>/`
- 安装 Python 依赖（如果有）
- 配置环境变量
- 软链 CLI 工具（如果有）

### 5. 验证

- 在新环境 clone 仓库
- 运行安装脚本
- 测试 skill 是否能被 agent 识别和使用

## 陷阱

- `.env` 文件**不要**提交，用 `.env.example` 代替
- `reports/`、`venv/`、`__pycache__/` 加入 `.gitignore`
- 如果 skill 依赖外部 API，在 README 说明如何申请 key
- 安装脚本要处理"目录已存在"的情况，提示用户是否覆盖
- **`gh auth login --with-token` 会因缺少 `read:org` 权限失败**（即使 `repo` 权限正常）。绕过方法：用 `export GH_TOKEN=...` 环境变量代替，`gh` 命令会自动读取
- **无头服务器上 `git push` HTTPS 无法弹出认证提示**，会直接 `fatal: could not read Username`。解决方案：将 token 嵌入 remote URL → `git remote set-url origin https://<username>:<token>@github.com/<username>/<repo>.git`
- Token 应持久化到 `~/.env` 中作为 `GH_TOKEN=...`，确保后续 session 可用
- **集合仓库 vs 独立仓库**：多个 skill 可放在同一个仓库中按目录组织（如 `hermes-skills/skill-name/`），无需每个 skill 一个仓库。创建集合仓库时先 `gh repo create` 再手动 init + push，不要用 `--source`（空目录会报错）
- **collection 模式 clone 大仓库慢**：如果集合仓库积累很多 skill，可用 `git clone --depth 1` 浅克隆加速
- **collection 模式推送前确认 skill 名称不冲突**：先检查目标仓库中是否已有同名目录，有则提示用户是"覆盖"还是"重命名"
- **skill 目录中的 scripts/ 可能有可执行权限**：git 会保留文件权限，`chmod +x` 后提交即可

## Troubleshooting

**gh auth status 显示未登录：**

1. 先搜索本地是否有现成 token：
   ```bash
   # 常见存储位置
   grep -i "GITHUB\|GH_TOKEN" ~/.env ~/.claude/.env ~/.hermes/.env ~/.config/gh/hosts.yml
   grep -h "ghp_\|github_pat_" ~/.git-credentials ~/.netrc 2>/dev/null
   ```

2. 如果找到 token（格式 `ghp_*` 或 `github_pat_*`）：
   ```bash
   echo "<token>" | gh auth login --with-token
   ```

3. 如果没找到，引导用户创建：
   - GitHub 网页 → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token → 勾选 `repo` 权限 → 复制 token
   - 执行：`echo "<token>" | gh auth login --with-token`

**git config 未配置：**
```bash
git config --global user.name "<用户名>"
git config --global user.email "<邮箱>"
```

## 检查清单

- [ ] 确认发布模式（collection / standalone）
- [ ] SKILL.md 和 README.md 存在且内容完整
- [ ] .gitignore 已配置
- [ ] .env.example 已创建（如有敏感依赖）
- [ ] **collection 模式**：skill 已推送到目标仓库子目录
- [ ] **standalone 模式**：独立仓库已创建并推送
- [ ] README 包含安装方式和使用示例
- [ ] install_as_skill.sh 可运行（如有）
- [ ] 在新环境验证通过

## 参考资料

- `references/github-beginner-guide.md` — GitHub 网页版入门速查（概念、界面、常见操作）
