"""
seed_db.py — Pre-populate khabarlens_cache.db with 30 analyzed stories per country.
Covers: US, UK, IN, FR, DE, JP, WORLD (210 stories total)
Usage:  cd backend && python seed_db.py

Run once before starting the server. Safe to re-run — skips countries already at 30.
"""

import asyncio, sys, os, hashlib
sys.path.insert(0, os.path.dirname(__file__))

from news_ingestion import fetch_google_search, get_all_articles
from clustering import cluster_articles
from ai_analysis import analyze_cluster
from polarization import calculate_polarization
from cache import init_db, save_stories, load_stories, count_stories, _headline_hash, MAX_STORIES

TARGET    = 30
SEMAPHORE = asyncio.Semaphore(3)

# Per-country seed queries — localised for relevance
SEED_QUERIES = {
    "US": [
        "breaking US news today",
        "Iran nuclear ceasefire negotiations",
        "SEC fraud enforcement penalty",
        "Federal Reserve inflation economy",
        "artificial intelligence regulation policy",
        "cybercrime ransomware hack",
        "sanctions Russia China",
        "climate change environment",
        "Supreme Court Congress legislation",
        "health outbreak disease CDC",
    ],
    "UK": [
        "UK breaking news today",
        "NHS healthcare crisis Britain",
        "UK economy inflation Bank of England",
        "Brexit trade immigration policy",
        "UK politics Keir Starmer Labour",
        "Scotland independence referendum",
        "London crime security police",
        "UK energy bills cost of living",
        "British tech AI startup",
        "Ukraine UK military aid",
    ],
    "IN": [
        "India breaking news today",
        "India Pakistan border tensions",
        "Indian economy GDP growth",
        "Modi government policy BJP",
        "India China border dispute",
        "Indian stock market Sensex Nifty",
        "India elections politics",
        "India technology startup unicorn",
        "India climate monsoon disaster",
        "India health disease outbreak",
    ],
    "FR": [
        "France breaking news today",
        "French politics Macron government",
        "France economy inflation strikes",
        "France immigration policy protest",
        "French election politics",
        "France Ukraine war EU",
        "France energy nuclear policy",
        "Paris crime security",
        "French tech industry AI",
        "France health crisis hospital",
    ],
    "DE": [
        "Germany breaking news today",
        "German economy recession industry",
        "Germany politics AfD SPD CDU",
        "Germany Ukraine war support",
        "German energy transition climate",
        "Germany immigration asylum policy",
        "German automotive industry crisis",
        "Germany EU relations policy",
        "German tech startup Berlin",
        "Germany health care system",
    ],
    "JP": [
        "Japan breaking news today",
        "Japan economy yen interest rates",
        "Japan China South China Sea",
        "Japan North Korea missile",
        "Japanese politics LDP elections",
        "Japan technology robotics AI",
        "Japan earthquake disaster",
        "Japan US alliance security",
        "Japan trade export economy",
        "Japan health aging population",
    ],
    "WORLD": [
        "global breaking news today",
        "United Nations Security Council resolution",
        "world economy recession trade",
        "global climate change summit COP",
        "international sanctions war conflict",
        "WHO global health pandemic",
        "global AI technology regulation",
        "world financial markets crash",
        "human rights violations international",
        "global cybersecurity threat attack",
    ],
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


async def seed_country(country: str, queries: list):
    existing = count_stories(country)
    if existing >= TARGET:
        print(f"\n[{country}] Already has {existing} stories — skipping.")
        print(f"       Delete khabarlens_cache.db to force re-seed.")
        return

    print(f"\n{'='*60}")
    print(f"  Seeding {country} — target {TARGET} stories ({existing} existing)")
    print(f"{'='*60}")

    all_stories = []
    seen_hashes = set()
    loop        = asyncio.get_event_loop()

    for i, query in enumerate(queries):
        current = count_stories(country) + len(all_stories)
        if current >= TARGET:
            print(f"  [{country}] Reached {TARGET} — done.")
            break

        print(f"\n  ({i+1}/{len(queries)}) '{query}'")
        try:
            articles = await loop.run_in_executor(None, fetch_google_search, query, country)
            if not articles:
                print(f"           No articles — skipping.")
                continue

            clusters = await cluster_articles(articles)
            print(f"           {len(articles)} articles → {len(clusters)} clusters")

            # Take up to 3 new clusters per query
            batch = []
            for c in clusters[:6]:
                h = _headline_hash(c["primary_title"])
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    batch.append(c)
                if len(batch) == 3:
                    break

            if not batch:
                print(f"           All clusters already seen — skipping.")
                continue

            print(f"           Analyzing {len(batch)} clusters...")
            results = await asyncio.gather(
                *[_proc_cluster(c) for c in batch],
                return_exceptions=True
            )
            stories = [r for r in results if r and not isinstance(r, Exception)]
            print(f"           ✓ {len(stories)} stories")
            for s in stories:
                print(f"             → {s['headline'][:65]}")

            all_stories.extend(stories)

        except Exception as e:
            print(f"           Error: {e}")
            continue

    if all_stories:
        saved = save_stories(all_stories, country)
        final = count_stories(country)
        print(f"\n  [{country}] Saved {saved} stories — DB now has {final} for {country}")
    else:
        print(f"\n  [{country}] No stories saved — check GROQ_API_KEY")


async def main():
    init_db()

    countries = list(SEED_QUERIES.keys())
    print(f"\nKhabarLens DB Seeder")
    print(f"Countries: {', '.join(countries)}")
    print(f"Target: {TARGET} stories each = {TARGET * len(countries)} total")
    print(f"\nEstimated time: {TARGET * len(countries) // 3 * 4 // 60}–{TARGET * len(countries) // 3 * 6 // 60} minutes\n")

    for country in countries:
        await seed_country(country, SEED_QUERIES[country])

    # Final summary
    print(f"\n{'='*60}")
    print(f"  SEED COMPLETE")
    print(f"{'='*60}")
    print(f"\n{'Country':<10} {'Stories':>8}  Categories")
    print("-" * 60)
    total = 0
    for country in countries:
        stories = load_stories(country)
        total += len(stories)
        cats = set(s["category"] for s in stories)
        print(f"{country:<10} {len(stories):>8}  {', '.join(sorted(cats)[:4])}{'...' if len(cats)>4 else ''}")
    print("-" * 60)
    print(f"{'TOTAL':<10} {total:>8}")
    print(f"\n✅ Run 'python main.py' — site loads instantly for all countries.\n")


if __name__ == "__main__":
    asyncio.run(main())
