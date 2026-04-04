# KhabarLens AI — Complete Feature Use Cases
## Hackathon Submission: AI News Agent Track

---

## 🎯 Core Mission
"An AI agent that delivers structured, easy-to-consume, and highly objective news
in a media environment where most outlets are perceived as politically biased."

---

## FEATURE 1: Multi-Source News Aggregation (Google News RSS + 8 Backup Feeds)

**What it does:** Scrapes 30+ articles from Google News RSS across 8 topic categories
(World, Nation, Business, Technology, Science, Health, Entertainment, Sports) plus
8 backup RSS feeds (Reuters, BBC, CNN, NPR, Al Jazeera, The Guardian, ABC, CBS).

**Use Case — Compliance Officer at a Bank:**
Sarah is a compliance officer at JPMorgan. Every morning she needs to scan news for
sanctions violations, money laundering cases, and regulatory actions across multiple
sources. Instead of opening 10 different news sites, she opens KhabarLens and sees
30+ articles already aggregated, categorized, and scored — saving her 45 minutes daily.

**Use Case — Journalism Student:**
Raj is studying journalism at Columbia. His professor asks him to compare how different
outlets cover the same story. KhabarLens shows him the same Iran conflict story from
AP, BBC, CNN, and Reuters side by side — with loaded phrases highlighted.

**Hackathon Requirement Met:** "reliable news from top sources"

---

## FEATURE 2: AI-Powered Story Clustering (Embeddings + Cosine Similarity)

**What it does:** Groups articles about the same story using title-overlap matching
(Phase 1) and OpenAI text-embedding-3-small with cosine similarity threshold 0.65
(Phase 2). Multiple articles about "Trump Iran ultimatum" from different sources
get merged into one story cluster.

**Use Case — News Consumer Avoiding Echo Chambers:**
Maria reads mostly CNN. She doesn't know that Fox News frames the same Iran story
completely differently. KhabarLens clusters both versions together, showing her that
the same event has 4 different source perspectives she never would have seen.

**Use Case — Political Science Researcher:**
Dr. Chen is studying media fragmentation. He needs data on how many sources cover
the same event and how differently they frame it. KhabarLens's clustering engine
gives him structured data: "This story covered by 5 sources with polarization 45/100."

**Hackathon Requirement Met:** "multiple viewpoints"

---

## FEATURE 3: Neutral 60-Word Summaries (GPT-4o-mini, Reuters-Style)

**What it does:** For each story cluster, GPT-4o-mini generates a strictly neutral,
60-word summary written in wire-service style (like Reuters/AP). No loaded language,
no emotional adjectives, no opinion.

**Use Case — Busy Executive:**
David is a CEO who has 10 minutes for news each morning. He doesn't want opinion —
he wants facts. KhabarLens gives him 60-word Reuters-style summaries for each story.
He reads 10 stories in 5 minutes instead of spending 30 minutes on full articles.

**Use Case — ESL Learner:**
Yuki in Japan is learning English. Long, complex news articles are overwhelming.
The 60-word structured summaries with key facts (who/what/when/where/why) help her
understand world events at her reading level.

**Hackathon Requirement Met:** "structured, easy-to-consume"

---

## FEATURE 4: Three-Perspective Viewpoints (Progressive / Conservative / Centrist)

**What it does:** For each story, the AI generates three distinct framings based on
actual language patterns in the source articles — not political labels. Each perspective
includes a 40-word summary and an "emphasis" field showing what that framing highlights.

**Use Case — Voter Before an Election:**
Tom is undecided about a policy issue. Instead of reading one outlet's take, KhabarLens
shows him how progressives frame it (social impact), how conservatives frame it
(economic impact), and the centrist view (pure facts). He makes a more informed decision.

**Use Case — Debate Team Preparation:**
A high school debate team needs to argue both sides of an immigration policy.
KhabarLens gives them the progressive emphasis ("humanitarian implications"),
conservative emphasis ("border security costs"), and centrist facts — all from the
same article cluster.

**Hackathon Requirement Met:** "highly objective" + "multiple viewpoints"

---

## FEATURE 5: Polarization Index (0-100 Composite Score)

**What it does:** Calculates how differently the same story is being reported using
three components: Sentiment Variance (30%), Language Bias (40%), Content Divergence
(30%). Uses sigmoid normalization. Shows full methodology explanation in the UI.

**Use Case — Media Literacy Teacher:**
Ms. Garcia teaches media literacy at a high school. She shows students a story with
Polarization 72/100 and asks "Why is this number high?" Students click into the
breakdown and see: "Sources express opposing emotional tones. At least one source
uses notably charged language." This is hands-on media literacy education.

**Use Case — Newsroom Editor:**
An editor at a digital publication wants to ensure their coverage isn't too biased
compared to competitors. They analyze their own articles through KhabarLens and see
their bias score relative to the same story's cross-source average.

**Hackathon Requirement Met:** "highly objective" (quantified objectivity)

---

## FEATURE 6: Adverse News Classification (21 Categories)

**What it does:** Classifies each story into one of 21 categories (Financial Crime,
Money Laundering, Fraud & Scams, Insider Trading, Terrorism, Sanctions, Regulatory
& Compliance, FINRA & SEC, Human Rights, War Crimes, Crime/Law/Justice, Cybercrime,
Drug Trafficking, Corruption, Economy & Markets, Geopolitics, AI & Tech Ethics,
Environment, Health, General News) and flags whether it's "adverse" using strict
compliance-grade criteria.

**Use Case — KYC/AML Analyst:**
Priya works in Know Your Customer (KYC) at HSBC. She needs to screen clients against
adverse media — specifically financial crime, sanctions, terrorism, and regulatory
penalties. KhabarLens filters to "Adverse Only" and shows her only stories that meet
the strict compliance definition, with reasons for each classification.

**Use Case — Risk Management at a Hedge Fund:**
A risk analyst monitors for events that could impact portfolio companies. She filters
by "Financial Crime" + "Regulatory & Compliance" to see only SEC enforcement actions
and fraud cases relevant to her investments.

**Hackathon Requirement Met:** Extends the brief with compliance/risk use case

---

## FEATURE 7: Article Analyzer (Paste URL or Text → Credibility Scores)

**What it does:** Users paste any article URL or text. The backend fetches the page,
extracts content, and GPT-4o-mini returns: Credibility Score (0-100), Fake News Risk
(Low/Medium/High), Category, Adverse flag, Bias Direction, Bias Score, Red Flags,
and a verdict sentence.

**Use Case — Social Media User Fact-Checking:**
Alex sees a viral article on Twitter claiming "Government secretly bans cryptocurrency."
Before sharing, he pastes the URL into KhabarLens Article Analyzer. It returns:
Credibility 35/100, Fake News Risk: High, Red Flags: ["No named sources",
"Sensationalist headline"]. Alex doesn't share it.

**Use Case — Corporate Communications:**
A PR team needs to assess whether a negative article about their company is credible
journalism or a hit piece. They paste the URL and get an objective bias score and
credibility assessment.

**Hackathon Requirement Met:** "highly objective" + fighting misinformation

---

## FEATURE 8: Deep Analysis (Perspective Slider + Omission Radar + Gen-Z Mode)

**What it does:** For any story, generates four advanced analysis sections:
1. Perspective Slider — Three-column LEFT/CENTER/RIGHT political lens analysis
2. Omission Radar — 3 critical facts the coverage might be missing
3. Gen-Z Mode — "The Tea", "The Receipts", "Vibe Check", "Main Character"
4. Bias Meter — Visual LEFT←→RIGHT slider with confidence score

**Use Case — Critical Thinking Education:**
Professor Williams uses KhabarLens in his Critical Thinking 101 class. He shows
the Omission Radar for an article about climate policy: "Context Missing: The article
doesn't mention that the proposed regulation exempts the top 3 polluting industries."
Students learn to ask "What's NOT being said?"

**Use Case — Gen-Z News Consumer:**
Zara, 19, doesn't read traditional news. But she engages with the Gen-Z Mode:
"THE TEA: The US just shot down Iranian jets for the first time since Desert Storm."
"VIBE CHECK: BIG DEAL." This format meets her where she is.

**Hackathon Requirement Met:** "expand across formats" + engaging younger audience

---

## FEATURE 9: Multi-Language Voice Briefings (ElevenLabs, 4 Languages)

**What it does:** Every article has EN/HI/ES/FR voice buttons. ElevenLabs generates
natural speech in English, Hindi, Spanish, and French. Also has a "Full Briefing"
button that reads the top 5 stories sequentially. Each perspective in the modal
also has individual language playback buttons.

**Use Case — Visually Impaired User:**
Mohammed is visually impaired and can't read screens easily. He clicks "Briefing"
and listens to a 60-second audio summary of today's top 5 stories while commuting.

**Use Case — Hindi-Speaking Parent in India:**
Sunita's English isn't strong. She clicks "HI" on an article about sanctions and
hears the summary in Hindi, making global news accessible in her language.

**Use Case — Language Learner:**
Pierre is learning Spanish. He reads the English summary, then clicks "ES" to hear
the same content in Spanish — comparing comprehension across languages.

**Hackathon Requirement Met:** "expand across formats, countries, languages"

---

## FEATURE 10: Country-Specific News Feeds (7 Countries)

**What it does:** Country pills (🇺🇸 US, 🇬🇧 UK, 🇮🇳 India, 🇫🇷 France, 🇩🇪 Germany,
🇯🇵 Japan, 🌍 World) switch the entire news feed to that country's Google News
localized RSS. Each country gets its own language/region code.

**Use Case — International Business Analyst:**
James works for a multinational. He needs to understand how the same trade policy
is covered in the US vs. Germany vs. Japan. He clicks each country and compares
headlines, categories, and polarization scores across regions.

**Use Case — Immigrant Staying Connected:**
Anita moved from India to the US. She clicks 🇮🇳 to read Indian news, then 🇺🇸
to see US news — all in one interface with the same analysis layer.

**Hackathon Requirement Met:** "expand across countries"

---

## FEATURE 11: AI Chat Assistant (Custom GPT-4o-mini Chat)

**What it does:** A floating chat bubble (bottom-right) opens an AI assistant that
knows about all currently loaded stories. Users can ask questions like "Which story
is most polarized?", "Any adverse news?", "Explain the Iran story", "Compare bias
across sources."

**Use Case — News Briefing for Executives:**
A CEO types "Give me a 3-sentence summary of the most important story today" and
gets an instant AI-generated briefing based on the actual loaded news data.

**Use Case — Student Research:**
A student asks "Are there any stories about human rights?" and the AI responds with
specific loaded stories that match, including their polarization scores and sources.

**Hackathon Requirement Met:** "structured" + AI agent interaction

---

## FEATURE 12: Real-Time Search with Local + Web Fallback

**What it does:** Two-layer search: (1) Instantly filters already-loaded articles
as user types (matches against headline, summary, category, tags, sources).
(2) If fewer than 3 local matches, automatically queries Google News RSS for
new articles matching the search term.

**Use Case — Breaking News:**
A bomb goes off somewhere. The user types "explosion" — local articles about it
appear instantly. If nothing loaded yet, the system fetches fresh results from
Google News and adds them to the feed.

**Use Case — Compliance Screening:**
A KYC analyst types a client's name — "Oleg Deripaska" — and the system filters
to any loaded articles mentioning him, or fetches new ones from Google News.

**Hackathon Requirement Met:** "daily access to reliable news"

---

## FEATURE 13: Pagination (12 Articles Per Page)

**What it does:** With 30+ articles, the UI paginates into pages of 12. Page 1 gets
a hero card (large image, 32px serif headline). Numbered page buttons at top and
bottom with Prev/Next navigation. Scrolls to top on page change.

**Use Case:** Any user with 30+ articles doesn't have to scroll infinitely.
Clean, newspaper-like reading experience.

**Hackathon Requirement Met:** "easy-to-consume" UX

---

## FEATURE 14: Opinion & Perspectives Column (NYT-Style Right Sidebar)

**What it does:** Right column shows all story perspectives grouped by political
framing — Progressive, Conservative, Centrist — in a newspaper editorial column
format. Each headline is clickable to the original source.

**Use Case — Comparative Analysis:**
A reader scrolls the right column and sees how 6 different stories are framed
from the progressive perspective, then scrolls to see the conservative framing
of the same 6 stories. Pattern recognition: "Progressives consistently emphasize
humanitarian impact while conservatives emphasize security costs."

**Hackathon Requirement Met:** "multiple viewpoints" in an accessible format

---

## FEATURE 15: Source-by-Source Bias Analysis (Per Article)

**What it does:** In the Perspectives modal, each source gets: tone (positive/
negative/neutral), loaded phrases highlighted in red, a bias score bar (0-100%),
and a framing note explaining how this source differs from others.

**Use Case — Media Bias Research:**
A researcher comparing AP News vs. The Daily Beast coverage of the same event
sees that AP has bias score 12% with zero loaded phrases, while The Daily Beast
has bias score 58% with loaded phrases like "brutal purge" and "retaliation."

**Hackathon Requirement Met:** "highly objective" with evidence

---

## FEATURE 16: Image Scraping from Articles (og:image Extraction)

**What it does:** Backend extracts images from RSS media tags, then falls back to
scraping the og:image meta tag from article URLs. Category-specific Unsplash
fallbacks if both fail.

**Use Case:** Visual news consumption — articles with real images from the source
are more engaging and trustworthy than placeholder stock photos.

**Hackathon Requirement Met:** Professional, newspaper-quality presentation

---

## FEATURE 17: NYT-Style Design with Playfair Display + Inter

**What it does:** The entire UI is designed to look like The New York Times:
- Playfair Display serif font for headlines (32px hero, 22px regular)
- Black masthead with white text
- 3-column layout (sidebar + articles + opinion column)
- Thin horizontal rules between articles
- Image-left, content-right card layout

**Use Case:** Trust through design. Users associate the newspaper aesthetic with
credible journalism, which aligns with the mission of objective reporting.

**Hackathon Requirement Met:** Professional-grade presentation

---

## FEATURE 18: Inference Engineering (Calibrated AI Prompts)

**What it does:** Every GPT-4o-mini prompt uses:
- Explicit classification rubrics (adverse criteria, bias score 0.0-1.0 scale)
- System prompt: "classify conservatively, write like Reuters"
- JSON mode (response_format: json_object) for guaranteed structured output
- Temperature 0.2 for deterministic outputs
- Few-shot style instructions with explicit examples of what IS and ISN'T adverse

**Use Case — Reproducible Results:**
Two users analyzing the same article get the same classification because the
inference engineering removes randomness. This is critical for compliance use
cases where consistency matters.

**Hackathon Requirement Met:** Technical depth + reliability

---

## SUMMARY: Hackathon Brief Compliance Matrix

| Brief Requirement                    | Features Covering It              |
|--------------------------------------|-----------------------------------|
| Structured, easy-to-consume          | #3, #8, #13, #17                  |
| Highly objective                     | #4, #5, #6, #7, #15, #18         |
| Reliable news from top sources       | #1, #2, #12                       |
| Daily access                         | #9 (briefing), #12, #13           |
| Expand across formats                | #8 (Gen-Z), #9 (voice), #14      |
| Expand across countries              | #10 (7 countries)                 |
| Expand across languages              | #9 (EN, HI, ES, FR)              |
| Multiple viewpoints                  | #4, #8, #14, #15                  |
| Politically biased perception solved | #4, #5, #8, #15, #18             |

---

## TECH STACK SUMMARY

| Layer          | Technology                                          |
|----------------|-----------------------------------------------------|
| Data Ingestion | Google News RSS (feedparser), 8 backup RSS feeds    |
| Image Scraping | httpx + og:image meta tag extraction                |
| Clustering     | Title-overlap + OpenAI text-embedding-3-small       |
| AI Analysis    | GPT-4o-mini with JSON mode, inference engineering   |
| Scoring        | Custom polarization formula with sigmoid norm        |
| Voice          | ElevenLabs API (4 languages, multilingual v2 model) |
| Backend        | Python FastAPI, async pipeline, semaphore control    |
| Frontend       | React 18, Vite, Axios, Lucide icons                 |
| Design         | Playfair Display + Inter, NYT-inspired layout        |
| AI Chat        | Custom chat component → GPT-4o-mini with context    |
