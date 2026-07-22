#!/usr/bin/env python3
"""
检查 OAuth Token 过期时间，提前提醒用户重新授权
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def get_tokens():
    """读取 tokens.json"""
    token_file = Path("/home/ubuntu/.hermes/profiles/hr-assistant/home/.lark/tokens.json")
    if not token_file.exists():
        print(f"❌ Token 文件不存在: {token_file}")
        return None
    
    with open(token_file, 'r') as f:
        return json.load(f)


def check_expiry(tokens):
    """检查 token 过期时间"""
    if not tokens:
        return None
    
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        print("❌ refresh_token 不存在")
        return None
    
    # 解析 JWT 获取过期时间
    # refresh_token 格式: header.payload.signature
    try:
        import base64
        payload = refresh_token.split('.')[1]
        # 补齐 padding
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.b64decode(payload)
        token_data = json.loads(decoded)
        exp_timestamp = token_data.get('exp')
        
        if not exp_timestamp:
            print("❌ 无法从 token 中获取过期时间")
            return None
        
        exp_time = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()
        remaining = exp_time - now
        
        return {
            'exp_time': exp_time,
            'remaining': remaining,
            'remaining_days': remaining.days,
            'remaining_hours': remaining.seconds // 3600,
            'is_expired': remaining.total_seconds() < 0
        }
    except Exception as e:
        print(f"❌ 解析 token 失败: {e}")
        return None


def send_reminder(expiry_info):
    """发送飞书提醒消息"""
    if not expiry_info:
        return
    
    remaining_days = expiry_info['remaining_days']
    remaining_hours = expiry_info['remaining_hours']
    exp_time = expiry_info['exp_time'].strftime('%Y-%m-%d %H:%M')
    
    if expiry_info['is_expired']:
        urgency = "⚠️ 已过期"
        action = "立即重新授权"
    elif remaining_days < 1:
        urgency = "🔴 紧急"
        action = "今天内重新授权"
    elif remaining_days < 3:
        urgency = "🟡 提醒"
        action = "尽快重新授权"
    else:
        return  # 不需要提醒
    
    message = f"""{urgency} OAuth Token 即将过期

📊 财务看板 Token 状态：
- refresh_token 过期时间: {exp_time}
- 剩余时间: {remaining_days}天 {remaining_hours}小时

⚡ 需要执行的操作:
{action}，否则月度更新脚本将无法运行。

🔗 授权命令:
```
hermes skills run monthly-finance-dashboard/reauth
```

或直接联系凛子助手协助处理。"""
    
    # 使用 lark CLI 发送消息
    chat_id = "oc_d811c650f76f16e98ac7a65517e0128f"  # 飞书群聊 ID
    
    try:
        result = subprocess.run(
            ['lark', 'msg', 'send', '--chat-id', chat_id, '--text', message],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ 提醒消息已发送")
            return True
        else:
            print(f"❌ 发送消息失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 发送消息异常: {e}")
        return False


def main():
    """主函数"""
    print("🔍 检查 OAuth Token 过期时间...")
    
    tokens = get_tokens()
    if not tokens:
        return
    
    expiry_info = check_expiry(tokens)
    if not expiry_info:
        return
    
    remaining_days = expiry_info['remaining_days']
    remaining_hours = expiry_info['remaining_hours']
    
    print(f"📅 refresh_token 过期时间: {expiry_info['exp_time'].strftime('%Y-%m-%d %H:%M')}")
    print(f"⏰ 剩余时间: {remaining_days}天 {remaining_hours}小时")
    
    if expiry_info['is_expired']:
        print("⚠️ Token 已过期，发送提醒...")
        send_reminder(expiry_info)
    elif remaining_days < 3:
        print("⚠️ Token 即将过期，发送提醒...")
        send_reminder(expiry_info)
    else:
        print("✅ Token 状态正常，无需提醒")


if __name__ == "__main__":
    main()
