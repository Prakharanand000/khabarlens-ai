# KhabarLens AI 

### AI-Powered News Intelligence Platform
**Built entirely during the "Who is the Agent Master" Hackathon by Fontaine Founders**

**Track:** Going Merry — AI News (Idea #1)

---

## 🎯 What Is KhabarLens AI?

KhabarLens AI is not another news summarizer. It is an **AI agent that exposes how the same story is told differently across sources** and quantifies that narrative divergence with a **Polarization Index (0–100)**.

In a media environment where 73% of Americans perceive news as politically biased, KhabarLens doesn't tell you *what* to think — it shows you **how different outlets frame the same event, by how much, and from which direction**.

> *"We don't just tell you the news is biased. We show you exactly HOW, by HOW MUCH, and from WHICH direction."*

---

## 🚀 18 Features Built Today

### Core Intelligence
| Feature | Description |
|---------|-------------|
| **Multi-Source Aggregation** | 30+ articles from Google News RSS across 8 topic categories + 8 backup feeds (Reuters, BBC, CNN, NPR, Al Jazeera, The Guardian, ABC, CBS) |
| **Story Clustering** | Groups same-story articles using OpenAI `text-embedding-3-small` embeddings + cosine similarity (threshold 0.65) |
| **Neutral Summaries** | 60-word Reuters wire-copy style summaries — no opinion, no loaded language |
| **Three-Perspective Viewpoints** | Progressive, Conservative, and Centrist framings generated from actual language patterns — not political labels |
| **Polarization Index** | Composite score (0–100) from Sentiment Variance (30%) + Language Bias (40%) + Content Divergence (30%), sigmoid-normalized |

### Explainability & Deep Analysis
| Feature | Description |
|---------|-------------|
| **Explainable Polarization** | "Why is this story polarized?" — bullet-point reasons referencing specific framing differences, loaded phrases, and omissions |
| **Side-by-Side Headline Comparison** | Three-column view showing how LEFT, NEUTRAL, and RIGHT outlets frame the same story |
| **Deep Analysis** | Perspective Slider (LEFT/CENTER/RIGHT columns), Omission Radar (what coverage is missing), Gen-Z Mode (THE TEA / THE RECEIPTS / VIBE CHECK) |
| **Narrative Timeline** | How a story's polarization evolves: Breaking → Reaction → Framing Battle → Current, with prediction |
| **Bias Meter** | Visual LEFT ← → RIGHT slider with confidence score and reasoning |

### Risk & Compliance
| Feature | Description |
|---------|-------------|
| **21 Risk Categories** | Financial Crime, Money Laundering, Fraud & Scams, Insider Trading, Terrorism, Sanctions, Regulatory & Compliance, FINRA & SEC, Human Rights, War Crimes, Crime/Law/Justice, Cybercrime, Drug Trafficking, Corruption, Economy & Markets, Geopolitics, AI & Tech Ethics, Environment, Health, General News |
| **Adverse Classification** | Compliance-grade screening — only flags financial fraud, terrorism, sanctions violations, regulatory penalties, human rights abuse, cybercrime |
| **Source Credibility Weighting** | 35+ outlets scored (Reuters 0.95, AP 0.95, BBC 0.90, CNN 0.78, Fox News 0.65, Daily Mail 0.50). Credibility-weighted polarization adjusts scores based on source reliability |
| **Article Analyzer** | Paste any URL or text → get Credibility Score, Fake News Risk, Bias Direction, Bias Score, Adverse flag, Red Flags, and Verdict |

### Accessibility & Reach
| Feature | Description |
|---------|-------------|
| **7-Country News Feeds** | 🇺🇸 US, 🇬🇧 UK, 🇮🇳 India, 🇫🇷 France, 🇩🇪 Germany, 🇯🇵 Japan, 🌍 World — each with localized Google News RSS |
| **4-Language Voice Briefings** | English, Hindi, Spanish, French — per-article and full-page audio via ElevenLabs multilingual v2 |
| **AI Chat Assistant** | Conversational AI that knows all loaded stories — ask "Which story is most polarized?", "Explain the bias", "Who benefits from this narrative?" |
| **Real-Time Search** | Instant local filtering as you type + Google News web fallback for new topics |

### UX & Design
| Feature | Description |
|---------|-------------|
| **NYT-Inspired Layout** | Playfair Display serif headlines, 3-column layout, image-left cards, thin rules — newspaper-quality design |
| **Most Polarized Story Banner** | 🔥 Auto-highlighted at the top of the feed |
| **Pagination** | 12 articles per page with numbered navigation |
| **Opinion Column** | Right sidebar showing all perspectives grouped by political framing with clickable headlines |

---

## 🏗️ Technical Architecture

```
Google News RSS (8 topics + top news)     ─┐
8 Backup RSS (Reuters, BBC, CNN, etc.)    ─┤──→ Article Ingestion
og:image scraping from article URLs       ─┘         │
                                                      ▼
                                            Story Clustering
                                    (title-overlap + embeddings)
                                                      │
                                                      ▼
                                          GPT-4o-mini Analysis
                                    (JSON mode, temp 0.2, rubrics)
                                                      │
                                          ┌───────────┼───────────┐
                                          ▼           ▼           ▼
                                    Neutral      3 Perspectives  21-Category
                                    Summary      + Bias Scores   Classification
                                                      │
                                                      ▼
                                          Polarization Index
                                    (sigmoid-normalized, 3 components,
                                     credibility-weighted)
                                                      │
                                          ┌───────────┼───────────┐
                                          ▼           ▼           ▼
                                    React UI     ElevenLabs    AI Chat
                                    (Vite)       Voice (4 lang) Assistant
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Data Ingestion** | Google News RSS via `feedparser`, 8 backup RSS feeds, `httpx` for og:image scraping |
| **Clustering** | OpenAI `text-embedding-3-small`, `scikit-learn` cosine similarity |
| **AI Analysis** | GPT-4o-mini with `response_format: json_object`, inference-engineered prompts with explicit rubrics |
| **Polarization** | Custom 3-component formula, sigmoid normalization, credibility-weighted adjustment |
| **Voice** | ElevenLabs API — `eleven_multilingual_v2` model for Hindi/Spanish/French, `eleven_monolingual_v1` for English |
| **Backend** | Python 3, FastAPI, async pipeline with `asyncio.Semaphore(4)`, `AsyncOpenAI` |
| **Frontend** | React 18, Vite, Axios, Lucide React icons |
| **Typography** | Playfair Display (headlines), Inter (body) — NYT-inspired |

---

## 📂 Project Structure

```
khabarlens-ai/
├── backend/
│   ├── main.py                 # FastAPI server — all endpoints
│   ├── news_ingestion.py       # Google News RSS + backup feeds + image scraping
│   ├── clustering.py           # Embedding-based story clustering
│   ├── ai_analysis.py          # GPT-4o-mini analysis with 21 categories
│   ├── polarization.py         # Polarization Index calculation
│   ├── requirements.txt
│   ├── .env                    # API keys (not committed)
│   ├── USE_CASES.md            # Detailed use cases for all 18 features
│   └── __pycache__/
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app with routing, search, pagination
│   │   ├── index.css           # Global styles, animations, hover effects
│   │   ├── main.jsx            # React entry point
│   │   └── components/
│   │       ├── NewsCard.jsx          # NYT-style article cards (hero + regular)
│   │       ├── PerspectiveModal.jsx  # 4-tab modal (Perspectives, Why Polarized, Deep Analysis, Timeline)
│   │       ├── Sidebar.jsx           # Category navigation with 21 grouped categories
│   │       ├── ArticleAnalyzer.jsx   # Paste URL → credibility/bias scores
│   │       ├── OpinionColumn.jsx     # Right-side perspective column
│   │       ├── AiChat.jsx            # Floating AI chat assistant
│   │       ├── DeepAnalysis.jsx      # Perspective Slider + Omission Radar + Gen-Z Mode
│   │       ├── ExplainPolarization.jsx  # "Why is this polarized?" with headline comparison
│   │       ├── NarrativeTimeline.jsx    # Story evolution timeline
│   │       └── MostPolarized.jsx        # 🔥 Most polarized story banner
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── .gitignore
├── README.md
├── PITCH_STRATEGY.md
└── DEMO_SCRIPT.md
```

---

## ⚡ Run Locally

### Backend
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder:
```
OPENAI_API_KEY=your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
```

```bash
python main.py
# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens on http://localhost:5173
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stories?limit=30&country=US` | Fetch, cluster, analyze, score news stories |
| `GET` | `/api/search?q=sanctions&country=US` | Search Google News + analyze results |
| `POST` | `/api/analyze` | Analyze any article URL or text for credibility/bias |
| `POST` | `/api/explain-polarization` | Generate human-readable polarization explanation |
| `POST` | `/api/deep-analysis` | Perspective Slider + Omission Radar + Gen-Z Mode |
| `POST` | `/api/narrative-timeline` | Story evolution timeline |
| `GET` | `/api/chat?message=...` | AI chat about loaded stories |
| `GET` | `/api/tts?text=...&lang=en` | Text-to-speech via ElevenLabs |
| `GET` | `/api/briefing-text?limit=5` | Get audio briefing script |

---

## 🎯 Hackathon Brief Compliance

The hackathon brief asks for: *"An AI agent that delivers structured, easy-to-consume, and highly objective news with the potential to expand across formats, countries, languages, and multiple viewpoints."*

| Requirement | How KhabarLens Delivers |
|-------------|------------------------|
| **Structured** | 60-word summaries, key facts (5W), card-based UI, 12-per-page pagination |
| **Easy-to-consume** | Gen-Z Mode (THE TEA / VIBE CHECK), voice briefings, visual polarization bars |
| **Highly objective** | Classify language not sources, Polarization Index with methodology, credibility weighting |
| **Top sources** | Reuters, BBC, AP, CNN, NPR, Al Jazeera, The Guardian + Google News aggregation |
| **Formats** | Text cards, voice audio, AI chat, article analyzer, deep analysis |
| **Countries** | 7 country-specific Google News feeds with localized RSS |
| **Languages** | 4-language voice (EN, HI, ES, FR) via ElevenLabs multilingual v2 |
| **Multiple viewpoints** | 3 perspectives per story + Explainable Polarization + Side-by-Side Headlines |

---

## 👥 Team

Built by **Prakhar Anand** and **Vaishali Hirereaddi** at the Fontaine Founders Hackathon, San Francisco.

**Built entirely during the hackathon — no pre-built code.**

---
