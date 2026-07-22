#!/usr/bin/env python3
"""Sync agent Profile/Memory to Feishu docs.

Compares local source files with Feishu docs, appends only new content.
Usage: python3 sync_feishu_docs.py [--dry-run]

Rules:
- Appends to existing docs, never creates new ones
- Skips if Feishu already contains the content
- Adds timestamp header to each update
- Saves tokens by only syncing what changed
"""

import subprocess, json, os, sys, glob
from datetime import datetime
from pathlib import Path

DRY_RUN = "--dry-run" in sys.argv
SYNC_SKILLS = "--skills" in sys.argv
SKILLS_FOLDER = "/home/ubuntu/.hermes/skills"
SKILLS_FEISHU_FOLDER = "PdkOfBF0nlUKlkdVABZcYuKFneh"

# 内置 Skill 名称列表（Hermes 安装时自带，2026-05-06 批次）
# 不在此列表中的 skill 视为用户自建型，需要自动同步到飞书
BUILTIN_SKILLS = {
    # autonomous-ai-agents
    "claude-code", "codex", "opencode",
    # creative
    "architecture-diagram", "ascii-art", "ascii-video", "baoyu-comic", "baoyu-infographic",
    "claude-design", "comfyui", "creative-ideation", "design-md", "excalidraw",
    "humanizer", "manim-video", "p5js", "pixel-art", "popular-web-designs",
    "pretext", "sketch", "songwriting-and-ai-music", "touchdesigner-mcp",
    # data-science
    "jupyter-live-kernel",
    # devops
    "webhook-subscriptions",
    # dogfood
    "dogfood",
    # email
    "himalaya",
    # gaming
    "minecraft-modpack-server", "pokemon-player",
    # github
    "codebase-inspection", "github-auth", "github-code-review",
    "github-issues", "github-pr-workflow", "github-repo-management",
    # mcp
    "native-mcp",
    # media
    "gif-search", "heartmula", "songsee", "spotify", "youtube-content",
    # mlops
    "huggingface-hub",
    # mlops/evaluation
    "lm-evaluation-harness", "weights-and-biases",
    # mlops/inference
    "llama-cpp", "obliteratus", "outlines", "vllm",
    # mlops/models
    "audiocraft", "segment-anything",
    # mlops/research
    "dspy",
    # mlops/training
    "axolotl", "trl-fine-tuning", "unsloth",
    # note-taking
    "obsidian",
    # productivity (built-in)
    "airtable", "google-workspace", "linear", "maps", "nano-pdf",
    "notion", "ocr-and-documents", "powerpoint",
    # red-teaming
    "godmode",
    # research
    "arxiv", "blogwatcher", "llm-wiki", "polymarket",
    "research-paper-writing", "web-search",
    # smart-home
    "openhue",
    # social-media
    "xurl",
    # software-development
    "debugging-hermes-tui-commands", "hermes-agent-skill-authoring",
    "node-inspect-debugger", "plan", "python-debugpy",
    "requesting-code-review", "spike", "subagent-driven-development",
    "systematic-debugging", "test-driven-development", "writing-plans",
    # apple (built-in)
    "apple-notes", "apple-reminders", "findmy", "imessage",
    # skills (built-in)
    "yuanbao",
}

# Doc mapping (v3)
DOCS = {
    "黑执事 Profile": {
        "doc_id": "LQbndYO2vowyN3xSAPNcJc6Vnyg",
        "source": "SYSTEM_PROMPT",  # No local file
        "type": "profile",
    },
    "黑执事 Memory": {
        "doc_id": "It9EdxZPdom9G0xV1s6csOh9nLb",
        "source": "memories",
        "paths": [
            "/home/ubuntu/.hermes/memories/MEMORY.md",
            "/home/ubuntu/.hermes/memories/USER.md",
        ],
        "type": "memory",
    },
    "凛子小姐 Profile": {
        "doc_id": "Z7nadOQNnoVlzQxgBkEcq6BznMc",
        "source": "file",
        "paths": ["/home/ubuntu/.hermes/profiles/hr-assistant/SOUL.md"],
        "type": "profile",
    },
    "凛子小姐 Memory": {
        "doc_id": "THxNdml89olQ5bxPXaAcvnESnne",
        "source": "memories",
        "paths": [
            "/home/ubuntu/.hermes/profiles/hr-assistant/memories/MEMORY.md",
            "/home/ubuntu/.hermes/profiles/hr-assistant/memories/USER.md",
        ],
        "type": "memory",
    },
    "数据大师 Profile": {
        "doc_id": "UX7gd3x6qoVnJGxuN1LcGItknTb",
        "source": "file",
        "paths": ["/home/ubuntu/.hermes/profiles/data-master/SOUL.md"],
        "type": "profile",
    },
    "数据大师 Memory": {
        "doc_id": "Q7YHdPDCCo82DExU0PRciA1gnff",
        "source": "memories",
        "paths": [
            "/home/ubuntu/.hermes/profiles/data-master/memories/MEMORY.md",
            "/home/ubuntu/.hermes/profiles/data-master/memories/USER.md",
        ],
        "type": "memory",
    },
}


def read_feishu(doc_id: str) -> str:
    """Get current Feishu doc content via lark-cli."""
    r = subprocess.run(["lark", "doc", "get", doc_id], capture_output=True, text=True)
    data = json.loads(r.stdout)
    return data.get("content", "")


def read_local(name: str, config: dict) -> str:
    """Read local source content."""
    src = config["source"]
    if src == "SYSTEM_PROMPT":
        # 黑执事 profile 来自系统 prompt，无法本地读取
        return "[系统设定，无本地文件]"
    if src == "empty":
        return "（暂无记忆条目）"
    parts = []
    for path in config.get("paths", []):
        if os.path.exists(path):
            content = open(path).read().strip()
            if content:
                # 纯文本化处理，避免 Markdown 转义符污染飞书文档
                clean_content = to_plain_text(content)
                parts.append(f"{os.path.basename(path).replace('.md', '')}：\n{clean_content}")
    return "\n\n---\n\n".join(parts) if parts else "（文件为空）"


def to_plain_text(md_text: str) -> str:
    """Convert markdown content to plain text for Feishu docs."""
    import re
    # Remove headers (# Title)
    text = re.sub(r'^#+\s+', '', md_text, flags=re.MULTILINE)
    # Remove bold/italic (*text*, **text**, _text_)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Remove list markers (- Item, * Item) -> just Item, maybe keep indentation
    text = re.sub(r'^(\s*)[-*]\s+', r'\1', text, flags=re.MULTILINE)
    # Remove code blocks (```code```)
    text = re.sub(r'```.+?```', '', text, flags=re.DOTALL)
    # Remove links [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text.strip()

def normalize(text: str) -> str:
    """Strip Feishu markdown escapes for comparison."""
    return (
        text.replace("\\#", "#")
        .replace("\\*", "*")
        .replace("\\-", "-")
        .replace("\\.", ".")
        .replace("\\_\\", "_")
        .replace("\\&#34;", '"')
        .replace("\\&amp;", "&")
        .strip()
    )


def needs_update(feishu_content: str, local_content: str) -> bool:
    """Check if Feishu doc is missing local content."""
    f = normalize(feishu_content)
    # Remove Feishu title line
    lines = f.split("\n")
    if lines and lines[0].startswith("# "):
        f = "\n".join(lines[1:]).strip()
    l = normalize(local_content)
    # Check if local content is already in Feishu
    # Use a fuzzy check: at least 80% of local chars present in Feishu
    if len(l) < 50:
        return False  # Skip tiny content
    match_ratio = sum(1 for c in l if c in f) / len(l)
    return match_ratio < 0.8


def append_to_feishu(doc_id: str, content: str) -> bool:
    """Append content to Feishu doc."""
    r = subprocess.run(
        ["lark", "doc", "append", doc_id, "--text", content],
        capture_output=True,
        text=True,
    )
    data = json.loads(r.stdout)
    return data.get("success", False)


def list_feishu_docs(folder_token: str) -> list:
    """List all docs in a Feishu folder, return [{name, token, type}]."""
    r = subprocess.run(["lark", "doc", "list", folder_token], capture_output=True, text=True)
    data = json.loads(r.stdout)
    result = []
    for item in data.get("items", []):
        result.append({
            "name": item.get("name", ""),
            "token": item.get("token", ""),
            "type": item.get("type", "docx"),
        })
    return result

def create_feishu_doc(title: str, folder_token: str, content: str) -> str:
    """Create a new Feishu doc and return document_id."""
    r = subprocess.run(
        ["lark", "doc", "create", "--title", title, "--folder", folder_token],
        capture_output=True, text=True
    )
    data = json.loads(r.stdout)
    doc_id = data.get("document_id", "")
    if doc_id:
        # Write initial content
        append_to_feishu(doc_id, content)
    return doc_id

def get_user_built_skills() -> set:
    """Discover user-built skills: all SKILL.md not in BUILTIN_SKILLS."""
    result = set()
    for root, dirs, files in os.walk(SKILLS_FOLDER):
        if ".archive" in root:
            continue
        if "SKILL.md" in files:
            skill_name = os.path.basename(root)
            if skill_name not in BUILTIN_SKILLS:
                result.add(skill_name)
    return result


def sync_skills():
    """Sync ONLY user-built SKILL.md to Feishu docs. Delete non-user-built."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    synced = 0
    skipped = 0
    errors = 0
    deleted = 0

    feishu_docs = list_feishu_docs(SKILLS_FEISHU_FOLDER)
    feishu_map = {d["name"]: d for d in feishu_docs}

    # Dynamically discover user-built skills
    user_built_skills = get_user_built_skills()

    # 1. Sync user-built skills
    for skill_name in sorted(user_built_skills):
        skill_path = None
        for root, dirs, files in os.walk(SKILLS_FOLDER):
            if skill_name in dirs and os.path.exists(os.path.join(root, skill_name, "SKILL.md")):
                skill_path = os.path.join(root, skill_name, "SKILL.md")
                break

        if not skill_path:
            print(f"⚠️  {skill_name}: SKILL.md 未找到")
            continue

        local_content = open(skill_path).read().strip()
        if not local_content:
            print(f"⏭️  {skill_name}: SKILL.md 为空，跳过")
            skipped += 1
            continue

        doc_title = skill_name.replace("-", " ").replace("_", " ").title()

        if doc_title in feishu_map:
            doc_token = feishu_map[doc_title]["token"]
            doc_type = feishu_map[doc_title]["type"]
            feishu_content = read_feishu(doc_token)
            if not needs_update(feishu_content, local_content):
                print(f"⏭️  {skill_name}: 已同步，跳过")
                skipped += 1
                continue

            update_text = f"\n\n### 🔄 更新于 {now}\n\n{local_content}\n"
            if DRY_RUN:
                print(f"🔍 [dry-run] {skill_name}: 会追加 {len(update_text)} chars")
                continue

            ok = append_to_feishu(doc_token, update_text)
            if ok:
                print(f"✅ {skill_name}: 已追加更新 {len(update_text)} chars")
                synced += 1
            else:
                print(f"❌ {skill_name}: 追加失败")
                errors += 1
        else:
            if DRY_RUN:
                print(f"🔍 [dry-run] {skill_name}: 会创建新文档 '{doc_title}'")
                continue

            doc_token = create_feishu_doc(doc_title, SKILLS_FEISHU_FOLDER, local_content)
            if doc_token:
                print(f"🆕 {skill_name}: 已创建飞书文档 '{doc_title}' (token: {doc_token})")
                synced += 1
            else:
                print(f"❌ {skill_name}: 创建文档失败")
                errors += 1

    # 2. Delete non-user-built skill docs from Feishu
    for doc in feishu_docs:
        doc_title = doc["name"]
        doc_token = doc["token"]
        doc_type = doc["type"]
        possible_name = doc_title.lower().replace(" ", "-")
        possible_name2 = doc_title.lower().replace(" ", "_")
        if possible_name not in user_built_skills and possible_name2 not in user_built_skills:
            if DRY_RUN:
                print(f"🗑️  [dry-run] 会删除非自建文档: '{doc_title}' ({doc_token})")
            else:
                ok = delete_feishu_doc(doc_token, doc_type)
                if ok:
                    print(f"🗑️  已删除非自建文档: '{doc_title}'")
                    deleted += 1
                else:
                    print(f"❌ 删除失败: '{doc_title}'")
                    errors += 1

    return synced, skipped, errors, deleted


def get_tenant_token() -> str:
    """Get Feishu tenant access token via app credentials."""
    config_path = os.path.expanduser("~/.lark/config.yaml")
    with open(config_path) as f:
        config = {}
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                config[k.strip()] = v.strip().strip('"')
    app_id = config.get("app_id", "")
    app_secret = os.environ.get("LARK_APP_SECRET", "")

    import urllib.request
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("tenant_access_token", "")


def delete_feishu_doc(doc_token: str, doc_type: str = "docx") -> bool:
    """Delete a Feishu doc via Drive API. Requires type parameter."""
    token = get_tenant_token()
    import urllib.request
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{doc_token}?type={doc_type}"
    req = urllib.request.Request(url, method="DELETE", headers={"Authorization": f"Bearer {token}"})
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        code = result.get("code", -1)
        if code != 0:
            print(f"  → API error: code={code}, msg={result.get('msg', '')}")
        return code == 0
    except Exception as e:
        print(f"  → Exception: {e}")
        return False


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    synced = 0
    skipped = 0
    errors = 0

    # If --skills flag, only sync skills
    if SYNC_SKILLS:
        synced, skipped, errors, deleted = sync_skills()
        print(f"\n{'[Dry Run] ' if DRY_RUN else ''}Skills - Synced: {synced}, Skipped: {skipped}, Deleted: {deleted}, Errors: {errors}")
        return

    # Otherwise, sync Profile/Memory docs (original behavior)
    for name, config in DOCS.items():
        doc_id = config["doc_id"]
        local = read_local(name, config)
        feishu = read_feishu(doc_id)

        if not needs_update(feishu, local):
            print(f"⏭️  {name}: 已同步，跳过")
            skipped += 1
            continue

        # Build update block
        if config["type"] == "profile":
            header = f"### 🔄 Profile 更新于 {now}"
        else:
            header = f"### 🔄 Memory 更新于 {now}"

        # For full sync, include all local content
        update_text = f"\n\n{header}\n\n{local}\n"

        if DRY_RUN:
            print(f"🔍 [dry-run] {name}: 会追加 {len(update_text)} chars")
            continue

        ok = append_to_feishu(doc_id, update_text)
        if ok:
            print(f"✅ {name}: 已追加 {len(update_text)} chars")
            synced += 1
        else:
            print(f"❌ {name}: 追加失败")
            errors += 1

    print(f"\n{'[Dry Run] ' if DRY_RUN else ''}Synced: {synced}, Skipped: {skipped}, Errors: {errors}")


if __name__ == "__main__":
    main()
