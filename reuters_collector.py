from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urljoin

from dateutil import parser as dtparser

from utils import clean_html

BASE_URL = "https://www.reuters.com"
SECTION_PATH = "/world/china/"
API_URL = f"{BASE_URL}/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1"
PAGE_SIZE = 20
SCRAPER_BROWSER = {"browser": "chrome", "platform": "darwin", "desktop": True}
HEADERS = {
    "Referer": urljoin(BASE_URL, SECTION_PATH),
    "Origin": BASE_URL,
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


def fetch_reuters_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 10,
    timeout: int = 20,
) -> List[Dict[str, Any]]:
    """
    Fetch Reuters China section articles using the Arc Publishing API.
    """
    try:
        import cloudscraper
    except ImportError as exc:  # pragma: no cover - defensive
        raise RuntimeError("cloudscraper is required for Reuters collection") from exc

    scraper = cloudscraper.create_scraper(browser=SCRAPER_BROWSER)
    results: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for page in range(max_pages):
        # 添加请求间隔，避免触发限流
        if page > 0:
            import time
            time.sleep(1)  # API 请求之间等待 1 秒
        
        offset = page * PAGE_SIZE
        query = {
            "arc-site": "reuters",
            "fetch_type": "collection",
            "offset": offset,
            "requestId": page,
            "section_id": SECTION_PATH,
            "size": str(PAGE_SIZE),
            "uri": SECTION_PATH,
            "website": "reuters",
        }
        params = {
            "query": json.dumps(query, separators=(",", ":")),
            "d": "331",
            "_website": "reuters",
        }

        try:
            resp = scraper.get(API_URL, params=params, headers=HEADERS, timeout=timeout)
        except Exception:
            break

        if resp.status_code != 200:
            break

        try:
            data = json.loads(resp.text)
        except Exception:
            break

        articles = (data.get("result") or {}).get("articles") or []
        if not articles:
            break

        for article in articles:
            url = article.get("canonical_url") or article.get("web", {}).get("url")
            if not url:
                continue
            if not url.startswith("http"):
                url = urljoin(BASE_URL, url)
            if url in seen_urls:
                continue

            published = (
                _parse_dt(article.get("published_time"))
                or _parse_dt(article.get("updated_time"))
                or _parse_dt(article.get("display_time"))
            )
            if not published:
                continue

            if published > date_to:
                continue

            if published < date_from:
                continue

            title = article.get("title") or article.get("basic_headline") or ""
            summary = article.get("description") or ""

            results.append(
                {
                    "title": clean_html(title),
                    "summary": clean_html(summary),
                    "url": url,
                    "published": published,
                    "raw_source": urljoin(BASE_URL, SECTION_PATH),
                }
            )
            seen_urls.add(url)

    return results


