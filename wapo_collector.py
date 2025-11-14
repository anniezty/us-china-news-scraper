from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import json
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from utils import clean_html

BASE_URL = "https://www.washingtonpost.com"
SECTION_PATH = "/world/asia-pacific/"
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


def _load_cookie_header() -> Optional[str]:
    cookie_path = os.getenv("WAPO_COOKIE_PATH")
    if not cookie_path:
        return None
    try:
        with open(cookie_path, "r", encoding="utf-8") as f:
            cookie = f.read().strip()
            return cookie if cookie else None
    except Exception:
        return None


def _make_session() -> Optional[requests.Session]:
    cookie_header = _load_cookie_header()
    if not cookie_header:
        print("⚠️ WAPO cookie header not found. Set WAPO_COOKIE_PATH to a file containing the Cookie header.")
        return None

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": os.getenv(
                "WAPO_USER_AGENT",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Cookie": cookie_header,
        }
    )
    return session


def _extract_articles_from_html(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []

    data_script = soup.find("script", type="application/json")
    if not data_script or not data_script.string:
        return results

    try:
        data = json.loads(data_script.string)
    except json.JSONDecodeError:
        return results

    items = (
        data.get("props", {})
        .get("pageProps", {})
        .get("globalContent", {})
        .get("items", [])
    )

    for item in items:
        title = clean_html(item.get("headlines", {}).get("basic", ""))
        link = item.get("canonical_url") or item.get("website_url") or ""
        if not link:
            continue
        if not link.startswith("http"):
            link = urljoin(BASE_URL, link)

        summary = clean_html(item.get("description", {}).get("basic", ""))
        published = _parse_dt(
            item.get("display_date")
            or item.get("publish_date")
            or item.get("created_date")
        )

        results.append(
            {
                "title": title,
                "summary": summary,
                "url": link,
                "published": published,
            }
        )

    return results


def fetch_wapo_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    session = _make_session()
    if session is None:
        return []

    articles: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        # 添加请求间隔，避免触发限流（Cookie 认证源需要更谨慎）
        if page > 1:
            import time
            time.sleep(1.5)  # 页面之间等待 1.5 秒
        
        url = urljoin(BASE_URL, SECTION_PATH)
        if page > 1:
            url = f"{url}?page={page}"

        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                print(f"⚠️ WAPO page {page} returned status {resp.status_code}")
                continue
            results = _extract_articles_from_html(resp.text)
        except Exception as e:
            print(f"⚠️ WAPO page {page} fetch failed: {e}")
            continue

        for item in results:
            link = item["url"]
            if link in seen_urls:
                continue
            seen_urls.add(link)

            published = item.get("published")
            if published:
                if published > date_to or published < date_from:
                    continue
            else:
                # If no publish date available, skip to avoid mis-timed entries.
                continue

            articles.append(
                {
                    "title": item["title"],
                    "summary": item["summary"],
                    "url": link,
                    "published": published,
                    "raw_source": url,
                }
            )

    return articles


