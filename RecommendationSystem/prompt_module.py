"""
prompt_module.py - Prompt Construction Engine
Implements Part C (Q4) of Experiment 4.
Constructs structured LLM prompts using collected user information,
preferences, feedback, and intent.
"""

from typing import Dict, Any, List, Optional
from .profile_module import UserProfile


def construct_initial_prompt(profile: UserProfile, preferences: Optional[Dict[str, Any]] = None) -> str:
    """
    Constructs the standard recommendation prompt matching Part C (Q4) of LAB QUESTION_4.pdf:
    
    You are a personalized recommendation assistant.
    User:
    Name: Arun
    Background: Computer Science
    Interests: Artificial Intelligence, Python
    Skill Level: Beginner
    Goal: Learn AI
    Preference: Practical learning
    
    Recommend five suitable learning resources.
    For each recommendation provide:
    1. Name
    2. Reason
    3. Suitability score
    """
    interests_str = ", ".join(profile.interests)
    pref_str = preferences.get("preference", profile.preferred_category) if preferences else profile.preferred_category
    goal_str = preferences.get("goal", profile.goal) if preferences else profile.goal

    num_words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    count_word = num_words.get(profile.num_recommendations, str(profile.num_recommendations))

    prompt = f"""You are a personalized recommendation assistant.

User:
Name: {profile.name}
Background: {profile.background}
Interests: {interests_str}
Skill Level: {profile.skill_level}
Goal: {goal_str}
Preference: {pref_str}

Recommend {count_word} suitable learning resources.

For each recommendation provide:
1. Name
2. Reason
3. Suitability score (as a percentage, e.g. 95%)

Format the response as a valid JSON list of objects with keys: "name", "score" (integer between 50 and 100), and "reason".
"""
    return prompt.strip()


def construct_refinement_prompt(
    profile: UserProfile,
    current_items: List[Dict[str, Any]],
    feedback: str
) -> str:
    """
    Constructs a refinement prompt taking user critique and previous recommendations into account.
    Implements Part G (Q8).
    """
    items_summary = "\n".join([f"- {it.get('name')} (Score: {it.get('score')}%)" for it in current_items])
    interests_str = ", ".join(profile.interests)

    prompt = f"""You are a personalized recommendation assistant refining prior suggestions based on user feedback.

Learner Profile:
Name: {profile.name}
Interests: {interests_str}
Skill Level: {profile.skill_level}
Goal: {profile.goal}
Preference: {profile.preferred_category}

Previous Recommendations:
{items_summary}

User Feedback:
"{feedback}"

Generate {profile.num_recommendations} updated and refined recommendations that strictly respect the user's feedback, exclusions, and preferred topics.

For each recommendation provide:
1. Name
2. Reason (mentioning how it directly addresses their feedback)
3. Suitability score (as an integer between 50 and 100)

Return ONLY valid JSON as an array of objects with keys: "name", "score", and "reason".
"""
    return prompt.strip()


def construct_explanation_prompt(profile: UserProfile, item_name: str, item_reason: str = "") -> str:
    """
    Constructs a dedicated explanation prompt for Part F (Q7).
    """
    prompt = f"""You are an educational recommendation assistant.
Explain in detail why the resource "{item_name}" is suitable for the learner.

Learner Profile:
Name: {profile.name}
Background: {profile.background}
Interests: {', '.join(profile.interests)}
Skill Level: {profile.skill_level}
Goal: {profile.goal}
Preference: {profile.preferred_category}

Initial reason: {item_reason}

Provide a clear, engaging explanation (2-3 sentences) specifically connecting the resource to the learner's skill level, background, and goals.
"""
    return prompt.strip()
