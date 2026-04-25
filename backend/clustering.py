"""
clustering.py - Groups articles covering the same story.
Migrated from OpenAI embeddings → sentence-transformers (free, local, no API cost).
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from sentence_transformers import SentenceTransformer

# Load once at module level — reused across all requests
_model = SentenceTransformer("all-MiniLM-L6-v2")

SIMILARITY_THRESHOLD = 0.65


def get_embeddings(texts: list) -> np.ndarray:
    """Get embeddings using local sentence-transformers model. Synchronous."""
    return _model.encode(texts, show_progress_bar=False)


def _title_overlap(t1: str, t2: str) -> float:
    """Quick word-overlap similarity."""
    w1 = set(re.sub(r'[^\w\s]', '', t1.lower()).split())
    w2 = set(re.sub(r'[^\w\s]', '', t2.lower()).split())
    stop = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'as', 'by', 'from'}
    w1 = w1 - stop
    w2 = w2 - stop
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / max(len(w1), len(w2))


async def cluster_articles(articles: list) -> list:
    """
    Cluster articles covering the same story.
    Phase 1: Title overlap + sub-source grouping.
    Phase 2: sentence-transformers embeddings for remaining merging.
    Returns list of cluster dicts.
    """
    if not articles:
        return []

    if len(articles) == 1:
        return [{
            "articles": articles,
            "primary_title": articles[0]["title"],
            "source_count": 1,
            "sources": [articles[0]["source"]],
            "embeddings": [],
        }]

    # --- Phase 1: Title-overlap based quick clustering ---
    used = set()
    clusters = []

    for i, art in enumerate(articles):
        if i in used:
            continue

        cluster_indices = [i]
        used.add(i)

        for j, other in enumerate(articles):
            if j in used:
                continue
            overlap = _title_overlap(art["title"], other["title"])
            if overlap > 0.4:
                cluster_indices.append(j)
                used.add(j)
            elif other["source"] in art.get("sub_sources", []):
                cluster_indices.append(j)
                used.add(j)

        cluster_arts = [articles[idx] for idx in cluster_indices]
        clusters.append({
            "articles": cluster_arts,
            "primary_title": art["title"],
            "source_count": len(set(a["source"] for a in cluster_arts)),
            "sources": list(set(a["source"] for a in cluster_arts)),
            "embeddings": [],
        })

    # --- Phase 2: Merge similar clusters using local embeddings ---
    if len(clusters) >= 2:
        rep_texts = [
            f"{c['primary_title']}. {c['articles'][0]['description'][:150]}"
            for c in clusters
        ]

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            # Run synchronous model in executor to avoid blocking event loop
            embeddings = await loop.run_in_executor(None, get_embeddings, rep_texts)
            sim_matrix = cosine_similarity(embeddings)

            merged = set()
            new_clusters = []

            for i in range(len(clusters)):
                if i in merged:
                    continue

                current = clusters[i]
                current_emb = [embeddings[i].tolist()]

                for j in range(i + 1, len(clusters)):
                    if j in merged:
                        continue
                    if sim_matrix[i][j] > SIMILARITY_THRESHOLD:
                        current["articles"].extend(clusters[j]["articles"])
                        current["sources"] = list(set(
                            current["sources"] + clusters[j]["sources"]
                        ))
                        current["source_count"] = len(current["sources"])
                        current_emb.append(embeddings[j].tolist())
                        merged.add(j)

                current["embeddings"] = current_emb
                new_clusters.append(current)

            clusters = new_clusters

        except Exception as e:
            print(f"Embedding clustering error: {e}")

    clusters.sort(key=lambda c: c["source_count"], reverse=True)

    print(f"Created {len(clusters)} clusters")
    for c in clusters[:5]:
        print(f"  [{c['source_count']} sources] {c['primary_title'][:60]}")

    return clusters
