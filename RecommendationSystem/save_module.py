"""
save_module.py - Recommendation Persistence Engine
Implements Part I (Q10) of Experiment 4.
Saves user profile, preferences, ranked recommendations, explanations,
and refinement history to outputs/recommendations.txt.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .profile_module import UserProfile
from .ranking_module import format_ranking_display
from .preference_module import format_preference_display


def get_default_output_path() -> Path:
    """Returns the absolute path to RecommendationSystem/outputs/recommendations.txt."""
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "recommendations.txt"


def save_recommendations_to_file(
    profile: UserProfile,
    ranked_items: List[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]] = None,
    feedback: Optional[str] = None,
    refined_items: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Saves the entire recommendation session neatly into outputs/recommendations.txt.
    Returns status confirmation for display in CLI and Web UI.
    """
    target_path = Path(output_path) if output_path else get_default_output_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "=" * 60,
        "PERSONALIZED RECOMMENDATION SYSTEM REPORT",
        "24CS2506 - Building Applications using GPT-4 | Experiment 4",
        f"Generated At: {timestamp}",
        "=" * 60,
        "",
        profile.display(),
        "",
    ]

    if preferences:
        lines.append(format_preference_display(preferences))
        lines.append("")

    lines.append(format_ranking_display(ranked_items))
    lines.append("")

    lines.append("DETAILED RECOMMENDATIONS & RATIONALE:")
    lines.append("-" * 60)
    for idx, it in enumerate(ranked_items, 1):
        lines.append(f"{idx}. {it.get('name')}")
        lines.append(f"   Suitability Score: {it.get('score')}%")
        reason = it.get('explanation') or it.get('reason') or "Matches profile preferences."
        lines.append(f"   Reason / Explanation: {reason}\n")
    lines.append("-" * 60)
    lines.append("")

    if feedback and refined_items:
        lines.append("USER FEEDBACK & REFINEMENT:")
        lines.append("-" * 60)
        lines.append(f"Feedback Received: \"{feedback}\"\n")
        lines.append("Refined Recommendations:")
        for idx, it in enumerate(refined_items, 1):
            lines.append(f"{idx}. {it.get('name')} (Score: {it.get('score')}%)")
            lines.append(f"   Reason: {it.get('reason')}\n")
        lines.append("-" * 60)
        lines.append("")

    lines.append("=" * 60)
    lines.append("End of Report")
    lines.append("=" * 60)

    content = "\n".join(lines)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "status": "success",
        "message": "Recommendation Saved Successfully",
        "file_path": str(target_path),
        "total_items": len(ranked_items),
        "timestamp": timestamp
    }
