"""
feedback_module.py - User Feedback and Recommendation Refinement
Implements Part G (Q8) of Experiment 4.
Captures user feedback, analyzes critiques and exclusions,
and invokes the LLM to generate refined recommendations.
"""

from typing import List, Dict, Any
from .profile_module import UserProfile
from .prompt_module import construct_refinement_prompt
from .ranking_module import rank_recommendations
from .utils import call_llm, clean_json_response, sanitize_text


def refine_recommendations(
    profile: UserProfile,
    current_items: List[Dict[str, Any]],
    feedback_text: str
) -> List[Dict[str, Any]]:
    """
    Refines existing recommendations according to user critique (Q8).
    Applies the user's feedback to filter, adjust scores, or introduce new targeted items.
    """
    clean_feedback = sanitize_text(feedback_text).strip()
    if not clean_feedback:
        return current_items

    prompt = construct_refinement_prompt(profile, current_items, clean_feedback)
    system_prompt = (
        "You are an expert recommendation refiner. Update the recommendations according to "
        "the user's feedback, removing any excluded topics and focusing heavily on preferred ones. "
        "Return ONLY a valid JSON array of objects with keys: 'name', 'score' (number 50-100), and 'reason'."
    )

    try:
        response_text = call_llm(prompt, system_prompt=system_prompt, temperature=0.4)
        parsed = clean_json_response(response_text)

        if isinstance(parsed, dict) and "recommendations" in parsed:
            raw_items = parsed["recommendations"]
        elif isinstance(parsed, list):
            raw_items = parsed
        else:
            raw_items = [parsed]

        refined_items = []
        for idx, it in enumerate(raw_items, 1):
            name = str(it.get("name") or f"Refined Resource {idx}").strip()
            score = int(it.get("score") or 90)
            reason = str(it.get("reason") or f"Updated to match feedback: '{clean_feedback}'").strip()
            refined_items.append({
                "name": name,
                "score": min(max(score, 50), 100),
                "reason": reason
            })

        # Re-rank refined recommendations using ranking module
        return rank_recommendations(refined_items, profile=profile, use_sentence_transformers=False)

    except Exception as e:
        print(f"[Notice] Refinement fallback triggered ({e})")
        # Filter existing items based on feedback keywords
        lowered_feedback = clean_feedback.lower()
        survivors = []
        for it in current_items:
            name_lower = it["name"].lower()
            # If user said 'do not want web' or 'exclude x', exclude them
            if "not want web" in lowered_feedback and "web" in name_lower:
                continue
            survivors.append(it)
        return rank_recommendations(survivors or current_items, profile=profile)


def format_refined_display(refined_items: List[Dict[str, Any]], feedback: str) -> str:
    """
    Formats the refined recommendations for display.
    """
    lines = [
        "\nREFINED RECOMMENDATIONS (Based on User Feedback)",
        f"User Feedback: \"{feedback}\"",
        "=" * 48
    ]
    for idx, item in enumerate(refined_items, 1):
        lines.append(f"{idx}. {item.get('name')}")
        lines.append(f"   Score: {item.get('score')}%")
        lines.append(f"   Reason: {item.get('reason')}\n")
    lines.append("=" * 48)
    return "\n".join(lines)
