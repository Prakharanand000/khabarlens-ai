"""
clustering.py - Lightweight clustering for Render free tier.
Uses title overlap + TF-IDF cosine similarity.
No sentence-transformers, no torch, no local model loading.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SIMILARITY_THRESHOLD = 0.45


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
    "for", "of", "and", "or", "but", "with", "as", "by", "from", "this",
    "that", "after", "over", "into", "about", "says", "said"
}


def clean_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_overlap(t1: str, t2: str) -> float:
    w1 = set(clean_text(t1).split()) - STOPWORDS
    w2 = set(clean_text(t2).split()) - STOPWORDS

    if not w1 or not w2:
        return 0.0

    return len(w1 & w2) / max(len(w1), len(w2))


def article_text(article: dict) -> str:
    title = article.get("title", "")
    desc = article.get("description", "")
    source = article.get("source", "")
    return clean_text(f"{title}. {desc}. {source}")


async def cluster_articles(articles: list) -> list:
    """
    Groups articles covering the same story.
    Render-safe: no torch / transformers / sentence-transformers.
    """

    if not articles:
        return []

    if len(articles) == 1:
        return [{
            "articles": articles,
            "primary_title": articles[0].get("title", ""),
            "source_count": 1,
            "sources": [articles[0].get("source", "Unknown")],
            "embeddings": [],
        }]

    texts = [article_text(a) for a in articles]

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=3000,
            ngram_range=(1, 2)
        )
        tfidf = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf)
    except Exception as e:
        print(f"TF-IDF clustering error: {e}")
        sim_matrix = np.zeros((len(articles), len(articles)))

    used = set()
    clusters = []

    for i, article in enumerate(articles):
        if i in used:
            continue

        cluster_indices = [i]
        used.add(i)

        for j, other in enumerate(articles):
            if j in used or i == j:
                continue

            overlap = title_overlap(
                article.get("title", ""),
                other.get("title", "")
            )

            tfidf_sim = sim_matrix[i][j]

            same_story = (
                overlap >= 0.35
                or tfidf_sim >= SIMILARITY_THRESHOLD
                or other.get("source") in article.get("sub_sources", [])
            )

            if same_story:
                cluster_indices.append(j)
                used.add(j)

        cluster_arts = [articles[idx] for idx in cluster_indices]
        sources = list(set(a.get("source", "Unknown") for a in cluster_arts))

        clusters.append({
            "articles": cluster_arts,
            "primary_title": article.get("title", ""),
            "source_count": len(sources),
            "sources": sources,
            "embeddings": [],
        })

    clusters.sort(key=lambda c: c["source_count"], reverse=True)

    print(f"Created {len(clusters)} clusters")
    for c in clusters[:5]:
        print(f"  [{c['source_count']} sources] {c['primary_title'][:60]}")

    return clusters