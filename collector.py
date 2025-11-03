import feedparser, yaml, re, requests, time
from urllib.parse import quote_plus
from datetime import datetime, timezone
from dateutil import parser as dtparser
import pandas as pd
from utils import clean_html, url_id, domain_of, compile_or_regex, bool_match, normalize_source_short

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
    # 简单重试
    for _ in range(2):
        d = feedparser.parse(url)
        if d and d.entries: return d
        time.sleep(0.6)
    return feedparser.parse(url)

def _entry_to_row(e, source_label: str, raw_source_url: str):
    url = e.get("link") or ""
    title = clean_html(e.get("title"))
    summary = clean_html(e.get("summary") or e.get("description") or "")
    published = None
    for k in ("published", "updated", "created"):
        if e.get(k):
            published = _parse_dt(e.get(k))
            if published: break
    fetched = datetime.now(timezone.utc)
    return {
        "id": url_id(url),
        "source": source_label,
        "title": title,
        "summary": summary,
        "url": url,
        "published_dt": published,
        "fetched_dt": fetched,
        "raw_source": raw_source_url
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
    for dom, feed_url in feed_jobs:
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
        score = _relevance_score(r, pos_regex, neg_regex) if us_china_only else 0.0
        if (not us_china_only) or score >= 0.6:
            kept.append(r)

    # 每源限制上限（避免某源刷屏）
    if kept:
        df = pd.DataFrame(kept)
        # 以 published_dt 优先，其次 fetched_dt 排序/分组
        df['sort_dt'] = pd.to_datetime(df.get('published_dt')).fillna(pd.to_datetime(df.get('fetched_dt')))
        window_days = (end - start).days + 1
        max_per = None if window_days <= 7 else policy.get('max_per_source', 200)
        if max_per is not None:
            df['rank'] = df.groupby('source')['sort_dt'].rank(ascending=False, method='first')
            df = df[df['rank'] <= max_per].copy()
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
