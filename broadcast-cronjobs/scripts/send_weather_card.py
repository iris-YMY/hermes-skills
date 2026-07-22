#!/usr/bin/env python3
"""
飞书天气卡片发送脚本
读取结构化 JSON → 构建飞书 Interactive Card → 发送到指定群聊
"""

import json
import sys
import urllib.request
import os
from datetime import datetime

# === Config ===
APP_ID = "cli_aa9ea34aaff85cda"
APP_SECRET = "LpTsYpJKYDBfDtl0qw4i8gV1PwTN2nSr"
CHAT_ID = "oc_a0422f2a7bebf7c3b831a4ff05b8c6db"  # AI在这里 group
INPUT_FILE = "/tmp/weather_card_data.json"

def get_tenant_token():
    payload = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET})
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=payload.encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if resp.get("code") != 0:
        raise Exception(f"Token error: {resp}")
    return resp["tenant_access_token"]

def build_card(data):
    """Build Feishu interactive weather card from structured data."""
    
    date_str = data.get("date", datetime.now().strftime("%Y年%m月%d日 星期X"))
    location = data.get("location", "上海")
    greeting = data.get("greeting", "早安！")
    
    temp_info = data.get("temperature", {})
    air_quality = data.get("air_quality", {})
    uv_sun = data.get("uv_sun", {})
    rain_forecast = data.get("rain_forecast", {})
    tips = data.get("tips", [])
    closing = data.get("closing", "祝您今天元气满满，一切顺利！✨")
    
    elements = []
    
    # Greeting
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": f"☀️ **{greeting}**\n📍 {location}"}
    })
    elements.append({"tag": "hr"})
    
    # Temperature section
    if temp_info:
        temp_lines = []
        if temp_info.get("current") is not None:
            feels = f"（体感 {temp_info['feels_like']}°C）" if temp_info.get("feels_like") else ""
            temp_lines.append(f"🌡️ **温度**：{temp_info['current']}°C {feels}")
        if temp_info.get("high") is not None and temp_info.get("low") is not None:
            temp_lines.append(f"📈 **最高 / 最低**：{temp_info['high']}°C / {temp_info['low']}°C")
        if temp_info.get("humidity") is not None:
            comfort = f"（{temp_info['comfort']}）" if temp_info.get("comfort") else ""
            temp_lines.append(f"💧 **湿度**：{temp_info['humidity']}% {comfort}")
        if temp_info.get("wind"):
            temp_lines.append(f"🌬️ **风力**：{temp_info['wind']}")
        if temp_info.get("pressure") is not None:
            temp_lines.append(f"🔵 **气压**：{temp_info['pressure']}hPa")
        
        if temp_lines:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**🌡️ 实时气温**\n" + "\n".join(temp_lines)}
            })
            elements.append({"tag": "hr"})
    
    # Air quality section
    if air_quality:
        air_lines = []
        if air_quality.get("aqi") is not None:
            level = f"（{air_quality['level']}）" if air_quality.get("level") else ""
            air_lines.append(f"🌫️ **AQI**：{air_quality['aqi']} {level}")
        if air_quality.get("pm25") is not None:
            pm10_str = f" | PM10：{air_quality['pm10']}μg/m³" if air_quality.get("pm10") is not None else ""
            air_lines.append(f"💨 **PM2.5**：{air_quality['pm25']}μg/m³{pm10_str}")
        
        if air_lines:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**🌬️ 空气质量**\n" + "\n".join(air_lines)}
            })
            elements.append({"tag": "hr"})
    
    # UV & Sun section
    if uv_sun:
        uv_lines = []
        if uv_sun.get("uv_index") is not None:
            uv_level = f"（{uv_sun['uv_level']}）" if uv_sun.get("uv_level") else ""
            uv_lines.append(f"☀️ **UV 指数**：{uv_sun['uv_index']} {uv_level}")
        if uv_sun.get("sunrise") or uv_sun.get("sunset"):
            sunrise = uv_sun.get("sunrise", "?")
            sunset = uv_sun.get("sunset", "?")
            uv_lines.append(f"🌅 **日出** {sunrise} / **日落** {sunset}")
        
        if uv_lines:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**☀️ 紫外线 · 日照**\n" + "\n".join(uv_lines)}
            })
            elements.append({"tag": "hr"})
    
    # Rain forecast section
    if rain_forecast:
        rain_lines = []
        if rain_forecast.get("weather"):
            rain_lines.append(f"🌤️ **今日天气**：{rain_forecast['weather']}")
        if rain_forecast.get("precipitation") is not None:
            rain_lines.append(f"🌧️ **预计雨量**：{rain_forecast['precipitation']}mm")
        if rain_forecast.get("rain_analysis"):
            rain_lines.append(f"⏰ {rain_forecast['rain_analysis']}")
        
        if rain_lines:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**🌧️ 降雨预报**\n" + "\n".join(rain_lines)}
            })
            elements.append({"tag": "hr"})
    
    # Tips section
    if tips:
        tip_lines = [f"• {t}" for t in tips]
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": "**💝 添添温馨提醒**\n" + "\n".join(tip_lines)}
        })
    
    # Closing
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": f"_{closing}_"}
    })
    
    # Determine header template color based on weather
    weather_desc = (rain_forecast or {}).get("weather", "")
    if "雨" in weather_desc or "雪" in weather_desc:
        template = "indigo"
    elif "晴" in weather_desc:
        template = "orange"
    elif "多云" in weather_desc or "阴" in weather_desc:
        template = "green"
    else:
        template = "turquoise"
    
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"☀️ 早安气象播报 | {date_str}"
            },
            "template": template
        },
        "elements": elements
    }
    
    return card

def send_card(token, card):
    payload = json.dumps({
        "receive_id": CHAT_ID,
        "msg_type": "interactive",
        "content": json.dumps(card, ensure_ascii=False)
    })
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=payload.encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"📦 Loaded weather data from {input_file}")
    print(f"   Date: {data.get('date', 'N/A')}")
    print(f"   Location: {data.get('location', 'N/A')}")
    
    token = get_tenant_token()
    print(f"🔑 Token obtained")
    
    card = build_card(data)
    print(f"🎨 Card built with {len(card['elements'])} elements (template: {card['header']['template']})")
    
    resp = send_card(token, card)
    
    if resp.get("code") == 0:
        msg_id = resp.get("data", {}).get("message_id", "unknown")
        print(f"✅ Card sent successfully! Message ID: {msg_id}")
    else:
        print(f"❌ Send failed: {json.dumps(resp, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
