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


def fetch_foreignpolicy_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    timeout: int = 20,
) -> List[Dict[str, Any]]:
    """
    Fetch articles from Foreign Policy's China project page.
    """
    soup = _fetch_project_page(timeout=timeout)
    if soup is None:
        return []

    cards = soup.select("div.project_related_articles div.excerpt-content--list")
    if not cards:
        return []

    # Collect post IDs and basic info from HTML
    post_summaries: Dict[str, Dict[str, Any]] = {}
    cards_without_id: List[Dict[str, Any]] = []

    for card in cards:
        post_id = card.get("data-post-id")
        title_tag = card.select_one("a.hed-heading")
        headline = title_tag.get_text(strip=True) if title_tag else ""
        url = title_tag["href"] if title_tag and title_tag.has_attr("href") else ""
        if url and not url.startswith("http"):
            url = urljoin(BASE_URL, url)
        summary_tag = card.select_one("div.dek-heading p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""

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
        
        meta = _fetch_post_metadata(post_id, timeout=timeout)
        if not meta:
            continue

        published = (
            _parse_dt(meta.get("date_gmt"))
            or _parse_dt(meta.get("date"))
        )
        if not published:
            continue

        if published > date_to or published < date_from:
            continue

        summary_html = meta.get("excerpt", {}).get("rendered")
        summary_text = clean_html(summary_html) if summary_html else basic.get("summary", "")

        title = clean_html(meta.get("title", {}).get("rendered")) or basic.get("title", "")
        link = meta.get("link") or basic.get("url", "")
        if link and not link.startswith("http"):
            link = urljoin(BASE_URL, link)

        articles.append(
            {
                "title": title,
                "summary": clean_html(summary_text),
                "url": link,
                "published": published,
                "raw_source": PROJECT_URL,
            }
        )

    # Fallback: include cards without ID using only HTML info (no publish date)
    # These will be treated as fetched now and may be filtered later by fetched_dt.
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
                "raw_source": PROJECT_URL,
            }
        )

    return articles


