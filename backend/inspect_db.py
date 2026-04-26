"""
inspect_db.py — shows what's currently in khabarlens_cache.db
Usage: cd backend && python inspect_db.py
"""
import sqlite3, json, os
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "khabarlens_cache.db")

if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
    print("❌ DB is empty or does not exist. Run: python seed_db.py")
    exit()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Total
total = conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
print(f"\n{'='*65}")
print(f"  khabarlens_cache.db — {total} total stories")
print(f"{'='*65}")

# Per country
print(f"\n{'Country':<10} {'Total':>6}  {'Non-expired':>12}  {'Oldest':>22}")
print("-" * 65)
countries = [r[0] for r in conn.execute("SELECT DISTINCT country FROM stories ORDER BY country").fetchall()]
cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

for c in countries:
    total_c   = conn.execute("SELECT COUNT(*) FROM stories WHERE country=?", (c,)).fetchone()[0]
    active_c  = conn.execute("SELECT COUNT(*) FROM stories WHERE country=? AND created_at>?", (c, cutoff)).fetchone()[0]
    oldest    = conn.execute("SELECT MIN(created_at) FROM stories WHERE country=?", (c,)).fetchone()[0]
    oldest_str = oldest[:16] if oldest else "—"
    print(f"{c:<10} {total_c:>6}  {active_c:>12}  {oldest_str:>22}")

# Categories breakdown
print(f"\n{'='*65}")
print(f"  Categories across all countries")
print(f"{'='*65}")
rows = conn.execute("""
    SELECT json_extract(data_json, '$.category') as cat, COUNT(*) as n
    FROM stories GROUP BY cat ORDER BY n DESC
""").fetchall()
for r in rows:
    bar = "█" * min(r["n"], 40)
    print(f"  {r['cat']:<35} {r['n']:>4}  {bar}")

# Per-country headlines
print(f"\n{'='*65}")
print(f"  Headlines per country (first 8 each)")
print(f"{'='*65}")
for c in countries:
    print(f"\n  [{c}]")
    rows = conn.execute("""
        SELECT headline, json_extract(data_json, '$.category') as cat,
               json_extract(data_json, '$.polarization.score') as pol
        FROM stories WHERE country=? AND created_at>?
        ORDER BY pol DESC LIMIT 8
    """, (c, cutoff)).fetchall()
    if not rows:
        print("    (all expired)")
    for r in rows:
        print(f"    [{r['cat'][:18]:<18}] Pol:{r['pol']:>3}  {r['headline'][:50]}")

conn.close()
print(f"\n{'='*65}\n")
