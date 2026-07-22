#!/usr/bin/env python3
"""Create a Feishu docx document from a markdown file.

Usage:
    python3 create_feishu_docx.py <md_file> <title> <folder_token> [--app-id APP_ID] [--secret-file PATH] [--user-token]

Defaults:
    --app-id: cli_aa9ebcbfc6e35cba (hr-assistant)
    --secret-file: ~/.hermes/profiles/hr-assistant/home/.lark/app_secret
    --user-token: Read user OAuth access_token from tokens.json (REQUIRED for user-owned folders like Skills folder PdkOfBF0nlUKlkdVABZcYuKFneh)

Output: Document URL and token printed to stdout.

Pitfalls:
    - heading2/heading3 blocks (type 3/4) fail with "invalid param" → uses bold text workaround
    - Max 50 blocks per batch → auto-splits
    - Tenant token can only create in app-accessible folders; user-owned folders (Skills, My Folder) MUST use --user-token
"""
import json, subprocess, os, sys, argparse

def get_token(app_id, secret_file):
    with open(os.path.expanduser(secret_file)) as f:
        app_secret = f.read().strip()
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"app_id": app_id, "app_secret": app_secret})
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    token = data.get("tenant_access_token", "")
    if not token:
        print(f"FATAL: Token failed: {data}", file=sys.stderr)
        sys.exit(1)
    return token

def get_user_token(tokens_file="~/.hermes/profiles/hr-assistant/home/.lark/tokens.json"):
    """Read user OAuth access_token from tokens.json. Required for user-owned folders."""
    path = os.path.expanduser(tokens_file)
    if not os.path.exists(path):
        print(f"FATAL: tokens.json not found at {path}. Run 'lark auth login' first.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    token = data.get("access_token", "")
    if not token:
        print(f"FATAL: No access_token in {path}. Token may be expired — run 'lark auth login'.", file=sys.stderr)
        sys.exit(1)
    return token

def api(method, url, token, payload=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", "Content-Type: application/json",
           "-H", f"Authorization: Bearer {token}"]
    if payload is not None:
        cmd += ["-d", json.dumps(payload)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def parse_markdown(md_content):
    """Convert markdown to Feishu docx blocks. Headings become bold text (heading blocks fail)."""
    blocks = []
    lines = md_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith('# ') and i == 0:
            i += 1; continue  # skip doc title

        if line.startswith('## '):
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {
                "content": "📌 " + line[3:].strip(), "text_element_style": {"bold": True}}}]}
            })
            i += 1; continue

        if line.startswith('### '):
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {
                "content": "▸ " + line[4:].strip(), "text_element_style": {"bold": True}}}]}
            })
            i += 1; continue

        if line.startswith('```'):
            i += 1; code_lines = []
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i]); i += 1
            i += 1
            code_text = '\n'.join(code_lines)
            if code_text.strip():
                blocks.append({"block_type": 14, "code": {"elements": [{"text_run": {"content": code_text}}]}})
            continue

        if line.startswith('- '):
            blocks.append({"block_type": 12, "bullet": {"elements": [{"text_run": {"content": line[2:].strip()}}]}})
            i += 1; continue

        if line and len(line) > 2 and line[0].isdigit() and line[1] == '.':
            blocks.append({"block_type": 13, "ordered": {"elements": [{"text_run": {"content": line[2:].strip()}}]}})
            i += 1; continue

        if line.strip():
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": line.strip()}}]}})

        i += 1
    return blocks

def main():
    parser = argparse.ArgumentParser(description="Create Feishu docx from markdown")
    parser.add_argument("md_file", help="Path to markdown file")
    parser.add_argument("title", help="Document title")
    parser.add_argument("folder_token", help="Target folder token")
    parser.add_argument("--app-id", default="cli_aa9ebcbfc6e35cba")
    parser.add_argument("--secret-file", default="~/.hermes/profiles/hr-assistant/home/.lark/app_secret")
    parser.add_argument("--user-token", action="store_true",
                        help="Use user OAuth token (required for user-owned folders like Skills folder)")
    parser.add_argument("--tokens-file", default="~/.hermes/profiles/hr-assistant/home/.lark/tokens.json",
                        help="Path to tokens.json for --user-token mode")
    args = parser.parse_args()

    if args.user_token:
        token = get_user_token(args.tokens_file)
        print("Using user OAuth token (for user-owned folders)", file=sys.stderr)
    else:
        token = get_token(args.app_id, args.secret_file)
        print("Using tenant token (for app-accessible folders only)", file=sys.stderr)

    with open(args.md_file) as f:
        md_content = f.read()

    # Create document
    create_result = api("POST", "https://open.feishu.cn/open-apis/docx/v1/documents", token, {
        "title": args.title, "folder_token": args.folder_token
    })
    if create_result.get("code") != 0:
        print(f"FATAL: Create failed: {create_result}", file=sys.stderr)
        sys.exit(1)

    doc_token = create_result["data"]["document"]["document_id"]
    blocks = parse_markdown(md_content)

    # Write in batches of 50
    batch_size = 50
    for start in range(0, len(blocks), batch_size):
        batch = blocks[start:start + batch_size]
        r = api("POST",
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{doc_token}/children",
                token, {"children": batch, "index": start})
        if r.get("code") == 0:
            print(f"  Batch {start}-{start+len(batch)}: OK")
        else:
            print(f"  Batch {start}-{start+len(batch)}: FAIL - {r.get('msg', '')}", file=sys.stderr)

    url = f"https://open.feishu.cn/docx/{doc_token}"
    print(f"\n✅ Document: {url}")
    print(f"   Token: {doc_token}")

if __name__ == "__main__":
    main()
