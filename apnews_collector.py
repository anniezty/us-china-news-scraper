from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from datetime import timezone as tz

from utils import clean_html

BASE_URL = "https://apnews.com"
SECTION_PATH = "/hub/china"
DEFAULT_TIMEOUT = (10, 45)  # (connect, read)


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


def _fetch_article_date(url: str) -> Optional[datetime]:
    """从 AP News 文章页面获取发布日期"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 查找 meta 标签
            date_meta = soup.find('meta', property='article:published_time')
            if date_meta:
                return _parse_dt(date_meta.get('content'))
            # 查找 JSON-LD
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'datePublished' in data:
                        return _parse_dt(data['datePublished'])
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'datePublished' in item:
                                return _parse_dt(item['datePublished'])
                except:
                    pass
    except Exception:
        pass
    return None


def _check_article_has_china_hub(url: str) -> bool:
    """检查文章页面是否包含 China hub 标签（检查 href 是否为 /hub/china）"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 查找 hub 标签链接，检查 href 是否为 /hub/china
            hub_links = soup.find_all('a', href=lambda x: x and '/hub/' in x)
            for link in hub_links:
                href = link.get('href', '').lower()
                # 只接受明确的 /hub/china 链接（不包括 /hub/asia-pacific 等）
                if '/hub/china' in href:
                    return True
                # 也接受 taiwan 和 hong kong
                if '/hub/taiwan' in href or '/hub/hong-kong' in href or '/hub/hongkong' in href:
                    return True
    except Exception:
        pass
    return False


def _is_china_related(title: str, url: str) -> bool:
    """判断文章是否与 China 相关（放宽条件，避免漏掉文章）"""
    china_keywords = [
        'china', 'chinese', 'beijing', 'shanghai', 'guangzhou', 'shenzhen',
        'taiwan', 'taipei', 'hong kong', 'macau', 'macao',
        'xi jinping', 'ccp', 'communist party',
        'prc', 'people\'s republic', 'mainland china',
        'tibet', 'xinjiang', 'uyghur', 'tibetan',
        'south china sea', 'belt and road', 'bri',
        'huawei', 'tiktok', 'tencent', 'alibaba', 'baidu',
        'semiconductor', 'chip', 'smic', 'tsmc',
        'trade war', 'tariff', 'sanction', 'export control',
        'us-china', 'u.s.-china', 'washington beijing',
        'cross-strait', 'one china', 'made in china',
        'asia', 'asian', 'pacific'  # 放宽：包含 Asia/Pacific 也可能相关
    ]
    
    text = (title + ' ' + url).lower()
    return any(keyword in text for keyword in china_keywords)


def _extract_articles_from_page(html: str) -> List[Dict[str, Any]]:
    """从 AP News China hub 页面提取文章列表（只从主要内容区域提取，排除广告/推荐）"""
    soup = BeautifulSoup(html, 'html.parser')
    results: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    # 只从主要内容区域（main）提取文章，排除广告、推荐、侧边栏等
    main_content = soup.find('main')
    if main_content:
        # 只在 main 内容区域内查找文章链接
        article_links = main_content.find_all('a', href=lambda x: x and ('/article/' in x or '/video/' in x))
    else:
        # 如果没有 main 标签，回退到全页面搜索（但这种情况应该很少）
        article_links = soup.find_all('a', href=lambda x: x and ('/article/' in x or '/video/' in x))

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

        # 获取标题（尝试多种方法）
        title = clean_html(link.get_text(strip=True))
        
        # 方法1: 从标题元素获取（h1-h5）
        if not title or len(title) < 10:
            heading = link.find_parent(['h1', 'h2', 'h3', 'h4', 'h5'])
            if heading:
                title = clean_html(heading.get_text(strip=True))
        
        # 方法2: 从父元素获取
        if not title or len(title) < 10:
            parent = link.parent
            if parent:
                # 只获取文本，排除其他链接
                parent_text = parent.get_text(strip=True)
                # 如果父元素包含多个链接，只取第一个链接的文本
                other_links = parent.find_all('a')
                if len(other_links) == 1:  # 只有一个链接，使用父元素文本
                    title = clean_html(parent_text)
                else:
                    # 多个链接，只使用当前链接的文本
                    title = clean_html(link.get_text(strip=True))
        
        # 方法3: 从 data 属性获取
        if not title or len(title) < 10:
            title = link.get('aria-label') or link.get('title') or ''
            title = clean_html(title)
        
        if not title or len(title) < 10:
            continue

        # 先不过滤，收集所有文章，后续通过检查 hub 标签来过滤
        # 这样可以避免漏掉文章
        results.append({
            "title": title,
            "url": href,
            "summary": "",  # 摘要稍后从文章页面获取
            "published": None,  # 日期稍后获取
        })

    return results


def fetch_apnews_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    """
    从 AP News China hub 获取文章
    
    Args:
        date_from: 开始日期
        date_to: 结束日期
        max_pages: 最大页数（AP News 使用分页）
    
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
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    all_articles: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        url = urljoin(BASE_URL, SECTION_PATH)
        if page > 1:
            url = f"{url}?page={page}"

        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                print(f"⚠️ AP News page {page} returned status {resp.status_code}")
                continue

            articles = _extract_articles_from_page(resp.text)
            
            # 批量获取日期和摘要
            for idx, article in enumerate(articles):
                article_url = article["url"]
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)

                # 添加请求间隔，避免触发限流（每 10 篇后稍长等待）
                if idx > 0 and idx % 10 == 0:
                    import time
                    time.sleep(2)  # 每 10 篇等待 2 秒
                elif idx > 0:
                    import time
                    time.sleep(0.5)  # 每篇之间等待 0.5 秒

                # 严格过滤：标题/URL 必须包含 China 相关关键词
                # 即使有 /hub/china 标签，如果标题/URL 完全没有 China 关键词，也跳过
                # 因为 AP News 的标签系统可能不够准确
                title_lower = article["title"].lower()
                url_lower = article_url.lower()
                
                # 强关键词：明确与 China 相关
                strong_china_indicators = [
                    'china', 'chinese', 'beijing', 'shanghai', 'guangzhou', 'shenzhen',
                    'taiwan', 'taipei', 'hong kong', 'macau', 'macao',
                    'xi jinping', 'ccp', 'communist party', 'prc',
                    'tibet', 'xinjiang', 'uyghur', 'tibetan',
                    'south china sea', 'belt and road',
                    'huawei', 'tiktok', 'tencent', 'alibaba',
                    'us-china', 'u.s.-china', 'washington beijing',
                    'cross-strait', 'one china'
                ]
                has_strong_keyword = any(indicator in title_lower or indicator in url_lower for indicator in strong_china_indicators)
                
                # 必须包含强关键词（即使有 hub 标签也要求，因为标签可能不准确）
                if not has_strong_keyword:
                    continue

                # 获取日期
                published = _fetch_article_date(article_url)
                if published:
                    # 日期过滤
                    if published > date_to or published < date_from:
                        continue
                    article["published"] = published
                else:
                    # 如果没有日期，跳过（避免误判）
                    continue

                # 获取摘要（可选，如果需要的话）
                # 目前先不获取摘要，因为需要额外的请求

                all_articles.append({
                    "title": article["title"],
                    "summary": article.get("summary", ""),
                    "url": article_url,
                    "published": published,
                    "raw_source": article_url,
                })

        except Exception as e:
            print(f"⚠️ AP News page {page} fetch failed: {e}")
            continue

    return all_articles

