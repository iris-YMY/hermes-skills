#!/usr/bin/env python3
"""
Post-import large expense review — list expenses above threshold for user audit.

Usage:
  python3 scripts/post_import_qa.py --month 2026-06 --threshold 999
  python3 scripts/post_import_qa.py --month 2026-06 --threshold 500 --platform 微信
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

APP_TOKEN = "TcxxbfP05adgltsZpJEcGKi9nme"
TABLE_ID = "tbln6KDEsF2QXyKB"


def get_user_token():
    token_file = os.path.expanduser("~/.lark/tokens.json")
    with open(token_file) as f:
        return json.load(f)['access_token']


def api_call(method, url, token, payload=None, timeout=30):
    cmd = ['curl', '-s', '-X', method, url,
           '-H', f'Authorization: Bearer {token}',
           '-H', 'Content-Type: application/json']
    tmp = None
    if payload is not None:
        tmp = f'/tmp/qa_{int(time.time())}.json'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False)
        cmd.extend(['-d', f'@{tmp}'])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if tmp and os.path.exists(tmp):
        os.remove(tmp)
    return json.loads(result.stdout)


def fetch_all_records(token):
    all_records = []
    page_token = None
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=500"
        if page_token:
            url += f"&page_token={page_token}"
        resp = api_call('GET', url, token)
        if resp.get('code') != 0:
            print(f"ERROR: {resp.get('msg')}", file=sys.stderr)
            break
        all_records.extend(resp.get('data', {}).get('items', []))
        if not resp.get('data', {}).get('has_more'):
            break
        page_token = resp['data'].get('page_token')
        time.sleep(0.2)
    return all_records


def main():
    parser = argparse.ArgumentParser(description='Post-import large expense review')
    parser.add_argument('--month', required=True, help='Target month (YYYY-MM)')
    parser.add_argument('--threshold', type=float, default=999, help='Minimum expense amount')
    parser.add_argument('--platform', default=None, help='Filter by platform (支付宝/微信)')
    args = parser.parse_args()

    try:
        target_year, target_month = map(int, args.month.split('-'))
    except ValueError:
        print(f"ERROR: Invalid month format '{args.month}', use YYYY-MM", file=sys.stderr)
        sys.exit(1)

    token = get_user_token()
    all_records = fetch_all_records(token)

    items = []
    for rec in all_records:
        fields = rec.get('fields', {})
        ts = fields.get('交易时间', 0)
        try:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=CST)
        except (ValueError, TypeError, OSError):
            continue
        if dt.year != target_year or dt.month != target_month:
            continue
        if str(fields.get('收支类型', '')) != '支出':
            continue
        try:
            amt = float(fields.get('金额', 0) or 0)
        except (ValueError, TypeError):
            amt = 0
        if amt <= args.threshold:
            continue

        platform = str(fields.get('平台', ''))
        if args.platform and platform != args.platform:
            continue

        items.append({
            'record_id': rec['record_id'],
            'dt': dt,
            'amt': amt,
            'platform': platform,
            'category': str(fields.get('分类', '')),
            'note': str(fields.get('备注', ''))[:60],
            'is_refund': bool(fields.get('是否退款', False))
        })

    items.sort(key=lambda x: x['amt'], reverse=True)
    total = sum(i['amt'] for i in items)

    print(f"{args.month} 支出 >¥{args.threshold:.0f}：{len(items)}条，合计 ¥{total:,.2f}")
    print()
    for i, item in enumerate(items, 1):
        refund_tag = ' ⚠️退款关联' if item['is_refund'] else ''
        print(f"{i:2d}. {item['dt'].strftime('%m-%d')} ¥{item['amt']:>10,.2f}  [{item['platform']}] {item['category']:8s} | {item['note']}{refund_tag}")

    # Also output record_ids for batch operations
    if items:
        print()
        print("--- record_ids (for corrections) ---")
        for item in items:
            print(f"{item['record_id']}")


if __name__ == '__main__':
    main()
