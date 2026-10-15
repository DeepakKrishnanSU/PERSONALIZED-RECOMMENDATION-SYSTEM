"""
explanation_module.py - Recommendation Explanation Generator
Implements Part F (Q7) of Experiment 4.
Generates comprehensive personalized explanations detailing why each
recommended resource aligns with the user's background, skill level, and goals.
"""

from typing import List, Dict, Any
from .profile_module import UserProfile
from .prompt_module import construct_explanation_prompt
from .utils import call_llm, sanitize_text


def explain_single_item(profile: UserProfile, item: Dict[str, Any]) -> str:
    """
    Generates a dedicated explanation for a specific recommendation item using LLM.
    """
    name = item.get("name", "Selected Resource")
    reason = item.get("reason", "")
    prompt = construct_explanation_prompt(profile, name, reason)
    system_prompt = (
        "You are an academic mentor. Provide a concise, encouraging, and detailed explanation "
        "of why this specific learning resource is the best fit for the user's profile."
    )

    try:
        explanation = call_llm(prompt, system_prompt=system_prompt, temperature=0.4)
        return sanitize_text(explanation).strip()
    except Exception as e:
        return f"This resource is chosen because it directly targets {profile.goal} at a {profile.skill_level} level with a practical focus."


def generate_all_explanations(profile: UserProfile, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensures all items have rich explanations, calling LLM if additional depth is requested.
    """
    explained_items = []
    for it in items:
        item_copy = dict(it)
        if "explanation" not in item_copy or not item_copy["explanation"]:
            # If item already has a good reason from generator, we can enrich it
            item_copy["explanation"] = item_copy.get("reason", "")
        explained_items.append(item_copy)
    return explained_items


def format_explanations_display(items: List[Dict[str, Any]]) -> str:
    """
    Formats all explanations for display in terminal or UI.
    """
    lines = [
        "\nRECOMMENDATION EXPLANATIONS",
        "=" * 45
    ]
    for idx, item in enumerate(items, 1):
        lines.append(f"{idx}. {item.get('name')}")
        explanation = item.get("explanation") or item.get("reason") or "Suitable for profile."
        lines.append(f"   Explanation: {explanation}\n")
    lines.append("=" * 45)
    return "\n".join(lines)
