import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import requests
from dateutil import parser as dtparser

from utils import clean_html, url_id

BASE_URL = "https://www.axios.com"
CHINA_PATH = "/world/china"


def _parse_dt(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = dtparser.parse(ts)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _load_cookie_string() -> Optional[str]:
    cookie_path = os.getenv("AXIOS_COOKIE_PATH")
    if cookie_path and os.path.exists(cookie_path):
        try:
            with open(cookie_path, "r", encoding="utf-8") as fh:
                content = fh.read().strip()
                if content:
                    return content
        except OSError as exc:
            print(f"⚠️ Failed to read AXIOS_COOKIE_PATH: {exc}")

    cookie_env = os.getenv("AXIOS_COOKIE")
    if cookie_env:
        return cookie_env.strip()

    print("⚠️ AXIOS cookie not provided; skipping Axios collection.")
    return None


def _extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    marker = '<script id="__NEXT_DATA__" type="application/json">'
    end_marker = "</script>"
    start_idx = html.find(marker)
    if start_idx == -1:
        return None
    start_idx += len(marker)
    end_idx = html.find(end_marker, start_idx)
    if end_idx == -1:
        return None
    try:
        return json.loads(html[start_idx:end_idx])
    except json.JSONDecodeError:
        return None


def _fetch_topic_json(
    session: requests.Session,
    build_id: str,
    topic_slug: str,
    subtopic_slug: str,
    page_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/_next/data/{build_id}/topic/{subtopic_slug}.json"
    params: Dict[str, Any] = {"slug": topic_slug}
    if page_token:
        params["pageToken"] = page_token
    try:
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"⚠️ Axios topic JSON returned {resp.status_code}")
            return None
        return resp.json()
    except (requests.RequestException, json.JSONDecodeError) as exc:
        print(f"⚠️ Axios topic JSON fetch failed: {exc}")
        return None


def _stories_from_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return payload["pageProps"]["data"]["hydratedStories"] or []
    except (KeyError, TypeError):
        return []


def _next_page_token(payload: Dict[str, Any]) -> Optional[str]:
    try:
        token = payload["pageProps"]["data"].get("nextPageToken")
        if token:
            return str(token)
    except (KeyError, TypeError):
        pass
    return None


def fetch_axios_articles(
    *,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    if date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    else:
        date_from = date_from.astimezone(timezone.utc)
    if date_to.tzinfo is None:
        date_to = date_to.replace(tzinfo=timezone.utc)
    else:
        date_to = date_to.astimezone(timezone.utc)
    # Include entire end day
    date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=0)

    cookie_string = _load_cookie_string()
    
    session = requests.Session()
    headers = {
        "User-Agent": os.getenv(
            "AXIOS_USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
    
    # 如果有 Cookie，添加；如果没有，尝试不用 Cookie 访问（可能可以获取部分内容）
    if cookie_string:
        headers["Cookie"] = cookie_string
    else:
        print("⚠️ AXIOS cookie not provided; attempting without cookie (may have limited access)")
    
    session.headers.update(headers)

    results: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    try:
        resp = session.get(f"{BASE_URL}{CHINA_PATH}", timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"⚠️ Axios landing page fetch failed: {exc}")
        return []

    next_data = _extract_next_data(resp.text)
    if not next_data:
        print("⚠️ Axios next.js payload missing; skipping.")
        return []

    try:
        build_id = next_data["buildId"]
        data_section = next_data["props"]["pageProps"]["data"]
        topic_slug = data_section["topic"]["slug"]
        subtopic_slug = data_section["subtopic"]["slug"]
    except (KeyError, TypeError):
        print("⚠️ Axios next.js payload malformed; skipping.")
        return []

    payload = {
        "pageProps": {
            "data": data_section,
        }
    }

    pages_fetched = 0
    while payload and pages_fetched < max_pages:
        # 添加请求间隔，避免触发限流（Cookie 认证源需要更谨慎）
        if pages_fetched > 0:
            import time
            time.sleep(1.5)  # 页面请求之间等待 1.5 秒
        
        stories = _stories_from_payload(payload)
        for story in stories:
            story_id = story.get("id")
            if not story_id or story_id in seen_ids:
                continue
            seen_ids.add(story_id)

            published = _parse_dt(story.get("timestamp"))
            if not published:
                continue
            if published < date_from or published > date_to:
                continue

            title = clean_html(story.get("headline") or "")
            url = story.get("permalink") or story.get("relativeURL") or ""
            if url and not url.startswith("http"):
                url = f"{BASE_URL}{url}"

            summary = clean_html(story.get("caption") or "")

            results.append(
                {
                    "id": url_id(url),
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "published": published,
                    "raw_source": f"{BASE_URL}{CHINA_PATH}",
                }
            )

        pages_fetched += 1
        next_token = _next_page_token(payload)
        if not next_token:
            break

        new_payload = _fetch_topic_json(
            session,
            build_id=build_id,
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            page_token=next_token,
        )
        if not new_payload:
            break
        new_stories = _stories_from_payload(new_payload)
        if not new_stories:
            break
        if all(story.get("id") in seen_ids for story in new_stories if story.get("id")):
            break
        payload = new_payload
        if _next_page_token(new_payload) == next_token:
            break

    return results


__all__ = ["fetch_axios_articles"]


