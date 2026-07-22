#!/usr/bin/env python3
"""Embed images into Feishu docx documents using the 3-step method.

Usage:
    python3 embed_docx_images.py <doc_id> <image_dir> <prefix> <count>

Example:
    python3 embed_docx_images.py QsV2dvLgMoadRDxnR0ZcO4ICnng /tmp/images post1 7

The 3-step method (CONFIRMED 2026-07-21):
  1. Create empty image block (block_type 27, NO index param)
  2. Upload with parent_type=docx_image + parent_node={block_id}
  3. PATCH block with replace_image: {token: file_token}

Requires: drive:drive scope on the Feishu app.
"""
import json, subprocess, os, sys, time

APP_ID = "cli_aa9ebcbfc6e35cba"
SECRET_FILE = "/home/ubuntu/.hermes/profiles/hr-assistant/home/.lark/app_secret"

def get_tenant_token():
    with open(SECRET_FILE) as f:
        secret = f.read().strip()
    r = subprocess.run(["curl", "-s", "-X", "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"app_id": APP_ID, "app_secret": secret})
    ], capture_output=True, text=True)
    return json.loads(r.stdout)["tenant_access_token"]

def api(method, url, token, payload=None, form_data=None):
    if form_data:
        cmd = ["curl", "-s", "-X", method, url, "-H", f"Authorization: Bearer {token}"]
        cmd.extend(form_data)
    else:
        cmd = ["curl", "-s", "-X", method, url,
               "-H", "Content-Type: application/json",
               "-H", f"Authorization: Bearer {token}"]
        if payload:
            cmd += ["-d", json.dumps(payload)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except:
        return {"code": -1, "msg": r.stdout[:200]}

def embed_one_image(doc_id, fpath, token):
    """3-step: create empty block -> upload -> patch. Returns (success, info)."""
    # Step 1: Create empty image block (NO index param!)
    r = api("POST",
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
        token, {"children": [{"block_type": 27, "image": {"width": 1080, "height": 1440}}]})
    if r.get("code") != 0:
        return False, f"create fail: {r.get('msg','')}"
    block_id = r["data"]["children"][0]["block_id"]

    # Step 2: Upload with docx_image + block_id as parent_node
    fsize = os.path.getsize(fpath)
    r = api("POST", "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
        token, form_data=[
            "-F", f"file_name={os.path.basename(fpath)}",
            "-F", "parent_type=docx_image",
            "-F", f"parent_node={block_id}",
            "-F", f"size={fsize}",
            "-F", f"file=@{fpath}"
        ])
    if r.get("code") != 0:
        return False, f"upload fail: {r.get('msg','')}"
    media_token = r["data"]["file_token"]

    # Step 3: PATCH replace_image
    r = api("PATCH",
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}",
        token, {"replace_image": {"token": media_token}})
    if r.get("code") == 0:
        return True, block_id
    return False, f"patch fail: {r.get('msg','')}"

def main():
    if len(sys.argv) < 5:
        print("Usage: embed_docx_images.py <doc_id> <image_dir> <prefix> <count>")
        sys.exit(1)

    doc_id, img_dir, prefix, count = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    token = get_tenant_token()
    if not token:
        print("FATAL: No token", file=sys.stderr); sys.exit(1)

    print(f"Embedding {count} images ({prefix}_*.jpg) into {doc_id}")
    ok_count = 0
    for i in range(1, count + 1):
        fpath = os.path.join(img_dir, f"{prefix}_{i}.jpg")
        if not os.path.exists(fpath):
            print(f"  [{i}/{count}] SKIP: {fpath} not found")
            continue
        print(f"  [{i}/{count}]", end=" ", flush=True)
        ok, info = embed_one_image(doc_id, fpath, token)
        if ok:
            print(f"OK (block={info[:16]}...)")
            ok_count += 1
        else:
            print(f"FAIL: {info}")
        time.sleep(0.3)

    print(f"\nDone: {ok_count}/{count} images embedded")

if __name__ == "__main__":
    main()
