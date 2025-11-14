import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from utils import clean_html


BASE_URL = "https://www.csis.org"
LIST_PATH = "/regions/asia/china"
LIST_URL = f"{BASE_URL}{LIST_PATH}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DATE_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
    re.IGNORECASE,
)
SUMMARY_DATE_SUFFIX = re.compile(
    r"\s*[–-—]\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$",
    re.IGNORECASE,
)


def _parse_dt(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = dtparser.parse(ts, fuzzy=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def _extract_date(article: BeautifulSoup) -> datetime | None:
    time_tag = article.find("time")
    if time_tag:
        dt = _parse_dt(time_tag.get("datetime") or time_tag.get_text(strip=True))
        if dt:
            return dt

    candidates: list[str] = []
    for selector in [
        ".utility-xs",
        ".utility-sm",
        ".utility-md",
        ".ts-card__dek",
        ".ts-card__body",
        ".ts-card__summary",
    ]:
        elem = article.select_one(selector)
        if elem:
            candidates.append(elem.get_text(" ", strip=True))

    candidates.append(article.get_text(" ", strip=True))

    for text in candidates:
        match = DATE_PATTERN.search(text or "")
        if match:
            dt = _parse_dt(match.group(0))
            if dt:
                return dt
    return None


def _extract_summary(article: BeautifulSoup) -> str:
    selectors = [
        ".ts-card__dek",
        ".ts-card__body",
        ".ts-card__summary",
        ".node--type-podcast .field--name-field-blurb",
        "p",
    ]

    for selector in selectors:
        elem = article.select_one(selector)
        if elem:
            text = clean_html(elem.get_text(" ", strip=True))
            if not text:
                continue
            text = SUMMARY_DATE_SUFFIX.sub("", text).strip(" •-–—")
            if text:
                return text
    return ""


def fetch_csis_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
    timeout: int = 20,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(max_pages):
        # 添加请求间隔，避免触发限流
        if page > 0:
            import time
            time.sleep(1)  # 页面请求之间等待 1 秒
        
        try:
            params = {"page": page} if page else None
            resp = session.get(LIST_URL, params=params, timeout=timeout)
            if resp.status_code != 200:
                break
        except Exception:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("article")
        if not articles:
            break

        stop_paging = False

        for art in articles:
            link = art.select_one("h3 a")
            if not link or not link.get("href"):
                continue
            url = urljoin(BASE_URL, link["href"])
            if url in seen_urls:
                continue

            # 只保留 /analysis/ 路径下的文章，明确过滤掉 /events/ 和 /podcasts/
            url_lower = url.lower()
            if "/podcast/" in url_lower or "/podcasts/" in url_lower:
                continue  # 跳过 podcast
            if "/event/" in url_lower or "/events/" in url_lower:
                continue  # 跳过 events
            
            # 只保留 /analysis/ 路径下的文章
            if "/analysis/" not in url_lower:
                continue  # 跳过非 analysis 路径的文章

            published = _extract_date(art)
            if not published:
                continue

            if published > date_to:
                continue

            if published < date_from:
                stop_paging = True
                continue

            title = clean_html(link.get_text(" ", strip=True))
            summary = _extract_summary(art)

            results.append(
                {
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "published": published,
                    "raw_source": LIST_URL,
                }
            )
            seen_urls.add(url)

        if stop_paging:
            break

    return results


