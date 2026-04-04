"""
news_ingestion.py - Fetches 30+ articles with country support. More topics, more sources.
"""

import re, time, feedparser, hashlib, httpx

def _gn_top(country="US"):
    codes = {"US":("en-US","US","US:en"),"UK":("en-GB","GB","GB:en"),"IN":("en-IN","IN","IN:en"),"FR":("fr-FR","FR","FR:fr"),"DE":("de-DE","DE","DE:de"),"JP":("ja-JP","JP","JP:ja"),"WORLD":("en-US","US","US:en")}
    hl,gl,ceid = codes.get(country, codes["US"])
    return f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"

def _gn_topic(tid, country="US"):
    codes = {"US":("en-US","US","US:en"),"UK":("en-GB","GB","GB:en"),"IN":("en-IN","IN","IN:en"),"FR":("fr-FR","FR","FR:fr"),"DE":("de-DE","DE","DE:de"),"JP":("ja-JP","JP","JP:ja"),"WORLD":("en-US","US","US:en")}
    hl,gl,ceid = codes.get(country, codes["US"])
    return f"https://news.google.com/rss/topics/{tid}?hl={hl}&gl={gl}&ceid={ceid}"

TOPIC_IDS = {
    "WORLD": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
    "NATION": "CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE",
    "BUSINESS": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
    "TECHNOLOGY": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
    "SCIENCE": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB",
    "HEALTH": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ",
    "ENTERTAINMENT": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB",
    "SPORTS": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
}

def _gn_search(query, country="US"):
    codes = {"US":("en-US","US","US:en"),"UK":("en-GB","GB","GB:en"),"IN":("en-IN","IN","IN:en"),"FR":("fr-FR","FR","FR:fr"),"DE":("de-DE","DE","DE:de"),"JP":("ja-JP","JP","JP:ja"),"WORLD":("en-US","US","US:en")}
    hl,gl,ceid = codes.get(country, codes["US"])
    q = query.replace(" ", "+")
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

BACKUP_RSS = {
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "ABC News": "https://abcnews.go.com/abcnews/topstories",
    "CBS News": "https://www.cbsnews.com/latest/rss/main",
}

_http = None
def _client():
    global _http
    if _http is None: _http = httpx.Client(timeout=6.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    return _http

def _clean(t):
    if not t: return ""
    return re.sub(r'&[a-zA-Z]+;', ' ', re.sub(r'<[^>]+>', '', t)).strip()

def _src(t):
    if " - " in t:
        p = t.rsplit(" - ", 1)
        if len(p)==2: return p[1].strip()
    return "Unknown"

def _title(t):
    if " - " in t:
        p = t.rsplit(" - ", 1)
        if len(p)==2: return p[0].strip()
    return t

def _id(t): return hashlib.md5(t.encode()).hexdigest()[:10]

def _og_image(url):
    if not url: return ""
    try:
        r = _client().get(url)
        if r.status_code != 200: return ""
        h = r.text[:15000]
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', h, re.I)
        if m: return m.group(1)
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', h, re.I)
        if m: return m.group(1)
    except: pass
    return ""

def _sub_sources(html):
    srcs = []
    if not html: return srcs
    for m in re.findall(r'<font[^>]*>([^<]+)</font>', html):
        c = m.strip()
        if c and len(c)<60: srcs.append(c)
    for m in re.findall(r'<a[^>]+>([^<]+)</a>', html):
        if " - " in m:
            s = _src(m)
            if s != "Unknown": srcs.append(s)
    return list(set(srcs))

def _img_entry(e):
    for m in e.get("media_content", []):
        u = m.get("url", "")
        if u: return u
    for t in e.get("media_thumbnail", []):
        if t.get("url"): return t["url"]
    for enc in e.get("enclosures", []):
        if "image" in enc.get("type", ""): return enc.get("href", enc.get("url", ""))
    sm = e.get("summary", "")
    im = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', sm)
    if im and im.group(1).startswith("http"): return im.group(1)
    return ""

def _parse(url, max_items=20, scrape=True):
    articles = []
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries: return []
        for e in feed.entries[:max_items]:
            raw = e.get("title", "")
            if not raw: continue
            src = _src(raw); title = _title(raw)
            desc = _clean(e.get("summary", e.get("description", "")))
            img = _img_entry(e)
            aurl = e.get("link", "")
            if not img and scrape and aurl: img = _og_image(aurl)
            articles.append({
                "id": _id(raw), "title": title,
                "description": desc[:500] if desc else title,
                "content": desc if desc else title,
                "source": src, "url": aurl,
                "published_at": e.get("published", ""),
                "image_url": img,
                "sub_sources": _sub_sources(e.get("summary", "")),
            })
    except Exception as ex:
        print(f"  Parse error: {ex}")
    return articles


def fetch_google_top_news(country="US"):
    print(f"Fetching Google News top ({country})...")
    arts = _parse(_gn_top(country), max_items=20, scrape=True)
    print(f"  Got {len(arts)} top articles")
    return arts

def fetch_google_topic_news(country="US"):
    """Fetch from ALL topic feeds — not just 4."""
    all_arts = []
    for t, tid in TOPIC_IDS.items():
        print(f"Fetching: {t} ({country})...")
        arts = _parse(_gn_topic(tid, country), max_items=10, scrape=True)
        print(f"  Got {len(arts)}")
        all_arts.extend(arts)
        time.sleep(0.3)
    return all_arts

def fetch_google_search(query, country="US"):
    """Search with country-aware URL and more results."""
    url = _gn_search(query, country)
    print(f"Search: '{query}' ({country})...")
    arts = _parse(url, max_items=20, scrape=True)
    print(f"  Got {len(arts)} search results")
    
    # If few results, also try without country restriction
    if len(arts) < 5:
        url2 = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        if url2 != url:
            print(f"  Expanding search to US...")
            arts2 = _parse(url2, max_items=15, scrape=True)
            arts.extend(arts2)
            print(f"  Total: {len(arts)}")
    
    return arts

def fetch_backup_rss():
    arts = []
    for name, url in BACKUP_RSS.items():
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries: continue
            for e in feed.entries[:8]:
                desc = _clean(e.get("summary", e.get("description", "")))
                if not desc or len(desc)<20: continue
                img = _img_entry(e)
                if not img: img = _og_image(e.get("link", ""))
                arts.append({
                    "id": _id(e.get("title", "")), "title": e.get("title", ""),
                    "description": desc[:500], "content": desc, "source": name,
                    "url": e.get("link", ""), "published_at": e.get("published", ""),
                    "image_url": img, "sub_sources": [],
                })
        except: pass
    print(f"Backup RSS: {len(arts)} articles")
    return arts


def get_all_articles(country="US"):
    """Fetch 30+ articles from top news + 8 topic feeds + 8 backup RSS sources."""
    top = fetch_google_top_news(country)
    time.sleep(0.3)
    topics = fetch_google_topic_news(country)
    time.sleep(0.3)
    backup = fetch_backup_rss()
    
    all_a = top + topics + backup
    seen = set()
    unique = []
    for a in all_a:
        key = re.sub(r'[^\w\s]', '', a["title"].lower()).strip()[:50]
        if key and key not in seen and len(a["title"]) > 10:
            seen.add(key)
            unique.append(a)
    img_ct = sum(1 for a in unique if a['image_url'])
    print(f"\n=== {len(unique)} unique articles, {img_ct} with images ({country}) ===\n")
    return unique
