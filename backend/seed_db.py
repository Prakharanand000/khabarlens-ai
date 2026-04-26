"""
seed_db.py — Pre-populate khabarlens_cache.db with 30 analyzed stories per country.
Guarantees ~1-2 stories per category across all 21 KhabarLens categories.
Covers: US, UK, IN, FR, DE, JP, WORLD (210 stories total)
Usage:  cd backend && python seed_db.py
"""

import asyncio, sys, os, hashlib
sys.path.insert(0, os.path.dirname(__file__))

from news_ingestion import fetch_google_search
from clustering import cluster_articles
from ai_analysis import analyze_cluster
from polarization import calculate_polarization
from cache import init_db, save_stories, load_stories, count_stories, _headline_hash, MAX_STORIES
from collections import Counter

TARGET    = 30
SEMAPHORE = asyncio.Semaphore(3)

# ── 21 categories × 1 query each = 21 queries per country ────────────────────
# Ordered so non-adverse categories run FIRST (they get cut off last if cap hit)
# Each query is written to make the category assignment unambiguous
CATEGORY_QUERIES = [
    # Non-adverse first — these tend to be under-represented
    ("Economy & Markets",        "stock market Federal Reserve interest rates GDP inflation"),
    ("Geopolitics",              "US China Russia diplomacy military tensions summit"),
    ("AI & Tech Ethics",         "OpenAI Google artificial intelligence technology news"),
    ("Environment",              "climate change wildfire flood extreme weather disaster"),
    ("Health",                   "hospital pandemic flu virus outbreak CDC WHO"),
    ("General News",             "politics election government Congress White House"),
    ("Crime, Law & Justice",     "murder trial court verdict sentencing justice"),
    ("Human Rights",             "protest crackdown civil rights UN human rights report"),
    ("War Crimes",               "Gaza Ukraine airstrike civilian casualties ICC"),
    ("Drug Trafficking",         "fentanyl cartel drug smuggling border seizure DEA"),
    ("Corruption",               "politician bribery corruption scandal fired removed"),
    # Adverse financial — run after non-adverse to prevent domination
    ("Financial Crime",          "bank fraud embezzlement billion dollar theft charged"),
    ("Money Laundering",         "money laundering shell company offshore prosecution"),
    ("Fraud & Scams",            "online scam phishing fraud victim identity theft"),
    ("Insider Trading",          "insider trading hedge fund executive stock tip SEC"),
    ("Terrorism",                "terror plot bomb attack arrest FBI foiled"),
    ("Sanctions",                "OFAC sanctions Russia Iran North Korea trade ban"),
    ("Regulatory & Compliance",  "FDA FCA GDPR regulatory fine compliance breach"),
    ("FINRA & SEC",              "SEC broker dealer FINRA penalty enforcement action"),
    ("Cybercrime",               "ransomware cyberattack data breach hacker arrested"),
    ("General News",             "sports championship NBA NFL result winner"),  # bonus
]

# Country-localised prefix to bias results toward that country
COUNTRY_PREFIX = {
    "US":    "",
    "UK":    "UK Britain ",
    "IN":    "India ",
    "FR":    "France ",
    "DE":    "Germany ",
    "JP":    "Japan ",
    "WORLD": "global international ",
}


async def _proc_cluster(cluster: dict) -> dict | None:
    async with SEMAPHORE:
        analysis = await analyze_cluster(cluster)
        if not analysis:
            return None
        pol = calculate_polarization(cluster, analysis)
        sa  = analysis.get("source_analysis", [])
        return {
            "id": int(hashlib.md5(cluster["primary_title"].encode()).hexdigest()[:8], 16) % 100000,
            "headline":            analysis.get("headline", cluster["primary_title"]),
            "neutral_summary":     analysis.get("neutral_summary", ""),
            "key_facts":           analysis.get("key_facts", {}),
            "perspectives":        analysis.get("perspectives", []),
            "source_analysis":     sa,
            "polarization":        pol,
            "credibility_weighted_pol": pol["score"],
            "source_credibility":  [],
            "headlines_by_source": [
                {"source": a["source"], "headline": a["title"],
                 "url": a["url"], "credibility": 0.7}
                for a in cluster["articles"]
            ],
            "sources":         cluster["sources"],
            "source_count":    cluster["source_count"],
            "topic_tags":      analysis.get("topic_tags", []),
            "category":        analysis.get("category", "General News"),
            "is_adverse":      analysis.get("is_adverse", False),
            "adverse_reason":  analysis.get("adverse_reason", ""),
            "severity":        analysis.get("severity", "low"),
            "sentiment_score": analysis.get("sentiment_score", 0.0),
            "article_count":   len(cluster["articles"]),
            "image_url":       next(
                (a["image_url"] for a in cluster["articles"] if a.get("image_url")), None
            ),
            "original_articles": [
                {"title": a["title"], "source": a["source"], "url": a["url"]}
                for a in cluster["articles"]
            ],
        }


async def seed_country(country: str):
    existing = count_stories(country)
    if existing >= TARGET:
        print(f"\n[{country}] Already has {existing} stories — skipping.")
        print(f"       Delete khabarlens_cache.db to force re-seed.")
        return

    prefix = COUNTRY_PREFIX.get(country, "")
    print(f"\n{'='*65}")
    print(f"  Seeding {country} — target {TARGET} stories ({existing} existing)")
    print(f"{'='*65}")

    all_stories = []
    seen_hashes = set()
    loop        = asyncio.get_event_loop()

    for i, (cat, base_query) in enumerate(CATEGORY_QUERIES):
        current = count_stories(country) + len(all_stories)
        if current >= TARGET:
            print(f"\n  [{country}] Reached {TARGET} — done.")
            break

        query = (prefix + base_query).strip()
        print(f"\n  ({i+1}/{len(CATEGORY_QUERIES)}) [{cat:<28}] '{query[:55]}'")

        try:
            articles = await loop.run_in_executor(None, fetch_google_search, query, country)
            if not articles:
                print(f"           No articles — skipping.")
                continue

            clusters = await cluster_articles(articles)
            print(f"           {len(articles)} articles → {len(clusters)} clusters")

            # 1 story per query — keeps distribution even (21 queries × 1 = 21 base, top up with 2nd pass)
            batch = []
            for c in clusters[:5]:
                h = _headline_hash(c["primary_title"])
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    batch.append(c)
                    break  # strictly 1 per query on first pass

            if not batch:
                print(f"           All seen — skipping.")
                continue

            results = await asyncio.gather(
                *[_proc_cluster(c) for c in batch],
                return_exceptions=True
            )
            stories = [r for r in results if r and not isinstance(r, Exception)]

            # Force correct category — override AI misclassification
            for s in stories:
                if s["category"] != cat:
                    print(f"           ↺ {s['category']} → {cat}")
                    s["category"] = cat
                print(f"           ✓ [{s['category'][:20]:<20}] {s['headline'][:48]}")

            all_stories.extend(stories)

        except Exception as e:
            print(f"           Error: {e}")
            continue

    # Second pass — fill remaining slots (target - current) with 2nd story per category
    remaining = TARGET - count_stories(country) - len(all_stories)
    if remaining > 0:
        print(f"\n  [{country}] Second pass — filling {remaining} remaining slots...")
        for i, (cat, base_query) in enumerate(CATEGORY_QUERIES):
            if remaining <= 0:
                break
            query = (prefix + base_query).strip()
            try:
                articles = await loop.run_in_executor(None, fetch_google_search, query, country)
                if not articles:
                    continue
                clusters = await cluster_articles(articles)
                # Now take 2nd cluster (skip 1st which was already seen)
                for c in clusters[1:4]:
                    h = _headline_hash(c["primary_title"])
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        results = await asyncio.gather(_proc_cluster(c), return_exceptions=True)
                        stories = [r for r in results if r and not isinstance(r, Exception)]
                        for s in stories:
                            s["category"] = cat
                            print(f"           ✓ [{cat[:20]:<20}] {s['headline'][:48]}")
                        all_stories.extend(stories)
                        remaining -= len(stories)
                        break
            except Exception:
                continue

    if all_stories:
        saved = save_stories(all_stories, country)
        final = count_stories(country)
        cats  = Counter(s["category"] for s in all_stories)

        print(f"\n  [{country}] ✅ {saved} saved — DB now has {final} stories")
        print(f"\n  {'Category':<35} {'Count':>5}")
        print(f"  {'-'*42}")
        for c, n in sorted(cats.items(), key=lambda x: x[0]):
            bar = "█" * n
            print(f"  {c:<35} {n:>5}  {bar}")
    else:
        print(f"\n  [{country}] ❌ No stories saved — check GROQ_API_KEY")


async def main():
    init_db()

    countries     = ["US", "UK", "IN", "FR", "DE", "JP", "WORLD"]
    existing_total = sum(count_stories(c) for c in countries)

    print(f"\nKhabarLens DB Seeder — Balanced across 21 categories")
    print(f"Countries  : {', '.join(countries)}")
    print(f"Target     : {TARGET} stories × {len(countries)} = {TARGET * len(countries)} total")
    print(f"Currently  : {existing_total} stories in DB")
    print(f"Strategy   : non-adverse categories first, 1 story/category/pass")
    print(f"Est. time  : 30–45 mins\n")

    for country in countries:
        await seed_country(country)

    # Final summary
    print(f"\n{'='*65}")
    print(f"  SEED COMPLETE")
    print(f"{'='*65}")
    print(f"\n{'Country':<10} {'Stories':>8}  Category spread (top 5)")
    print("-" * 65)
    grand_total = 0
    for country in countries:
        stories     = load_stories(country)
        grand_total += len(stories)
        cats        = Counter(s["category"] for s in stories)
        top         = ", ".join(f"{c}({n})" for c, n in cats.most_common(5))
        print(f"{country:<10} {len(stories):>8}  {top}")
    print("-" * 65)
    print(f"{'TOTAL':<10} {grand_total:>8}")
    print(f"\n✅ Run 'python main.py' — site loads instantly for all {len(countries)} countries.")
    print(f"   Run 'python inspect_db.py' to verify.\n")


if __name__ == "__main__":
    asyncio.run(main())
