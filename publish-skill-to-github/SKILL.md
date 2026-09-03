---
name: publish-skill-to-github
description: 将 Hermes Skill（或 skill 全家桶）发布到 GitHub 仓库（collection 模式推入已有仓库 / standalone 模式新建仓库）。含中国服务器（腾讯云）网络绕行（ghfast.top 镜像 clone+push 主路径）、更新前 diff 对比、体积裁剪、敏感信息扫描、推送后验证。触发词：发布 skill 到 github / skill 上传 github / 打包 skill 发 github / publish skill。
tags: [github, skill, publish, deploy]
triggers:
  - 发布 skill 到 github
  - skill 上传 github
  - 开源 skill
  - publish skill
---

# 发布 Skill 到 GitHub

## 触发
用户说"把 skill 发到 github / 打包发 github / publish skill"。

## 输入

| 参数 | 说明 | 示例 |
|------|------|------|
| 本地 skill 路径 | 必须 | `~/.hermes/skills/productivity/my-skill/` |
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
- 将 skill 推送到已有仓库的子目录（如 `hermes-skills/<skill-name>/` 或全家桶 `ppt-suite/`）
- 适合：统一管理多个 skill、私有收藏
- 默认仓库：`iris-YMY/hermes-skills`

**模式 B — 独立仓库（standalone）**：
- 为 skill 单独创建 GitHub 仓库
- 适合：开源单个 skill、独立分发
- 需要指定仓库名和公开/私有

## ⚠️ 核心认知（2026-09-03 实弹修订，解决"总是上传不成功"）

**直连 GitHub 的 git 传输（SSH 或 HTTPS）在腾讯云上不可靠**：`ssh -T git@github.com` 认证成功
≠ 能传大包（fetch/clone 报 `unexpected disconnect` / `early EOF`）；HTTPS 直连报 `GnuTLS recv error`。
**唯一稳定路径 = ghfast.top 镜像 remote：clone 和 push 都走它，一次成功。**

**主路径（推荐，2026-09-03 实测唯一成功路径）**：`ghfast.top clone --depth 1` 仓库 → 覆盖发布文件 →
commit → push（镜像 remote）。**不要**走"tarball 重建 + git init + fetch + reset --soft"——
那条路 fetch 会假成功/断连/超时，白耗 30 分钟（见陷阱）。

## Pre-flight Checks（先做这个）

执行前必须确认：

```bash
# 1. 检查 gh CLI 登录状态（standalone 模式需要）
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

**如果 gh auth status 显示未登录：**
- 搜索上述 env 文件中的 `ghp_*` 或 `github_pat_*` 格式的 token
- 如果找不到，需要引导用户去 GitHub 网页创建新 token
- Token 创建路径：Settings → Developer settings → Personal access tokens → Tokens (classic)
- 必须勾选 `repo` 权限
- ⚠️ `gh auth login --with-token` 缺 `read:org` 会失败；用 `export GH_TOKEN=...` 环境变量代替

## 执行步骤（collection 模式 · 主路径）

1. **clone 仓库**（镜像，自带 .git 历史，最稳）：
   ```bash
   export GH_TOKEN=$(grep GH_TOKEN ~/.env | cut -d= -f2)
   cd /tmp && rm -rf repo-push && \
   git clone --depth 1 "https://ghfast.top/https://github.com/<owner>/<repo>.git" repo-push
   # 实测：hermes-skills 8MB 秒下
   cd repo-push && git log --oneline -1   # 确认历史在（如 d720147 Add skill...）
   ```
   兜底（ghfast.top 不可用时）：API tarball `curl -sL -H "Authorization: Bearer $GH_TOKEN"
   "https://api.github.com/repos/<owner>/<repo>/tarball/main"` 解包（但后续需按"备选路径"对齐历史）。
   ⚠️ clone 后**立即确认 `.git` 存在且 `git log` 有输出**——网络差时 clone 会静默失败（exit=0 但目录空/无 .git）。

2. **推更新前先对比**（不是全量重推）：`diff -rq` 找出哪些子 skill 缺失/过期/新增，只动有差异的：
   ```bash
   diff -rq /tmp/repo-push/<suite>/<skill> ~/.hermes/skills/<path>/ 2>/dev/null | head -20
   # 核对单文件是否与上游一致用 blob sha：
   python3 -c "import hashlib,os; d=open('FILE','rb').read(); print(hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest())"
   # 与 GitHub API git/trees 返回的 sha 比对；相同 = 无需更新
   ```
   决策：文件级 diff 干净 = 只需更新有差异的子目录；本地独有/仓库缺失 = 新增；避免误推本地工作文件
   （如 projects/、__pycache__、19MB 参考图集——仓库若已裁剪过就保持裁剪，不同步大图）。
   ⚠️ **两版 SKILL.md 定位可能不同**（教学通用版 vs 实战精简版）：合并而非互覆——保留对方独有章节
   （教学版：输入表/Pre-flight/standalone/Troubleshooting/清单；实战版：ghfast 网络/腾讯云陷阱/主路径）。

3. **覆盖发布文件到 clone 目录**：
   ```bash
   # 更新已有 skill：直接替换子目录
   rm -rf /tmp/repo-push/<suite>/<skill> && cp -r ~/.hermes/skills/<path>/<skill> /tmp/repo-push/<suite>/<skill>
   # 新增 skill：整目录复制
   # ⚠️ 用 `cp -r <src>/. <dst>/` 或显式补隐藏文件——`cp -r <src>/*` 会漏 .gitignore/.env.example（2026-09 实测）
   # ⚠️ 若本地版缺仓库版已有辅助文件（README/references/scripts），先备份再合并，勿整目录覆盖丢文件
   ```

4. **体积裁剪**（大 skill 必做）：
   - 示例图/参考图：Pillow 压成 JPG（`resize(1200)` + quality=85），35M→~650K
   - 可选参考 PNG 图集：仅留 README 说明，正文注明"完整图集按需可补"
   - 清理 `__pycache__`/`*.pyc`/`.DS_Store`/`.git`/`projects/`
   - 裁剪后 `du -sh` 确认（lieflat-charts 20M→1.5M 去掉 docs/assets 预览图即可，运行不依赖）

5. **敏感扫描**（推送前必做）：
   ```bash
   grep -rn -i -E "sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}" --include="*.py" --include="*.md" --include="*.yaml" <dir>
   ```
   `.env.example` 只允许占位符（`your-xxx-key`）。⚠️ 复杂 grep 管道可能触发 agent 命令拦截，
   用 search_files 工具分目录查（pattern: `sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}`，output_mode=files_only）。

6. **git add + commit + push**（clone 目录自带历史，无需 fetch/reset）：
   ```bash
   cd /tmp/repo-push
   git config user.name "iris-YMY" && git config user.email "ymy_iris@163.com"
   git add <suite>/<skill> 或 git add .          # 只加有差异的；检查 status 无意外文件
   git status --short | awk '{print $1}' | sort | uniq -c   # 应只见 M <suite>/<skill>/... A 新增
   git commit -m "Add skill: <name> vX (或 Update ...)"
   git remote set-url origin "https://ghfast.top/https://github.com/<owner>/<repo>.git"
   git push origin main        # 输出形如 To https://ghfast.top/... d720147..3851c53 main -> main
   ```
   ⚠️ commit 前 `git status --short` 检查**没有意外大文件/敏感文件被 add**（如 19MB 图集）。

7. **验证**（推送后必做，勿只信 push 输出）：
   ```bash
   curl -s -H "Authorization: Bearer $GH_TOKEN" \
     "https://api.github.com/repos/<owner>/<repo>/commits?per_page=1" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['sha'][:12], d[0]['commit']['message'][:60])"
   curl -s -H "Authorization: Bearer $GH_TOKEN" \
     "https://api.github.com/repos/<owner>/<repo>/contents/<skill-name>" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d),'files'); [print(' ',i['name']) for i in d[:5]]"
   ```
   API 验证 sha 匹配本地 commit、目录文件数正确 = 真成功。

## 执行步骤（standalone 模式）

**方式 B1 — gh CLI 一键创建：**
```bash
gh repo create <repo-name> --<public|private> --source=<local-skill-path> --push
```

**方式 B2 — 手动创建：**
```bash
cd <local-skill-path>
git init && git add . && git commit -m "Initial release: <skill-name> v0.1.0"
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```
**无头服务器注意**：HTTPS push 需要 token 嵌入 URL：
```bash
git remote set-url origin https://<username>:<token>@github.com/<username>/<repo-name>.git
# 或腾讯云直接改用 ghfast 镜像 remote（见主路径），直连 HTTPS 会 GnuTLS 断连
```

## 备选路径（ghfast.top 不可用时；尽量别走，耗时且易失败）

tarball 重建仓库后本地无 .git 历史，直接 push 会被拒（历史分叉）。需对齐远程：
```bash
cd /tmp/repo-push && git init && git checkout -b main
git remote add origin "https://ghfast.top/https://github.com/<owner>/<repo>.git"
timeout 120 git fetch origin main
# ⚠️ fetch 后必须验证：git cat-file -t <remote-sha> 能返回 commit 才说明对象真入库；
#    exit=0 但 FETCH_HEAD 空 / objects 只有 tmp_pack = 假成功（见陷阱）
git reset --soft origin/main && git add . && git commit -m "..." && git push origin main
```

## 中国服务器网络要点（腾讯云实测，2026-09 修订）

- **下载/推送仓库一律走 ghfast.top 镜像**：
  - 下载 tarball：`https://ghfast.top/https://github.com/<owner>/<repo>/archive/refs/heads/main.tar.gz`（8–18MB 秒下）
  - git remote：`https://ghfast.top/https://github.com/<owner>/<repo>.git`（clone + push 都通）
  - 此镜像对任何 GitHub 仓库通用，也用于升级上游 skill（如 lieflat-charts 18MB 秒下）
- ⚠️ **SSH remote 并不比 HTTPS 可靠（2026-09 实测推翻旧建议）**：认证成功 ≠ 能传大包——fetch/clone 会
  `unexpected disconnect while reading sideband packet` / `fatal: early EOF`。HTTPS 直连报 `GnuTLS recv error`。
  **传输一律走 ghfast.top 镜像 remote，别在 SSH/HTTPS 直连上反复重试。**
- ⚠️ **git fetch 可能静默假成功**：exit=0 但 `FETCH_HEAD` 空（0 字节）、objects 里只有 `tmp_pack_*` 垃圾文件
  （`git count-objects -v` 见 garbage）→ 对象没入库。验证：`git cat-file -t <remote-sha>`；失败则清
  `rm -f .git/objects/pack/tmp_pack_*` 重试，或直接改走 ghfast.top clone（`--depth 1` 最稳）。
- api.github.com + GH_TOKEN：稳定可用（REST/raw 单文件读取、推送后验证都走它；匿名对私有仓库 404=存在但无权限）
- git:// 协议只读可用，不支持 push

## 多 skill 全家桶打包（用户 2026-08-17 确认的形态）
- 一个逻辑全家桶 = 仓库单个目录（如 `ppt-suite/`），内含 `SKILL.md`（统一入口/路由）+ `README.md`（总览+路由图+安装说明）+ 各子 skill 子目录
- 物理不强行合并：生产引擎类 skill（含大量相互引用脚本）保持独立子目录，避免破坏内部路径引用
- 安装给别的 agent：`cp -r <repo>/<suite>/ ~/.hermes/skills/productivity/<suite>/` 一步到位

## 陷阱（全部实测）
- ⚠️ **主路径 = ghfast clone 直接覆盖 push；tarball 重建 + fetch + reset --soft 是备选且易假成功**——别按旧文档走 fetch 路径白耗时间
- tarball 重建仓库后**不要直接 `git init && commit && push`**（历史分叉必被拒）——必须 clone 或先 fetch 对齐
- push 输出可能为空或只有 `To github.com...`，以 API 验证为准
- 大文件（>100MB）git 会拒；发布前先裁剪；**仓库已裁剪的目录保持裁剪**，不同步本地大图集（如 19MB ai-image-comparison）
- ⚠️ **`cp -r <src>/* <dst>/` 会漏掉隐藏文件**（.gitignore/.env.example 等，2026-09 实测）：用 `cp -r <src>/. <dst>/` 或显式补
- 仓库里某 skill 版本旧于本地时，直接覆盖该子目录推送即可（`git add <suite>/<skill>` 只推变更文件，不碰其他 skill）
- `.env` 文件**不要**提交，用 `.env.example` 代替；`reports/`、`venv/`、`__pycache__/` 加入 `.gitignore`
- **collection 模式推送前确认 skill 名称不冲突**：先检查目标仓库中是否已有同名目录，有则提示用户是"覆盖"还是"重命名"
- skill 目录中的 scripts/ 可能有可执行权限：git 会保留文件权限，`chmod +x` 后提交即可
- 用户对网页版 GitHub 不熟，交付时给链接 + 简单说明

## Troubleshooting

**gh auth status 显示未登录：**
1. 先搜索本地是否有现成 token：`grep -i "GITHUB\|GH_TOKEN" ~/.env ~/.claude/.env ~/.hermes/.env ~/.config/gh/hosts.yml`
2. 如果找到 token（格式 `ghp_*` 或 `github_pat_*`）：`echo "<token>" | gh auth login --with-token`
3. 如果没找到，引导用户创建（GitHub 网页 → Settings → Developer settings → Personal access tokens → Tokens (classic) → 勾选 `repo`）
4. ⚠️ `gh auth login --with-token` 缺 `read:org` 会失败 → 用 `export GH_TOKEN=...` 环境变量代替

**git fetch/push 反复失败（腾讯云）：**
1. 别在 SSH/HTTPS 直连上重试——直接改走 ghfast.top 镜像 clone（`--depth 1`）+ push
2. 若已 tarball 重建且 fetch 假成功（exit=0 但 FETCH_HEAD 空）：`rm -f .git/objects/pack/tmp_pack_*` 后重试，或重 clone

**git config 未配置：**
```bash
git config --global user.name "<用户名>"
git config --global user.email "<邮箱>"
```

## 检查清单
- [ ] 确认发布模式（collection / standalone）
- [ ] SKILL.md 和 README.md 存在且内容完整
- [ ] 更新前已 `diff -rq` 对比，只推有差异的子目录
- [ ] 两版定位不同时已合并（教学通用版 + 实战 ghfast 版），未互覆丢章节
- [ ] .gitignore 已配置；隐藏文件已用 `cp -r <src>/.` 带上
- [ ] .env.example 已创建（如有敏感依赖）
- [ ] 大文件/图集已裁剪，本地工作文件（projects/缓存）未误 add
- [ ] 敏感扫描通过（search_files 查 sk-/ghp_ 无命中）
- [ ] push 后 API 验证：commit sha 匹配 + 目录文件数正确
- [ ] 新环境验证通过（standalone 模式）

## 参考资料
- `references/github-beginner-guide.md` — GitHub 网页版入门速查（概念、界面、常见操作）
