import requests
from datetime import datetime, timezone
from dateutil import parser as dtparser
from typing import List, Dict, Any

from utils import clean_html


WSJ_GRAPHQL_ENDPOINT = "https://shared-data.dowjones.io/gateway/graphql"

WSJ_GRAPHQL_QUERY = """
query ArticlesByContentType($searchQuery: SearchQuery!, $contentType: [SearchContentType], $page: Int) {
  articlesByContentType(searchQuery: $searchQuery, contentType: $contentType, page: $page) {
    headline { text }
    sourceUrl
    publishedDateTimeUtc
    liveDateTimeUtc
    articleFlashline { text }
    flattenedSummary {
      flashline { text }
      headline { text }
      description {
        content { text }
      }
      list {
        items {
          text
        }
      }
    }
  }
}
"""

WSJ_DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.wsj.com",
    "Referer": "https://www.wsj.com/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "ApolloGraphQL-Client-Name": "wsj:autofeed",
}

# China section 的搜索查询（原有）
WSJ_SEARCH_QUERY_CHINA = {
    "and": [
        {"terms": {"key": "Product", "value": ["WSJ.com", "WSJ Blogs"]}}
    ],
    "not": [
        {"terms": {"key": "SectionName", "value": ["Opinion"]}},
        {"terms": {"key": "SectionName", "value": [
            "Breaking News China Traditional",
            "Corrections and Amplifications",
            "Decos and Corrections",
            "Direct Push Alert",
            "DJON Wire",
            "NewsPlus",
            "Opinion",
            "WSJ Puzzles"
        ]}},
        {"terms": {"key": "SectionType", "value": [
            "Breaking News China Simplified",
            "Board Pack Exclusive",
            "Cryptic",
            "Crossword",
            "Crossword Contest",
            "Deco Summary (Content)",
            "Deco Summary (Plain)",
            "Deco Summary Barrons Cover Story",
            "Deco Summary Barrons Market Week",
            "Deco Summary Barrons Preview",
            "Deco Summary Japanese",
            "Deco Summary Liondoor",
            "Infogrfx Slide Show",
            "Infogrfx House Of The Day",
            "Pepper%20%26%20Salt",
            "Pro Bankruptcy Data Tables",
            "Recipes",
            "Style & Substance",
            "Whats News",
            "Whats News Business Finance",
            "Whats News World Wide"
        ]}}
    ],
    "or": [
        {"terms": {"key": "DJEThing", "value": ["world/china"]}}
    ],
    "sort": [
        {"key": "LiveDate", "order": "desc"}
    ]
}

# World/Asia section 的 China 相关文章搜索查询（新增）
# 注意：只搜索 world/asia，不搜索整个 world section（因为 world section 文章量太大）
# 由于 GraphQL API 的限制，我们无法直接在查询中排除 world/china
# 所以我们在应用层通过 URL 去重来避免重复
WSJ_SEARCH_QUERY_WORLD_ASIA = {
    "and": [
        {"terms": {"key": "Product", "value": ["WSJ.com", "WSJ Blogs"]}},
        # 只搜索 world/asia section（不搜索整个 world section，因为文章量太大）
        {"terms": {"key": "DJEThing", "value": ["world/asia"]}}
    ],
    "not": [
        {"terms": {"key": "SectionName", "value": ["Opinion"]}},
        {"terms": {"key": "SectionName", "value": [
            "Breaking News China Traditional",
            "Corrections and Amplifications",
            "Decos and Corrections",
            "Direct Push Alert",
            "DJON Wire",
            "NewsPlus",
            "Opinion",
            "WSJ Puzzles"
        ]}},
        {"terms": {"key": "SectionType", "value": [
            "Breaking News China Simplified",
            "Board Pack Exclusive",
            "Cryptic",
            "Crossword",
            "Crossword Contest",
            "Deco Summary (Content)",
            "Deco Summary (Plain)",
            "Deco Summary Barrons Cover Story",
            "Deco Summary Barrons Market Week",
            "Deco Summary Barrons Preview",
            "Deco Summary Japanese",
            "Deco Summary Liondoor",
            "Infogrfx Slide Show",
            "Infogrfx House Of The Day",
            "Pepper%20%26%20Salt",
            "Pro Bankruptcy Data Tables",
            "Recipes",
            "Style & Substance",
            "Whats News",
            "Whats News Business Finance",
            "Whats News World Wide"
        ]}}
    ],
    "or": [
        # 只搜索 world/asia section（更精确，减少文章量）
        {"terms": {"key": "DJEThing", "value": ["world/asia"]}}
    ],
    "sort": [
        {"key": "LiveDate", "order": "desc"}
    ]
}


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


def _summary_from_article(article: Dict[str, Any]) -> str:
    flattened = article.get("flattenedSummary") or {}
    parts: List[str] = []

    flashline = flattened.get("flashline", {}) or {}
    if flashline.get("text"):
        parts.append(flashline["text"])

    description = flattened.get("description", {}) or {}
    content = description.get("content")
    if isinstance(content, dict):
        text = content.get("text")
        if text:
            parts.append(text)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
            else:
                text = str(block)
            if text:
                parts.append(text)
    elif isinstance(content, str):
        parts.append(content)

    list_block = flattened.get("list", {}) or {}
    items = list_block.get("items") or []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text")
        else:
            text = str(item)
        if text:
            parts.append(text)

    article_flashline = article.get("articleFlashline", {}) or {}
    if article_flashline.get("text"):
        parts.append(article_flashline["text"])

    cleaned = clean_html(" ".join(parts))
    if not cleaned:
        headline = (article.get("headline") or {}).get("text") or ""
        cleaned = clean_html(headline)
    return cleaned


def _is_china_related(title: str, summary: str) -> bool:
    """
    判断文章是否与 China 相关（用于过滤 world section 的文章）
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


def _fetch_wsj_articles_by_query(
    search_query: dict,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
    timeout: int = 15,
    raw_source: str = "https://www.wsj.com",
    filter_china_related: bool = False
) -> List[Dict[str, Any]]:
    """
    根据搜索查询拉取 WSJ 文章（通用函数）
    
    Args:
        search_query: GraphQL 搜索查询
        date_from: 开始日期
        date_to: 结束日期
        max_pages: 最大页数
        timeout: 超时时间
        raw_source: 原始来源 URL
        filter_china_related: 是否过滤 China 相关文章（用于 world section）
    """
    results: List[Dict[str, Any]] = []
    session = requests.Session()

    for page in range(max_pages):
        # 添加请求间隔，避免触发限流
        if page > 0:
            import time
            time.sleep(1)  # GraphQL 请求之间等待 1 秒
        
        payload = {
            "query": WSJ_GRAPHQL_QUERY,
            "variables": {
                "contentType": ["ARTICLE"],
                "page": page,
                "searchQuery": search_query
            }
        }

        try:
            resp = session.post(
                WSJ_GRAPHQL_ENDPOINT,
                json=payload,
                headers=WSJ_DEFAULT_HEADERS,
                timeout=timeout
            )
            if resp.status_code != 200:
                break
            data = resp.json()
        except Exception:
            break

        articles = (data.get("data") or {}).get("articlesByContentType") or []
        if not articles:
            break

        stop_paging = False
        for article in articles:
            url = article.get("sourceUrl")
            title = (article.get("headline") or {}).get("text")
            published_dt = _parse_dt(article.get("publishedDateTimeUtc")) or _parse_dt(article.get("liveDateTimeUtc"))

            if not url or not title or not published_dt:
                continue

            if published_dt > date_to:
                continue

            if published_dt < date_from:
                stop_paging = True
                continue

            # 如果设置了 filter_china_related，过滤非 China 相关文章
            if filter_china_related:
                summary = _summary_from_article(article)
                if not _is_china_related(title, summary):
                    continue

            summary = _summary_from_article(article)
            results.append({
                "title": clean_html(title),
                "summary": summary,
                "url": url,
                "published": published_dt,
                "raw_source": raw_source,
            })

        if stop_paging:
            break

    return results


def fetch_wsj_articles(*, date_from: datetime, date_to: datetime, max_pages: int = 5, timeout: int = 15, include_world_asia: bool = True) -> List[Dict[str, Any]]:
    """
    拉取 WSJ China 相关文章。
    
    包括：
    1. world/china section 的文章（原有，完整收集）
    2. world/asia section 中的 China 相关文章（新增，可选）
    
    策略优化：
    - 只搜索 world/asia，不搜索整个 world section（因为 world section 文章量太大）
    - world/asia 只取前 3 页（减少处理量，因为大部分 China 相关文章会在前几页）
    - 通过 URL 去重，避免与 world/china section 重复
    
    Args:
        date_from: 开始日期
        date_to: 结束日期
        max_pages: world/china section 的最大页数（默认 5）
        timeout: 超时时间
        include_world_asia: 是否包含 world/asia section 的 China 相关文章（默认 True）
    
    Returns:
        去重后的文章列表（按 URL 去重）
    """
    all_results: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()
    
    # 1. 拉取 world/china section 的文章（原有，完整收集）
    china_section_results = _fetch_wsj_articles_by_query(
        search_query=WSJ_SEARCH_QUERY_CHINA,
        date_from=date_from,
        date_to=date_to,
        max_pages=max_pages,  # 保持原有的页数
        timeout=timeout,
        raw_source="https://www.wsj.com/world/china",
        filter_china_related=False  # world/china section 的文章都是 China 相关的，不需要过滤
    )
    
    for article in china_section_results:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            all_results.append(article)
    
    # 2. 拉取 world/asia section 中的 China 相关文章（新增，只取前 3 页以减少处理量）
    if include_world_asia:
        # 只取前 3 页，因为：
        # 1. world/asia section 文章量较大
        # 2. 大部分 China 相关文章会在前几页（按时间排序）
        # 3. 减少处理量，提高速度
        world_asia_max_pages = min(3, max_pages)  # 最多 3 页
        
        world_asia_results = _fetch_wsj_articles_by_query(
            search_query=WSJ_SEARCH_QUERY_WORLD_ASIA,
            date_from=date_from,
            date_to=date_to,
            max_pages=world_asia_max_pages,  # 只取前 3 页
            timeout=timeout,
            raw_source="https://www.wsj.com/world/asia",
            filter_china_related=True  # 过滤非 China 相关文章（因为 world/asia 包含很多非 China 文章）
        )
        
        for article in world_asia_results:
            url = article.get("url", "")
            # 去重：如果 URL 已存在（在 world/china section 中），跳过（避免重复）
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(article)
    
    return all_results


