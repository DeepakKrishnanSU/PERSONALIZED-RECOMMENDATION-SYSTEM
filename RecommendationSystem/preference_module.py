"""
preference_module.py - User Preference Analysis
Implements Part B (Q3) of Experiment 4.
Analyzes the user profile to identify:
- Major interests (Primary, Secondary, Additional)
- Skill level
- Learning goal
- Preferred type
- Important constraints
"""

from typing import Dict, Any
from .profile_module import UserProfile
from .utils import call_llm, clean_json_response


def analyze_preferences(profile: UserProfile, use_llm: bool = True) -> Dict[str, Any]:
    """
    Analyzes the user profile and extracts structured preferences.
    Uses rule-based extraction with optional LLM refinement for constraints.
    """
    interests = profile.interests if profile.interests else ["General AI"]
    primary_interest = interests[0] if len(interests) > 0 else "Artificial Intelligence"
    secondary_interest = interests[1] if len(interests) > 1 else (interests[0] if len(interests) > 0 else "Python")

    # Determine default constraints based on skill level and preference
    default_constraints = f"Suitable for {profile.skill_level} level with focus on {profile.preferred_category}."

    preference_data = {
        "primary_interest": primary_interest,
        "secondary_interest": secondary_interest,
        "all_interests": interests,
        "skill_level": profile.skill_level,
        "goal": profile.goal,
        "preference": profile.preferred_category,
        "constraints": default_constraints
    }

    if use_llm:
        try:
            system_prompt = (
                "You are an educational advisor analyzing a learner's profile. "
                "Extract learning preferences and constraints in clean JSON format."
            )
            user_prompt = f"""
Learner Profile:
Name: {profile.name}
Background: {profile.background}
Interests: {', '.join(interests)}
Skill Level: {profile.skill_level}
Preference: {profile.preferred_category}
Goal: {profile.goal}

Return ONLY valid JSON matching this structure:
{{
  "primary_interest": "{primary_interest}",
  "secondary_interest": "{secondary_interest}",
  "skill_level": "{profile.skill_level}",
  "goal": "{profile.goal}",
  "preference": "{profile.preferred_category}",
  "constraints": "Brief 1-sentence constraint or requirement"
}}
"""
            raw_response = call_llm(user_prompt, system_prompt=system_prompt, temperature=0.3)
            parsed = clean_json_response(raw_response)
            preference_data.update(parsed)
        except Exception:
            # Fall back to structured rule-based analysis
            pass

    return preference_data


def format_preference_display(pref: Dict[str, Any]) -> str:
    """
    Formats the preference analysis output matching Part B (Q3) of LAB QUESTION_4.pdf:
    Preference Analysis
    ------------------------------
    Primary Interest   : Artificial Intelligence
    Secondary Interest : Python
    Skill Level        : Beginner
    Goal               : Learn AI
    Preference         : Practical
    Constraints        : Beginner friendly hands-on
    """
    output = [
        "\nPreference Analysis",
        "-" * 30,
        f"Primary Interest   : {pref.get('primary_interest', 'N/A')}",
        f"Secondary Interest : {pref.get('secondary_interest', 'N/A')}",
        f"Skill Level        : {pref.get('skill_level', 'N/A')}",
        f"Goal               : {pref.get('goal', 'N/A')}",
        f"Preference         : {pref.get('preference', 'N/A')}",
        f"Constraints        : {pref.get('constraints', 'None specified')}",
        "-" * 30
    ]
    return "\n".join(output)
