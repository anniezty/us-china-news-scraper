"""
Nikkei Asia Collector
Extract articles from Nikkei Asia China news page
Based on: https://asia.nikkei.com/location/east-asia/china
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin
from datetime import datetime, timezone
from dateutil import parser as dtparser

NIKKEI_BASE_URL = "https://asia.nikkei.com"
NIKKEI_CHINA_URL = "https://asia.nikkei.com/location/east-asia/china"

NIKKEI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def extract_date_from_text(text):
    """Extract date from text"""
    if not text:
        return None
    
    # Match "28 October 2025" format
    date_pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})'
    match = re.search(date_pattern, text, re.IGNORECASE)
    if match:
        try:
            return dtparser.parse(match.group(1)).isoformat()
        except:
            pass
    
    # Match ISO format "2025-10-28"
    iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if iso_match:
        return iso_match.group(1)
    
    return None

def extract_articles_from_page(html_content, date_from=None, date_to=None):
    """
    Extract articles from listing page
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []
    seen_urls = set()
    
    # Find all article links
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        if not href:
            continue
        
        # Build full URL
        if not href.startswith('http'):
            href = urljoin(NIKKEI_BASE_URL, href)
        
        # Exclude non-article links
        if any(skip in href for skip in ['/location/', '/tag/', '/member/', '/marketing/', '/category/', '/about', '/help']):
            continue
        
        # Check if it's an article link (URL typically has multiple parts, last part is article slug)
        # Parse URL to get path segments (excluding domain)
        try:
            from urllib.parse import urlparse
            parsed = urlparse(href)
            path_segments = [p for p in parsed.path.split('/') if p]  # Path segments only, excluding domain
        except:
            path_segments = [p for p in href.split('/') if p]
            # Remove domain if present
            if len(path_segments) > 0 and '.' in path_segments[0]:
                path_segments = path_segments[1:]
        
        # Article link features:
        # 1. At least 2 path segments (e.g., /politics/article-slug or /politics/category/article-slug)
        # 2. Last segment is article slug (usually long, contains hyphens)
        if len(path_segments) < 2:
            continue
        
        last_part = path_segments[-1]
        # Article slug usually:
        # - Length >= 20 characters (longer than category names)
        # - Contains hyphens or underscores
        # - No file extensions
        if (len(last_part) < 20 or 
            ('-' not in last_part and '_' not in last_part) or
            '.' in last_part):
            continue
        
        # Exclude category pages: URLs with 2 path segments where the last part is short (category name)
        # e.g., /politics/international-relations (category page, last part is short)
        # vs /politics/thai-king-heads-to-china-for-landmark-state-visit (article, last part is long slug)
        # If 2 segments and last part is long slug (>= 20 chars), it's an article
        # If 2 segments and last part is short, it's likely a category page
        if len(path_segments) == 2 and len(last_part) < 20:
            continue
        
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        # Extract title - prioritize h4 element (Nikkei's structure)
        title = None
        
        # Method 1: Find h4 element in parent container (Nikkei uses h4 for article titles)
        parent = link.parent
        for _ in range(3):  # Search up to 3 levels
            if not parent:
                break
            
            # Priority: h4 element (Nikkei's article title structure)
            h4_elem = parent.find('h4')
            if h4_elem:
                h4_text = h4_elem.get_text(strip=True)
                if h4_text and len(h4_text) >= 30:  # Title should be at least 30 chars
                    title = h4_text
                    break
            
            # Fallback: other heading elements
            if not title:
                title_elem = parent.find(['h1', 'h2', 'h3', 'h5', 'h6'])
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) >= 30:
                        title = title_text
                        break
            
            parent = parent.parent
        
        # Method 2: From link text (if h4 not found)
        if not title or len(title) < 30:
            link_text = link.get_text(strip=True)
            if link_text and len(link_text) >= 30:
                title = link_text
        
        # Method 3: From link attributes
        if not title or len(title) < 30:
            aria_label = link.get('aria-label')
            if aria_label and len(aria_label) >= 30:
                title = aria_label
            else:
                title_attr = link.get('title')
                if title_attr and len(title_attr) >= 30:
                    title = title_attr
        
        # Title must be long enough (at least 30 characters for complete sentence)
        if not title or len(title) < 30:
            continue
        
        # Exclude category names and navigation items
        title_lower = title.lower()
        # Category names are usually short phrases
        category_names = ['international relations', 'companies', 'politics', 'economy', 'business', 
                         'tech', 'markets', 'defense', 'trade war', 'electric cars in china',
                         'trump administration', 'artificial intelligence', 'editor-in-chief\'s picks']
        if title_lower in category_names:
            continue
        
        # Exclude navigation items
        nav_items = ['read more', 'more', 'view all', 'see all', 'next', 'previous', 'back', 'home']
        if title_lower in nav_items:
            continue
        
        # Try to extract date from listing page
        published = None
        
        # Method 1: Find nearby time tag or date text
        parent = link.parent
        if parent:
            # Find time tag
            time_tag = parent.find('time')
            if time_tag:
                date_attr = time_tag.get('datetime')
                if date_attr:
                    published = date_attr
                else:
                    time_text = time_tag.get_text(strip=True)
                    if time_text:
                        published = extract_date_from_text(time_text)
            
            # If time tag not found, find date in container text
            if not published:
                container_text = parent.get_text()
                published = extract_date_from_text(container_text)
        
        # Method 2: Find date from link's row
        if not published:
            # Find link's row or container
            row = link
            for _ in range(3):  # Search up to 3 levels
                row = row.parent if row else None
                if not row:
                    break
                row_text = row.get_text()
                published = extract_date_from_text(row_text)
                if published:
                    break
        
        articles.append({
            'url': href,
            'title': title,
            'summary': '',
            'published': published,
        })
    
    return articles

def fetch_nikkei_articles(date_from=None, date_to=None, max_pages=3, max_retries=3):
    """
    Fetch articles from Nikkei Asia
    
    Args:
        date_from: Start date (datetime or string, e.g., "2025-11-01")
        date_to: End date (datetime or string, e.g., "2025-11-05")
        max_pages: Maximum number of pages
        max_retries: Maximum retry attempts
    
    Returns:
        list: List of articles
    """
    from datetime import datetime, timezone
    from dateutil import parser as dtparser
    
    # Convert date parameters to datetime objects
    if date_from:
        if isinstance(date_from, str):
            date_from_dt = dtparser.parse(date_from)
            if date_from_dt.tzinfo is None:
                date_from_dt = date_from_dt.replace(tzinfo=timezone.utc)
            else:
                date_from_dt = date_from_dt.astimezone(timezone.utc)
            date_from = date_from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif isinstance(date_from, datetime):
            if date_from.tzinfo is None:
                date_from = date_from.replace(tzinfo=timezone.utc)
            else:
                date_from = date_from.astimezone(timezone.utc)
    
    if date_to:
        if isinstance(date_to, str):
            date_to_dt = dtparser.parse(date_to)
            if date_to_dt.tzinfo is None:
                date_to_dt = date_to_dt.replace(tzinfo=timezone.utc)
            else:
                date_to_dt = date_to_dt.astimezone(timezone.utc)
            date_to = date_to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif isinstance(date_to, datetime):
            if date_to.tzinfo is None:
                date_to = date_to.replace(tzinfo=timezone.utc)
            else:
                date_to = date_to.astimezone(timezone.utc)
    
    all_articles = []
    
    for page in range(1, max_pages + 1):
        url = f"{NIKKEI_CHINA_URL}?page={page}" if page > 1 else NIKKEI_CHINA_URL
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=NIKKEI_HEADERS, timeout=15)
                
                if response.status_code == 200:
                    articles = extract_articles_from_page(response.content, date_from, date_to)
                    
                    # Filter by date range
                    if date_from or date_to:
                        filtered = []
                        for article in articles:
                            pub_str = article.get('published')
                            if pub_str:
                                try:
                                    pub_dt = dtparser.parse(pub_str)
                                    if pub_dt.tzinfo is None:
                                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                                    else:
                                        pub_dt = pub_dt.astimezone(timezone.utc)
                                    
                                    # Check if within date range
                                    if date_from and pub_dt < date_from:
                                        continue
                                    if date_to and pub_dt > date_to:
                                        continue
                                    
                                    filtered.append(article)
                                except:
                                    # Date parsing failed, skip if date filtering is required
                                    continue
                            else:
                                # No date, skip if date filtering is required
                                continue
                        articles = filtered
                    
                    all_articles.extend(articles)
                    break  # Success, exit retry loop
                elif response.status_code == 403:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Nikkei 403 Forbidden (page {page}, attempt {attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        print(f"❌ Nikkei page {page} consistently returns 403")
                        break
                elif response.status_code == 429:
                    wait_time = 5 + attempt * 2
                    if attempt < max_retries - 1:
                        print(f"⚠️ Nikkei rate limited (429), waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Nikkei page {page} consistently rate limited")
                        break
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Nikkei page {page} returned {response.status_code}")
                        time.sleep(2)
                        continue
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⚠️ Nikkei page {page} timeout (attempt {attempt + 1}/{max_retries})")
                    time.sleep(3)
                    continue
                else:
                    print(f"❌ Nikkei page {page} timeout")
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Nikkei page {page} error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Nikkei page {page} error: {e}")
                    break
        
        # Delay between pages
        if page < max_pages:
            time.sleep(1)
    
    # Deduplicate
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    return unique_articles

