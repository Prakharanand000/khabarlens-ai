"""
export_seed_json.py — Export your local SQLite DB to seed_data.json.

Run this LOCALLY after seed_db.py is done, then commit seed_data.json to git.
Render will load this file on startup instead of hitting any APIs.

Usage:
    cd backend
    python seed_db.py          # if you haven't seeded yet
    python export_seed_json.py # exports to seed_data.json
    git add seed_data.json
    git commit -m "chore: add pre-baked seed dataset"
    git push
"""

import sqlite3, json, os
from datetime import datetime

DB_PATH     = os.path.join(os.path.dirname(__file__), "khabarlens_cache.db")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "seed_data.json")


def export():
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 1000:
        print("❌  khabarlens_cache.db is empty or missing.")
        print("    Run:  python seed_db.py   first.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Export ALL stories regardless of age — Render sets fresh created_at on load
    rows = conn.execute(
        "SELECT country, data_json FROM stories ORDER BY country"
    ).fetchall()
    conn.close()

    if not rows:
        print("❌  No stories found in DB.")
        return

    # Group by country
    by_country: dict = {}
    for row in rows:
        country = row["country"]
        story   = json.loads(row["data_json"])
        by_country.setdefault(country, []).append(story)

    # Sort each country by polarization score desc (same as load_stories)
    for country in by_country:
        by_country[country].sort(
            key=lambda s: s.get("polarization", {}).get("score", 0),
            reverse=True
        )

    output = {
        "exported_at": datetime.utcnow().isoformat(),
        "countries":   list(by_country.keys()),
        "stories":     by_country,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    total   = sum(len(v) for v in by_country.values())

    print(f"\n✅  Exported {total} stories across {len(by_country)} countries")
    print(f"    File:  seed_data.json  ({size_kb:.0f} KB)")
    print(f"\n  Country breakdown:")
    for country, stories in sorted(by_country.items()):
        print(f"    {country:<8} {len(stories):>4} stories")

    print(f"""
Next steps:
  1. git add backend/seed_data.json
  2. git commit -m "chore: add pre-baked seed dataset"
  3. git push

On Render, startup will now load from seed_data.json instantly
instead of running _auto_seed() — page loads in <1 second.
""")


if __name__ == "__main__":
    export()
