# NewsLens AI

Multi-perspective news analysis with Polarization Index scoring.

## Quick Start (Hackathon Setup)

### 1. Backend Setup

```bash
cd backend

# Create virtual env
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI key to .env file
# Open .env and paste your key

# Run the server
python main.py
```

Backend runs on: http://localhost:8000
Test it: http://localhost:8000/api/stories?limit=3

### 2. Frontend Setup

```bash
cd frontend

# Install
npm install

# Run
npm run dev
```

Frontend runs on: http://localhost:5173

### 3. Open http://localhost:5173 in your browser

---

## How It Works

1. **Fetch**: Pulls news from Google News RSS + backup RSS feeds (no API key needed)
2. **Cluster**: Groups same-story articles using title overlap + OpenAI embeddings
3. **Analyze**: GPT-4o-mini generates neutral summary + 3 perspectives per story
4. **Score**: Polarization Index (0-100) measures narrative divergence across sources
5. **Display**: Card UI with perspective modal showing all viewpoints side by side

## Tech Stack

- **Backend**: Python, FastAPI, OpenAI API, feedparser, scikit-learn
- **Frontend**: React, Vite, Axios, Lucide icons
- **AI**: GPT-4o-mini (summaries + bias), text-embedding-3-small (clustering)
- **Data**: Google News RSS (free, no key), backup RSS feeds
