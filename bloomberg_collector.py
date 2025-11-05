#!/usr/bin/env python3
"""
Bloomberg API 收集器
处理 Bloomberg Next China API 的数据收集
"""
import requests
from urllib.parse import urljoin
from datetime import datetime, timezone
from dateutil import parser as dtparser
import time

BLOOMBERG_URL = "https://www.bloomberg.com/lineup-next/api/page/next-china/module/story_package_2,story_package_4,story_package_5,hub_ad_4,story_package_6,story_package_7,hub_video,hub_story_list_2,hub_story_list_3?moduleVariations=3_up_images,3_up_images,3_up_images,default,3_up_images,3_up_images,default,simple,simple&moduleTypes=story_package,story_package,story_package,ad,story_package,story_package,video,story_list,story_list&locale=en&publishedState=PUBLISHED"

BLOOMBERG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bloomberg.com/next-china",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

def iter_bbg_articles(j, host="https://www.bloomberg.com"):
    """
    递归遍历 Bloomberg API 响应，提取文章
    """
    stack = [j]
    articles = []
    
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            # 识别"像文章"的对象：有标题+链接
            title = None
            if isinstance(x.get("headline"), dict):
                title = x.get("headline", {}).get("text")
            else:
                title = x.get("headline") or x.get("title")
            
            url = x.get("url") or x.get("path") or x.get("longURL") or x.get("shortURL")
            
            if title and url:
                dek = x.get("dek") or x.get("summary") or x.get("description") or ""
                ts = x.get("publishedAt") or x.get("published_time") or x.get("display_time") or x.get("date")
                
                # 处理 URL
                full_url = url if str(url).startswith("http") else urljoin(host, str(url))
                
                articles.append({
                    "url": full_url,
                    "title": title,
                    "summary": dek,
                    "published": ts,
                    "source": "bloomberg.com",
                    "raw_source": BLOOMBERG_URL
                })
            
            # 继续深入常见容器字段
            for k in ("stories", "items", "cards", "modules", "content", "results", 
                     "story_package", "data", "children", "list", "entries"):
                v = x.get(k)
                if isinstance(v, (list, dict)):
                    stack.append(v)
        elif isinstance(x, list):
            stack.extend(x)
    
    return articles

def fetch_bloomberg_articles(date_from: datetime = None, date_to: datetime = None, max_retries: int = 3):
    """
    从 Bloomberg API 获取文章
    
    Args:
        date_from: 开始日期（可选，用于过滤）
        date_to: 结束日期（可选，用于过滤）
        max_retries: 最大重试次数
    
    Returns:
        list: 文章列表
    """
    articles = []
    
    for attempt in range(max_retries):
        try:
            response = requests.get(BLOOMBERG_URL, headers=BLOOMBERG_HEADERS, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                articles = iter_bbg_articles(data)
                
                # 过滤日期范围
                if date_from or date_to:
                    filtered_articles = []
                    for article in articles:
                        pub_str = article.get("published")
                        if pub_str:
                            try:
                                pub_dt = dtparser.parse(pub_str)
                                if pub_dt.tzinfo is None:
                                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                                else:
                                    pub_dt = pub_dt.astimezone(timezone.utc)
                                
                                if date_from and pub_dt < date_from:
                                    continue
                                if date_to and pub_dt > date_to:
                                    continue
                                
                                filtered_articles.append(article)
                            except:
                                # 日期解析失败，保留文章
                                filtered_articles.append(article)
                    articles = filtered_articles
                
                return articles
                
            elif response.status_code == 403:
                if attempt < max_retries - 1:
                    print(f"⚠️ Bloomberg API 403 Forbidden (尝试 {attempt + 1}/{max_retries})，可能需要更真实的浏览器环境")
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Bloomberg API 持续返回 403 Forbidden")
                    return []
                    
            elif response.status_code == 429:
                wait_time = 5 + (attempt * 2)
                if attempt < max_retries - 1:
                    print(f"⚠️ Bloomberg API 限流 (429)，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Bloomberg API 持续限流")
                    return []
            else:
                print(f"⚠️ Bloomberg API 返回 {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return []
                    
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"⚠️ Bloomberg API 超时 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(3)
                continue
            else:
                print(f"❌ Bloomberg API 超时")
                return []
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Bloomberg API 错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)
                continue
            else:
                print(f"❌ Bloomberg API 错误: {e}")
                return []
    
    return articles

