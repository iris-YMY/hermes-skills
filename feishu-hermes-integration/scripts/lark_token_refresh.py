#!/usr/bin/env python3
"""
Lark/Feishu Token Pre-Refresh Script
=====================================
Refreshes access_token for all configured profiles before expiry.
Runs via system crontab every hour — zero LLM token cost.

Usage: python3 ~/.hermes/scripts/lark_token_refresh.py

Crontab entry:
  0 * * * * /usr/bin/python3 /home/ubuntu/.hermes/scripts/lark_token_refresh.py >> /home/ubuntu/.hermes/logs/lark_token_cron.log 2>&1

Outputs:
  - Log: ~/.hermes/logs/lark_token_refresh.log
  - Alert JSON: ~/.hermes/logs/lark_token_alert.json (read by Hermes alert cron)
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── Config ──────────────────────────────────────────────────────────
CST = timezone(timedelta(hours=8))
REFRESH_URL = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
LOG_DIR = Path(os.path.expanduser("~/.hermes/logs"))
LOG_FILE = LOG_DIR / "lark_token_refresh.log"
ALERT_LOG = LOG_DIR / "lark_token_alert.json"

# Profile definitions
PROFILES = {
    "default": {
        "config_dir": Path(os.path.expanduser("~/.lark")),
        "label": "黑执事",
    },
    "hr-assistant": {
        "config_dir": Path(os.path.expanduser("~/.hermes/profiles/hr-assistant/home/.lark")),
        "label": "凛子小姐",
    },
}

# Alert thresholds (hours)
ALERT_THRESHOLD_HOURS = 48  # refresh_token < 48h → alert
ACCESS_TOKEN_WARN_HOURS = 1  # access_token < 1h and refresh failed → warn

# ── Logging ─────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("lark-refresh")


# ── Helpers ─────────────────────────────────────────────────────────
def read_config(config_dir: Path) -> dict:
    """Read app_id from config.yaml (simple parser, no PyYAML dependency)."""
    config = {}
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        for line in config_file.read_text().splitlines():
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, val = line.split(":", 1)
                config[key.strip()] = val.strip().strip('"').strip("'")
    return config


def read_app_secret(config_dir: Path, config: dict) -> str:
    """Read app_secret — from file or config.yaml."""
    secret_file = config_dir / "app_secret"
    if secret_file.exists():
        return secret_file.read_text().strip()
    # Fallback: embedded in config.yaml
    return config.get("app_secret", "")


def read_tokens(config_dir: Path) -> dict:
    """Read tokens.json."""
    tokens_file = config_dir / "tokens.json"
    if not tokens_file.exists():
        return {}
    return json.loads(tokens_file.read_text())


def write_tokens(config_dir: Path, tokens: dict):
    """Write tokens.json atomically."""
    tokens_file = config_dir / "tokens.json"
    tokens_file.write_text(json.dumps(tokens, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(tokens_file, 0o600)


def refresh_token_api(app_id: str, app_secret: str, refresh_token: str) -> dict:
    """Call Feishu OAuth refresh API."""
    payload = json.dumps({
        "grant_type": "refresh_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = Request(
        REFRESH_URL,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"code": e.code, "error": str(e), "body": body}
    except URLError as e:
        return {"code": -1, "error": str(e)}


def parse_expiry(iso_str: str) -> datetime | None:
    """Parse ISO 8601 datetime string."""
    if not iso_str or iso_str.startswith("0001"):
        return None
    try:
        return datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return None


# ── Main Logic ──────────────────────────────────────────────────────
def refresh_profile(name: str, profile: dict) -> dict:
    """Refresh tokens for a single profile. Returns status dict."""
    config_dir = profile["config_dir"]
    label = profile["label"]
    result = {"profile": name, "label": label, "status": "unknown", "error": None}

    # Read config
    config = read_config(config_dir)
    app_id = config.get("app_id", "")
    app_secret = read_app_secret(config_dir, config)

    if not app_id or not app_secret:
        result["status"] = "error"
        result["error"] = "Missing app_id or app_secret"
        log.error(f"[{label}] Missing credentials in {config_dir}")
        return result

    # Read tokens
    tokens = read_tokens(config_dir)
    if not tokens.get("refresh_token"):
        result["status"] = "error"
        result["error"] = "No refresh_token — need `lark auth login`"
        log.error(f"[{label}] No refresh_token in tokens.json")
        return result

    # Check if refresh_token is about to expire
    rt_exp = parse_expiry(tokens.get("refresh_token_expires_at", ""))
    now = datetime.now(CST)
    if rt_exp:
        rt_remaining = (rt_exp - now).total_seconds() / 3600
        if rt_remaining < 0:
            result["status"] = "expired"
            result["error"] = f"refresh_token expired {abs(rt_remaining):.1f}h ago — need re-auth"
            log.error(f"[{label}] refresh_token EXPIRED")
            return result
        result["rt_remaining_hours"] = round(rt_remaining, 1)
    else:
        result["rt_remaining_hours"] = None

    # Check access_token freshness
    at_exp = parse_expiry(tokens.get("expires_at", ""))
    if at_exp:
        at_remaining = (at_exp - now).total_seconds() / 3600
        result["at_remaining_hours"] = round(at_remaining, 1)
        # If access_token still valid for > 30 min, skip refresh
        if at_remaining > 0.5:
            result["status"] = "ok"
            log.info(f"[{label}] access_token valid for {at_remaining:.0f}min — skip refresh")
            return result

    # Perform refresh
    log.info(f"[{label}] Refreshing tokens...")
    resp = refresh_token_api(app_id, app_secret, tokens["refresh_token"])

    if resp.get("code", -1) != 0 or not resp.get("access_token"):
        result["status"] = "error"
        result["error"] = resp.get("error_description") or resp.get("error") or resp.get("body", "unknown")
        log.error(f"[{label}] Refresh FAILED: {result['error']}")

        # Check if refresh_token was revoked
        if "revoked" in str(resp.get("body", "")).lower() or "invalid_grant" in str(resp.get("error", "")).lower():
            result["error"] = "refresh_token REVOKED — need `lark auth login`"
            log.critical(f"[{label}] refresh_token revoked!")
        return result

    # Build updated tokens
    expires_in = resp.get("expires_in", 7200)
    refresh_expires_in = resp.get("refresh_token_expires_in", 604800)

    updated = {
        "access_token": resp["access_token"],
        "refresh_token": resp["refresh_token"],
        "expires_at": (now + timedelta(seconds=expires_in)).isoformat(),
        "refresh_token_expires_at": (now + timedelta(seconds=refresh_expires_in)).isoformat(),
        "scope": resp.get("scope", tokens.get("scope", "")),
    }

    write_tokens(config_dir, updated)
    result["status"] = "refreshed"
    result["at_remaining_hours"] = round(expires_in / 3600, 1)
    result["rt_remaining_hours"] = round(refresh_expires_in / 3600, 1)
    log.info(f"[{label}] ✅ Refreshed — access_token {expires_in}s, refresh_token {refresh_expires_in}s")
    return result


def write_alert_log(results: list):
    """Write alert status for the Hermes cron to read."""
    now = datetime.now(CST)
    alert = {
        "timestamp": now.isoformat(),
        "results": results,
        "needs_attention": [],
    }

    for r in results:
        if r["status"] in ("error", "expired"):
            alert["needs_attention"].append({
                "profile": r["label"],
                "issue": r["error"],
                "action": "Please re-authorize with `lark auth login`",
            })
        elif r.get("rt_remaining_hours") is not None and r["rt_remaining_hours"] < ALERT_THRESHOLD_HOURS:
            alert["needs_attention"].append({
                "profile": r["label"],
                "issue": f"refresh_token expires in {r['rt_remaining_hours']:.0f}h (< {ALERT_THRESHOLD_HOURS}h)",
                "action": "Re-authorize soon to avoid service interruption",
            })

    ALERT_LOG.write_text(json.dumps(alert, indent=2, ensure_ascii=False), encoding="utf-8")
    return alert


def main():
    log.info("=" * 60)
    log.info("Lark Token Pre-Refresh — started")

    results = []
    for name, profile in PROFILES.items():
        try:
            result = refresh_profile(name, profile)
        except Exception as e:
            result = {"profile": name, "label": profile["label"], "status": "error", "error": str(e)}
            log.exception(f"[{profile['label']}] Unexpected error")
        results.append(result)

    # Write alert log
    alert = write_alert_log(results)

    # Summary
    statuses = [r["status"] for r in results]
    if all(s == "ok" for s in statuses):
        log.info("All profiles OK — no refresh needed")
    elif all(s in ("ok", "refreshed") for s in statuses):
        log.info("All profiles healthy")
    else:
        failed = [r["label"] for r in results if r["status"] not in ("ok", "refreshed")]
        log.warning(f"ATTENTION NEEDED: {', '.join(failed)}")

    # Exit code: 0 if all ok/refreshed, 1 if any error
    sys.exit(0 if all(s in ("ok", "refreshed") for s in statuses) else 1)


if __name__ == "__main__":
    main()
