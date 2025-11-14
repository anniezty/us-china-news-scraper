import feedparser, yaml, re, requests, time
from io import BytesIO
from urllib.parse import quote_plus
from datetime import datetime, timezone
from dateutil import parser as dtparser
import pandas as pd
from utils import clean_html, url_id, domain_of, compile_or_regex, bool_match, normalize_source_short

_BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
}

# -------- Google News RSS builder --------
def google_news_rss(query: str, lang="en", country="US"):
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}-{country}&gl={country}&ceid={country}:{lang}"

def _parse_dt(ts: str | None) -> datetime | None:
    if not ts: return None
    try:
        dt = dtparser.parse(ts)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        else: dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None

def _in_range(dt: datetime | None, start: datetime, end: datetime) -> bool:
    if not dt: return False
    return (dt >= start) and (dt <= end)

def _fetch_feed(url: str) -> feedparser.FeedParserDict:
    # 重试逻辑，对 RSSHub 等慢速源增加超时和稳定性处理
    import requests
    from io import BytesIO
    
    # RSSHub 等源可能需要更长时间
    is_rsshub = "rsshub.app" in url or "rss-bridge.org" in url
    
    for attempt in range(5):  # 增加到5次重试
        try:
            if is_rsshub:
                # RSSHub 连接建立慢，但读取快
                # timeout=(连接超时, 读取超时) - 增加到 120 秒以应对慢速响应
                response = requests.get(url, timeout=(20, 120), headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
                })
                
                # 处理 429 (Too Many Requests) 错误
                if response.status_code == 429:
                    # RSSHub 限流，等待更长时间
                    wait_time = 5 + (attempt * 2)  # 递增等待：5, 7, 9, 11, 13 秒
                    if attempt < 4:
                        print(f"⚠️ RSSHub 限流 (429)，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 最后一次尝试也失败，返回空
                        print(f"❌ RSSHub 持续限流，无法获取数据")
                        continue
                
                if response.status_code == 200:
                    # 检查内容是否有效（至少要有一定长度）
                    if len(response.content) < 500:  # 太短可能是错误页面
                        if attempt < 4:
                            time.sleep(3)  # 等待更长时间
                            continue
                        else:
                            # 最后一次，即使内容短也尝试解析
                            pass
                    
                    d = feedparser.parse(BytesIO(response.content))
                    
                    # 检查是否有条目，或者是否是有效的 feed
                    if d and (d.entries or (hasattr(d.feed, 'title') and len(d.feed.title) > 0)):
                        # 如果有条目，直接返回
                        if d.entries:
                            return d
                        # 如果没有条目但 feed 有效，可能是空的但结构正确，再试一次
                        elif attempt < 4:
                            time.sleep(3)
                            continue
                        else:
                            # 最后一次，返回空 feed
                            return d
                    else:
                        # Feed 解析失败或无效
                        if attempt < 4:
                            time.sleep(3)
                            continue
                else:
                    # 其他非 200 状态码
                    if attempt < 4:
                        wait_time = 3 + attempt  # 递增等待
                        print(f"⚠️ RSSHub 返回 {response.status_code}，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
            else:
                # 普通源使用 feedparser
                needs_browser_headers = any(host in url for host in [
                    "washingtonpost.com"
                ])
                if needs_browser_headers:
                    try:
                        response = requests.get(url, timeout=(5, 15), headers=_BROWSER_HEADERS)
                        if response.status_code == 200 and response.content:
                            d = feedparser.parse(BytesIO(response.content))
                            if d and d.entries:
                                return d
                    except Exception:
                        if attempt < 4:
                            time.sleep(1)
                            continue
                d = feedparser.parse(url)
                if d and d.entries:
                    return d
                elif attempt < 4:
                    time.sleep(1)
                    continue
        except requests.exceptions.Timeout as e:
            if attempt < 4:
                wait_time = 8 + (attempt * 2)  # 递增等待：8, 10, 12, 14 秒
                print(f"⚠️ RSSHub 超时 (尝试 {attempt + 1}/5), 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)  # RSSHub 超时后等待更长时间
                continue
            else:
                print(f"❌ RSSHub 最终超时: {e}")
        except Exception as e:
            if attempt < 4:
                print(f"⚠️ 尝试 {attempt + 1}/5 失败: {type(e).__name__}, 重试...")
                time.sleep(3 if is_rsshub else 1)
                continue
            else:
                print(f"❌ 最终失败: {e}")
    
    # 最后一次尝试
    try:
        if is_rsshub:
            response = requests.get(url, timeout=(20, 120), headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*'
            })
            if response.status_code == 200 and len(response.content) >= 500:
                return feedparser.parse(BytesIO(response.content))
        return feedparser.parse(url)
    except:
        pass
    
    # 所有尝试都失败，返回空 feed
    return feedparser.FeedParserDict({})

# 注意：AP News 日期获取已移至 apnews_collector.py，不再需要此函数

def _entry_to_row(e, source_label: str, raw_source_url: str):
    url = e.get("link") or ""
    title = clean_html(e.get("title"))
    # 尝试多个字段获取摘要（RSSHub 可能使用不同的字段名）
    summary = ""
    if e.get("summary"):
        summary = clean_html(e.get("summary"))
    elif e.get("description"):
        summary = clean_html(e.get("description"))
    elif e.get("content"):
        # content 可能是列表或字符串
        content = e.get("content")
        if isinstance(content, list) and len(content) > 0:
            summary = clean_html(content[0].get("value", ""))
        elif isinstance(content, str):
            summary = clean_html(content)
    else:
        summary = ""
    published = None
    
    # 方法1: 尝试从字符串日期字段解析
    for k in ("published", "updated", "created", "modified", "pubDate"):
        if e.get(k):
            published = _parse_dt(e.get(k))
            if published: break
    
    # 方法2: 如果字符串解析失败，尝试从 parsed 字段（feedparser 自动解析的）
    if not published:
        from time import mktime
        if e.get("published_parsed"):
            try:
                published = datetime.fromtimestamp(mktime(e["published_parsed"]), tz=timezone.utc)
            except:
                pass
        elif e.get("updated_parsed"):
            try:
                published = datetime.fromtimestamp(mktime(e["updated_parsed"]), tz=timezone.utc)
            except:
                pass
    
    # 注意：AP News 现在使用专门的 collector，不再需要这里获取日期
    
    fetched = datetime.now(timezone.utc)
    return {
        "id": url_id(url),
        "source": source_label,
        "title": title,
        "summary": summary,
        "url": url,
        "published_dt": published,
        "fetched_dt": fetched,
        "raw_source": raw_source_url,
        "keep_filter": False,
        "keep_limit": False,
    }

def _relevance_score(row, pos_regex: re.Pattern | None, neg_regex: re.Pattern | None) -> float:
    # 规则评分：命中正向 +1，命中负向 -0.6，标题加权
    t = row["title"]; s = row["summary"]; u = row["url"]
    score = 0.0
    if pos_regex:
        if bool_match(t, pos_regex): score += 1.0
        if bool_match(s, pos_regex): score += 0.6
    if neg_regex:
        if bool_match(t, neg_regex): score -= 0.6
        if bool_match(s, neg_regex): score -= 0.4
    # 来源加一点点常识加权（白名单主流媒体 +0.1）
    dom = domain_of(u)
    if any(k in (row["source"] or "") for k in ["NYT","WSJ","Bloomberg","Reuters","FT","Economist","SCMP","WaPo","BBC","CNN","Nikkei","AP","FP","FA"]):
        score += 0.1
    return score

def collect(config_path: str,
            date_from: str, date_to: str,
            us_china_only: bool = True,
            limit_sources: list[str] | None = None) -> pd.DataFrame:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    rss_map: dict = cfg.get("rss_feeds", {})
    gnews_cfg: dict = cfg.get("google_news", {})
    policy: dict = cfg.get("harvest_policy", {})
    rel_cfg: dict = cfg.get("relevance", {})

    start = dtparser.parse(date_from).replace(tzinfo=timezone.utc) if dtparser.parse(date_from).tzinfo is None else dtparser.parse(date_from).astimezone(timezone.utc)
    end_raw = dtparser.parse(date_to)
    if end_raw.tzinfo is None: end = end_raw.replace(tzinfo=timezone.utc)
    else: end = end_raw.astimezone(timezone.utc)
    # 结束日到当天 23:59:59
    end = end.replace(hour=23, minute=59, second=59, microsecond=0)

    # 限定可选来源（UI 可传入）
    allowed_domains = set(rss_map.keys())
    if limit_sources and len(limit_sources) > 0 and "ALL" not in limit_sources:
        allowed_domains = set([d for d in allowed_domains if d in limit_sources])

    # 构造 RSS 列表
    feed_jobs = []
    for dom, feeds in rss_map.items():
        if dom not in allowed_domains: continue
        for u in feeds:
            feed_jobs.append((dom, u))

    # 读取 RSS
    rows = []
    for idx, (dom, feed_url) in enumerate(feed_jobs):
        # Special handling: PIIE China listing page (AJAX interface)
        if dom == "piie.com":
            try:
                from piie_collector import fetch_piie_articles
                piie_articles = fetch_piie_articles(date_from=start, date_to=end, max_pages=10)
                for article in piie_articles:
                    published = None
                    if article.get("published"):
                        try:
                            published = _parse_dt(article["published"])
                        except Exception:
                            pass
                    row = {
                        "id": url_id(article["url"]),
                        "source": dom,
                        "title": article["title"],
                        "summary": article.get("summary", ""),
                        "url": article["url"],
                        "published_dt": published,
                        "fetched_dt": datetime.now(timezone.utc),
                        "raw_source": feed_url,
                        "keep_filter": False,
                        "keep_limit": False,
                    }
                    # Time filtering safeguard
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end):
                        continue
                    rows.append(row)
            except ImportError:
                print("⚠️ PIIE collector not found, skipping")
            except Exception as e:
                print(f"⚠️ PIIE collection failed: {e}")
            continue
        # Special handling: Nikkei Asia HTML page
        if dom == "asia.nikkei.com" or dom == "nikkei.com":
            try:
                from nikkei_collector import fetch_nikkei_articles
                nikkei_articles = fetch_nikkei_articles(date_from=start, date_to=end, max_pages=3)
                for article in nikkei_articles:
                    # Convert to standard format
                    published = None
                    if article.get("published"):
                        try:
                            published = _parse_dt(article["published"])
                        except:
                            pass
                    
                    row = {
                        "id": url_id(article["url"]),
                        "source": dom,
                        "title": article["title"],
                        "summary": article.get("summary", ""),
                        "url": article["url"],
                        "published_dt": published,
                        "fetched_dt": datetime.now(timezone.utc),
                        "raw_source": feed_url
                    }
                    row.setdefault("keep_filter", False)
                    row.setdefault("keep_limit", False)
                    rows.append(row)
            except ImportError:
                print(f"⚠️ Nikkei collector not found, skipping")
            except Exception as e:
                print(f"⚠️ Nikkei collection failed: {e}")
            continue
        
        # Special handling: Politico RSS feeds (filter China-related articles)
        if dom == "politico.com" and "rss.politico.com" in feed_url:
            # Fetch RSS feed and filter for China-related articles
            d = _fetch_feed(feed_url)
            for e in d.entries:
                title = e.get("title", "").lower()
                link = e.get("link", "").lower()
                summary = e.get("summary", "").lower()
                
                # Check if URL path contains /news/china/
                is_china_url = "/news/china/" in link
                
                # Check for China-related keywords (expanded list)
                keywords = ["china", "chinese", "beijing", "taiwan", "xi jinping", "hong kong", 
                           "taipei", "shanghai", "ccp", "communist party", "prc", "people's republic",
                           "mainland china", "beijing", "chinese government", "chinese officials"]
                has_keyword = any(kw in text for kw in keywords for text in [title, summary])
                
                # Only include China-related articles
                if is_china_url or has_keyword:
                    row = _entry_to_row(e, dom, feed_url)
                    # Time filtering: prioritize published, fallback to fetched
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end): continue
                    row.setdefault("keep_filter", False)
                    row.setdefault("keep_limit", False)
                    rows.append(row)
            continue

        # Special handling: Axios China section (requires authenticated cookies)
        if dom == "axios.com":
            try:
                from axios_collector import fetch_axios_articles

                axios_articles = fetch_axios_articles(
                    date_from=start,
                    date_to=end,
                    max_pages=policy.get("max_pages", 5),
                )
            except ImportError:
                print("⚠️ Axios collector not found, skipping")
                continue
            except Exception as e:
                print(f"⚠️ Axios collection failed: {e}")
                continue

            if not axios_articles:
                continue

            for art in axios_articles:
                row = {
                    "id": art.get("id") or url_id(art.get("url", "")),
                    "source": dom,
                    "title": art.get("title", ""),
                    "summary": art.get("summary", ""),
                    "url": art.get("url", ""),
                    "published_dt": art.get("published"),
                    "fetched_dt": datetime.now(timezone.utc),
                    "raw_source": art.get("raw_source", feed_url),
                    "keep_filter": False,
                    "keep_limit": False,
                }
                base_dt = row["published_dt"] or row["fetched_dt"]
                if not _in_range(base_dt, start, end):
                    continue
                rows.append(row)
            continue

        # Special handling: The Atlantic tag river (GraphQL endpoint)
        if dom == "theatlantic.com":
            try:
                from atlantic_collector import fetch_atlantic_articles

                atlantic_articles = fetch_atlantic_articles(
                    feed_url=feed_url,
                    date_from=start,
                    date_to=end,
                    max_pages=policy.get("max_pages", 5),
                )
            except ImportError:
                print("⚠️ Atlantic collector not found, skipping")
                continue
            except Exception as e:
                print(f"⚠️ Atlantic collection failed: {e}")
                continue

            if not atlantic_articles:
                continue

            for art in atlantic_articles:
                row = {
                    "id": art["id"],
                    "source": dom,
                    "title": art["title"],
                    "summary": art.get("summary", ""),
                    "url": art["url"],
                    "published_dt": art.get("published"),
                    "fetched_dt": datetime.now(timezone.utc),
                    "raw_source": art.get("raw_source", feed_url),
                    "keep_filter": False,
                    "keep_limit": False,
                }
                base_dt = row["published_dt"] or row["fetched_dt"]
                if not _in_range(base_dt, start, end):
                    continue
                rows.append(row)
            continue

        # Special handling: AP News China hub (HTML parser, direct from website)
        if dom == "apnews.com":
            try:
                from apnews_collector import fetch_apnews_articles
                apnews_articles = fetch_apnews_articles(date_from=start, date_to=end, max_pages=5)
            except ImportError:
                print("⚠️ AP News collector not found, skipping")
                continue
            except Exception as e:
                print(f"⚠️ AP News collection failed: {e}")
                continue

            if not apnews_articles:
                continue

            for art in apnews_articles:
                row = {
                    "id": url_id(art["url"]),
                    "source": dom,
                    "title": art["title"],
                    "summary": art.get("summary", ""),
                    "url": art["url"],
                    "published_dt": art.get("published"),
                    "fetched_dt": datetime.now(timezone.utc),
                    "raw_source": art.get("raw_source", feed_url),
                    "keep_filter": False,
                    "keep_limit": False,
                }
                base_dt = row["published_dt"] or row["fetched_dt"]
                if not _in_range(base_dt, start, end):
                    continue
                rows.append(row)
            continue

        # Special handling: Washington Post Asia-Pacific section (HTML with auth cookies)
        if dom == "washingtonpost.com":
            try:
                from wapo_collector import fetch_wapo_articles
                wapo_articles = fetch_wapo_articles(date_from=start, date_to=end, max_pages=5)
            except ImportError:
                print("⚠️ WAPO collector not found, skipping")
                continue
            except Exception as e:
                print(f"⚠️ WAPO collection failed: {e}")
                continue

            if not wapo_articles:
                continue

            china_terms = [
                "china", "chinese", "beijing", "xi jinping", "prc", "people's republic",
                "communist party", "ccp", "hong kong", "xinjiang", "tibet", "shenzhen",
                "shanghai", "guangzhou", "belt and road", "south china sea", "pla",
                "taiwan", "taipei", "cross-strait", "one china", "made in china"
            ]
            us_terms = [
                "united states", "u.s.", "us ", "america", "american", "washington",
                "biden", "white house", "pentagon", "congress", "capitol hill"
            ]
            high_interest_terms = [
                "trade", "tariff", "sanction", "semiconductor", "chip", "export control",
                "tech war", "supply chain", "spy", "espionage", "military", "navy"
            ]

            for art in wapo_articles:
                title = art.get("title", "") or ""
                summary = art.get("summary", "") or ""
                link = art.get("url", "") or ""
                combined = " ".join([title, summary, link]).lower()

                has_china_topic = any(term in combined for term in china_terms)
                has_us_reference = any(term in combined for term in us_terms)
                has_policy_signal = any(term in combined for term in high_interest_terms)

                if not has_china_topic:
                    continue
                if us_china_only and not (has_us_reference or has_policy_signal):
                    continue

                row = {
                    "id": url_id(link),
                    "source": dom,
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "published_dt": art.get("published"),
                    "fetched_dt": datetime.now(timezone.utc),
                    "raw_source": art.get("raw_source", link),
                    "keep_filter": False,
                    "keep_limit": False,
                }
                base_dt = row["published_dt"] or row["fetched_dt"]
                if not _in_range(base_dt, start, end):
                    continue
                rows.append(row)
            continue
        
        # Special handling: Wall Street Journal China GraphQL feed
        if dom == "wsj.com":
            try:
                from wsj_collector import fetch_wsj_articles
                wsj_articles = fetch_wsj_articles(date_from=start, date_to=end, max_pages=5)
                for article in wsj_articles:
                    row = {
                        "id": url_id(article["url"]),
                        "source": dom,
                        "title": article["title"],
                        "summary": article["summary"],
                        "url": article["url"],
                        "published_dt": article["published"],
                        "fetched_dt": datetime.now(timezone.utc),
                        "raw_source": article.get("raw_source", feed_url) or feed_url,
                    }
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end):
                        continue
                    rows.append(row)
            except ImportError:
                print("⚠️ WSJ collector not found, skipping")
            except Exception as e:
                print(f"⚠️ WSJ collection failed: {e}")
            continue
        
        # Special handling: CSIS China landing page (HTML parser)
        if dom == "csis.org":
            try:
                from csis_collector import fetch_csis_articles
                csis_articles = fetch_csis_articles(date_from=start, date_to=end, max_pages=5)
                for article in csis_articles:
                    row = {
                        "id": url_id(article["url"]),
                        "source": dom,
                        "title": article["title"],
                        "summary": article["summary"],
                        "url": article["url"],
                        "published_dt": article["published"],
                        "fetched_dt": datetime.now(timezone.utc),
                        "raw_source": article.get("raw_source", feed_url) or feed_url,
                    }
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end):
                        continue
                    rows.append(row)
            except ImportError:
                print("⚠️ CSIS collector not found, skipping")
            except Exception as e:
                print(f"⚠️ CSIS collection failed: {e}")
            continue

        # Special handling: Foreign Policy China project page
        if dom == "foreignpolicy.com":
            try:
                from foreignpolicy_collector import fetch_foreignpolicy_articles
                fp_articles = fetch_foreignpolicy_articles(date_from=start, date_to=end)
                for article in fp_articles:
                    row = {
                        "id": url_id(article["url"]),
                        "source": dom,
                        "title": article["title"],
                        "summary": article["summary"],
                        "url": article["url"],
                        "published_dt": article.get("published"),
                        "fetched_dt": datetime.now(timezone.utc),
                        "raw_source": article.get("raw_source", feed_url) or feed_url,
                        "keep_filter": False,
                        "keep_limit": False,
                    }
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end):
                        continue
                    rows.append(row)
            except ImportError:
                print("⚠️ Foreign Policy collector not found, skipping")
            except Exception as e:
                print(f"⚠️ Foreign Policy collection failed: {e}")
            continue

        # Special handling: Reuters Arc Publishing API (China section)
        if dom == "reuters.com":
            try:
                from reuters_collector import fetch_reuters_articles
                reuters_articles = fetch_reuters_articles(date_from=start, date_to=end, max_pages=20)
                for article in reuters_articles:
                    row = {
                        "id": url_id(article["url"]),
                        "source": dom,
                        "title": article["title"],
                        "summary": article["summary"],
                        "url": article["url"],
                        "published_dt": article["published"],
                        "fetched_dt": datetime.now(timezone.utc),
                        "raw_source": article.get("raw_source", feed_url) or feed_url,
                        "keep_filter": True,
                        "keep_limit": True,
                    }
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end):
                        continue
                    rows.append(row)
            except ImportError:
                print("⚠️ Reuters collector not found, skipping")
            except Exception as e:
                print(f"⚠️ Reuters collection failed: {e}")
            continue
        
        # Special handling: Bloomberg search page (HTML parser with CloudScraper)
        if dom == "bloomberg.com":
            try:
                from bloomberg_collector import fetch_bloomberg_articles
                bloomberg_articles = fetch_bloomberg_articles(date_from=start, date_to=end, max_pages=5)
            except ImportError:
                print("⚠️ Bloomberg collector not found, skipping")
                continue
            except Exception as e:
                print(f"⚠️ Bloomberg collection failed: {e}")
                continue

            if not bloomberg_articles:
                continue

            for art in bloomberg_articles:
                row = {
                    "id": url_id(art["url"]),
                    "source": dom,
                    "title": art["title"],
                    "summary": art.get("summary", ""),
                    "url": art["url"],
                    "published_dt": art.get("published"),
                    "fetched_dt": datetime.now(timezone.utc),
                    "raw_source": art.get("raw_source", feed_url),
                    "keep_filter": False,
                    "keep_limit": False,
                }
                base_dt = row["published_dt"] or row["fetched_dt"]
                if not _in_range(base_dt, start, end):
                    continue
                rows.append(row)
            continue
        
        # 对 RSSHub 源添加延迟，避免同时发送多个请求触发限流
        is_rsshub = "rsshub.app" in feed_url or "rss-bridge.org" in feed_url
        if is_rsshub and idx > 0:
            # 在 RSSHub 源之间添加 3 秒延迟，避免触发 429
            time.sleep(3)
        
        d = _fetch_feed(feed_url)
        for e in d.entries:
            row = _entry_to_row(e, dom, feed_url)
            # 时间过滤：优先 published，其次 fetched
            base_dt = row["published_dt"] or row["fetched_dt"]
            if not _in_range(base_dt, start, end): continue
            rows.append(row)

    # 如果某些来源明显不足，且开启 GNews 兜底，则用 site:domain + keywords 拉一小撮补齐
    if gnews_cfg.get("enabled", True) and policy.get("fallback_google", True):
        base_kw = gnews_cfg.get("base_keywords", [])
        per_domain = gnews_cfg.get("per_domain", True)

        def site_query(domain: str) -> list[str]:
            return [f"site:{domain} ({kw})" for kw in base_kw] if per_domain else base_kw

        # 以来源为单位检查数量
        df_tmp = pd.DataFrame(rows)
        count_by_dom = df_tmp.groupby("source")["id"].nunique().to_dict() if not df_tmp.empty else {}
        for dom in allowed_domains:
            have = count_by_dom.get(dom, 0)
            if have >= policy.get("min_per_source", 0):
                continue
            # 兜底抓取
            for q in site_query(dom):
                rss_url = google_news_rss(q)
                d = _fetch_feed(rss_url)
                for e in d.entries:
                    row = _entry_to_row(e, dom, rss_url)
                    base_dt = row["published_dt"] or row["fetched_dt"]
                    if not _in_range(base_dt, start, end): continue
                    rows.append(row)

    if not rows:
        return pd.DataFrame(columns=["Nested?","URL","Date","Outlet","Headline","Nut Graph"])

    # 去重（按 url）
    seen = set()
    uniq = []
    for r in rows:
        if r["url"] in seen: continue
        seen.add(r["url"])
        uniq.append(r)
    rows = uniq

    # 相关性过滤：us_china_only 时，用正向/负向规则打分
    pos_regex = compile_or_regex(rel_cfg.get("us_china_only_keywords", [])) if us_china_only else None
    neg_regex = compile_or_regex(rel_cfg.get("negative_patterns", [])) if us_china_only else None

    kept = []
    for r in rows:
        if r.get("keep_filter"):
            kept.append(r)
            continue
        score = _relevance_score(r, pos_regex, neg_regex) if us_china_only else 0.0
        if (not us_china_only) or score >= 0.6:
            kept.append(r)

    # 每源限制上限（避免某源刷屏）
    if kept:
        df = pd.DataFrame(kept)
        # 以 published_dt 优先，其次 fetched_dt 排序/分组
        df['sort_dt'] = pd.to_datetime(df.get('published_dt')).fillna(pd.to_datetime(df.get('fetched_dt')))
        if 'keep_limit' not in df.columns:
            df['keep_limit'] = False
        window_days = (end - start).days + 1
        max_per = None if window_days <= 7 else policy.get('max_per_source', 200)
        if max_per is not None:
            df['rank'] = df.groupby('source')['sort_dt'].rank(ascending=False, method='first')
            df = df[(df['rank'] <= max_per) | df['keep_limit'].fillna(False)].copy()
            df.drop(columns=['rank'], inplace=True)
        df.drop(columns=['sort_dt'], inplace=True)
    else:
        df = pd.DataFrame(kept)

    # 整理成导出所需列
    if not df.empty:
        df["Outlet"] = df["raw_source"].apply(normalize_source_short)
        df["Date"] = df["published_dt"].fillna(df["fetched_dt"]).dt.strftime("%Y-%m-%d %H:%M")
        df["Headline"] = df["title"]
        df["Nut Graph"] = df["summary"]
        df["URL"] = df["url"]
        df["Nested?"] = ""  # 先空着
        df = df[["Nested?","URL","Date","Outlet","Headline","Nut Graph"]].sort_values("Date", ascending=False)
    return df.reset_index(drop=True)
