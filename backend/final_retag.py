"""
final_retag.py — One final retag pass on the current 210 stories.
Fixes any remaining miscategorisations using the full keyword ruleset.
Usage: cd backend && python final_retag.py
"""
import sqlite3, json, os, re
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(__file__), "khabarlens_cache.db")

RULES = [
    ("Cybercrime",            ["ransomware","cyberattack","cyber attack","data breach","hacker","hacked","dark web","malware","phishing","ddos","cybercrime","network intrusion","data leak","stolen data"]),
    ("Drug Trafficking",      ["fentanyl","drug trafficking","cocaine","heroin","cartel","drug smuggling","narcotics","drug bust","opioid trafficking","smuggled drugs","dea"]),
    ("Money Laundering",      ["money laundering","laundered","shell company","offshore account","illicit funds","laundering scheme","laundering charges","crypto laundering","hawala"]),
    ("Insider Trading",       ["insider trading","insider tip","front-running","material non-public","insider information","securities fraud trade","illegal trading"]),
    ("Fraud & Scams",         ["ponzi","scam","phishing","identity theft","wire fraud","mail fraud","fake invoice","romance scam","investment fraud","pyramid scheme","fraudulent scheme","defraud","online fraud"]),
    ("FINRA & SEC",           ["finra","sec charges","sec penalty","sec enforcement","sec investigation","broker dealer","sec fine","sec lawsuit","sec settlement","securities exchange commission"]),
    ("Financial Crime",       ["embezzlement","bank fraud","financial crime","theft of funds","misappropriation","accounting fraud","tax evasion","asset misappropriation","financial misconduct"]),
    ("Sanctions",             ["sanctions","ofac","trade ban","export control","asset freeze","blacklisted","sanctioned entity","travel ban","embargo","sanctioned country"]),
    ("Regulatory & Compliance",["gdpr","regulatory fine","compliance breach","regulatory penalty","fca fine","data protection","compliance failure","regulatory action","osha","epa fine","aml compliance"]),
    ("Terrorism",             ["terror","terrorist","isis","al qaeda","bomb plot","suicide bomber","extremist","jihad","radicalization","terror cell","attack plot","foiled attack","domestic terrorism"]),
    ("War Crimes",            ["war crime","icc","genocide","ethnic cleansing","civilian massacre","crimes against humanity","tribunal","airstrike civilian","chemical weapon","torture prisoner"]),
    ("Human Rights",          ["human rights","crackdown","political prisoner","freedom of press","unlawful detention","forced labour","child soldier","amnesty international","hrw report","persecution minority","censorship"]),
    ("Corruption",            ["bribery","corruption","kickback","graft","bribe","embezzle","corrupt official","nepotism","public official arrested","government corruption","abuse of power","corrupt politician"]),
    ("Crime, Law & Justice",  ["murder","homicide","trial","verdict","sentenced","convicted","acquitted","court ruling","prison sentence","criminal charges","arrested","indicted","grand jury","plea deal","supreme court ruling"]),
    ("Geopolitics",           ["diplomacy","ceasefire","nato","un security council","bilateral","foreign policy","military alliance","geopolitical","treaty","nuclear deal","peace talks","invasion","occupation","troops","missile","iran","ukraine","russia","china taiwan","south china sea","middle east","israel","hamas","north korea","military tension","coup"]),
    ("Economy & Markets",     ["federal reserve","interest rate","inflation","gdp","recession","stock market","wall street","dow jones","nasdaq","s&p","bond yield","unemployment","economic growth","trade deficit","tariff","oil price","imf","world bank","central bank","rate hike","rate cut","cpi","ipo","market crash","earnings report"]),
    ("AI & Tech Ethics",      ["artificial intelligence","machine learning","chatgpt","openai","google ai","ai regulation","ai ethics","ai bias","deepfake","llm","generative ai","neural network","ai safety","facial recognition","algorithmic","big tech","nvidia","semiconductor"]),
    ("Environment",           ["climate change","global warming","carbon emission","renewable energy","solar","wind energy","wildfire","flood","hurricane","drought","deforestation","biodiversity","plastic pollution","paris agreement","cop","greenhouse gas","fossil fuel","net zero","extreme weather","sea level"]),
    ("Health",                ["pandemic","epidemic","outbreak","virus","covid","flu","mpox","who","cdc","vaccine","hospital","healthcare","disease","cancer","mental health","obesity","diabetes","drug approval","clinical trial","public health","mortality","infection","pathogen"]),
    ("General News",          []),  # catch-all
]

def classify(headline: str, summary: str) -> str:
    text = (headline + " " + summary).lower()
    for category, keywords in RULES:
        if not keywords:
            return category
        for kw in keywords:
            if kw in text:
                return category
    return "General News"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT headline_hash, country, headline, data_json FROM stories").fetchall()

print(f"\nFinal retag — {len(rows)} stories\n")
before = Counter()
after  = Counter()
updates = []

for row in rows:
    data    = json.loads(row["data_json"])
    old_cat = data.get("category", "General News")
    new_cat = classify(row["headline"], data.get("neutral_summary", ""))
    before[old_cat] += 1
    after[new_cat]  += 1
    if old_cat != new_cat:
        data["category"] = new_cat
        updates.append((json.dumps(data), row["headline_hash"], row["country"]))

with conn:
    for data_json, h, country in updates:
        conn.execute("UPDATE stories SET data_json=? WHERE headline_hash=? AND country=?",
                     (data_json, h, country))
conn.commit()

print(f"Changed {len(updates)}/{len(rows)} stories\n")
all_cats = sorted(set(list(before.keys()) + list(after.keys())))
print(f"{'Category':<35} {'Before':>7}  {'After':>7}")
print("-" * 55)
for cat in all_cats:
    b, a = before.get(cat,0), after.get(cat,0)
    diff = a - b
    ds   = f"+{diff}" if diff>0 else str(diff) if diff<0 else "—"
    print(f"{cat:<35} {b:>7}  {a:>7}  {ds:>5}  {'█'*a}")

conn.close()
print(f"\n✅ Done.\n")
