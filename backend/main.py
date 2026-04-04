"""
main.py — KhabarLens AI. Now with explainable polarization, headline comparison,
credibility-weighted scoring, and narrative timeline.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import asyncio, hashlib, httpx, os, json, re
from dotenv import load_dotenv
from openai import AsyncOpenAI
from news_ingestion import get_all_articles, fetch_google_search
from clustering import cluster_articles
from ai_analysis import analyze_cluster
from polarization import calculate_polarization

load_dotenv()
app = FastAPI(title="KhabarLens AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SEMAPHORE = asyncio.Semaphore(4)
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_cache = {"stories": [], "country": "US"}

# Source credibility weights (0.0 = unreliable, 1.0 = gold standard)
SOURCE_CREDIBILITY = {
    "reuters": 0.95, "ap news": 0.95, "associated press": 0.95,
    "bbc": 0.90, "bbc news": 0.90, "npr": 0.88,
    "the guardian": 0.85, "the washington post": 0.85, "the new york times": 0.87,
    "cnn": 0.78, "cbs news": 0.82, "abc news": 0.82, "nbc news": 0.80,
    "al jazeera": 0.80, "pbs": 0.88, "bloomberg": 0.87,
    "fox news": 0.65, "the daily beast": 0.62, "breitbart": 0.45,
    "huffpost": 0.60, "daily mail": 0.50, "new york post": 0.58,
    "politico": 0.82, "axios": 0.83, "the hill": 0.78,
    "forbes": 0.80, "financial times": 0.88, "wall street journal": 0.87,
    "slate": 0.68, "vox": 0.65, "the intercept": 0.65,
    "usa today": 0.75, "newsweek": 0.70, "time": 0.78,
    "yahoo news": 0.65, "yahoo news uk": 0.65,
    "eurogamer": 0.70, "kotaku": 0.65, "the verge": 0.75,
}

def get_credibility(source_name):
    return SOURCE_CREDIBILITY.get(source_name.lower().strip(), 0.60)


async def _proc(cluster):
    async with SEMAPHORE:
        analysis = await analyze_cluster(cluster)
        if not analysis: return None
        pol = calculate_polarization(cluster, analysis)
        
        # Credibility-weighted polarization
        source_analysis = analysis.get("source_analysis", [])
        if len(source_analysis) >= 2:
            weights = []
            for sa in source_analysis:
                cred = get_credibility(sa.get("source_name", ""))
                bias = sa.get("bias_score", 0.0)
                weights.append({"source": sa["source_name"], "credibility": cred, "bias": bias})
            
            total_w = sum(w["credibility"] for w in weights) or 1
            weighted_bias = sum(w["bias"] * w["credibility"] for w in weights) / total_w
            credibility_adjusted_pol = round(weighted_bias * 100)
        else:
            weights = []
            credibility_adjusted_pol = pol["score"]

        # Build headline comparison data
        headlines_by_source = []
        for art in cluster["articles"]:
            cred = get_credibility(art["source"])
            headlines_by_source.append({
                "source": art["source"],
                "headline": art["title"],
                "url": art["url"],
                "credibility": cred,
            })

        return {
            "id": int(hashlib.md5(cluster["primary_title"].encode()).hexdigest()[:8], 16) % 100000,
            "headline": analysis.get("headline", cluster["primary_title"]),
            "neutral_summary": analysis.get("neutral_summary", ""),
            "key_facts": analysis.get("key_facts", {}),
            "perspectives": analysis.get("perspectives", []),
            "source_analysis": analysis.get("source_analysis", []),
            "polarization": pol,
            "credibility_weighted_pol": credibility_adjusted_pol,
            "source_credibility": weights,
            "headlines_by_source": headlines_by_source,
            "sources": cluster["sources"],
            "source_count": cluster["source_count"],
            "topic_tags": analysis.get("topic_tags", []),
            "category": analysis.get("category", "General News"),
            "is_adverse": analysis.get("is_adverse", False),
            "adverse_reason": analysis.get("adverse_reason", ""),
            "severity": analysis.get("severity", "low"),
            "sentiment_score": analysis.get("sentiment_score", 0.0),
            "article_count": len(cluster["articles"]),
            "image_url": next((a["image_url"] for a in cluster["articles"] if a.get("image_url")), None),
            "original_articles": [
                {"title": a["title"], "source": a["source"], "url": a["url"]}
                for a in cluster["articles"]
            ],
        }


@app.get("/api/stories")
async def get_stories(limit: int = 30, country: str = "US"):
    loop = asyncio.get_event_loop()
    articles = await loop.run_in_executor(None, get_all_articles, country)
    if not articles: return {"stories": [], "all_stories": [], "total": 0}
    clusters = await cluster_articles(articles)
    tasks = [_proc(c) for c in clusters[:min(limit, 30)]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_stories = [r for r in results if r and not isinstance(r, Exception)]
    all_stories.sort(key=lambda s: s["polarization"]["score"], reverse=True)
    _cache["stories"] = all_stories
    _cache["country"] = country
    
    # Find most polarized
    most_pol = all_stories[0] if all_stories else None
    
    return {
        "stories": all_stories[:12],
        "all_stories": all_stories,
        "total": len(all_stories),
        "total_articles_processed": len(articles),
        "total_clusters": len(clusters),
        "most_polarized": {
            "headline": most_pol["headline"],
            "score": most_pol["polarization"]["score"],
            "category": most_pol["category"],
        } if most_pol else None,
    }


@app.get("/api/search")
async def search_stories(q: str = Query(..., min_length=1), limit: int = 15, country: str = "US"):
    loop = asyncio.get_event_loop()
    articles = await loop.run_in_executor(None, fetch_google_search, q, country)
    if not articles: return {"stories": [], "query": q, "total": 0}
    clusters = await cluster_articles(articles)
    tasks = [_proc(c) for c in clusters[:min(limit, 15)]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    stories = [r for r in results if r and not isinstance(r, Exception)]
    stories.sort(key=lambda s: s["polarization"]["score"], reverse=True)
    return {"stories": stories, "query": q, "total": len(stories)}


class ExplainReq(BaseModel):
    headline: str
    summary: str
    sources: list = []
    perspectives: list = []
    source_analysis: list = []

@app.post("/api/explain-polarization")
async def explain_polarization(req: ExplainReq):
    """Generate human-readable explanation of WHY a story is polarized."""
    perspectives_text = "\n".join([f"- {p.get('label','')}: {p.get('summary','')}" for p in req.perspectives])
    sources_text = "\n".join([f"- {s.get('source_name','')}: tone={s.get('tone','')}, bias={s.get('bias_score',0)}, phrases={s.get('loaded_phrases',[])}" for s in req.source_analysis])

    try:
        r = await ai.chat.completions.create(model="gpt-4o-mini", messages=[
            {"role": "system", "content": "You analyze WHY news stories are polarized. Be specific, reference actual framing differences. Return ONLY valid JSON."},
            {"role": "user", "content": f"""Story: "{req.headline}"
Summary: {req.summary}
Sources: {', '.join(req.sources[:5])}
Perspectives: {perspectives_text}
Source Analysis: {sources_text}

Return JSON:
{{
    "reasons": [
        "Specific reason #1 referencing actual framing/tone differences between sources",
        "Specific reason #2 about word choice or emotional language",
        "Specific reason #3 about topic emphasis or omission"
    ],
    "headline_framing": {{
        "left_leaning": ["headline or framing from progressive sources"],
        "neutral": ["headline or framing from neutral sources"],
        "right_leaning": ["headline or framing from conservative sources"]
    }},
    "key_differences": [
        {{"aspect": "Emotional Tone", "description": "How tones differ across sources"}},
        {{"aspect": "Accountability Framing", "description": "Who is blamed or praised"}},
        {{"aspect": "Context Emphasis", "description": "What facts are highlighted vs downplayed"}}
    ],
    "one_line_summary": "One sentence explaining the core narrative split"
}}

Be SPECIFIC to this story. Reference actual source names and framing differences."""}
        ], temperature=0.3, max_tokens=1200, response_format={"type": "json_object"})
        return json.loads(r.choices[0].message.content.strip())
    except Exception as e:
        return {"error": str(e)[:100], "reasons": ["Analysis unavailable"]}


class TimelineReq(BaseModel):
    headline: str
    summary: str
    category: str = ""

@app.post("/api/narrative-timeline")
async def narrative_timeline(req: TimelineReq):
    """Generate a narrative evolution timeline for a story."""
    try:
        r = await ai.chat.completions.create(model="gpt-4o-mini", messages=[
            {"role": "system", "content": "You create narrative evolution timelines for news stories. Return ONLY valid JSON."},
            {"role": "user", "content": f"""Story: "{req.headline}"
Summary: {req.summary}
Category: {req.category}

Create a timeline showing how this type of story typically evolves in the media cycle.
Return JSON:
{{
    "timeline": [
        {{"phase": "Breaking", "description": "Initial wire reports, raw facts only", "sentiment": "neutral", "polarization": "low"}},
        {{"phase": "Reaction", "description": "Political reactions, expert commentary begins", "sentiment": "mixed", "polarization": "rising"}},
        {{"phase": "Framing Battle", "description": "Competing narratives emerge from different outlets", "sentiment": "diverging", "polarization": "high"}},
        {{"phase": "Current", "description": "Where the story is now — describe specifically", "sentiment": "describe", "polarization": "describe"}}
    ],
    "prediction": "One sentence: where this story is likely heading next",
    "narrative_shift": "What changed most in how this story is being told"
}}

Be specific to THIS story, not generic."""}
        ], temperature=0.3, max_tokens=800, response_format={"type": "json_object"})
        return json.loads(r.choices[0].message.content.strip())
    except Exception as e:
        return {"error": str(e)[:100]}


@app.get("/api/chat")
async def ai_chat(message: str = Query(..., max_length=500)):
    stories = _cache.get("stories", [])
    ctx = "\n".join([
        f"- \"{s['headline']}\" | {s['category']} | Pol:{s['polarization']['score']} "
        f"| Cred-Weighted:{s.get('credibility_weighted_pol','N/A')} "
        f"| {'ADVERSE' if s['is_adverse'] else 'Safe'} "
        f"| Sources: {', '.join(s['sources'][:3])}"
        for s in stories[:15]
    ])
    try:
        r = await ai.chat.completions.create(model="gpt-4o-mini", messages=[
            {"role": "system", "content": f"""You are KhabarLens AI analyst. You explain bias in simple terms, summarize both sides, explain why stories are controversial, and identify who benefits from narratives.

Stories loaded:
{ctx}

Be concise (2-3 sentences), insightful, reference actual story data. You can explain:
- Why a story is polarized
- Both sides of any issue
- Who benefits from a narrative
- What's missing from coverage
- Simple bias explanations"""},
            {"role": "user", "content": message}
        ], temperature=0.5, max_tokens=400)
        return {"reply": r.choices[0].message.content.strip()}
    except Exception as e: return {"reply": f"Error: {str(e)[:80]}"}


class AnalyzeReq(BaseModel):
    content: str
    mode: str = "text"

@app.post("/api/analyze")
async def analyze_article(req: AnalyzeReq):
    content = req.content.strip()
    if not content: return {"error": "No content"}
    article_text = content
    if req.mode == "url":
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
                resp = await http.get(content, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    html = resp.text[:20000]
                    title = ""; tm = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
                    if tm: title = tm.group(1).strip()
                    desc = ""; dm = re.search(r'<meta[^>]+(?:name=["\']description|property=["\']og:description)["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
                    if not dm: dm = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name=["\']description|property=["\']og:description)', html, re.I)
                    if dm: desc = dm.group(1).strip()
                    paras = re.findall(r'<p[^>]*>([^<]{20,})</p>', html)
                    body = " ".join(p.strip() for p in paras[:10])
                    article_text = f"Title: {title}\nDescription: {desc}\nBody: {body[:1500]}"
        except Exception as e:
            article_text = f"URL: {content} (failed: {str(e)[:50]})"
    try:
        r = await ai.chat.completions.create(model="gpt-4o-mini", messages=[
            {"role": "system", "content": "News credibility analyst. Return ONLY valid JSON."},
            {"role": "user", "content": f"""Analyze:\n\n{article_text[:2000]}\n\nReturn JSON:\n{{"credibility_score":0-100,"fake_news_risk":"Low/Medium/High","category":"one category","is_adverse":true/false,"adverse_reason":"","bias_direction":"Left-leaning/Right-leaning/Centrist/Neutral","bias_score":0-100,"summary":"2 sentences","red_flags":["list"],"verdict":"1 sentence"}}"""}
        ], temperature=0.2, max_tokens=800, response_format={"type": "json_object"})
        return json.loads(r.choices[0].message.content.strip())
    except Exception as e:
        return {"error": str(e)[:100], "verdict": "Analysis failed."}


class DeepReq(BaseModel):
    headline: str
    summary: str
    sources: list = []
    category: str = ""

@app.post("/api/deep-analysis")
async def deep_analysis(req: DeepReq):
    src = ", ".join(req.sources[:5]) if req.sources else "multiple"
    try:
        r = await ai.chat.completions.create(model="gpt-4o-mini", messages=[
            {"role": "system", "content": "Objective news architect. Return ONLY valid JSON. Be specific."},
            {"role": "user", "content": f"""Analyze: "{req.headline}" — {req.summary} (Sources: {src}, Category: {req.category})
Return JSON: {{"perspective_slider":{{"left":{{"title":"Progressive Lens","summary":"3-4 sentences","key_angle":"1 sentence"}},"center":{{"title":"Neutral Analysis","summary":"3-4 clinical sentences","key_angle":"1 sentence"}},"right":{{"title":"Conservative Lens","summary":"3-4 sentences","key_angle":"1 sentence"}}}},"omission_radar":[{{"missing_context":"fact","why_it_matters":"why"}},{{"missing_context":"fact","why_it_matters":"why"}},{{"missing_context":"fact","why_it_matters":"why"}}],"gen_z_mode":{{"the_tea":"1 sentence","the_receipts":["fact1","fact2","fact3"],"vibe_check":"big deal/overhyped/developing story","vibe_explanation":"why","main_character":"name","main_character_role":"role"}},"bias_meter":{{"overall_lean":"Left/Center-Left/Center/Center-Right/Right","confidence":"High/Medium/Low","reasoning":"1-2 sentences"}}}}
Be SPECIFIC to this story."""}
        ], temperature=0.3, max_tokens=2000, response_format={"type": "json_object"})
        return json.loads(r.choices[0].message.content.strip())
    except Exception as e: return {"error": str(e)[:100]}


@app.get("/api/tts")
async def tts(text: str = Query(..., max_length=1000), lang: str = "en"):
    if not ELEVENLABS_KEY: return Response(content=b"", status_code=503)
    async with httpx.AsyncClient() as http:
        try:
            r = await http.post(f"https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
                json={"text": text[:1000], "model_id": "eleven_multilingual_v2" if lang != "en" else "eleven_monolingual_v1",
                       "voice_settings": {"stability": 0.7, "similarity_boost": 0.8}}, timeout=30.0)
            return Response(content=r.content, media_type="audio/mpeg") if r.status_code == 200 else Response(content=b"", status_code=r.status_code)
        except: return Response(content=b"", status_code=500)

@app.get("/api/briefing-text")
async def briefing(limit: int = 5):
    s = _cache.get("stories", [])[:limit]
    if not s: return {"text": "No stories.", "count": 0}
    return {"text": "KhabarLens briefing. " + " ".join([f"Story {i+1}: {x['headline']}. {x['neutral_summary']} " for i,x in enumerate(s)]) + "End.", "count": len(s)}

if __name__ == "__main__":
    import uvicorn
    print("\n  KhabarLens AI v3 — http://localhost:8000/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
