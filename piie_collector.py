"""
PIIE Collector
Extract articles from PIIE China research page using Drupal AJAX interface:
  https://www.piie.com/views/ajax

Uses the Drupal AJAX interface for more efficient data retrieval.
Supports pagination via page parameter.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from urllib.parse import urljoin

BASE = "https://www.piie.com"
AJAX_URL = "https://www.piie.com/views/ajax"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

AJAX_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.piie.com/research/china",
    "Accept-Language": "en-US,en;q=0.9",
}


def _extract_date_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    # Common patterns like: November 5, 2025; 5 November 2025; 2025-11-05
    patterns = [
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
        r"\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
        r"\d{4}-\d{2}-\d{2}",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return dtparser.parse(m.group(0)).isoformat()
            except Exception:
                pass
    return None


def _parse_ajax_html(html_content: str) -> List[Dict]:
    """Parse HTML content from AJAX response to extract articles"""
    soup = BeautifulSoup(html_content, "html.parser")
    articles: List[Dict] = []
    seen = set()

    # Search for article links
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = urljoin(BASE, href)

        if "piie.com" not in href:
            continue

        # Likely article paths
        if not any(seg in href for seg in [
            "/blogs/", "/blog/", "/publications/", "/working-papers/", "/commentary/", "/events/", "/policy-brief/"
        ]):
            continue

        if href in seen:
            continue
        seen.add(href)

        # Extract title
        title = a.get_text(strip=True)
        if not title or len(title) < 15:
            # Climb up to find headings
            parent = a.parent
            for _ in range(5):
                if not parent:
                    break
                h = parent.find(["h1", "h2", "h3", "h4", "h5"])
                if h:
                    t = h.get_text(strip=True)
                    if t and len(t) >= 15:
                        title = t
                        break
                parent = parent.parent

        if not title or len(title) < 15:
            continue

        # Find date near link
        published = None
        container = a.parent
        for _ in range(5):
            if not container:
                break
            # time tag
            time_tag = container.find("time")
            if time_tag:
                dt_text = time_tag.get("datetime") or time_tag.get_text(strip=True)
                parsed = _extract_date_from_text(dt_text)
                if parsed:
                    published = parsed
                    break
            # any date-like text
            d = _extract_date_from_text(container.get_text(" "))
            if d:
                published = d
                break
            container = container.parent

        articles.append({
            "url": href,
            "title": title,
            "summary": "",
            "published": published,
        })

    return articles


def _fetch_ajax_page(session: requests.Session, page: int = 0) -> List[Dict]:
    """Fetch a single page from AJAX interface"""
    params = {
        "_wrapper_format": "drupal_ajax",
        "view_name": "taxonomy_detail_page",
        "view_display_id": "taxonomy_detail_page",
        "view_args": "181",  # China category ID
        "view_path": "/taxonomy/term/181",
        "view_base_path": "taxonomy/term/%",
        "pager_element": "0",
        "page": str(page),
        "_drupal_ajax": "1",
    }

    try:
        response = session.get(AJAX_URL, params=params, headers=AJAX_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Find HTML content in response
                for item in data:
                    if isinstance(item, dict):
                        cmd = item.get("command", "")
                        if cmd in ["insert", "replace", "prepend", "append"]:
                            html_content = item.get("data", "")
                            if html_content:
                                return _parse_ajax_html(html_content)
        return []
    except Exception as e:
        print(f"⚠️ PIIE AJAX request failed for page {page}: {e}")
        return []


def fetch_piie_articles(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    max_pages: int = 10,  # Increased from 3 since AJAX is more efficient
    max_retries: int = 3,
) -> List[Dict]:
    """
    Fetch articles from PIIE using Drupal AJAX interface.
    
    Args:
        date_from: Start date for filtering (optional)
        date_to: End date for filtering (optional)
        max_pages: Maximum number of pages to fetch (default: 10)
        max_retries: Maximum retry attempts per page (default: 3)
    
    Returns:
        List of article dictionaries with url, title, summary, published fields
    """
    # Normalize dates to UTC bounds
    if date_from and date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    if date_to and date_to.tzinfo is None:
        date_to = date_to.replace(tzinfo=timezone.utc)

    # Create session for cookie handling
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Try to get initial cookies (optional, may not be needed)
    try:
        session.get("https://www.piie.com/research/china", timeout=10)
    except:
        pass

    results: List[Dict] = []
    for page in range(0, max_pages):
        items = []
        for attempt in range(max_retries):
            try:
                items = _fetch_ajax_page(session, page)
                
                if items:
                    # Date filter
                    if date_from or date_to:
                        filtered = []
                        for it in items:
                            ts = it.get("published")
                            if not ts:
                                # If no date, include it (let collector handle filtering)
                                filtered.append(it)
                                continue
                            try:
                                dt = dtparser.parse(ts)
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                                # bounds
                                if date_from and dt < date_from:
                                    continue
                                if date_to and dt > date_to:
                                    continue
                                filtered.append(it)
                            except Exception:
                                # If date parsing fails, include it
                                filtered.append(it)
                        items = filtered
                    
                    results.extend(items)
                    break
                elif attempt < max_retries - 1:
                    time.sleep(1 + attempt)
                    continue
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
        
        # If no items found, might have reached the end
        if not items and page > 0:
            break
            
        if page < max_pages - 1:
            time.sleep(0.5)  # Reduced delay since AJAX is faster

    # Deduplicate by URL
    seen = set()
    uniq: List[Dict] = []
    for it in results:
        if it["url"] not in seen:
            seen.add(it["url"])
            uniq.append(it)
    return uniq


