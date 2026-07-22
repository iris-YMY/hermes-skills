"""
News Card JSON Builder — Template
==================================
USE THIS INSTEAD OF write_file FOR NEWS JSON.
Write this script via write_file to /tmp/build_news_json.py, 
then run with: python3 /tmp/build_news_json.py
Then validate: python3 /tmp/validate_json.py
Then send: python3 send_news_card.py /tmp/news_card_data.json

The key: json.dump() handles Chinese quotation marks safely.
"""
import json

data = {
    "date": "2026年M月D日 星期X",  # Fill in
    "greeting": "小艾主人早上好呀～...",  # Fill in
    "sections": [
        {
            "emoji": "📌", "title": "今日看点", "tag": "TOP",
            "items": [
                {"text": "新闻概要（2句话）", "source": "来源"},
                # ... 2-3 items
            ]
        },
        {
            "emoji": "🤖", "title": "AI 与科技",
            "items": [
                {"text": "...", "source": "..."},
                # ... 3-5 items
            ]
        },
        {
            "emoji": "💰", "title": "财经与商业",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "🌐", "title": "国际形势",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "📜", "title": "政府政策动态",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "🏙️", "title": "上海本地民生",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "🎬", "title": "影视与短剧",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "👜", "title": "时尚 / 奢侈品",
            "items": []  # Empty if no data
        },
        {
            "emoji": "🏮", "title": "国潮文化与国货品牌",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "🏭", "title": "实体行业发展",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "🏯", "title": "国风 / 文化 / 艺术",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "📱", "title": "社交媒体热门",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "📈", "title": "股市 / 基金 / 财经",
            "items": [{"text": "...", "source": "..."}]
        },
        {
            "emoji": "💰", "title": "基金板块影响分析",
            "items": [
                {"text": "（此板块为推测性内容，仅供参考）...", "source": "推断"}
            ]
        },
        {
            "emoji": "🐟", "title": "摸鱼日历",
            "items": [{"text": "农历XX | 本周进度X% | ...", "source": ""}]
        }
    ],
    "tip": "温馨提示..."
}

# json.dump handles all Chinese quotation marks safely
with open('/tmp/news_card_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Self-validate
with open('/tmp/news_card_data.json', 'r') as f:
    validated = json.load(f)
print(f"✅ JSON valid: {len(validated['sections'])} sections written to /tmp/news_card_data.json")
