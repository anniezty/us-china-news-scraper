from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from utils import clean_html

BASE_URL = "https://www.bloomberg.com"
SEARCH_URL = f"{BASE_URL}/search"
DEFAULT_TIMEOUT = (10, 45)  # (connect, read)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.bloomberg.com/",
}


def _load_cookie_string() -> Optional[str]:
    """加载 Bloomberg Cookie（可选）"""
    cookie_path = os.getenv("BLOOMBERG_COOKIE_PATH")
    if cookie_path and os.path.exists(cookie_path):
        try:
            with open(cookie_path, "r", encoding="utf-8") as fh:
                content = fh.read().strip()
                if content:
                    return content
        except OSError as exc:
            print(f"⚠️ Failed to read BLOOMBERG_COOKIE_PATH: {exc}")

    cookie_env = os.getenv("BLOOMBERG_COOKIE")
    if cookie_env:
        return cookie_env.strip()

    return None


def _parse_dt(ts: str | None) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = dtparser.parse(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def _fetch_article_date_and_summary(url: str) -> tuple[Optional[datetime], str]:
    """从 Bloomberg 文章页面获取发布日期和摘要"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取日期
            published = None
            # 方法1: meta 标签
            date_meta = soup.find('meta', property='article:published_time')
            if date_meta:
                published = _parse_dt(date_meta.get('content'))
            
            # 方法2: JSON-LD
            if not published:
                json_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'datePublished' in data:
                            published = _parse_dt(data['datePublished'])
                            break
                    except:
                        pass
            
            # 获取摘要
            summary = ""
            # 方法1: meta 标签
            summary_meta = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
            if summary_meta:
                summary = summary_meta.get('content', '')
            
            # 方法2: JSON-LD
            if not summary:
                json_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'description' in data:
                            summary = data['description']
                            break
                    except:
                        pass
            
            return published, clean_html(summary)
    except Exception:
        pass
    return None, ""


def _is_china_related(title: str, url: str, summary: str = "") -> bool:
    """判断文章是否与 China 相关"""
    china_keywords = [
        'china', 'chinese', 'beijing', 'shanghai', 'taiwan', 'hong kong',
        'xi jinping', 'ccp', 'tibet', 'xinjiang', 'huawei', 'tiktok',
        'us-china', 'u.s.-china', 'south china sea', 'belt and road'
    ]
    
    text = (title + ' ' + url + ' ' + summary).lower()
    return any(keyword in text for keyword in china_keywords)


def fetch_bloomberg_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
    use_cloudscraper: bool = True,
) -> List[Dict[str, Any]]:
    """
    从 Bloomberg 搜索页面获取 China 相关文章
    
    Args:
        date_from: 开始日期
        date_to: 结束日期
        max_pages: 最大页数
        use_cloudscraper: 是否使用 CloudScraper（绕过反爬）
    
    Returns:
        文章列表
    """
    # 确保日期有时区信息
    if date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    else:
        date_from = date_from.astimezone(timezone.utc)
    
    if date_to.tzinfo is None:
        date_to = date_to.replace(tzinfo=timezone.utc)
    else:
        date_to = date_to.astimezone(timezone.utc)
    
    # 尝试使用 CloudScraper（如果可用）
    session = None
    if use_cloudscraper:
        try:
            import cloudscraper
            session = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'darwin', 'desktop': True})
            session.headers.update(HEADERS)
        except ImportError:
            print("⚠️ cloudscraper not available, using requests (may get 403)")
            session = requests.Session()
            session.headers.update(HEADERS)
    else:
        session = requests.Session()
        session.headers.update(HEADERS)
    
    # 如果有 Cookie，添加到请求头
    cookie_string = _load_cookie_string()
    if cookie_string:
        session.headers.update({"Cookie": cookie_string})
        print("✅ Using Bloomberg Cookie for authentication")
    else:
        print("⚠️ Bloomberg Cookie not provided; may get 403 (free account Cookie recommended)")
    
    all_articles: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()
    
    for page in range(max_pages):
        # 添加请求间隔
        if page > 0:
            time.sleep(1.5)  # 页面之间等待 1.5 秒
        
        params = {
            'query': 'China',
            'page': page + 1,
        }
        
        try:
            resp = session.get(SEARCH_URL, params=params, timeout=DEFAULT_TIMEOUT)
            
            if resp.status_code == 403:
                print(f"⚠️ Bloomberg page {page + 1} returned 403 (may need Cookie or proxy)")
                if page == 0:
                    # 第一页就失败，可能无法继续
                    break
                continue
            
            if resp.status_code != 200:
                print(f"⚠️ Bloomberg page {page + 1} returned {resp.status_code}")
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找文章链接
            article_links = soup.find_all('a', href=lambda x: x and '/news/articles' in x if x else False)
            
            if not article_links:
                # 如果没有找到链接，可能到达最后一页
                break
            
            for link in article_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # 完整 URL
                if not href.startswith('http'):
                    href = urljoin(BASE_URL, href)
                
                # 去重
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # 获取标题
                title = clean_html(link.get_text(strip=True))
                if not title or len(title) < 10:
                    # 尝试从父元素获取
                    parent = link.parent
                    if parent:
                        title = clean_html(parent.get_text(strip=True))
                
                if not title or len(title) < 10:
                    continue
                
                # 初步过滤：标题/URL 必须包含 China 关键词
                if not _is_china_related(title, href):
                    continue
                
                # 访问文章页面获取日期和摘要
                published, summary = _fetch_article_date_and_summary(href)
                
                if published:
                    # 日期过滤
                    if published > date_to or published < date_from:
                        continue
                else:
                    # 如果没有日期，跳过（避免误判）
                    continue
                
                all_articles.append({
                    "title": title,
                    "summary": summary,
                    "url": href,
                    "published": published,
                    "raw_source": SEARCH_URL,
                })
                
                # 添加请求间隔（访问文章页面）
                time.sleep(0.5)
        
        except Exception as e:
            print(f"⚠️ Bloomberg page {page + 1} fetch failed: {e}")
            continue
    
    return all_articles

