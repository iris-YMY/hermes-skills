# TODO Reminder System — CRUD & Architecture

> Absorbed from `todo-reminder-system` skill (2026-07-06 consolidation)

## 核心架构

| 组件 | 路径 | 作用 |
|------|------|------|
| `todo_manager.py` | `~/.hermes/scripts/todo_manager.py` | 持久化 CRUD，数据存 `/home/ubuntu/.hermes/todo.json`（绝对路径） |
| Hermes cron job | `443e0b7686ce` | 黑执事专属，工作日 10:30 自动播报（卡片模式） |
| Card sender | `~/.hermes/scripts/todo_card_sender.py` | 飞书卡片发送脚本 |

### ⚠️ 路径陷阱（2026-06-29 修复）
`todo_manager.py` 必须使用**绝对路径** `/home/ubuntu/.hermes/todo.json`，而非 `Path.home() / ".hermes" / "todo.json"`。

**原因**：Named profile 的 `Path.home()` 会解析到 `~/.hermes/profiles/<name>/home/`，导致每个 profile 创建独立的 todo.json，数据分散。

### 架构分离
- **CRUD 功能**：所有 profile 共享，读写全局 `todo.json`
- **播报功能**：仅黑执事的 Hermes cron job 负责（每工作日 10:30）

## 使用方式

### 添加任务
```bash
python3 ~/.hermes/scripts/todo_manager.py add "任务内容"
python3 ~/.hermes/scripts/todo_manager.py add "任务内容" --due 2026-07-01
python3 ~/.hermes/scripts/todo_manager.py add "任务内容" --priority high
```

### 查看/完成/删除/编辑
```bash
python3 ~/.hermes/scripts/todo_manager.py list          # 未完成
python3 ~/.hermes/scripts/todo_manager.py list --all    # 全部
python3 ~/.hermes/scripts/todo_manager.py complete 3
python3 ~/.hermes/scripts/todo_manager.py delete 3
python3 ~/.hermes/scripts/todo_manager.py edit 3 --content "新内容"
python3 ~/.hermes/scripts/todo_manager.py edit 3 --priority high
python3 ~/.hermes/scripts/todo_manager.py edit 3 --due 2026-07-15
```

## 数据格式

`/home/ubuntu/.hermes/todo.json` 结构：
```json
[
  {
    "id": "1",
    "content": "提交周报",
    "status": "pending",
    "priority": "high",
    "due": "2026-07-01",
    "created_at": "2026-06-26T10:30:00",
    "completed_at": null
  }
]
```

## ⛔ 双系统陷阱（CONFIRMED 2026-07-20）

**Hermes 内置 `todo` 工具和 `~/.hermes/todo.json` 是两套完全独立的系统！**

| 系统 | 入口 | 数据存储 | 用途 |
|------|------|---------|------|
| 内置 `todo` 工具 | `todo()` 函数调用 | Hermes 内部状态 | 临时任务（经常为空） |
| 文件 `todo.json` | `~/.hermes/todo.json` | 磁盘文件 | **持久化待办 + cron 播报数据源** |

**事故回放**：用户说"打开todo"，agent 调用内置 `todo` 工具 → 返回空 → 用户说"今天早上还播报了"。实际待办数据在 `todo.json` 文件中（8项），内置工具完全不知道。

**铁律**：
- ❌ **禁止**使用内置 `todo` 工具查看/操作待办（数据不互通）
- ✅ **必须**读写 `~/.hermes/todo.json` 文件（用 `execute_code` 或 `todo_manager.py`）
- ✅ 查看待办：`read_file(path="/home/ubuntu/.hermes/todo.json")` 或 `todo_manager.py list`
- ✅ 添加待办：`execute_code` 操作 JSON 或 `todo_manager.py add`
- ✅ 标记完成：`execute_code` 修改 status 字段或 `todo_manager.py complete`

## Agent 交互规范

当用户说"记个 todo"、"帮我记一下"、"加个任务"等：
1. 调用 `terminal` 执行 `python3 ~/.hermes/scripts/todo_manager.py add "内容"`
2. 如果用户指定了截止日期或优先级，加上 `--due` 和 `--priority` 参数
3. 向用户确认已记录

当用户说"打开todo"、"看看待办"、"todo列表"等：
1. 使用 `read_file(path="/home/ubuntu/.hermes/todo.json")` 或 `execute_code` 读取 JSON
2. **不要**调用内置 `todo` 工具

## 验证方法
```bash
# 检查是否存在多个 todo.json（应该只有全局那一个）
find ~/.hermes -name "todo.json" -type f
```
