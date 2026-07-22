---
name: xhs-scraper
category: web-research
description: 抓取小红书帖子内容和图片
---

# 小红书帖子抓取

## 抓取HTML
```bash
curl -s -L --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" \
  "https://www.xiaohongshu.com/discovery/item/{NOTE_ID}?完整分享参数"
```

## 提取文字
```python
title = re.search(r'"title":"([^"]*)"', html)
desc  = re.search(r'"desc":"([^"]*)"', html)
```

## 提取图片URL
```python
urls = re.findall(r'src="(http://sns-webpic[^"]+!h5_1080jpg)"', html)
urls = [u.replace('\\u002F', '/') for u in urls]
```
⚠️ URL含 `\u002F` 转义，必须 replace

## 下载图片（必须并发+快速）
```python
import urllib.request, concurrent.futures

def dl(item):
    name, url = item
    urllib.request.urlretrieve(url, f'/tmp/xhs/{name}')

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    list(ex.map(dl, urls.items()))
```
⚠️ CDN链接有时效，失败则重新curl获取新URL
