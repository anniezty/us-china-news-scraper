#!/usr/bin/env python3
"""
Nikkei Asia 收集器
从 Nikkei Asia 中国新闻页面提取文章
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone
from dateutil import parser as dtparser
from urllib.parse import urljoin
import time

NIKKEI_BASE_URL = "https://asia.nikkei.com"
NIKKEI_CHINA_URL = "https://asia.nikkei.com/location/east-asia/china"

NIKKEI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def extract_date_from_article_page(url):
    """
    从文章详情页提取发布日期（优化版，更快）
    """
    try:
        response = requests.get(url, headers=NIKKEI_HEADERS, timeout=8)
        if response.status_code == 200:
            # 快速检查：先查找 HTML 中的日期
            content = response.text
            
            # 方法1: 查找 time 标签的 datetime 属性（最快）
            time_match = re.search(r'<time[^>]*datetime=["\']([^"\']+)["\']', content)
            if time_match:
                return time_match.group(1)
            
            # 方法2: 查找 JSON 数据中的日期（快速提取）
            json_match = re.search(r'__NEXT_DATA__\s*=\s*({.+?})', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    date = _find_date_in_json(data)
                    if date:
                        return date
                except:
                    pass
            
            # 方法3: 查找包含 datetime 属性的元素
            datetime_match = re.search(r'datetime=["\']([^"\']+)["\']', content)
            if datetime_match:
                return datetime_match.group(1)
            
            # 方法4: 查找日期格式的文本（如 "31 October 2025"）
            date_patterns = [
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{2}/\d{2}/\d{4})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
    except Exception as e:
        pass  # 静默失败，不影响主流程
    
    return None

def _find_date_in_json(obj):
    """
    从 JSON 数据中递归查找日期字段
    """
    if isinstance(obj, dict):
        # 检查常见的日期字段
        for key in ['publishedAt', 'published', 'date', 'datePublished', 'pubDate', 'createdAt', 'created']:
            if key in obj and obj[key]:
                return obj[key]
        # 递归查找
        for value in obj.values():
            if isinstance(value, (dict, list)):
                result = _find_date_in_json(value)
                if result:
                    return result
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                result = _find_date_in_json(item)
                if result:
                    return result
    return None

def extract_articles_from_html(html_content):
    """
    从 HTML 页面提取文章
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []
    
    # 方法1: 查找 __NEXT_DATA__ JSON
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and '__NEXT_DATA__' in script.string:
            try:
                # 提取 JSON 数据
                json_match = re.search(r'__NEXT_DATA__\s*=\s*({.+?})', script.string, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    # 递归查找文章数据（包含日期）
                    articles.extend(_extract_from_json(data))
            except Exception as e:
                print(f"⚠️ JSON 解析失败: {e}")
    
    # 方法2: 直接查找文章链接（改进版）
    # 查找所有可能的文章链接
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # 匹配文章 URL 模式（更宽泛，包含更多可能的路径）
        # 匹配常见的文章路径模式
        article_patterns = [
            r'/(Politics|Business|Economy|Companies|Markets|Tech|Opinion|Defense|International-relations|Trade-war|Supply-Chain|Automobiles|Semiconductors|Electric-vehicles|Artificial-intelligence|spotlight|Companies|Equities|Materials|Transportation|China-up-close|Policy-Asia)',
            r'/Economy/',
            r'/Politics/',
            r'/Business/',
            r'/Companies/',
            r'/Markets/',
            r'/Tech/',
            r'/Opinion/',
            r'/Defense/',
            r'/World/',
            r'/Asia/',
        ]
        
        # 检查是否匹配任何模式
        is_article_url = False
        for pattern in article_patterns:
            if re.match(pattern, href):
                is_article_url = True
                break
        
        # 也检查是否是完整的文章URL（包含文章ID或slug）
        if not is_article_url and href.startswith('/') and len(href) > 10:
            # 排除明显的非文章链接
            non_article_patterns = [
                r'/location/', r'/tag/', r'/author/', r'/search', r'/rss', r'/newsletter',
                r'/editor-s-picks/?$',  # 编辑推荐页面（不是具体文章）
                r'/editor-s-picks/[^/]+/?$',  # 编辑推荐的分类页面（不是具体文章）
                r'/spotlight/[^/]+/?$',  # spotlight分类页面（没有具体文章）
                r'/member/',  # 会员相关页面
                r'/marketing/',  # 营销页面
                r'/business/[^/]+/?$',  # 业务分类页面（如 /business/media-entertainment）
            ]
            if not any(re.search(pattern, href) for pattern in non_article_patterns):
                # 检查是否是真正的文章（有具体的文章slug）
                path_parts = [p for p in href.split('/') if p]
                if len(path_parts) >= 2:  # 至少有两个路径段
                    # 检查最后一个路径段是否像文章slug（通常比较长）
                    last_part = path_parts[-1]
                    if len(last_part) > 20 and ('-' in last_part or last_part.isalnum()):
                        is_article_url = True
        
        if is_article_url:
            if len(text) > 20:
                full_url = urljoin(NIKKEI_BASE_URL, href) if not href.startswith('http') else href
                
                # 去重
                if not any(a['url'] == full_url for a in articles):
                    # 尝试从父元素获取更多信息
                    parent = link.parent
                    summary = ''
                    if parent:
                        # 查找摘要
                        summary_elem = parent.find(['p', 'div'], class_=re.compile(r'summary|excerpt|description', re.I))
                        if summary_elem:
                            summary = summary_elem.get_text(strip=True)
                    
                    articles.append({
                        'url': full_url,
                        'title': text,
                        'summary': summary[:200] if summary else '',
                        'published': None,
                    })
    
    # 方法3: 查找特定的文章容器
    if not articles:
        # 尝试查找文章卡片
        article_containers = soup.find_all(['article', 'div'], class_=re.compile(r'article|story|card', re.I))
        for container in article_containers:
            link = container.find('a', href=True)
            if link:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                if len(title) > 20:
                    full_url = urljoin(NIKKEI_BASE_URL, href)
                    if not any(a['url'] == full_url for a in articles):
                        articles.append({
                            'url': full_url,
                            'title': title,
                            'summary': '',
                            'published': None,
                        })
    
    return articles

def _extract_from_json(data, articles=None):
    """
    递归从 JSON 数据中提取文章（改进版，更好地提取日期）
    """
    if articles is None:
        articles = []
    
    if isinstance(data, dict):
        # 检查是否是文章对象
        if 'url' in data or 'href' in data or 'slug' in data or 'path' in data:
            title = data.get('title') or data.get('headline') or data.get('name')
            url = data.get('url') or data.get('href') or data.get('slug') or data.get('path')
            
            if title and url:
                if not url.startswith('http'):
                    url = urljoin(NIKKEI_BASE_URL, url)
                
                # 更全面地查找日期字段
                published = (data.get('publishedAt') or data.get('published') or 
                           data.get('date') or data.get('datePublished') or 
                           data.get('pubDate') or data.get('createdAt') or 
                           data.get('created') or data.get('timestamp') or
                           data.get('publishTime') or data.get('publishedTime'))
                
                articles.append({
                    'url': url,
                    'title': title,
                    'summary': data.get('summary') or data.get('description') or data.get('dek') or '',
                    'published': published,
                })
        
        # 递归查找
        for value in data.values():
            if isinstance(value, (dict, list)):
                _extract_from_json(value, articles)
    
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                _extract_from_json(item, articles)
    
    return articles

def fetch_nikkei_articles(date_from=None, date_to=None, max_pages=3, max_retries=3):
    """
    从 Nikkei Asia 获取文章
    
    Args:
        date_from: 开始日期（datetime 或字符串，如 "2025-11-01"）
        date_to: 结束日期（datetime 或字符串，如 "2025-11-05"）
        max_pages: 最大页数
        max_retries: 最大重试次数
    
    Returns:
        list: 文章列表
    """
    from datetime import datetime, timezone, timedelta
    from dateutil import parser as dtparser
    
    # 转换日期参数为 datetime 对象
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
        url = f"{NIKKEI_CHINA_URL}?page={page}"
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=NIKKEI_HEADERS, timeout=15)
                
                if response.status_code == 200:
                    articles = extract_articles_from_html(response.content)
                    
                    # 如果没有日期，尝试从文章详情页获取（优化：根据是否有日期过滤要求决定）
                    articles_needing_date = [a for a in articles if not a.get('published')]
                    if articles_needing_date:
                        # 如果有日期过滤要求，需要获取所有文章的日期；否则只获取前10篇
                        if date_from or date_to:
                            # 有日期过滤要求，需要获取所有文章的日期
                            max_date_extractions = len(articles_needing_date)
                            print(f"  页面 {page}: 从详情页提取日期（{max_date_extractions} 篇，需要日期过滤）...")
                        else:
                            # 没有日期过滤要求，只获取前10篇
                            max_date_extractions = min(10, len(articles_needing_date))
                            print(f"  页面 {page}: 从详情页提取日期（{max_date_extractions} 篇）...")
                        
                        for i, article in enumerate(articles_needing_date[:max_date_extractions]):
                            date = extract_date_from_article_page(article['url'])
                            if date:
                                article['published'] = date
                            time.sleep(0.3)  # 请求之间稍作延迟，避免触发限流
                    
                    # 过滤日期范围
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
                                    
                                    # 检查是否在日期范围内
                                    if date_from and pub_dt < date_from:
                                        continue  # 早于开始日期，跳过
                                    if date_to and pub_dt > date_to:
                                        continue  # 晚于结束日期，跳过
                                    
                                    # 在范围内，保留文章
                                    article['published'] = pub_str  # 保留原始字符串
                                    filtered.append(article)
                                except Exception as e:
                                    # 日期解析失败，跳过这篇文章（因为无法判断是否在范围内）
                                    # print(f"⚠️ 日期解析失败: {pub_str}, 错误: {e}")
                                    continue
                            else:
                                # 没有日期，如果有日期过滤要求，跳过（因为无法判断是否在范围内）
                                # 如果没有日期过滤要求，保留文章
                                if not (date_from or date_to):
                                    filtered.append(article)
                        articles = filtered
                    
                    all_articles.extend(articles)
                    print(f"  页面 {page}: 获取 {len(articles)} 篇文章")
                    break  # 成功，跳出重试循环
                    
                elif response.status_code == 403:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Nikkei 403 Forbidden (页面 {page}, 尝试 {attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        print(f"❌ Nikkei 页面 {page} 持续返回 403")
                        break
                elif response.status_code == 429:
                    wait_time = 5 + (attempt * 2)
                    if attempt < max_retries - 1:
                        print(f"⚠️ Nikkei 限流 (429)，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Nikkei 页面 {page} 持续限流")
                        break
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Nikkei 页面 {page} 返回 {response.status_code}")
                        time.sleep(2)
                        continue
                    else:
                        break
                        
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⚠️ Nikkei 页面 {page} 超时 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(3)
                    continue
                else:
                    print(f"❌ Nikkei 页面 {page} 超时")
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Nikkei 页面 {page} 错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Nikkei 页面 {page} 错误: {e}")
                    break
        
        # 页面之间延迟
        if page < max_pages:
            time.sleep(2)
    
    # 去重
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    return unique_articles

