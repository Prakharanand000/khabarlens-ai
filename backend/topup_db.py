"""
topup_db.py — Fetch stories only for under-represented categories.
Does NOT wipe the DB. Adds to existing stories, respects 30-story cap per country.
Usage: cd backend && python topup_db.py
"""

import asyncio, sys, os, hashlib, sqlite3, json
sys.path.insert(0, os.path.dirname(__file__))

from news_ingestion import fetch_google_search
from clustering import cluster_articles
from ai_analysis import analyze_cluster
from polarization import calculate_polarization
from cache import init_db, save_stories, load_stories, count_stories, _headline_hash
from collections import Counter

DB_PATH   = os.path.join(os.path.dirname(__file__), "khabarlens_cache.db")
SEMAPHORE = asyncio.Semaphore(2)

# ── Categories we want to top up + exactly what to search ─────────────────────
# These are the thin/missing categories from the retag output.
# Each tuple: (forced_category, search_query)
TOPUP_QUERIES = [
    ("Economy & Markets",   "stock market Federal Reserve interest rates GDP"),
    ("Economy & Markets",   "recession unemployment inflation consumer prices"),
    ("AI & Tech Ethics",    "OpenAI ChatGPT artificial intelligence regulation"),
    ("AI & Tech Ethics",    "Google DeepMind AI ethics technology policy"),
    ("Environment",         "climate change wildfire flood hurricane disaster"),
    ("Environment",         "carbon emissions renewable energy COP climate"),
    ("Health",              "WHO pandemic outbreak hospital disease treatment"),
    ("Health",              "FDA drug approval vaccine clinical trial"),
    ("War Crimes",          "Gaza Ukraine ICC war crimes civilian casualties"),
    ("War Crimes",          "airstrike massacre tribunal prosecution genocide"),
    ("Human Rights",        "protest crackdown political prisoner civil rights"),
    ("Human Rights",        "UN human rights report minority persecution"),
    ("Geopolitics",         "US China Russia diplomacy military summit"),
    ("Geopolitics",         "Iran nuclear Middle East ceasefire negotiations"),
    ("Crime, Law & Justice","murder trial Supreme Court verdict sentencing"),
    ("Corruption",          "politician bribery corruption scandal arrested"),
]

COUNTRY_PREFIX = {
    "US":    "",
    "UK":    "UK ",
    "IN":    "India ",
    "FR":    "France ",
    "DE":    "Germany ",
    "JP":    "Japan ",
    "WORLD": "global ",
}

# Per country: minimum stories we want for each thin category
MIN_PER_CATEGORY = 2


async def _proc_cluster(cluster):
    async with SEMAPHORE:
        analysis = await analyze_cluster(cluster)
        if not analysis: return None
        pol = calculate_polarization(cluster, analysis)
        return {
            "id": int(hashlib.md5(cluster["primary_title"].encode()).hexdigest()[:8], 16) % 100000,
            "headline":            analysis.get("headline", cluster["primary_title"]),
            "neutral_summary":     analysis.get("neutral_summary", ""),
            "key_facts":           analysis.get("key_facts", {}),
            "perspectives":        analysis.get("perspectives", []),
            "source_analysis":     analysis.get("source_analysis", []),
            "polarization":        pol,
            "credibility_weighted_pol": pol["score"],
            "source_credibility":  [],
            "headlines_by_source": [{"source": a["source"], "headline": a["title"],
                                      "url": a["url"], "credibility": 0.7}
                                     for a in cluster["articles"]],
            "sources":         cluster["sources"],
            "source_count":    cluster["source_count"],
            "topic_tags":      analysis.get("topic_tags", []),
            "category":        analysis.get("category", "General News"),
            "is_adverse":      analysis.get("is_adverse", False),
            "adverse_reason":  analysis.get("adverse_reason", ""),
            "severity":        analysis.get("severity", "low"),
            "sentiment_score": analysis.get("sentiment_score", 0.0),
            "article_count":   len(cluster["articles"]),
            "image_url":       next((a["image_url"] for a in cluster["articles"]
                                     if a.get("image_url")), None),
            "original_articles": [{"title": a["title"], "source": a["source"],
                                    "url": a["url"]} for a in cluster["articles"]],
        }


def get_category_counts(country: str) -> Counter:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT data_json FROM stories WHERE country=?", (country,)).fetchall()
    conn.close()
    return Counter(json.loads(r["data_json"]).get("category", "General News") for r in rows)


async def topup_country(country: str):
    prefix = COUNTRY_PREFIX.get(country, "")
    cats   = get_category_counts(country)
    total  = sum(cats.values())

    print(f"\n{'='*60}")
    print(f"  [{country}] — {total} stories currently")

    # Figure out which categories need topping up
    needed = {}
    for cat, query in TOPUP_QUERIES:
        current = cats.get(cat, 0)
        if current < MIN_PER_CATEGORY:
            if cat not in needed:
                needed[cat] = []
            needed[cat].append(query)

    if not needed:
        print(f"  All categories already at {MIN_PER_CATEGORY}+ — skipping.")
        return

    print(f"  Need to top up: {', '.join(needed.keys())}")

    loop        = asyncio.get_event_loop()
    new_stories = []
    conn_tmp = sqlite3.connect(DB_PATH)
    conn_tmp.row_factory = sqlite3.Row
    seen_hashes = set()
    for row in conn_tmp.execute("SELECT data_json FROM stories WHERE country=?", (country,)).fetchall():
        try:
            seen_hashes.add(_headline_hash(json.loads(row["data_json"])["headline"]))
        except Exception:
            pass
    conn_tmp.close()

    for cat, queries in needed.items():
        current = cats.get(cat, 0) + sum(1 for s in new_stories if s["category"] == cat)
        if current >= MIN_PER_CATEGORY:
            continue

        for query in queries:
            if current >= MIN_PER_CATEGORY:
                break
            full_q = (prefix + query).strip()
            print(f"\n  [{cat}] '{full_q[:55]}'")
            try:
                articles = await loop.run_in_executor(None, fetch_google_search, full_q, country)
                if not articles:
                    print(f"    No articles.")
                    continue

                clusters = await cluster_articles(articles)
                print(f"    {len(articles)} articles → {len(clusters)} clusters")

                for c in clusters[:4]:
                    h = _headline_hash(c["primary_title"])
                    if h in seen_hashes:
                        continue
                    seen_hashes.add(h)

                    results = await asyncio.gather(_proc_cluster(c), return_exceptions=True)
                    stories = [r for r in results if r and not isinstance(r, Exception)]

                    for s in stories:
                        s["category"] = cat  # force correct category
                        print(f"    ✓ [{cat[:22]:<22}] {s['headline'][:45]}")
                        new_stories.append(s)
                        current += 1

                    if current >= MIN_PER_CATEGORY:
                        break

            except Exception as e:
                print(f"    Error: {e}")
                continue

    if new_stories:
        saved = save_stories(new_stories, country)
        final_cats = get_category_counts(country)
        print(f"\n  [{country}] Added {saved} stories. New distribution:")
        for c, n in sorted(final_cats.items(), key=lambda x: -x[1]):
            bar = "█" * n
            print(f"    {c:<35} {n:>3}  {bar}")
    else:
        print(f"  [{country}] Nothing new added.")


async def main():
    init_db()
    countries = ["US", "UK", "IN", "FR", "DE", "JP", "WORLD"]

    print(f"\nKhabarLens DB Top-Up")
    print(f"Target: {MIN_PER_CATEGORY}+ stories per category per country")
    print(f"Thin categories: Economy, AI & Tech, Environment, Health,")
    print(f"                 War Crimes, Human Rights, Geopolitics, Corruption")
    print(f"Est. time: 15-20 mins\n")

    for country in countries:
        await topup_country(country)

    # Final global summary
    print(f"\n{'='*60}")
    print(f"  TOP-UP COMPLETE — Global category distribution")
    print(f"{'='*60}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    all_rows = conn.execute("SELECT data_json FROM stories").fetchall()
    conn.close()
    global_cats = Counter(json.loads(r["data_json"]).get("category","General News") for r in all_rows)
    print(f"\n{'Category':<35} {'Total':>6}  Bar")
    print("-" * 60)
    for cat, n in sorted(global_cats.items(), key=lambda x: -x[1]):
        bar = "█" * min(n, 50)
        print(f"{cat:<35} {n:>6}  {bar}")
    total = sum(global_cats.values())
    print(f"\n{'TOTAL':<35} {total:>6}")
    print(f"\n✅ Done. Run 'python main.py' — site loads instantly.\n")


if __name__ == "__main__":
    asyncio.run(main())
