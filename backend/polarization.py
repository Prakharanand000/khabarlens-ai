"""
polarization.py - Calibrated Polarization Index (0-100).

Key fix: The sigmoid was too aggressive, pushing most scores to 60+.
Now uses a gentler curve with a higher center point (0.45 instead of 0.35).
Scores should distribute as:
  - 0-25: Very aligned coverage (same facts, same tone)
  - 25-45: Somewhat different framing but similar facts
  - 45-65: Notably different perspectives, some loaded language
  - 65-85: Very different framing, strong editorial angles
  - 85-100: Extremely polarized, opposite narratives

Also includes explanation text for each score range.
"""

import math
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def calculate_polarization(cluster: dict, analysis: dict) -> dict:
    source_analysis = analysis.get("source_analysis", [])

    if not source_analysis or len(source_analysis) < 2:
        return {
            "score": 12,
            "level": "Low",
            "color": "green",
            "explanation": "Only one source available — insufficient data for polarization measurement.",
            "components": {"sentiment_variance": 5, "language_bias": 10, "content_divergence": 5},
            "insight": "Single-source story. Polarization requires multiple sources to measure.",
        }

    # --- Component 1: Sentiment Variance (30%) ---
    tone_map = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
    tones = [tone_map.get(sa.get("tone", "neutral"), 0.5) for sa in source_analysis]

    if len(set(tones)) <= 1:
        sentiment_variance = 0.0
    else:
        sentiment_variance = max(tones) - min(tones)

    # --- Component 2: Language Bias Score (40%) ---
    bias_scores = [sa.get("bias_score", 0.0) for sa in source_analysis]
    if not bias_scores:
        language_bias = 0.0
    else:
        max_bias = max(bias_scores)
        avg_bias = sum(bias_scores) / len(bias_scores)
        # Use max and average, but DON'T amplify
        language_bias = (max_bias * 0.5 + avg_bias * 0.5)

    # --- Component 3: Content Divergence (30%) ---
    embeddings = cluster.get("embeddings", [])
    if embeddings and len(embeddings) >= 2:
        try:
            emb_array = np.array(embeddings)
            sim_matrix = cosine_similarity(emb_array)
            n = len(emb_array)
            total_sim = (sim_matrix.sum() - n) / (n * (n - 1))
            raw_div = 1.0 - total_sim
            # Gentler amplification: 2x instead of 3x
            content_divergence = min(raw_div * 2.0, 1.0)
        except Exception:
            content_divergence = 0.2
    else:
        content_divergence = 0.2

    content_divergence = max(0, min(content_divergence, 1.0))

    # --- Raw Score ---
    raw = (
        0.30 * sentiment_variance +
        0.40 * language_bias +
        0.30 * content_divergence
    )

    # --- Gentler sigmoid ---
    # Center at 0.45 (was 0.35), slope 6 (was 8)
    # This means raw=0.2 → ~15, raw=0.35 → ~35, raw=0.5 → ~57, raw=0.7 → ~82
    stretched = 1 / (1 + math.exp(-6 * (raw - 0.45)))
    score = round(stretched * 100)
    score = max(5, min(95, score))

    # --- Level + Color ---
    if score <= 25:
        level, color = "Low", "green"
    elif score <= 45:
        level, color = "Moderate", "yellow"
    elif score <= 65:
        level, color = "Notable", "orange"
    else:
        level, color = "High", "red"

    # --- Explanation (shows reasoning) ---
    explanations = []
    if sentiment_variance > 0.4:
        explanations.append(f"Sources show opposing emotional tones (variance: {round(sentiment_variance*100)}%).")
    elif sentiment_variance > 0.1:
        explanations.append(f"Sources have somewhat different tones (variance: {round(sentiment_variance*100)}%).")
    else:
        explanations.append("Sources share a similar emotional tone.")

    if max(bias_scores) > 0.5:
        explanations.append(f"At least one source uses notably charged language (max bias: {round(max(bias_scores)*100)}%).")
    elif max(bias_scores) > 0.25:
        explanations.append(f"Some editorial framing detected (max bias: {round(max(bias_scores)*100)}%).")
    else:
        explanations.append("Language across sources is mostly neutral and factual.")

    if content_divergence > 0.5:
        explanations.append("Sources emphasize significantly different aspects of the story.")
    elif content_divergence > 0.2:
        explanations.append("Sources cover similar facts but with different emphasis.")
    else:
        explanations.append("Sources cover the same facts with little divergence.")

    insight = " ".join(explanations)

    # Shorter version for card display
    if score <= 25:
        short_insight = "Coverage is well-aligned across sources."
    elif score <= 45:
        short_insight = "Some framing differences between sources."
    elif score <= 65:
        short_insight = "Notable differences in how sources report this story."
    else:
        short_insight = "Sources report this story very differently — significant narrative divergence."

    return {
        "score": score,
        "level": level,
        "color": color,
        "explanation": insight,
        "components": {
            "sentiment_variance": round(sentiment_variance * 100),
            "language_bias": round(language_bias * 100),
            "content_divergence": round(content_divergence * 100),
        },
        "insight": short_insight,
    }
