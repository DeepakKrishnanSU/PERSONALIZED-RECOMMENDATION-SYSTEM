"""
input_module.py - User Profile Collection and Input Validation
Implements Part A (Q1) of Experiment 4.
Collects and validates:
- Name
- Age
- Background (Educational / Professional)
- Interests
- Skill Level
- Preferred Category
- Goal
- Number of recommendations required
"""

from typing import Dict, Any, List


def parse_interests(interests_input: Any) -> List[str]:
    """Converts a comma-separated string or list into a clean list of interests."""
    if isinstance(interests_input, list):
        return [str(i).strip() for i in interests_input if str(i).strip()]
    if isinstance(interests_input, str):
        return [item.strip() for item in interests_input.split(",") if item.strip()]
    return []


def validate_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes raw input data from CLI or Web UI.
    Raises ValueError with descriptive messages for invalid fields.
    """
    name = str(data.get("name", "")).strip()
    if not name:
        raise ValueError("Name is required.")

    # Validate age
    raw_age = data.get("age", 20)
    try:
        age = int(raw_age)
        if age < 5 or age > 120:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Age must be a valid integer between 5 and 120.")

    background = str(data.get("background", "")).strip() or "General Education"
    
    interests = parse_interests(data.get("interests", ""))
    if not interests:
        interests = ["General Artificial Intelligence"]

    skill_level = str(data.get("skill_level", "Beginner")).strip().capitalize()
    if skill_level not in ["Beginner", "Intermediate", "Advanced", "Expert"]:
        skill_level = "Beginner"

    preferred_category = str(data.get("preferred_category", "Practical learning")).strip()
    goal = str(data.get("goal", "Learn AI")).strip()
    
    # Validate number of recommendations
    raw_num = data.get("num_recommendations", data.get("no_of_items", 5))
    try:
        num_recommendations = int(raw_num)
        if num_recommendations < 1 or num_recommendations > 20:
            num_recommendations = 5
    except (ValueError, TypeError):
        num_recommendations = 5

    return {
        "name": name,
        "age": age,
        "background": background,
        "interests": interests,
        "skill_level": skill_level,
        "preferred_category": preferred_category,
        "goal": goal,
        "num_recommendations": num_recommendations
    }


def get_user_input_cli(use_defaults: bool = False) -> Dict[str, Any]:
    """
    Interactively prompts the user via CLI.
    Supports pressing Enter to accept sensible default values (matches sample input from PDF).
    """
    print("\n--- Enter User Profile Details ---")
    if use_defaults:
        print("[Using default sample profile: Arun, Computer Science, AI/Python]")
        return validate_user_input({
            "name": "Arun",
            "age": 20,
            "background": "Computer Science",
            "interests": "Artificial Intelligence, Python",
            "skill_level": "Beginner",
            "preferred_category": "Practical learning",
            "goal": "Learn AI",
            "num_recommendations": 5
        })

    def ask(prompt: str, default: str) -> str:
        res = input(f"{prompt} [{default}]: ").strip()
        return res if res else default

    raw = {
        "name": ask("Name", "Arun"),
        "age": ask("Age", "20"),
        "background": ask("Educational/Professional Background", "Computer Science"),
        "interests": ask("Interests (comma separated)", "Artificial Intelligence, Python"),
        "skill_level": ask("Skill Level (Beginner/Intermediate/Advanced)", "Beginner"),
        "preferred_category": ask("Preferred Category/Type", "Practical learning"),
        "goal": ask("Learning Goal", "Learn AI"),
        "num_recommendations": ask("Number of recommendations required", "5")
    }

    return validate_user_input(raw)
