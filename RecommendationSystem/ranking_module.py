"""
ranking_module.py - Recommendation Ranking and Tabulation
Implements Part E (Q6) of Experiment 4.
Utilizes Pandas and Sentence Transformers for semantic scoring, ranking,
and tabular presentation of recommendations.
"""

from typing import List, Dict, Any
import pandas as pd
from .profile_module import UserProfile

# Cache sentence-transformer model instance
_EMBED_MODEL = None


def get_embed_model():
    """Lazily loads SentenceTransformer model to optimize startup time."""
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            # Sentence transformers optional fallback if torch/download unavailable
            _EMBED_MODEL = False
    return _EMBED_MODEL


def rank_recommendations(
    items: List[Dict[str, Any]],
    profile: UserProfile = None,
    use_sentence_transformers: bool = False
) -> List[Dict[str, Any]]:
    """
    Ranks recommendations according to their suitability.
    Uses Pandas DataFrame for structured sorting and optional SentenceTransformer
    semantic similarity scoring against the user profile.
    """
    if not items:
        return []

    # Create Pandas DataFrame
    df = pd.DataFrame(items)

    # Ensure 'score' column exists and is numeric
    if "score" not in df.columns:
        df["score"] = 80
    else:
        df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(80).astype(int)

    # Optional Sentence Transformers semantic boost
    if use_sentence_transformers and profile is not None:
        try:
            model = get_embed_model()
            if model:
                from sentence_transformers import util
                profile_text = f"Goal: {profile.goal}. Interests: {', '.join(profile.interests)}. Level: {profile.skill_level}."
                profile_emb = model.encode(profile_text, convert_to_tensor=True)

                item_texts = [f"{it.get('name', '')} {it.get('reason', '')}" for it in items]
                item_embs = model.encode(item_texts, convert_to_tensor=True)

                cos_sims = util.cos_sim(profile_emb, item_embs)[0].cpu().numpy()
                
                # Blend LLM score (70%) with semantic similarity score (30%)
                blended_scores = []
                for orig_score, sim in zip(df["score"], cos_sims):
                    sim_pct = int(min(max(sim * 100, 60), 99))
                    blended = int(0.75 * orig_score + 0.25 * sim_pct)
                    blended_scores.append(blended)
                
                df["score"] = blended_scores
        except Exception:
            pass

    # Sort descending by score
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    ranked_items = df.to_dict(orient="records")
    return ranked_items


def format_ranking_display(ranked_items: List[Dict[str, Any]]) -> str:
    """
    Formats ranked recommendations into the exact table layout from Part E (Q6):
    Rank | Recommendation     | Score
    --------------------------------
    1    | Python for AI      | 95%
    2    | ML Fundamentals    | 92%
    3    | Generative AI      | 88%
    """
    headers = "Rank | Recommendation                 | Score"
    sep = "-" * 46
    lines = ["\nRECOMMENDATION RANKINGS", headers, sep]

    for item in ranked_items:
        rank_val = str(item.get("rank", 1))
        name_val = str(item.get("name", "Item"))
        # Truncate or pad name cleanly for table alignment
        if len(name_val) > 30:
            name_display = name_val[:27] + "..."
        else:
            name_display = name_val.ljust(30)

        score_val = f"{item.get('score', 80)}%"
        lines.append(f"{rank_val.ljust(4)} | {name_display} | {score_val}")

    lines.append(sep)
    return "\n".join(lines)
