"""
main.py — KhabarLens AI
- SQLite cache: max 30 unique stories per country
- On load: serve cache instantly, kick off background fetch of 5 new stories
- Cold start: loads from seed_data.json (pre-baked, committed to git) instantly
- Dedup: headline hash + word-overlap check in cache.py
- Rate limit: only /api/stories and /api/search (10 loads per IP, 30s cooldown)
- All AI endpoints use Groq retry on 429
"""

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import asyncio, hashlib, httpx, os, json, re, time
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from groq import AsyncGroq
from news_ingestion import get_all_articles, fetch_google_search
from clustering import cluster_articles
from ai_analysis import analyze_cluster
from polarization import calculate_polarization
from cache import (
    init_db, save_stories, load_stories, count_stories,
    delete_expired, get_cached_headlines,
    set_refresh_status, get_refresh_status,
    _headline_hash, MAX_STORIES,
)

load_dotenv()
app = FastAPI(title="KhabarLens AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

SEMAPHORE           = asyncio.Semaphore(3)
ELEVENLABS_KEY      = os.getenv("ELEVENLABS_API_KEY", "")
ai                  = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL               = "llama-3.1-8b-instant"   # 30k TPM free tier
_cache              = {"stories": [], "country": "US"}
_refresh_lock       = defaultdict(asyncio.Lock)

COLD_FETCH_LIMIT    = 10   # clusters to analyze on cold cache (fills DB to ~10 stories)
REFRESH_BATCH       = 5    # new stories fetched per background refresh
SERVE_LIMIT         = 30   # max stories returned to frontend

SEED_JSON_PATH      = os.path.join(os.path.dirname(__file__), "seed_data.json")


@app.on_event("startup")
async def startup():
    init_db()
    delete_expired()

    # --- INSTANT LOAD: if DB is empty, hydrate from pre-baked seed_data.json ---
    # This runs in <100ms vs 2 minutes for live API seeding.
    total_in_db = sum(count_stories(c) for c in ["US", "UK", "IN", "FR", "DE", "JP", "WORLD"])
    if total_in_db == 0:
        if os.path.exists(SEED_JSON_PATH):
            print("[startup] Empty DB — loading from seed_data.json instantly...")
            _load_seed_json()
        else:
            # Fallback: no seed file, run background auto-seed (old behaviour)
            print("[startup] Empty DB and no seed_data.json — auto-seeding in background (slow)...")
            asyncio.create_task(_auto_seed())
    else:
        print(f"[startup] DB has {total_in_db} stories — ready instantly.")

    # Pre-warm the US cache into memory so first /api/stories is instant
    us_stories = load_stories("US")
    if us_stories:
        _cache.update({"stories": us_stories, "country": "US"})
        print(f"[startup] Pre-warmed US cache with {len(us_stories)} stories.")


def _load_seed_json():
    """
    Loads pre-baked stories from seed_data.json into SQLite.
    Stamps them with today's created_at so TTL doesn't expire them immediately.
    """
    try:
        with open(SEED_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        stories_by_country = data.get("stories", {})
        now = datetime.utcnow().isoformat()
        total_saved = 0

        for country, stories in stories_by_country.items():
            # Stamp fresh created_at so they survive TTL check
            for s in stories:
                s["_seed_loaded_at"] = now

            saved = save_stories(stories, country)
            total_saved += saved
            print(f"[seed_json] {country}: {saved} stories loaded")

        print(f"[seed_json] ✅ Total: {total_saved} stories loaded from seed_data.json in <1s")

    except Exception as e:
        print(f"[seed_json] ❌ Failed to load seed_data.json: {e}")
        # Fallback to background seeding so the app doesn't stay empty
        asyncio.create_task(_auto_seed())


async def _auto_seed():
    """Quick seed on cold start — fetches 1 story per key category for US only.
    Only used as fallback when seed_data.json is not present."""
    QUICK_QUERIES = [
        ("Economy & Markets",  "Federal Reserve interest rates inflation GDP"),
        ("Geopolitics",        "US China Russia diplomacy military tensions"),
        ("AI & Tech Ethics",   "OpenAI artificial intelligence regulation news"),
        ("Health",             "WHO disease outbreak hospital pandemic"),
        ("Environment",        "climate change wildfire flood disaster"),
        ("General News",       "US politics Congress White House news today"),
        ("Terrorism",          "terror attack arrest FBI foiled plot"),
        ("Sanctions",          "US sanctions Russia Iran trade ban OFAC"),
        ("Cybercrime",         "ransomware cyberattack data breach hacker"),
        ("War Crimes",         "Gaza Ukraine ICC war crimes civilian"),
    ]
    loop = asyncio.get_event_loop()
    seen = set()
    stories = []
    for country in ["US", "UK", "IN", "WORLD"]:
        for cat, query in QUICK_QUERIES:
            try:
                articles = await loop.run_in_executor(None, fetch_google_search, query, country)
                if not articles: continue
                clusters = await cluster_articles(articles)
                for c in clusters[:1]:
                    h = _headline_hash(c["primary_title"])
                    if h in seen: continue
                    seen.add(h)
                    story = await _proc(c)
                    if story:
                        story["category"] = cat
                        stories.append((story, country))
                        print(f"[seed] [{country}] {story['headline'][:60]}")
                        break
            except Exception as e:
                print(f"[seed] Error: {e}")
                continue
    from itertools import groupby
    from operator import itemgetter
    by_country = {}
    for story, country in stories:
        by_country.setdefault(country, []).append(story)
    for country, s_list in by_country.items():
        save_stories(s_list, country)
        print(f"[seed] Saved {len(s_list)} stories for {country}")


# ── Rate limiting ──────────────────────────────────────────────────────────────
RATE_LIMIT       = 10
COOLDOWN_SECONDS = 30
_usage: dict     = defaultdict(int)
_last_call: dict = {}

def check_rate_limit(request: Request):
    ip  = request.client.host
    now = time.time()
    if now - _last_call.get(ip, 0) < COOLDOWN_SECONDS:
        return
    _last_call[ip] = now
    if _usage[ip] >= RATE_LIMIT:
        raise HTTPException(429,
            detail=f"You've used your {RATE_LIMIT} free story loads. Self-host on GitHub for unlimited access!")
    _usage[ip] += 1


# ── Groq retry ────────────────────────────────────────────────────────────────
async def groq_with_retry(fn):
    for attempt in range(6):
        try:
            return await fn()
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate_limit_exceeded" in msg:
                wait = float(re.search(r'try again in ([\d.]+)s', msg).group(1)) + 1 \
                       if re.search(r'try again in ([\d.]+)s', msg) else 20
                print(f"Groq 429 — waiting {wait:.0f}s (attempt {attempt+1}/6)")
                await asyncio.sleep(wait)
            else:
                raise
    raise Exception("Max Groq retries exceeded")


# ── Source credibility ─────────────────────────────────────────────────────────
SOURCE_CREDIBILITY = {
    "reuters":0.95,"ap news":0.95,"associated press":0.95,"bbc":0.90,"bbc news":0.90,
    "npr":0.88,"the guardian":0.85,"the washington post":0.85,"the new york times":0.87,
    "cnn":0.78,"cbs news":0.82,"abc news":0.82,"nbc news":0.80,"al jazeera":0.80,
    "pbs":0.88,"bloomberg":0.87,"fox news":0.65,"the daily beast":0.62,"breitbart":0.45,
    "huffpost":0.60,"daily mail":0.50,"new york post":0.58,"politico":0.82,"axios":0.83,
    "the hill":0.78,"forbes":0.80,"financial times":0.88,"wall street journal":0.87,
    "slate":0.68,"vox":0.65,"the intercept":0.65,"usa today":0.75,"newsweek":0.70,
    "time":0.78,"yahoo news":0.65,"yahoo news uk":0.65,"the verge":0.75,
}
def get_cred(src): return SOURCE_CREDIBILITY.get(src.lower().strip(), 0.60)


# ── Process cluster → story dict ──────────────────────────────────────────────
async def _proc(cluster):
    async with SEMAPHORE:
        analysis = await analyze_cluster(cluster)
        if not analysis:
            return None
        pol = calculate_polarization(cluster, analysis)
        sa  = analysis.get("source_analysis", [])
        if len(sa) >= 2:
            weights = [{"source": x["source_name"],
                        "credibility": get_cred(x.get("source_name","")),
                        "bias": x.get("bias_score", 0.0)} for x in sa]
            tw  = sum(w["credibility"] for w in weights) or 1
            cap = round(sum(w["bias"]*w["credibility"] for w in weights)/tw*100)
        else:
            weights, cap = [], pol["score"]

        return {
            "id": int(hashlib.md5(cluster["primary_title"].encode()).hexdigest()[:8],16)%100000,
            "headline":           analysis.get("headline", cluster["primary_title"]),
            "neutral_summary":    analysis.get("neutral_summary", ""),
            "key_facts":          analysis.get("key_facts", {}),
            "perspectives":       analysis.get("perspectives", []),
            "source_analysis":    sa,
            "polarization":       pol,
            "credibility_weighted_pol": cap,
            "source_credibility": weights,
            "headlines_by_source": [{"source":a["source"],"headline":a["title"],
                                      "url":a["url"],"credibility":get_cred(a["source"])}
                                     for a in cluster["articles"]],
            "sources":       cluster["sources"],
            "source_count":  cluster["source_count"],
            "topic_tags":    analysis.get("topic_tags", []),
            "category":      analysis.get("category", "General News"),
            "is_adverse":    analysis.get("is_adverse", False),
            "adverse_reason":analysis.get("adverse_reason", ""),
            "severity":      analysis.get("severity", "low"),
            "sentiment_score":analysis.get("sentiment_score", 0.0),
            "article_count": len(cluster["articles"]),
            "image_url":     next((a["image_url"] for a in cluster["articles"]
                                   if a.get("image_url")), None),
            "original_articles": [{"title":a["title"],"source":a["source"],"url":a["url"]}
                                   for a in cluster["articles"]],
        }


# ── Background refresh: fetch 5 new stories ───────────────────────────────────
async def _background_refresh(country: str):
    async with _refresh_lock[country]:
        set_refresh_status(country, "running", 0)
        print(f"[refresh] Starting for {country}…")
        try:
            loop     = asyncio.get_event_loop()
            articles = await loop.run_in_executor(None, get_all_articles, country)
            if not articles:
                set_refresh_status(country, "idle", 0)
                return

            clusters = await cluster_articles(articles)

            existing = get_cached_headlines(country)
            new_clusters = [
                c for c in clusters
                if _headline_hash(c["primary_title"]) not in existing
            ][:REFRESH_BATCH]

            if not new_clusters:
                print(f"[refresh] No new clusters for {country}")
                set_refresh_status(country, "done", 0)
                return

            print(f"[refresh] Analyzing {len(new_clusters)} new clusters…")
            results = await asyncio.gather(
                *[_proc(c) for c in new_clusters], return_exceptions=True
            )
            new_stories = [r for r in results if r and not isinstance(r, Exception)]

            if new_stories:
                saved = save_stories(new_stories, country)
                updated = load_stories(country)
                _cache["stories"] = updated
                print(f"[refresh] +{saved} stories, DB now {len(updated)} for {country}")
                set_refresh_status(country, "done", saved)
            else:
                set_refresh_status(country, "done", 0)

        except Exception as e:
            print(f"[refresh] Error: {e}")
            set_refresh_status(country, "idle", 0)


# ── /api/stories ──────────────────────────────────────────────────────────────
@app.get("/api/stories")
async def get_stories(request: Request, country: str = "US", force_refresh: bool = False):
    check_rate_limit(request)
    delete_expired(country)

    cached = load_stories(country)

    if cached and not force_refresh:
        _cache.update({"stories": cached, "country": country})
        most_pol = cached[0]

        if get_refresh_status(country)["status"] != "running":
            asyncio.create_task(_background_refresh(country))

        return {
            "stories":     cached[:SERVE_LIMIT],
            "all_stories": cached,
            "total":       len(cached),
            "source":      "cache",
            "most_polarized": {
                "headline": most_pol["headline"],
                "score":    most_pol["polarization"]["score"],
                "category": most_pol["category"],
            },
        }

    # Cold cache — full blocking fetch
    print(f"[stories] Cold cache for {country}, full fetch…")
    loop     = asyncio.get_event_loop()
    articles = await loop.run_in_executor(None, get_all_articles, country)
    if not articles:
        return {"stories":[], "all_stories":[], "total":0, "source":"fresh"}

    clusters = await cluster_articles(articles)
    results  = await asyncio.gather(
        *[_proc(c) for c in clusters[:COLD_FETCH_LIMIT]], return_exceptions=True
    )
    stories = [r for r in results if r and not isinstance(r, Exception)]
    stories.sort(key=lambda s: s["polarization"]["score"], reverse=True)

    if stories:
        save_stories(stories, country)

    _cache.update({"stories": stories, "country": country})
    most_pol = stories[0] if stories else None

    return {
        "stories":     stories[:SERVE_LIMIT],
        "all_stories": stories,
        "total":       len(stories),
        "source":      "fresh",
        "most_polarized": {
            "headline": most_pol["headline"],
            "score":    most_pol["polarization"]["score"],
            "category": most_pol["category"],
        } if most_pol else None,
    }


# ── /api/refresh-status ───────────────────────────────────────────────────────
@app.get("/api/refresh-status")
async def refresh_status(country: str = "US"):
    status = get_refresh_status(country)
    if status["status"] == "done" and status["new_count"] > 0:
        latest = load_stories(country)
        set_refresh_status(country, "idle", 0)
        return {
            "status":      "done",
            "new_count":   status["new_count"],
            "stories":     latest[:SERVE_LIMIT],
            "all_stories": latest,
        }
    return {"status": status["status"], "new_count": status["new_count"]}


# ── /api/search ───────────────────────────────────────────────────────────────
@app.get("/api/search")
async def search_stories(request: Request,
                          q: str = Query(..., min_length=1),
                          country: str = "US"):
    check_rate_limit(request)
    loop     = asyncio.get_event_loop()
    articles = await loop.run_in_executor(None, fetch_google_search, q, country)
    if not articles:
        return {"stories":[], "query":q, "total":0}

    clusters = await cluster_articles(articles)
    results  = await asyncio.gather(
        *[_proc(c) for c in clusters[:5]], return_exceptions=True
    )
    stories = [r for r in results if r and not isinstance(r, Exception)]
    stories.sort(key=lambda s: s["polarization"]["score"], reverse=True)

    if stories:
        save_stories(stories, country)

    return {"stories": stories, "query": q, "total": len(stories)}


# ── Deep analysis (no rate limit, Groq retry) ─────────────────────────────────

class ExplainReq(BaseModel):
    headline: str; summary: str; sources: list = []; perspectives: list = []; source_analysis: list = []

@app.post("/api/explain-polarization")
async def explain_polarization(req: ExplainReq):
    pt = "\n".join([f"- {p.get('label','')}: {p.get('summary','')}" for p in req.perspectives])
    st = "\n".join([f"- {s.get('source_name','')}: bias={s.get('bias_score',0)}" for s in req.source_analysis])
    try:
        r = await groq_with_retry(lambda: ai.chat.completions.create(
            model=MODEL, temperature=0.3, max_tokens=1000,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":"Analyze WHY stories are polarized. Return ONLY valid JSON, no markdown."},
                {"role":"user","content":f"""Story: "{req.headline}"\nSummary: {req.summary}\nSources: {', '.join(req.sources[:5])}\nPerspectives: {pt}\nAnalysis: {st}\n\nReturn JSON:\n{{"reasons":["...","...","..."],"headline_framing":{{"left_leaning":["..."],"neutral":["..."],"right_leaning":["..."]}},"key_differences":[{{"aspect":"Emotional Tone","description":"..."}},{{"aspect":"Accountability","description":"..."}},{{"aspect":"Context","description":"..."}}],"one_line_summary":"..."}}"""},
            ],
        ))
        return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',r.choices[0].message.content.strip()))
    except Exception as e:
        return {"error":str(e)[:100],"reasons":["Analysis unavailable"]}


class TimelineReq(BaseModel):
    headline: str; summary: str; category: str = ""

@app.post("/api/narrative-timeline")
async def narrative_timeline(req: TimelineReq):
    try:
        r = await groq_with_retry(lambda: ai.chat.completions.create(
            model=MODEL, temperature=0.3, max_tokens=700,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":"Create narrative timelines. Return ONLY valid JSON, no markdown."},
                {"role":"user","content":f"""Story: "{req.headline}"\nSummary: {req.summary}\nCategory: {req.category}\n\nReturn JSON:\n{{"timeline":[{{"phase":"Breaking","description":"...","sentiment":"neutral","polarization":"low"}},{{"phase":"Reaction","description":"...","sentiment":"mixed","polarization":"rising"}},{{"phase":"Framing Battle","description":"...","sentiment":"diverging","polarization":"high"}},{{"phase":"Current","description":"...","sentiment":"...","polarization":"..."}}],"prediction":"...","narrative_shift":"..."}}"""},
            ],
        ))
        return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',r.choices[0].message.content.strip()))
    except Exception as e:
        return {"error":str(e)[:100]}


@app.get("/api/chat")
async def ai_chat(message: str = Query(..., max_length=500)):
    ctx = "\n".join([
        f"- \"{s['headline']}\" | {s['category']} | Pol:{s['polarization']['score']} | {'ADVERSE' if s['is_adverse'] else 'Safe'}"
        for s in _cache.get("stories",[])[:10]
    ])
    try:
        r = await groq_with_retry(lambda: ai.chat.completions.create(
            model=MODEL, temperature=0.5, max_tokens=300,
            messages=[
                {"role":"system","content":f"KhabarLens AI analyst. Explain bias simply, 2-3 sentences.\n\nStories:\n{ctx}"},
                {"role":"user","content":message},
            ],
        ))
        return {"reply": r.choices[0].message.content.strip()}
    except Exception as e:
        return {"reply": f"Error: {str(e)[:80]}"}


class AnalyzeReq(BaseModel):
    content: str; mode: str = "text"

@app.post("/api/analyze")
async def analyze_article(req: AnalyzeReq):
    content = req.content.strip()
    if not content: return {"error":"No content"}
    text = content
    if req.mode == "url":
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
                resp = await http.get(content, headers={"User-Agent":"Mozilla/5.0"})
                if resp.status_code == 200:
                    html = resp.text[:20000]
                    tm = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
                    dm = re.search(r'<meta[^>]+(?:name=["\']description|property=["\']og:description)["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
                    ps = re.findall(r'<p[^>]*>([^<]{20,})</p>', html)
                    text = f"Title: {tm.group(1).strip() if tm else ''}\nDesc: {dm.group(1).strip() if dm else ''}\nBody: {' '.join(p.strip() for p in ps[:10])[:1500]}"
        except Exception as e:
            text = f"URL failed: {str(e)[:50]}"
    try:
        r = await groq_with_retry(lambda: ai.chat.completions.create(
            model=MODEL, temperature=0.2, max_tokens=800,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":"News credibility analyst. Return ONLY valid JSON, no markdown."},
                {"role":"user","content":f"Analyze:\n\n{text[:2000]}\n\nReturn JSON:\n{{\"credibility_score\":0,\"fake_news_risk\":\"Low\",\"category\":\"\",\"is_adverse\":false,\"adverse_reason\":\"\",\"bias_direction\":\"Neutral\",\"bias_score\":0,\"summary\":\"\",\"red_flags\":[],\"verdict\":\"\"}}"},
            ],
        ))
        return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',r.choices[0].message.content.strip()))
    except Exception as e:
        return {"error":str(e)[:100],"verdict":"Analysis failed."}


class DeepReq(BaseModel):
    headline: str; summary: str; sources: list = []; category: str = ""

@app.post("/api/deep-analysis")
async def deep_analysis(req: DeepReq):
    src = ", ".join(req.sources[:5]) or "multiple"
    try:
        r = await groq_with_retry(lambda: ai.chat.completions.create(
            model=MODEL, temperature=0.3, max_tokens=1500,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":"Objective news architect. Return ONLY valid JSON, no markdown."},
                {"role":"user","content":f"""Analyze: "{req.headline}" — {req.summary} (Sources: {src}, Category: {req.category})\n\nReturn JSON:\n{{"perspective_slider":{{"left":{{"title":"Progressive Lens","summary":"3-4 sentences","key_angle":"1 sentence"}},"center":{{"title":"Neutral Analysis","summary":"3-4 sentences","key_angle":"1 sentence"}},"right":{{"title":"Conservative Lens","summary":"3-4 sentences","key_angle":"1 sentence"}}}},"omission_radar":[{{"missing_context":"...","why_it_matters":"..."}},{{"missing_context":"...","why_it_matters":"..."}},{{"missing_context":"...","why_it_matters":"..."}}],"gen_z_mode":{{"the_tea":"...","the_receipts":["...","...","..."],"vibe_check":"big deal/overhyped/developing story","vibe_explanation":"...","main_character":"...","main_character_role":"..."}},"bias_meter":{{"overall_lean":"Left/Center-Left/Center/Center-Right/Right","confidence":"High/Medium/Low","reasoning":"..."}}}}"""},
            ],
        ))
        return json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',r.choices[0].message.content.strip()))
    except Exception as e:
        return {"error":str(e)[:100]}


# ── Non-AI ─────────────────────────────────────────────────────────────────────

@app.get("/api/tts")
async def tts(text: str = Query(..., max_length=1000), lang: str = "en"):
    if not ELEVENLABS_KEY: return Response(content=b"", status_code=503)
    async with httpx.AsyncClient() as http:
        try:
            r = await http.post(
                "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                headers={"xi-api-key":ELEVENLABS_KEY,"Content-Type":"application/json"},
                json={"text":text[:1000],"model_id":"eleven_multilingual_v2" if lang!="en" else "eleven_monolingual_v1","voice_settings":{"stability":0.7,"similarity_boost":0.8}},
                timeout=30.0)
            return Response(content=r.content, media_type="audio/mpeg") if r.status_code==200 else Response(content=b"",status_code=r.status_code)
        except: return Response(content=b"",status_code=500)

@app.get("/api/briefing-text")
async def briefing(limit: int = 5):
    s = _cache.get("stories",[])[:limit]
    if not s: return {"text":"No stories.","count":0}
    return {"text":"KhabarLens briefing. "+" ".join([f"Story {i+1}: {x['headline']}. {x['neutral_summary']} " for i,x in enumerate(s)])+"End.","count":len(s)}

if __name__ == "__main__":
    import uvicorn
    print("\n  KhabarLens AI — max 30 stories, 5-story refresh — http://localhost:8000/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
