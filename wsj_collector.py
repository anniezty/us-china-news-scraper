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

WSJ_SEARCH_QUERY = {
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


def fetch_wsj_articles(*, date_from: datetime, date_to: datetime, max_pages: int = 5, timeout: int = 15) -> List[Dict[str, Any]]:
    """
    拉取 WSJ China (world/china) 相关文章。
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
                "searchQuery": WSJ_SEARCH_QUERY
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

            summary = _summary_from_article(article)
            results.append({
                "title": clean_html(title),
                "summary": summary,
                "url": url,
                "published": published_dt,
                "raw_source": "https://www.wsj.com/world/china",
            })

        if stop_paging:
            break

    return results


