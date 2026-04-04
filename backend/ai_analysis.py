"""
ai_analysis.py — 21 categories, calibrated adverse detection, inference engineering.
"""

import json, re
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def analyze_cluster(cluster: dict) -> dict:
    articles_text = ""
    for i, art in enumerate(cluster["articles"][:6]):
        content = art.get("content", "") or art.get("description", "")
        articles_text += f"\n--- Article {i+1} (Source: {art['source']}) ---\nTitle: {art['title']}\nContent: {content[:700]}\n"

    subs = list(set(s for a in cluster["articles"] for s in a.get("sub_sources", [])))
    if subs: articles_text += f"\nOther sources: {', '.join(subs[:8])}\n"

    prompt = f"""Analyze these articles about the SAME story. Return JSON.

{articles_text}

Return ONLY valid JSON:
{{
    "headline": "Neutral headline, max 12 words",
    "neutral_summary": "Exactly 60 words. Factual, coherent paragraph. Write like Reuters wire copy. NEVER concatenate titles.",
    "key_facts": {{"who": "...", "what": "...", "when": "...", "where": "...", "why": "..."}},
    "category": "Pick ONE: Financial Crime | Money Laundering | Fraud & Scams | Insider Trading | Terrorism | Sanctions | Regulatory & Compliance | FINRA & SEC | Human Rights | War Crimes | Crime, Law & Justice | Cybercrime | Drug Trafficking | Corruption | Economy & Markets | Geopolitics | AI & Tech Ethics | Environment | Health | General News",
    "is_adverse": false,
    "adverse_reason": "",
    "perspectives": [
        {{"label": "Progressive framing", "summary": "35-40 words. How progressive media frames this based on ACTUAL language patterns.", "emphasis": "What this lens highlights"}},
        {{"label": "Conservative framing", "summary": "35-40 words. How conservative media frames this based on ACTUAL language patterns.", "emphasis": "What this lens highlights"}},
        {{"label": "Centrist framing", "summary": "35-40 words. Neutral, fact-focused framing.", "emphasis": "Core factual takeaway"}}
    ],
    "source_analysis": [
        {{"source_name": "...", "tone": "positive/negative/neutral", "loaded_phrases": ["actual phrases"], "bias_score": 0.0, "framing_note": "How this source frames it differently"}}
    ],
    "topic_tags": ["tag1", "tag2", "tag3"],
    "severity": "low/medium/high",
    "sentiment_score": -1.0 to 1.0
}}

ADVERSE RULES (is_adverse=true ONLY for):
- Financial fraud, embezzlement, Ponzi schemes, market manipulation
- Money laundering, sanctions evasion
- Terrorism, terrorist financing
- Regulatory fines/penalties by SEC, FINRA, FCA, etc.
- Human rights abuse, war crimes, genocide
- Cybercrime, ransomware attacks
- Drug trafficking, organized crime
- Bribery, corruption charges

NOT adverse: politics, elections, policy debates, military conflicts (unless war crimes), business decisions, layoffs, protests, natural disasters, technology changes.

BIAS RUBRIC: 0.0-0.2=wire-service neutral | 0.2-0.4=slight framing | 0.4-0.6=clear editorial | 0.6-0.8=strong opinion | 0.8-1.0=advocacy"""

    try:
        r = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Precise news analyst. Classify conservatively. Write Reuters-style summaries. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, max_tokens=2500,
            response_format={"type": "json_object"},
        )
        txt = r.choices[0].message.content.strip()
        txt = re.sub(r'^```(?:json)?\s*', '', txt)
        txt = re.sub(r'\s*```$', '', txt)
        txt = re.sub(r',\s*([}\]])', r'\1', txt)
        analysis = json.loads(txt)
        for k, v in {"headline": cluster["primary_title"][:80], "neutral_summary": "", "key_facts": {}, "category": "General News", "is_adverse": False, "adverse_reason": "", "perspectives": [], "source_analysis": [], "topic_tags": ["news"], "severity": "low", "sentiment_score": 0.0}.items():
            if k not in analysis: analysis[k] = v
        return analysis
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        return _fb(cluster)
    except Exception as e:
        print(f"AI error: {e}")
        return _fb(cluster)


def _fb(cluster):
    d = cluster["articles"][0].get("description", cluster["articles"][0].get("title", ""))
    return {
        "headline": cluster["primary_title"][:80], "neutral_summary": d[:250],
        "key_facts": {"who": "N/A", "what": cluster["primary_title"], "when": "Today", "where": "N/A", "why": "N/A"},
        "category": "General News", "is_adverse": False, "adverse_reason": "",
        "perspectives": [
            {"label": "Progressive framing", "summary": "Multiple diverse sources needed for meaningful perspective comparison.", "emphasis": ""},
            {"label": "Conservative framing", "summary": "Multiple diverse sources needed for meaningful perspective comparison.", "emphasis": ""},
            {"label": "Centrist framing", "summary": d[:150], "emphasis": ""},
        ],
        "source_analysis": [{"source_name": a["source"], "tone": "neutral", "loaded_phrases": [], "bias_score": 0.15, "framing_note": "Analysis pending."} for a in cluster["articles"][:3]],
        "topic_tags": ["news"], "severity": "low", "sentiment_score": 0.0,
    }
