"""
cache.py — SQLite-backed story cache for KhabarLens AI.
Hard rules:
  - MAX 30 stories per country at any time
  - No duplicates: keyed by headline_hash (PRIMARY KEY)
  - Regular stories expire after TTL_HOURS (6h)
  - Background refresh adds up to 5 new, evicting oldest if over cap
"""

import sqlite3, json, hashlib, os, re
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "khabarlens_cache.db")
TTL_HOURS   = 24   # stories last 24h (seed fills DB, background refresh tops up)
MAX_STORIES = 30   # hard cap per country


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                headline_hash TEXT    NOT NULL,
                country       TEXT    NOT NULL,
                headline      TEXT    NOT NULL,
                data_json     TEXT    NOT NULL,
                created_at    TEXT    NOT NULL,
                PRIMARY KEY (headline_hash, country)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS refresh_status (
                country    TEXT PRIMARY KEY,
                status     TEXT    NOT NULL,
                new_count  INTEGER DEFAULT 0,
                updated_at TEXT    NOT NULL
            )
        """)
        conn.commit()
    print(f"[cache] DB ready — {DB_PATH}")


# ── Hashing ────────────────────────────────────────────────────────────────────

def _headline_hash(headline: str) -> str:
    """Normalise headline before hashing to catch near-duplicates."""
    # strip punctuation, lowercase, collapse whitespace
    clean = re.sub(r'[^\w\s]', '', headline.lower())
    clean = re.sub(r'\s+', ' ', clean).strip()
    return hashlib.md5(clean.encode()).hexdigest()[:12]


def _similar_headline_exists(conn, headline: str, country: str,
                              cutoff: str, threshold: int = 6) -> bool:
    """
    Word-overlap check against existing headlines.
    Returns True if any cached headline shares >= threshold words with the new one.
    Catches cases like 'Japan and Apple Announcements' vs
    'Japan and Apple Announcements Update' that have different hashes.
    """
    words_new = set(re.sub(r'[^\w\s]', '', headline.lower()).split())
    rows = conn.execute(
        "SELECT headline FROM stories WHERE country = ? AND created_at > ?",
        (country, cutoff)
    ).fetchall()
    for row in rows:
        words_existing = set(re.sub(r'[^\w\s]', '', row["headline"].lower()).split())
        overlap = len(words_new & words_existing)
        if overlap >= threshold:
            return True
    return False


# ── CRUD ───────────────────────────────────────────────────────────────────────

def save_stories(stories: list, country: str):
    """
    Insert new stories. Skips:
      - exact hash duplicates (PRIMARY KEY)
      - near-duplicate headlines (word overlap >= 6 words)
    After insert, enforces MAX_STORIES cap by evicting oldest stories.
    """
    now    = datetime.utcnow().isoformat()
    cutoff = (datetime.utcnow() - timedelta(hours=TTL_HOURS)).isoformat()
    saved  = 0

    with _connect() as conn:
        for s in stories:
            h = _headline_hash(s["headline"])

            # Skip near-duplicates via word overlap
            if _similar_headline_exists(conn, s["headline"], country, cutoff):
                print(f"[cache] Skipping near-duplicate: {s['headline'][:60]}")
                continue

            try:
                conn.execute("""
                    INSERT INTO stories (headline_hash, country, headline, data_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(headline_hash, country) DO UPDATE SET
                        data_json  = excluded.data_json,
                        created_at = excluded.created_at
                """, (h, country, s["headline"], json.dumps(s), now))
                saved += 1
            except Exception as e:
                print(f"[cache] Insert error: {e}")

        # Enforce MAX_STORIES cap — delete oldest beyond cap
        count = conn.execute(
            "SELECT COUNT(*) FROM stories WHERE country = ?", (country,)
        ).fetchone()[0]

        if count > MAX_STORIES:
            excess = count - MAX_STORIES
            conn.execute("""
                DELETE FROM stories WHERE (headline_hash, country) IN (
                    SELECT headline_hash, country FROM stories
                    WHERE country = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                )
            """, (country, excess))
            print(f"[cache] Evicted {excess} oldest stories to maintain {MAX_STORIES} cap")

        conn.commit()

    print(f"[cache] Saved {saved}/{len(stories)} stories for {country}")
    return saved


def load_stories(country: str) -> list:
    """
    Return all non-expired stories sorted by polarization score DESC.
    Deduped at DB level — no Python-side dedup needed.
    """
    cutoff = (datetime.utcnow() - timedelta(hours=TTL_HOURS)).isoformat()
    with _connect() as conn:
        rows = conn.execute("""
            SELECT data_json FROM stories
            WHERE country = ? AND created_at > ?
            ORDER BY json_extract(data_json, '$.polarization.score') DESC
        """, (country, cutoff)).fetchall()

    stories = [json.loads(r["data_json"]) for r in rows]
    print(f"[cache] Loaded {len(stories)} stories for {country}")
    return stories


def count_stories(country: str) -> int:
    cutoff = (datetime.utcnow() - timedelta(hours=TTL_HOURS)).isoformat()
    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM stories WHERE country = ? AND created_at > ?",
            (country, cutoff)
        ).fetchone()[0]


def get_cached_headlines(country: str) -> set:
    """Return hashes of all non-expired cached headlines."""
    cutoff = (datetime.utcnow() - timedelta(hours=TTL_HOURS)).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT headline_hash FROM stories WHERE country = ? AND created_at > ?",
            (country, cutoff)
        ).fetchall()
    return {r["headline_hash"] for r in rows}


def delete_expired(country: str = None):
    cutoff = (datetime.utcnow() - timedelta(hours=TTL_HOURS)).isoformat()
    with _connect() as conn:
        if country:
            conn.execute(
                "DELETE FROM stories WHERE country = ? AND created_at <= ?",
                (country, cutoff)
            )
        else:
            conn.execute("DELETE FROM stories WHERE created_at <= ?", (cutoff,))
        deleted = conn.total_changes
        conn.commit()
    if deleted:
        print(f"[cache] Pruned {deleted} expired stories")


# ── Refresh status ─────────────────────────────────────────────────────────────

def set_refresh_status(country: str, status: str, new_count: int = 0):
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO refresh_status (country, status, new_count, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(country) DO UPDATE SET
                status     = excluded.status,
                new_count  = excluded.new_count,
                updated_at = excluded.updated_at
        """, (country, status, new_count, now))
        conn.commit()


def get_refresh_status(country: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT status, new_count, updated_at FROM refresh_status WHERE country = ?",
            (country,)
        ).fetchone()
    return dict(row) if row else {"status": "idle", "new_count": 0, "updated_at": None}
