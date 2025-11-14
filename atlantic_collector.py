import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import requests
from dateutil import parser as dtparser
from urllib.parse import urlparse

from utils import clean_html, url_id

API_URL = "https://graphql.theatlantic.com/"
DEFAULT_API_KEY = "JakhyMEXwa9odtB8gBxFI63ITyKqDGkn7ciGVIJf"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/118.0.0.0 Safari/537.36"
)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = dtparser.parse(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _get_api_key() -> str:
    return os.getenv("ATLANTIC_API_KEY", DEFAULT_API_KEY).strip()


def _build_variables(slug: str, first: int, after: Optional[str]) -> Dict[str, Any]:
    variables: Dict[str, Any] = {
        "first": first,
        "slug": slug,
    }
    if after:
        variables["after"] = after
    return variables


def fetch_atlantic_articles(
    *,
    feed_url: str,
    date_from: datetime,
    date_to: datetime,
    max_pages: int = 5,
    page_size: int = 36,
) -> List[Dict[str, Any]]:
    if date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    else:
        date_from = date_from.astimezone(timezone.utc)

    if date_to.tzinfo is None:
        date_to = date_to.replace(tzinfo=timezone.utc)
    else:
        date_to = date_to.astimezone(timezone.utc)
    date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=0)

    api_key = _get_api_key()
    if not api_key:
        print("⚠️ ATLANTIC_API_KEY not provided; skipping The Atlantic collection.")
        return []

    parsed = urlparse(feed_url)
    clean_path = parsed.path.rstrip("/")
    slug = clean_path.split("/")[-1]
    if not slug:
        print(f"⚠️ Unable to derive Atlantic slug from {feed_url}, skipping.")
        return []

    referer_path = clean_path if clean_path else f"/tag/{slug}/"
    referer = f"https://www.theatlantic.com{referer_path if referer_path.startswith('/') else '/' + referer_path}"
    if not referer.endswith("/"):
        referer = referer + "/"

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": os.getenv("ATLANTIC_USER_AGENT", DEFAULT_USER_AGENT),
            "Accept": "application/json",
            "x-api-key": api_key,
            "Origin": "https://www.theatlantic.com",
            "Referer": referer,
        }
    )

    results: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    after: Optional[str] = None

    for _ in range(max_pages):
        variables = _build_variables(slug=slug, first=page_size, after=after)
        # 添加请求间隔，避免触发限流
        if after is not None:  # 不是第一次请求
            import time
            time.sleep(1)  # GraphQL 请求之间等待 1 秒
        
        params = {
            "operationName": "TagRiverPage",
            "variables": json.dumps(variables),
            "extensions": json.dumps(
                {
                    "persistedQuery": {
                        "sha256Hash": "631871ffc42dfade42db85c457f9db54642874b0a7bec00d4973c69ad00dadee",
                        "version": 1,
                    }
                }
            ),
        }
        try:
            resp = session.get(API_URL, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            print(f"⚠️ Atlantic request failed: {exc}")
            break
        except ValueError:
            print("⚠️ Atlantic response was not valid JSON.")
            break

        if payload.get("errors"):
            print(f"⚠️ Atlantic returned errors: {payload['errors']}")
            break

        river = (
            payload.get("data", {})
            .get("tag", {})
            .get("river", {})
        )
        edges = river.get("edges") or []
        if not edges:
            break

        for edge in edges:
            node = edge.get("node") or {}
            article_id = node.get("id")
            if not article_id or article_id in seen_ids:
                continue
            seen_ids.add(article_id)

            published = _parse_dt(node.get("datePublished"))
            if not published:
                continue
            if published < date_from or published > date_to:
                continue

            url = node.get("url") or ""
            title = clean_html(node.get("title") or "")
            summary = ""
            image = node.get("riverImage") or {}
            if image.get("altText"):
                summary = clean_html(image["altText"])

            results.append(
                {
                    "id": url_id(url or article_id),
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "published": published,
                    "raw_source": feed_url,
                }
            )

        page_info = river.get("pageInfo") or {}
        end_cursor = page_info.get("endCursor")
        has_next = page_info.get("hasNextPage")
        if not has_next or not end_cursor:
            break
        after = end_cursor

    return results


__all__ = ["fetch_atlantic_articles"]


