"""
profile_module.py - User Profile Representation and Neatly Formatted Display
Implements Part A (Q2) of Experiment 4.
Builds the user profile and displays the collected information neatly.
"""

from typing import Dict, Any, List


class UserProfile:
    """Represents a structured user profile for personalized recommendation."""

    def __init__(
        self,
        name: str,
        age: int,
        background: str,
        interests: List[str],
        skill_level: str,
        preferred_category: str,
        goal: str,
        num_recommendations: int = 5
    ):
        self.name = name
        self.age = age
        self.background = background
        self.interests = interests if isinstance(interests, list) else [interests]
        self.skill_level = skill_level
        self.preferred_category = preferred_category
        self.goal = goal
        self.num_recommendations = num_recommendations

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Factory method to instantiate a UserProfile from a dictionary."""
        return cls(
            name=data.get("name", "Unknown"),
            age=int(data.get("age", 20)),
            background=data.get("background", "General Education"),
            interests=data.get("interests", ["General Artificial Intelligence"]),
            skill_level=data.get("skill_level", "Beginner"),
            preferred_category=data.get("preferred_category", "Practical learning"),
            goal=data.get("goal", "Learn AI"),
            num_recommendations=int(data.get("num_recommendations", data.get("no_of_items", 5)))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the profile to a serializable dictionary."""
        return {
            "name": self.name,
            "age": self.age,
            "background": self.background,
            "interests": self.interests,
            "skill_level": self.skill_level,
            "preferred_category": self.preferred_category,
            "goal": self.goal,
            "num_recommendations": self.num_recommendations,
            "no_of_items": self.num_recommendations
        }

    def display(self) -> str:
        """
        Formats the profile neatly, matching Q2 Sample Output in LAB QUESTION_4.pdf:
        Name        : Arun
        Age         : 20
        Background  : Computer Science
        Interests   : Artificial Intelligence, Python
        Skill Level : Beginner
        Preference  : Practical learning
        Goal        : Learn AI
        No. of Items: 5
        """
        interests_str = ", ".join(self.interests)
        output = [
            "\n" + "-" * 35,
            "COLLECTED USER PROFILE",
            "-" * 35,
            f"Name         : {self.name}",
            f"Age          : {self.age}",
            f"Background   : {self.background}",
            f"Interests    : {interests_str}",
            f"Skill Level  : {self.skill_level}",
            f"Preference   : {self.preferred_category}",
            f"Goal         : {self.goal}",
            f"No. of Items : {self.num_recommendations}",
            "-" * 35
        ]
        formatted = "\n".join(output)
        return formatted


def build_profile(data: Dict[str, Any]) -> UserProfile:
    """Helper function to create a UserProfile from raw or validated dictionary."""
    return UserProfile.from_dict(data)
