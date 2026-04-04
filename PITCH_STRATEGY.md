# KhabarLens AI — Hackathon Pitch Strategy & Script
## "Who is the Agent Master" — Fontaine Founders Hackathon
## Track: Going Merry → AI News (Idea #1)

---

# PART 1: STRATEGIC POSITIONING

## Why AI News Track?

The brief says: "An AI agent that delivers structured, easy-to-consume, and
highly objective news in a media environment where most outlets are perceived
as politically biased."

Most teams will build: a news summarizer.
We built: **an AI agent that EXPOSES how narratives differ across sources and
lets you SEE bias — not just read about it.**

That distinction is everything.

## How We Hit Every Evaluation Criteria

### CLARITY (Weight: High)
- One sentence: "Same story, different narratives — we quantify the gap."
- Demo flow is visual: card → click → 3 perspectives side by side → polarization score
- Judges SEE it in 10 seconds

### TECHNICAL EXECUTION (Weight: High)
- Real pipeline: Google News RSS → embedding clustering → GPT-4o-mini analysis → scoring
- 18 features working end-to-end (not mockups)
- Inference engineering: calibrated prompts with rubrics, JSON mode, temperature control
- Credibility-weighted polarization (Reuters 0.95 vs blogs 0.45)
- Side-by-side headline comparison with source bias mapping
- Article Analyzer: paste any URL → credibility/fake-news/bias scores

### NOVELTY (Weight: High)
- "Explainable Polarization" — not just a score, but WHY it's polarized with bullet points
- "Omission Radar" — what's MISSING from coverage
- "Gen-Z Mode" — THE TEA / THE RECEIPTS / VIBE CHECK format
- "Narrative Timeline" — how a story evolves through the media cycle
- No other team will have this depth

### IMPACT (Weight: High)
- 73% of Americans don't trust news media
- Echo chambers are measurable — we measure them
- Compliance use case: adverse news screening for KYC/AML (21 categories)
- Works in 7 countries, 4 languages
- "Democracy depends on informed citizens, not citizens trapped in echo chambers"

---

# PART 2: THE 120-SECOND PITCH SCRIPT

## [Read this at a confident, measured pace — ~2 words/second]

---

### 0:00–0:15 | THE JOLT (Pattern Interrupt)

"Right now, if you Google 'Iran conflict' — CNN says 'crisis escalates.'
Fox says 'decisive response.' Reuters says 'tensions rise.'
Same event. Three completely different stories.
And you have no way to know which framing you're trapped in."

[PAUSE — 1 beat]

### 0:15–0:45 | THE GAP (Problem → Agent)

"73% of Americans say news is biased. But WHICH way? And HOW MUCH?
Nobody quantifies it.

KhabarLens AI does.

It's not a summarizer. It's an AI agent that pulls the same story from
multiple sources, clusters them using embeddings, then generates three
distinct framings — progressive, conservative, centrist — and calculates
a Polarization Index that tells you EXACTLY how differently this story
is being told."

### 0:45–1:45 | THE HOW (Demo + Technical Flex)

"Here's how it works.

[SHOW HOMEPAGE]
We scrape 30+ articles from Google News across 8 topic feeds and 8 backup
RSS sources. Every article gets an image, source credibility score, and
adverse classification across 21 categories — from financial crime to
sanctions to human rights.

[CLICK INTO AN ARTICLE]
Each story gets a Polarization Index — sentiment variance, language bias,
and content divergence — weighted by source credibility. Reuters at 95%
weighs more than a blog at 45%.

[CLICK 'WHY POLARIZED' TAB]
This is our differentiator. We don't just score bias — we EXPLAIN it.
Bullet points showing: which sources use charged language, who's being
blamed, what facts are being omitted.

[CLICK 'DEEP ANALYSIS']
Perspective Slider: LEFT, CENTER, RIGHT — three columns.
Omission Radar: what the coverage is missing.
Gen-Z Mode: THE TEA, THE RECEIPTS, VIBE CHECK.

[SHOW ARTICLE ANALYZER]
Paste any URL — get credibility score, fake news risk, bias direction,
and adverse classification. Instant.

[SHOW VOICE]
Four-language voice briefing — English, Hindi, Spanish, French.
Built for expanding across countries and formats.

Everything was built today. No pre-built code."

### 1:45–2:00 | THE ZEIGARNIK EFFECT (Open Loop)

"We built 18 features in 7 hours. But here's what we didn't show you yet.

The Narrative Timeline tracks how a story's polarization CHANGES over
the media cycle. Today it's at 45. Tomorrow, after the political reaction
phase, our model predicts it'll hit 72.

We're not just showing you today's bias.
We're predicting tomorrow's."

[END — no "thank you", no closing. Leave it hanging.]

---

## WORD COUNT: ~235 words ✓ (fits in 120 seconds at 2 words/sec)

---

# PART 3: LOOM RECORDING CHECKLIST

## Before Recording:
□ Backend running (python main.py) — verify at localhost:8000/docs
□ Frontend running (npm run dev) — verify at localhost:5173
□ Load stories FIRST — wait for full load so demo is instant
□ Open 1 article's Perspective modal, pre-click "Why Polarized" to cache
□ Have a URL ready in Article Analyzer (e.g., a Daily Beast or Fox article)
□ Close all other browser tabs (clean look)
□ Test audio works (ElevenLabs briefing) — optional, skip if no key

## Recording Flow (Scene by Scene):

### Scene 1: Hook (0:00–0:15)
- Camera: Full screen, just you talking (or voiceover over homepage)
- Show the homepage briefly but focus on the WORDS
- Energy: High, direct, slightly provocative

### Scene 2: Problem (0:15–0:45)
- Camera: Zoom into the homepage showing multiple stories
- Scroll slowly — show polarization scores, adverse badges, categories
- Energy: Explanatory, building urgency

### Scene 3: Demo (0:45–1:45) — THIS IS 60% OF YOUR SCORE
- Camera: Screen recording, mouse movements, clicks
- Show these in order:
  1. Homepage with 30+ articles, pagination
  2. Category sidebar with 21 categories
  3. Country switcher (click India → show it loading)
  4. Click into ONE story → Perspectives tab
  5. Click "Why Polarized" → show explainable polarization
  6. Click "Deep Analysis" → show Gen-Z mode + Omission Radar
  7. Show Article Analyzer with a pasted URL
  8. Show the AI Chat answering a question
  9. (Optional) Click voice button
- Energy: Fast-paced, confident, name each feature clearly

### Scene 4: Close (1:45–2:00)
- Camera: Back to you (or dramatic pause on the timeline feature)
- Deliver the Zeigarnik hook
- Energy: Visionary, forward-looking, STOP abruptly

## Technical Points to Mention:
□ "30+ articles, 8 topic feeds, 8 backup RSS sources"
□ "OpenAI text-embedding-3-small for clustering"
□ "GPT-4o-mini with JSON mode for structured analysis"
□ "Sigmoid-normalized polarization with 3-component weighting"
□ "Credibility-weighted scoring — Reuters 95%, blogs 45%"
□ "21 adverse categories for compliance use cases"
□ "4-language ElevenLabs voice briefing"
□ "Everything built today — no pre-built code"

## Common Mistakes to Avoid:
✗ Don't start with "Hi, I'm [name] and today I'm presenting..."
✗ Don't say "thank you" at the end
✗ Don't show loading screens — pre-load everything
✗ Don't explain how APIs work — show the OUTPUT
✗ Don't spend more than 5 seconds on any single feature
✗ Don't read from a script visibly — memorize the hook at minimum

---

# PART 4: WHY WE WIN

## vs. Other Teams Building "AI News":

| Other Teams | KhabarLens |
|---|---|
| Summarize articles | COMPARE how sources frame differently |
| One neutral summary | THREE perspective framings + explainability |
| "It's unbiased" (trust me) | Polarization Index with methodology |
| Basic categories | 21 compliance-grade categories |
| English only | 4 languages, 7 countries |
| Read-only | Paste any URL → instant analysis |
| Static output | AI chat that knows your loaded stories |
| No explanation | "WHY is it polarized" with bullet points |

## The Judge's Thought Process:

1. "Oh, another news summarizer" — then they see the Polarization Index
2. "Interesting score" — then they see the 3-perspective breakdown
3. "Smart" — then they see "Why Polarized" with bullet points
4. "Wow, they EXPLAIN the bias" — this is the moment you win
5. Gen-Z Mode is the viral moment — judges will screenshot it

## The One Line That Wins:

"We don't just tell you the news is biased.
We show you exactly HOW, by HOW MUCH, and from WHICH direction."

---

# APPENDIX: FEATURE COUNT FOR PITCH

If asked "how many features did you build?" — the answer is:

"18 features in 7 hours:
Multi-source aggregation, story clustering, neutral summaries,
three-perspective viewpoints, polarization index, adverse classification,
article analyzer, deep analysis with Gen-Z mode, voice briefings in
4 languages, 7-country support, AI chat, real-time search, pagination,
opinion column, source bias analysis, image scraping, explainable
polarization, and narrative timeline."

That list alone wins the technical execution criterion.
