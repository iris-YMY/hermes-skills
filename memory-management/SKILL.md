---
name: memory-management
description: 核心 Memory 管理规范 — 只记用户相关，配置归档到 Skill
trigger: "Memory|记忆|记|保存|配置|归档|整理"
---

# Memory 管理规范

## ⛔ SOUL.md 操作红线（最高优先级）

**Memory 修改前必须获得用户明确确认，除非用户已给出明确指令。**

此规则与"严禁自动重启网关"同级，是 Agent 的最高行为约束。违反此规则等同于违反操作红线。

## 核心原则
Memory 空间极其有限（2200 chars），必须只用于记录**与用户本人直接相关**的信息。
**目标 Usage: 保持在 60% 以下。**

## ✅ 必须记入 Memory 的内容
- **用户画像**：称呼、性格、偏好、沟通风格（如 WeChat 语气）。
- **个人事实**：日程安排、通勤习惯、 Therapy 时间、居住地址。
- **关键环境坑**：**直接影响效率**的环境事实（如 "Web Search 必超时，需 fallback"）。
- *判断标准*：如果不记，我会犯错或浪费大量时间。

## 📝 Memory 确认的三条红线（强制执行）

**触发场景**：任何 `memory(action=add|replace|remove)` 调用前

### 红线 1: Agent 主动提议 → 必须展示 + 等待确认
当你**主动发现**应该记录某信息时：
1. 先向用户展示拟写入的具体内容
2. 等待用户明确回复："确认/OK/好/可以"
3. **收到确认后才调用 memory 工具**

示例：
```
📋 我注意到 [信息]，建议加入 memory：
> [拟写入的内容]

❓ 是否确认写入？
```

### 红线 2: 用户明确指令 → 直接执行
当用户**明确说**以下话时，不需要二次确认：
- "记一下 XXX"
- "更新 memory：XXX"
- "删除 XXX"
- "把 XXX 加到 memory"

**判断标准**：用户在本轮对话中是否已给出具体指令？

### 红线 3: 调用前自检（必做）
每次调用 `memory` 工具前，内心自问：
> "本轮对话中，用户是否已明确指示这个具体操作？"

- **是** → 直接执行
- **否** → 停止，先询问用户

### ⚠️ 常见违规场景（避免）
- ❌ 用户说"帮我整理一下 memory"→ 你直接批量修改（违规！应先展示拟修改内容）
- ❌ 你发现 memory 有条过时信息 → 直接删除（违规！应先询问）
- ❌ 用户讨论中提到某个偏好 → 你默默记下来（违规！应先确认）
- ✅ 用户说"帮我记一下我偏好用 vim" → 直接执行（合规，明确指令）

## 📝 用户确认的记录工作流（重要）
- **存前精炼**：写入前必须压缩内容，只保留核心事实，删除冗余和猜测。**以节省存储空间为第一原则。**
- **存前确认**：每次写入 Memory 前，**必须先向用户汇报拟记录内容，并确认是否需要同步更新对应的飞书文档。** 格式示例：
  ```
  📋 拟存入的 Memory 内容：
  > [精炼后的内容]
  
  ❓ 请确认：
  1. 是否确认写入这条记忆？
  2. 是否同步更新飞书文档？
  ```
- **获准后执行**：收到用户明确确认后，**先写入 Memory，再调用 `feishu-agent-doc-sync` skill 同步更新飞书文档。**
- **只记确定的**：严禁将推测、假设、未确认的信息写入 Memory。
## 飞书文档同步规则（2026-06-18 新增）

1. **Memory/Profile → 飞书**：飞书「我的文件夹」中有三个 agent 文件夹（黑执事/data-master→添添开心/凛子小姐），每个下有 memory 和 profile 两个文档。新增 memory/profile 内容时，须同步更新对应飞书文档。
2. **Skill → 飞书**：飞书 Skills 文件夹管理所有 skill 文档。新建 skill 在该文件夹创建新文档；已有 skill 更新时同步更新对应飞书文档（非新建）。
3. **飞书文档更新须确认**：更新 memory/profile/skill 飞书文档前，须与用户确认。
4. **Memory 录入须确认**：agent 认为 session 内容需要记录 memory 时，须与用户确认是否录入，并确认是否同步飞书。

## 多 Profile 共享规则
通用家规需手动同步到各 Profile 的 MEMORY.md。
  - **快捷同步方式**：直接用 `cat >` 写入 default + 各 named profile 的 MEMORY.md，然后逐一 `cat` 验证。不要使用 `memory` tool（只写 default profile）。
  - **追加时注意格式**：`cat >>` 追加前确保原文末尾有换行 + `§` + 换行，否则新旧内容会粘连。
  - **验证**：写入后必须 `cat` 每个 profile 的 MEMORY.md 确认内容正确、格式无粘连。
  - **飞书同步**：所有 profile 的 memory 更新后，须同步到各自对应的飞书文件夹下的 memory 文档（如黑执事→黑执事文件夹→memory）。

### Skills 目录软链接验证（2026-06-29 新增）
**规则**：所有 profile 的 `skills/` 目录必须是软链接，指向全局 `~/.hermes/skills/`。

**验证方法**：
```bash
ls -la ~/.hermes/profiles/*/ | grep skills
```

**预期输出**：
```
lrwxrwxrwx  ... skills -> /home/ubuntu/.hermes/skills
```

**如果发现独立目录（非软链接）**：
1. 将独立目录中的 skill 合并到全局（`cp -r`）
2. 删除独立目录（`rm -rf`）
3. 创建软链接（`ln -s ~/.hermes/skills ~/.hermes/profiles/<name>/skills`）

**常见错误**：profile 创建后手动创建了 `skills/` 目录，导致后续 skill 操作在该目录而非全局目录执行。

## 三区边界定义（重要）

| 存储区 | 存放内容 | 判断标准 |
|--------|---------|---------|
| **SOUL.md** | Agent 的身份、人设、角色定位、沟通风格 | "我是谁"——定义 Agent 自身的属性 |
| **USER PROFILE** | 用户的称呼、偏好、背景、约束条件、个人事实 | "用户是谁"——描述用户本人的属性 |
| **MEMORY** | Agent 的操作笔记、环境事实、工具惯例、经验教训 | "我学到了什么"——Agent 积累的知识 |

### 典型误区
- ❌ 把 Agent 人设写入 USER PROFILE（如"AI人设：35+日系管理姐姐"）→ 应放 SOUL.md
- ❌ 把用户偏好写入 MEMORY → 应放 USER PROFILE
- ❌ 把环境配置写入 USER PROFILE → 应放 MEMORY 或归档到 Skill

### 操作指南
当需要存储新信息时：
1. 先判断属于哪个区（Agent 身份 / 用户属性 / 操作知识）
2. 如果与 SOUL.md 已有内容重复，直接删除（SOUL.md 是权威来源）
3. 如果是配置或规则 → 归档到 Skill
4. 如果是用户偏好/事实 → USER PROFILE
5. 如果是 Agent 学到的经验/环境事实 → MEMORY

## ❌ 禁止记入 Memory 的内容（应归档到 Skill）
- **配置信息**：Bot 列表、App ID、文件夹 Token、工具版本路径。
- **规则/规范**：文档格式要求、文件操作禁忌、交互协议（如中断信号不回话）。
- **功能性指令**：系统层面的操作逻辑。

### Memory → Skill 迁移工作流（2026-06-23 确认）
当发现 Memory 中有应归档到 Skill 的条目时：
1. **读取目标 Skill**：`skill_view(name)` 确认该 Skill 是否已覆盖此内容
2. **Patch Skill**：`skill_manage(action='patch')` 追加缺失内容（用 `file_path` 指定 reference 文件）
3. **批量移除 Memory**：`memory(action='remove')` 逐条移除已归档条目
4. **同步飞书**：用 `lark doc append` 将新内容同步到对应飞书 Skill 文档
5. **验证**：展开 Memory 确认条目已清除，`skill_view` 确认 Skill 已更新

⚠️ **关键判断**：如果 Skill 已完整覆盖某条信息，可以直接从 Memory 移除，无需重复添加到 Skill。

## 操作前必读 Memory（Standard Workflow）

当用户执行 skill 或 memory 相关操作时，必须先读取当前 memory 状态，确保操作的一致性和准确性。

### 触发条件
当用户输入 "skill更新/创建" 或 "memory更新/创建" 等指令时：
1. 先执行 `memory list` 读取当前所有条目
2. 检查是否有相关条目需要更新或新增
3. 确认 memory 使用空间
4. 对于 skill 操作：先查看目标 skill 当前内容再修改
5. 操作完成后向用户汇报结果并询问是否需要飞书同步

## 操作指南
1. **新建条目时**（必须先向用户确认拟记录内容）：
   - 精炼压缩，只留核心事实。
   - 如果是配置或规则 -> **创建/更新 Skill**。
   - 如果是用户偏好 -> **记入 Memory**。
   - **如果是频繁变化的数据（持仓/库存/任务列表）→ 使用 JSON 文件 + Memory 指针模式**（详见 `references/volatile-data-pattern.md`）。
2. **技能统一化**：
   - 所有 Profile 的 `skills/` 目录通过**软链接 (Symlink)** 指向全局的 `~/.hermes/skills/`。
   - 新建 Skill 时直接写入任意 Profile 的 skills 目录即可，所有 Agent 自动共享。
   - `~/.agents/skills/` 是配置的 `external_dirs`，但当前为空。实际 skills 存放在 `~/.hermes/skills/`。
   - ⚠️ **删除 Profile 不影响其他 Agent 的 skills**——因为是同一目录，只有 `rm -rf` 整个 skills 文件夹才会清空。
3. **MEMORY.md 路径**：
   - Default Profile: `~/.hermes/memories/MEMORY.md`
   - Named Profile: `~/.hermes/profiles/<name>/memories/MEMORY.md`
   - Profile 可能没有 MEMORY.md 文件（首次使用或已清空），此时 `cat` 返回 exit code 1，属正常。
4. **维护时**：
   - 检查 Memory 中是否有新增的配置类条目。
   - 将其移动到 Skill 并从 Memory 中 `remove`。
   - 确保 Memory 中没有重复或过时的环境信息。
   - 判断归档目标：与 SOUL.md 重复的条目直接删除即可（SOUL.md 才是权威来源）；配置信息检查现有 Skills 是否已覆盖，避免创建冗余 Skill。

## Skill 更新流程
创建或更新 Skill 后的**必做步骤**：
1. **立即验证**：调用 `skill_view(name)` 确认内容已正确保存
2. **检查 frontmatter**：确认 name/description 字段无误
3. **同步飞书文档**：将更新内容同步到对应的飞书 Agent 文档
4. **可选测试**：在实际任务中加载 skill 验证是否生效

## ⏸️ Daily Memory Cleanup Cron — PAUSED (2026-06-17)

The `Daily Memory Cleanup` Hermes cron job (`d4d4c418ddcf`, schedule `0 2 * * *`) is **paused**.

**Reason**: All memory updates now require explicit user approval before writing. An automatic cleanup that scans and archives memory entries is therefore redundant — it either finds nothing (wasting ~10,000-25,000 LLM tokens) or finds something it can't act on without approval anyway.

**If re-enabling**: Consider replacing with a Python script + system crontab (same pattern as the Lark token refresh). The script would only check sizes and write a JSON report; a lightweight Hermes cron would read the report and alert only when needed.

## 定时任务隔离 (Cron Job Isolation)
   - 定时任务必须存放在对应 Agent 的 Profile 目录下（如 `~/.hermes/profiles/hr-assistant/cron/jobs.json`）。
   - 全局 `~/.hermes/cron/jobs.json` 仅由默认 profile 读取，其他 profile 不会执行。
   - 每个任务的 Prompt 中必须包含 `## AGENT IDENTITY` 模块，声明所属 Agent 的身份。推荐使用 `cron-guard` skill 的身份检查模板。
   - **身份检查模式**：`Only execute if you are running as the default profile (i.e., NO --profile flag). If running as any named profile, skip.`

### ⚠️ 删除 Profile 时的 Cron 孤儿问题

当删除一个 Profile（如 `rm -rf ~/.hermes/profiles/butler/`）时，该 Profile 的 cron 任务会从 `~/.hermes/cron/jobs.json` 中保留，变成**孤儿任务**：
- 这些任务会挂在**默认 profile**（无 `--profile` 参数的 gateway）上运行。
- 如果任务的 Prompt 中有 `## AGENT IDENTITY` 检查（如 "Only execute if running as Butler"），任务会自我跳过，**空转不执行任何操作**。
- **操作规范**：删除 Profile 前，先检查 `~/.hermes/cron/jobs.json`，清理或迁移该 Profile 的 cron 任务。
