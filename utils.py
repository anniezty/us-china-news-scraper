import re, hashlib, html, warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

def clean_html(text: str | None) -> str:
    if not text:
        return ""
    # 优先用 BS 去标签，再兜底正则
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)
        txt = BeautifulSoup(text, "html.parser").get_text(" ")
    txt = TAG_RE.sub(" ", txt)
    txt = html.unescape(txt)
    txt = SPACE_RE.sub(" ", txt).strip()
    return txt

def url_id(url: str | None) -> str:
    return hashlib.sha256((url or "").encode("utf-8")).hexdigest()[:16]

def domain_of(url: str | None) -> str:
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        d = urlparse(url).netloc.lower()
        if d.startswith("www."): d = d[4:]
        return d
    except Exception:
        return ""

def compile_or_regex(patterns: list[str]) -> re.Pattern:
    # 将多条 OR 逻辑合并，忽略大小写
    joined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(joined, flags=re.I)

def bool_match(text: str, pattern: re.Pattern) -> bool:
    return bool(pattern.search(text or ""))

def normalize_source_short(raw_source: str) -> str:
    # 将 RSS/GNews URL 或域名映射为 Outlet 简写
    
    # 域名映射（优先检查，因为用户选择的是域名）
    domain_map = {
        "nytimes.com": "NYT",
        "thediplomat.com": "Diplomat",
        "foreignaffairs.com": "FA",
        "foreignpolicy.com": "FP",
        "scmp.com": "SCMP",
        "foxnews.com": "Fox",
        "pekingnology.substack.com": "Pekingnology",
        "thewirechina.com": "The Wire China",
        "bbc.com": "BBC",
        "feeds.bbci.co.uk": "BBC",
        "reuters.com": "Reuters",
        "bloomberg.com": "Bloomberg",
        "economist.com": "Economist",
        "chinafile.com": "ChinaFile",
        "washingtonpost.com": "WaPo",
        "politico.com": "Politico",
        "apnews.com": "AP",
        "nikkei.com": "Nikkei",
        "asia.nikkei.com": "Nikkei",
        "piie.com": "PIIE",
        "warontherocks.com": "WOTR",
        "hoover.org": "CLM",
        "cbsnews.com": "CBS",
        "nbcnews.com": "NBC",
        "cnn.com": "CNN",
        "ft.com": "FT",
        "wired.com": "Wired",
        "prcleader.org": "CLM",
        "wsj.com": "WSJ",
        "restofworld.org": "ROW",
        "latimes.com": "LA Times",
        "csis.org": "CSIS",
        "theatlantic.com": "Atlantic",
        "axios.com": "Axios",
    }
    
    # 如果输入本身就是域名（不包含 http/https），直接查找
    if not raw_source.startswith("http"):
        if raw_source in domain_map:
            return domain_map[raw_source]
    
    # URL 前缀映射
    mapping_starts = {
        "https://feeds.a.dj.com/": "WSJ",
        "https://feeds.bloomberg.com/": "Bloomberg",
        "https://rss.nytimes.com/": "NYT",
        "https://www.nytimes.com/svc/collections/": "NYT",
        "http://feeds.washingtonpost.com/": "WaPo",
        "https://asia.nikkei.com/": "Nikkei",
        "https://www.economist.com/": "Economist",
        "https://feeds.reuters.com/": "Reuters",
        "https://apnews.com/": "AP",
        "https://www.scmp.com/": "SCMP",
        "https://thediplomat.com/": "Diplomat",
        "https://foreignpolicy.com/": "FP",
        "https://www.foreignaffairs.com/": "FA",
        "https://warontherocks.com/": "WOTR",
        "https://www.hoover.org/": "CLM",
        "https://www.piie.com/": "PIIE",
        "https://pekingnology.substack.com/": "Pekingnology",
        "https://feeds.bbci.co.uk/": "BBC",
        "http://rss.cnn.com/": "CNN",
        "https://moxie.foxnews.com/": "Fox",
        "https://feeds.nbcnews.com/": "NBC",
        "https://www.cbsnews.com/": "CBS",
        "https://www.chinafile.com/": "ChinaFile",
        "https://feeds.feedburner.com/chinafile/": "ChinaFile",
        "https://www.csis.org/": "CSIS",
        "https://www.theatlantic.com/": "Atlantic",
        "https://www.axios.com/": "Axios",
        # RSSHub proxies
        "https://rsshub.app/wired/": "Wired",
        "https://rsshub.app/apnews/": "AP",
    }
    for k, v in mapping_starts.items():
        if raw_source.startswith(k):
            return v
    if "news.google.com" in raw_source:
        return "GNews"
    # 特殊：rss-bridge 的 Reuters 源
    if "rss-bridge.org" in raw_source and "ReutersBridge" in raw_source:
        return "Reuters"
    
    # 退化为域名映射（从 URL 中提取域名）
    dom = domain_of(raw_source)
    if dom in domain_map:
        return domain_map[dom]
    # 未命中则返回域名（不是 URL），避免展示长链接
    return dom or raw_source
