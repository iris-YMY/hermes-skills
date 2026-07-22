"""Tencent Docs Drive v2 API helper."""
import subprocess
import json

ENV_PATH = "/home/ubuntu/.env"

def load_creds():
    """Load TENCENT_DOCS_* credentials from .env file."""
    c = {}
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith("TENCENT_DOCS_") and "=" in line:
                k, v = line.strip().split("=", 1)
                c[k] = v
    return c

def api(method, path, data=None):
    """Call Tencent Docs Open API with ternary headers."""
    c = load_creds()
    cmd = [
        "curl", "-s", "-L", "-X", method, f"https://docs.qq.com/openapi{path}",
        "-H", f"Access-Token: {c['TENCENT_DOCS_ACCESS_TOKEN']}",
        "-H", f"Client-Id: {c['TENCENT_DOCS_CLIENT_ID']}",
        "-H", f"Open-Id: {c['TENCENT_DOCS_OPEN_ID']}"
    ]
    if data:
        cmd += ["-H", "Content-Type: application/x-www-form-urlencoded"]
        for k, v in data.items():
            cmd += ["--data-urlencode", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)
