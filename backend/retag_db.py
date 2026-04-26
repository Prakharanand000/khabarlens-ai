"""
retag_db.py — Re-classify all stories in khabarlens_cache.db using their
headline + summary, without calling Groq. Uses keyword rules to assign
the correct KhabarLens category to each story.

Usage: cd backend && python retag_db.py
"""

import sqlite3, json, os, re
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(__file__), "khabarlens_cache.db")

# ── Keyword rules ─────────────────────────────────────────────────────────────
# Ordered from most specific → most general. First match wins.
# Each rule: (category, [keywords that must appear in headline+summary])
RULES = [
    # Cybercrime
    ("Cybercrime", [
        "ransomware","cyberattack","cyber attack","data breach","hacker","hacked",
        "dark web","malware","phishing","ddos","cybercrime","cybersecurity breach",
        "data leak","stolen data","network intrusion",
    ]),
    # Drug Trafficking
    ("Drug Trafficking", [
        "fentanyl","drug trafficking","cocaine","heroin","cartel","dea bust",
        "drug smuggling","narcotics seizure","meth","opioid trafficking",
        "drug bust","border drug","smuggled drugs",
    ]),
    # Money Laundering
    ("Money Laundering", [
        "money laundering","laundered","shell company","offshore account",
        "illicit funds","layering funds","smurfing","hawala","crypto laundering",
        "laundering scheme","laundering charges","financial flows",
    ]),
    # Insider Trading
    ("Insider Trading", [
        "insider trading","insider tip","illegal trading","front-running",
        "trading on non-public","material non-public","insider information",
        "tipped off stock","securities fraud trade",
    ]),
    # Fraud & Scams
    ("Fraud & Scams", [
        "ponzi","scam","phishing","identity theft","wire fraud","mail fraud",
        "fake invoice","romance scam","investment fraud","pyramid scheme",
        "fraudulent scheme","defraud","stolen identity","online fraud",
    ]),
    # FINRA & SEC
    ("FINRA & SEC", [
        "finra","sec charges","sec penalty","sec enforcement","sec investigation",
        "broker dealer","securities violation","sec fine","sec lawsuit",
        "securities exchange commission","sec settlement",
    ]),
    # Financial Crime (broad — after more specific financial categories)
    ("Financial Crime", [
        "embezzlement","bank fraud","financial crime","theft of funds",
        "misappropriation","accounting fraud","tax evasion","asset misappropriation",
        "financial misconduct","fictitious invoices",
    ]),
    # Sanctions
    ("Sanctions", [
        "sanctions","ofac","trade ban","export control","asset freeze",
        "blacklisted","sanctioned entity","travel ban","embargo",
        "sanctioned country","sanctioned individual",
    ]),
    # Regulatory & Compliance
    ("Regulatory & Compliance", [
        "fda","gdpr","regulatory fine","compliance breach","regulatory penalty",
        "fca fine","data protection","compliance failure","regulatory action",
        "compliance violation","anti-money laundering rule","aml compliance",
        "regulatory enforcement","regulatory settlement","osha","epa fine",
    ]),
    # Terrorism
    ("Terrorism", [
        "terror","terrorist","isis","al qaeda","bomb plot","suicide bomber",
        "extremist","jihad","radicalization","terror cell","attack plot",
        "foiled attack","domestic terrorism","islamist","far-right extremist",
    ]),
    # War Crimes
    ("War Crimes", [
        "war crime","icc","genocide","ethnic cleansing","civilian massacre",
        "crimes against humanity","tribunal","airstrike civilian",
        "chemical weapon","torture prisoner","sexual violence war",
    ]),
    # Human Rights
    ("Human Rights", [
        "human rights","crackdown","protest suppressed","freedom of press",
        "political prisoner","unlawful detention","torture","forced labour",
        "child soldier","un rights","amnesty international","hrw report",
        "disappearance activist","censorship","persecution minority",
    ]),
    # Corruption
    ("Corruption", [
        "bribery","corruption","kickback","graft","bribe","embezzle",
        "corrupt official","nepotism","public official arrested",
        "government corruption","abuse of power","misuse of funds",
        "misconduct official","corrupt politician",
    ]),
    # Crime, Law & Justice
    ("Crime, Law & Justice", [
        "murder","homicide","trial","verdict","sentenced","convicted",
        "acquitted","court ruling","prison sentence","criminal charges",
        "law enforcement","arrested","indicted","grand jury","plea deal",
        "supreme court ruling","appeals court",
    ]),
    # Geopolitics
    ("Geopolitics", [
        "diplomacy","ceasefire","nato","un security council","bilateral",
        "foreign policy","military alliance","geopolitical","treaty",
        "nuclear deal","peace talks","war","invasion","occupation","troops",
        "missile","nuclear","iran","ukraine","russia","china taiwan",
        "south china sea","middle east","israel","hamas","hezbollah",
        "north korea","military tension","coup","regime",
    ]),
    # Economy & Markets
    ("Economy & Markets", [
        "federal reserve","interest rate","inflation","gdp","recession",
        "stock market","wall street","dow jones","nasdaq","s&p","bond yield",
        "unemployment","economic growth","trade deficit","tariff","oil price",
        "imf","world bank","central bank","rate hike","rate cut","cpi","ppi",
        "ipo","market crash","hedge fund","private equity","earnings report",
    ]),
    # AI & Tech Ethics
    ("AI & Tech Ethics", [
        "artificial intelligence","machine learning","deep learning","chatgpt",
        "openai","google ai","ai regulation","ai ethics","ai bias","deepfake",
        "autonomous","llm","generative ai","neural network","ai safety",
        "facial recognition","algorithmic","tech regulation","data privacy",
        "big tech","apple","meta","microsoft","amazon","nvidia","semiconductor",
    ]),
    # Environment
    ("Environment", [
        "climate change","global warming","carbon emission","renewable energy",
        "solar","wind energy","wildfire","flood","hurricane","drought",
        "deforestation","biodiversity","plastic pollution","coral reef",
        "paris agreement","cop","greenhouse gas","fossil fuel","net zero",
        "extreme weather","sea level","glacier","arctic","amazon rainforest",
    ]),
    # Health
    ("Health", [
        "pandemic","epidemic","outbreak","virus","covid","flu","mpox",
        "who","cdc","vaccine","hospital","healthcare","disease","cancer",
        "mental health","obesity","diabetes","drug approval","clinical trial",
        "public health","mortality","infection","pathogen","quarantine",
    ]),
    # General News (catch-all)
    ("General News", [
        "election","government","parliament","congress","senate","prime minister",
        "president","policy","legislation","budget","sports","championship",
        "nfl","nba","football","cricket","olympic","world cup","film","music",
        "celebrity","entertainment","education","science","space","nasa",
    ]),
]


def classify(headline: str, summary: str) -> str:
    text = (headline + " " + summary).lower()
    for category, keywords in RULES:
        for kw in keywords:
            if kw in text:
                return category
    return "General News"


def retag():
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        print("❌ DB not found or empty.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("SELECT headline_hash, country, headline, data_json FROM stories").fetchall()
    print(f"\nRetag DB — {len(rows)} stories\n")

    updates   = []
    before    = Counter()
    after     = Counter()
    changed   = 0

    for row in rows:
        data     = json.loads(row["data_json"])
        old_cat  = data.get("category", "General News")
        summary  = data.get("neutral_summary", "")
        new_cat  = classify(row["headline"], summary)

        before[old_cat] += 1
        after[new_cat]  += 1

        if old_cat != new_cat:
            changed += 1
            data["category"] = new_cat
            updates.append((json.dumps(data), new_cat, row["headline_hash"], row["country"]))

    # Apply updates
    with conn:
        for data_json, cat, h, country in updates:
            conn.execute(
                "UPDATE stories SET data_json=? WHERE headline_hash=? AND country=?",
                (data_json, h, country)
            )
    conn.commit()

    print(f"Updated {changed}/{len(rows)} stories\n")

    # Before/after comparison
    all_cats = sorted(set(list(before.keys()) + list(after.keys())))
    print(f"{'Category':<35} {'Before':>7}  {'After':>7}  {'Change':>7}")
    print("-" * 62)
    for cat in all_cats:
        b = before.get(cat, 0)
        a = after.get(cat, 0)
        diff = a - b
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "—"
        bar = "█" * a
        print(f"{cat:<35} {b:>7}  {a:>7}  {diff_str:>7}  {bar}")

    # Per-country breakdown
    print(f"\n{'='*65}")
    print(f"  Per-country category distribution (after retag)")
    print(f"{'='*65}")
    countries = [r[0] for r in conn.execute("SELECT DISTINCT country FROM stories ORDER BY country").fetchall()]
    for country in countries:
        rows_c = conn.execute(
            "SELECT data_json FROM stories WHERE country=?", (country,)
        ).fetchall()
        cats_c = Counter(json.loads(r["data_json"])["category"] for r in rows_c)
        print(f"\n  [{country}] — {sum(cats_c.values())} stories")
        for cat, n in sorted(cats_c.items(), key=lambda x: -x[1]):
            bar = "█" * n
            print(f"    {cat:<35} {n:>3}  {bar}")

    conn.close()
    print(f"\n✅ Done. Run 'python inspect_db.py' to verify.\n")


if __name__ == "__main__":
    retag()
