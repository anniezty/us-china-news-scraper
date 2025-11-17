from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from utils import clean_html

BASE_URL = "https://foreignpolicy.com"
PROJECT_PATH = "/projects/china/"
PROJECT_URL = urljoin(BASE_URL, PROJECT_PATH)
ASIA_PATH = "/projects/asia/"
ASIA_URL = urljoin(BASE_URL, ASIA_PATH)
WP_POST_ENDPOINT = urljoin(BASE_URL, "/wp-json/wp/v2/posts")


def _parse_dt(ts: str | None) -> datetime | None:
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


def _fetch_project_page(timeout: int = 20) -> BeautifulSoup | None:
    try:
        resp = requests.get(
            PROJECT_URL,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return None


def _fetch_asia_page(timeout: int = 20, page: int = 1) -> BeautifulSoup | None:
    """Fetch Asia project page"""
    try:
        # 支持分页
        if page > 1:
            url = f"{ASIA_URL}page/{page}/"
        else:
            url = ASIA_URL
        
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return None


def _is_china_related(title: str, summary: str) -> bool:
    """
    判断文章是否与 China 相关（用于过滤 Asia section 的文章）
    """
    text = f"{title} {summary}".lower()
    
    # China 相关关键词
    china_keywords = [
        'china', 'chinese', 'beijing', 'shanghai', 'guangzhou', 'shenzhen',
        'taiwan', 'taipei', 'hong kong', 'macau', 'macao',
        'xi jinping', 'ccp', 'communist party', 'prc',
        'tibet', 'xinjiang', 'uyghur', 'tibetan',
        'south china sea', 'belt and road',
        'huawei', 'tiktok', 'tencent', 'alibaba',
        'us-china', 'u.s.-china', 'washington beijing',
        'cross-strait', 'one china'
    ]
    
    return any(keyword in text for keyword in china_keywords)


def _fetch_post_metadata(post_id: str, timeout: int = 20) -> Dict[str, Any] | None:
    """
    Fetch metadata for a single post ID.
    """
    try:
        resp = requests.get(
            f"{WP_POST_ENDPOINT}/{post_id}",
            params={"_embed": "1"},
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def _extract_articles_from_page(soup: BeautifulSoup, source_url: str, filter_china_related: bool = False) -> List[Dict[str, Any]]:
    """
    从页面提取文章（通用函数）
    
    Args:
        soup: BeautifulSoup 对象
        source_url: 来源 URL
        filter_china_related: 是否过滤 China 相关文章
    """
    # 尝试多种选择器（China project page 和 Asia Pacific page 结构不同）
    cards = soup.select("div.project_related_articles div.excerpt-content--list")
    if not cards:
        # 尝试 Asia Pacific page 的选择器（有 data-post-id 的元素）
        cards = soup.select("[data-post-id]")
        # 过滤掉重复的（同一个 post-id 可能有多个元素，只保留一个）
        seen_ids = set()
        unique_cards = []
        for card in cards:
            post_id = card.get("data-post-id")
            if post_id and post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_cards.append(card)
        cards = unique_cards
    
    if not cards:
        return []

    # Collect post IDs and basic info from HTML
    post_summaries: Dict[str, Dict[str, Any]] = {}
    cards_without_id: List[Dict[str, Any]] = []

    for card in cards:
        post_id = card.get("data-post-id")
        
        # 尝试多种方式找到标题和链接
        title_tag = None
        headline = ""
        url = ""
        
        # 方法1: 尝试 H2 中的链接
        h2 = card.find("h2")
        if h2:
            h2_link = h2.find("a")
            if h2_link:
                title_tag = h2_link
                headline = h2_link.get_text(strip=True)
                url = h2_link.get("href", "")
        
        # 方法2: 如果 H2 没有链接，查找所有链接，找到最可能是文章标题的
        if not title_tag or not url:
            all_links = card.find_all("a", href=True)
            for link in all_links:
                href = link.get("href", "")
                text = link.get_text(strip=True)
                # 文章链接通常：
                # 1. 指向 foreignpolicy.com
                # 2. 包含日期路径（如 /2025/ 或 /2024/）
                # 3. 文本较长（标题）
                if text and len(text) > 15:
                    if "foreignpolicy.com" in href or (href.startswith("/") and "/20" in href):
                        title_tag = link
                        headline = text
                        url = href
                        break
        
        # 如果还是没有找到，尝试其他选择器
        if not title_tag:
            title_tag = card.select_one("a.hed-heading, h3 a, a.headline")
            if title_tag:
                headline = title_tag.get_text(strip=True)
                url = title_tag.get("href", "")
        
        if url and not url.startswith("http"):
            url = urljoin(BASE_URL, url)
        
        summary_tag = card.select_one("div.dek-heading p, div.excerpt p, p.excerpt, div.excerpt-content p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""

        # 如果设置了过滤，提前过滤非 China 相关文章
        if filter_china_related and not _is_china_related(headline, summary):
            continue

        record = {
            "title": headline,
            "url": url,
            "summary": summary,
        }

        if post_id:
            post_summaries[post_id] = record
        else:
            cards_without_id.append(record)

    # Fetch metadata via REST API for cards with IDs
    articles: List[Dict[str, Any]] = []

    # Combine metadata with HTML info
    for idx, (post_id, basic) in enumerate(post_summaries.items()):
        # 添加请求间隔，避免触发限流
        if idx > 0:
            import time
            time.sleep(0.5)  # API 请求之间等待 0.5 秒
        
        meta = _fetch_post_metadata(post_id, timeout=20)
        if not meta:
            continue

        published = (
            _parse_dt(meta.get("date_gmt"))
            or _parse_dt(meta.get("date"))
        )
        if not published:
            continue

        summary_html = meta.get("excerpt", {}).get("rendered")
        summary_text = clean_html(summary_html) if summary_html else basic.get("summary", "")

        title = clean_html(meta.get("title", {}).get("rendered")) or basic.get("title", "")
        link = meta.get("link") or basic.get("url", "")
        if link and not link.startswith("http"):
            link = urljoin(BASE_URL, link)

        # 如果设置了过滤，再次检查（因为 API 返回的摘要可能更完整）
        if filter_china_related and not _is_china_related(title, summary_text):
            continue

        articles.append(
            {
                "title": title,
                "summary": clean_html(summary_text),
                "url": link,
                "published": published,
                "raw_source": source_url,
            }
        )

    # Fallback: include cards without ID using only HTML info (no publish date)
    for record in cards_without_id:
        link = record.get("url")
        if not link:
            continue
        articles.append(
            {
                "title": clean_html(record.get("title", "")),
                "summary": clean_html(record.get("summary", "")),
                "url": link,
                "published": None,
                "raw_source": source_url,
            }
        )

    return articles


def fetch_foreignpolicy_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    timeout: int = 20,
    include_asia_pacific: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch articles from Foreign Policy.
    
    包括：
    1. China project page 的文章（原有，完整收集）
    2. Asia project page 中的 China 相关文章（新增，可选）
    
    Args:
        date_from: 开始日期
        date_to: 结束日期
        timeout: 超时时间
        include_asia_pacific: 是否包含 Asia project page 的 China 相关文章（默认 True）
    
    Returns:
        去重后的文章列表（按 URL 去重）
    """
    all_articles: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()
    
    # 1. 拉取 China project page 的文章（原有，完整收集）
    china_soup = _fetch_project_page(timeout=timeout)
    if china_soup:
        china_articles = _extract_articles_from_page(
            china_soup, 
            source_url=PROJECT_URL,
            filter_china_related=False  # China project page 的文章都是 China 相关的
        )
        
        for article in china_articles:
            # 过滤日期
            published = article.get("published")
            if published:
                if published > date_to or published < date_from:
                    continue
            
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(article)
    
    # 2. 拉取 Asia project page 中的 China 相关文章（新增）
    if include_asia_pacific:
        max_pages = 3
        for page_num in range(1, max_pages + 1):
            asia_soup = _fetch_asia_page(timeout=timeout, page=page_num)
            if not asia_soup:
                break
            
            asia_articles = _extract_articles_from_page(
                asia_soup,
                source_url=ASIA_URL if page_num == 1 else f"{ASIA_URL}page/{page_num}/",
                filter_china_related=True
            )
            
            if not asia_articles:
                break
            
            added_any = False
            for article in asia_articles:
                published = article.get("published")
                if published:
                    if published > date_to or published < date_from:
                        continue
                
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(article)
                    added_any = True
            
            if not added_any:
                # 如果这一页没有任何符合条件的新文章，尝试下一页，
                # 但若连续页都没有新文章，循环会自然在 soup/articles 为空时停止
                continue
    
    return all_articles


