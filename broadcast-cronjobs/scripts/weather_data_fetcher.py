#!/usr/bin/env python3
"""
weather_data_fetcher.py — Pre-fetch weather data for morning broadcast cron job.
Fetches: weather (Open-Meteo), air quality (Open-Meteo + WAQI fallback), rain forecast.
Outputs structured 【预抓取天气数据】 for LLM formatting.

Usage: python3 weather_data_fetcher.py
Output: printed to stdout (injected into cron prompt)
"""

import json
import urllib.request
from datetime import datetime

# ============================================================
# 1. Geolocation (ip-api.com — no rate limit)
# ============================================================
def get_location():
    """Get lat/lon + city name. Fallback to Shanghai."""
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=status,message,country,regionName,city,lat,lon",
            headers={"User-Agent": "weather-fetcher/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            if data.get("status") == "success":
                return {
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "city": data.get("city", "上海"),
                    "region": data.get("regionName", "上海"),
                    "country": data.get("country", "中国"),
                }
    except Exception as e:
        print(f"# [WARN] ip-api.com failed: {e}, using Shanghai fallback")
    return {"lat": 31.22, "lon": 121.46, "city": "上海", "region": "上海", "country": "中国"}

# ============================================================
# 2. Weather (Open-Meteo)
# ============================================================
def fetch_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure,cloud_cover"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m,cloud_cover"
        f"&daily=temperature_2m_max,temperature_2m_min,weather_code,uv_index_max,sunrise,sunset"
        f"&timezone=Asia/Shanghai&forecast_days=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "weather-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

# ============================================================
# 3. Air Quality (Open-Meteo primary, WAQI fallback)
# ============================================================
def fetch_air_quality_openmeteo(lat, lon):
    try:
        url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={lat}&longitude={lon}"
            f"&current=us_aqi,pm2_5,pm10,ozone"
            f"&timezone=Asia/Shanghai"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "weather-fetcher/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            cur = data.get("current", {})
            return {
                "aqi": cur.get("us_aqi"),
                "pm25": cur.get("pm2_5"),
                "pm10": cur.get("pm10"),
                "o3": cur.get("ozone"),
            }
    except Exception:
        return None

def fetch_air_quality_waqi(city="shanghai"):
    """WAQI demo API fallback."""
    try:
        url = f"https://api.waqi.info/feed/{city}/?token=demo"
        req = urllib.request.Request(url, headers={"User-Agent": "weather-fetcher/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("status") == "ok":
                d = data.get("data", {})
                iaqi = d.get("iaqi", {})
                return {
                    "aqi": d.get("aqi"),
                    "pm25": iaqi.get("pm25", {}).get("v"),
                    "pm10": iaqi.get("pm10", {}).get("v"),
                    "o3": iaqi.get("o3", {}).get("v"),
                }
    except Exception:
        pass
    return None

# ============================================================
# 4. Parsers
# ============================================================
WEATHER_CODES = {
    0: "晴", 1: "大部晴", 2: "多云", 3: "阴",
    45: "雾", 48: "冻雾",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨(小)", 67: "冻雨(大)",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒", 80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
}

def weather_code_to_chinese(code):
    return WEATHER_CODES.get(code, f"未知({code})")

def wind_degree_to_direction(deg):
    directions = [
        "北", "北北东", "东北", "东北东", "东", "东南东", "东南", "南南东",
        "南", "南南西", "西南", "西南西", "西", "西北西", "西北", "北北西"
    ]
    idx = round(deg / 22.5) % 16
    return directions[idx]

def aqi_level(aqi):
    if aqi is None: return "未知"
    if aqi <= 50: return "优"
    if aqi <= 100: return "良"
    if aqi <= 150: return "轻度污染"
    if aqi <= 200: return "中度污染"
    if aqi <= 300: return "重度污染"
    return "严重污染"

def uv_level(uv):
    if uv is None: return "未知"
    if uv <= 2: return "低"
    if uv <= 5: return "中"
    if uv <= 7: return "高"
    if uv <= 10: return "很高"
    return "极高"

def humidity_desc(h):
    if h < 30: return "干燥"
    if h <= 60: return "舒适"
    if h <= 70: return "微湿"
    if h <= 85: return "潮湿"
    return "闷热"

# ============================================================
# 5. Rain period analysis
# ============================================================
def analyze_rain_periods(hourly_data):
    """Merge consecutive high-probability rain hours into time ranges."""
    periods = []
    current_start = None
    current_end = None

    for i, h in enumerate(hourly_data):
        prob = h.get("precipitation_probability", 0) or 0
        code = h.get("weather_code", 0) or 0
        is_rain = prob >= 50 or code in (51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99)

        if is_rain:
            if current_start is None:
                current_start = i
            current_end = i
        else:
            if current_start is not None:
                periods.append((current_start, current_end))
                current_start = None
                current_end = None

    if current_start is not None:
        periods.append((current_start, current_end))

    result = []
    for start, end in periods:
        start_h = start % 24
        end_h = end % 24
        prob = hourly_data[start].get("precipitation_probability", 0) or 0
        end_prob = hourly_data[end].get("precipitation_probability", 0) or 0
        if start_h == end_h:
            result.append(f"  - {start_h:02d}:00 (概率 {prob}%)")
        else:
            result.append(f"  - {start_h:02d}:00-{end_h:02d}:00 (概率 {prob}%-{end_prob}%)")
    return result

# ============================================================
# 6. Main
# ============================================================
def main():
    loc = get_location()
    print(f"# Location: {loc['city']}, {loc['region']}")

    w = fetch_weather(loc["lat"], loc["lon"])
    cur = w.get("current", {})
    daily = w.get("daily", {})
    hourly = w.get("hourly", {})

    temp = cur.get("temperature_2m", "N/A")
    feels = cur.get("apparent_temperature", "N/A")
    humidity = cur.get("relative_humidity_2m", "N/A")
    wind_speed = cur.get("wind_speed_10m", "N/A")
    wind_deg = cur.get("wind_direction_10m", 0) or 0
    wind_dir = wind_degree_to_direction(wind_deg)
    pressure = cur.get("surface_pressure", "N/A")
    cloud_cover = cur.get("cloud_cover", "N/A")
    weather_code = cur.get("weather_code", 0) or 0
    weather_desc = weather_code_to_chinese(weather_code)

    max_temp = daily.get("temperature_2m_max", ["N/A"])[0]
    min_temp = daily.get("temperature_2m_min", ["N/A"])[0]
    uv_max = daily.get("uv_index_max", ["N/A"])[0]
    sunrise = daily.get("sunrise", ["N/A"])[0]
    sunset = daily.get("sunset", ["N/A"])[0]
    if isinstance(sunrise, str) and "T" in sunrise:
        sunrise = sunrise.split("T")[1]
    if isinstance(sunset, str) and "T" in sunset:
        sunset = sunset.split("T")[1]

    hourly_temps = hourly.get("temperature_2m", [])
    hourly_probs = hourly.get("precipitation_probability", [])
    hourly_humidity = hourly.get("relative_humidity_2m", [])
    hourly_codes = hourly.get("weather_code", [])

    hourly_list = []
    for i in range(len(hourly_temps)):
        hourly_list.append({
            "hour": i,
            "temperature": hourly_temps[i] if i < len(hourly_temps) else None,
            "precipitation_probability": hourly_probs[i] if i < len(hourly_probs) else 0,
            "weather_code": hourly_codes[i] if i < len(hourly_codes) else 0,
            "humidity": hourly_humidity[i] if i < len(hourly_humidity) else None,
        })

    rain_periods = analyze_rain_periods(hourly_list)
    now_hour = datetime.now().hour

    aqi = fetch_air_quality_openmeteo(loc["lat"], loc["lon"])
    if aqi is None or aqi.get("aqi") is None:
        aqi = fetch_air_quality_waqi("shanghai")

    # === OUTPUT ===
    print(f"城市: {loc['city']}")
    print(f"省份: {loc['region']}")
    print(f"温度: {temp}")
    print(f"体感: {feels}")
    print(f"最高: {max_temp}")
    print(f"最低: {min_temp}")
    print(f"湿度: {humidity}")
    print(f"湿度描述: {humidity_desc(humidity) if isinstance(humidity, (int, float)) else '未知'}")
    print(f"风向: {wind_dir}")
    print(f"风速: {wind_speed}")
    print(f"气压: {pressure}")
    print(f"云量: {cloud_cover}%")
    print(f"天气: {weather_desc}")
    print(f"UV: {uv_max}")
    print(f"UV等级: {uv_level(uv_max)}")
    print(f"日出: {sunrise}")
    print(f"日落: {sunset}")
    print(f"当前小时: {now_hour}")

    if aqi:
        print(f"AQI: {aqi.get('aqi', 'N/A')}")
        print(f"AQI等级: {aqi_level(aqi.get('aqi'))}")
        print(f"PM2.5: {aqi.get('pm25', 'N/A')}")
        print(f"PM10: {aqi.get('pm10', 'N/A')}")
        print(f"O3: {aqi.get('o3', 'N/A')}")
    else:
        print("AQI: 数据获取失败")

    if rain_periods:
        print("降雨时段:")
        for p in rain_periods:
            print(p)
    else:
        print("降雨: 无")

    print("--- hourly ---")
    for h in hourly_list:
        prob = h.get("precipitation_probability", 0) or 0
        temp_h = h.get("temperature", "N/A")
        hum_h = h.get("humidity", "N/A")
        if prob >= 30:
            print(f"  {h['hour']:02d}:00 降水={prob}% 温度={temp_h} 湿度={hum_h}")

if __name__ == "__main__":
    main()
