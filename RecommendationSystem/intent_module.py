"""
intent_module.py - Intelligent Intent Detection
Implements Part H (Q9) of Experiment 4.
Uses LLM to classify user inputs into one of the 6 canonical intents:
- GENERATE_RECOMMENDATION
- REFINE_RECOMMENDATION
- SHOW_PROFILE
- EXPLAIN_RECOMMENDATION
- SAVE_RECOMMENDATION
- EXIT
"""

from typing import Dict, Any
from .utils import call_llm, clean_json_response

VALID_INTENTS = [
    "GENERATE_RECOMMENDATION",
    "REFINE_RECOMMENDATION",
    "SHOW_PROFILE",
    "EXPLAIN_RECOMMENDATION",
    "SAVE_RECOMMENDATION",
    "EXIT"
]


def detect_intent_rule_based(user_text: str) -> str:
    """Fast fallback rule-based intent detector for standard keywords."""
    lower = user_text.strip().lower()
    if lower in ["exit", "quit", "bye", "q", "stop", "close"]:
        return "EXIT"
    if any(k in lower for k in ["save", "export", "download", "write to file"]):
        return "SAVE_RECOMMENDATION"
    if any(k in lower for k in ["show profile", "view profile", "my profile", "display profile"]):
        return "SHOW_PROFILE"
    if any(k in lower for k in ["why did you recommend", "explain", "why this", "tell me why"]):
        return "EXPLAIN_RECOMMENDATION"
    if any(k in lower for k in ["refine", "more beginner", "don't want", "do not want", "prefer", "filter", "exclude"]):
        return "REFINE_RECOMMENDATION"
    if any(k in lower for k in ["recommend", "generate", "suggest", "give me recommendations", "courses"]):
        return "GENERATE_RECOMMENDATION"
    return "REFINE_RECOMMENDATION"


def detect_intent(user_input: str, conversation_context: str = "") -> Dict[str, Any]:
    """
    Classifies user query into one of the 6 canonical intents using LLM.
    Falls back to rule-based classification if network/parsing error occurs.
    """
    clean_input = user_input.strip()
    if not clean_input:
        return {"intent": "GENERATE_RECOMMENDATION", "reason": "Empty input, default to recommendation generation."}

    # Fast check for simple exit
    if clean_input.lower() in ["exit", "quit", "q"]:
        return {"intent": "EXIT", "reason": "User requested termination."}

    system_prompt = (
        "You are an intent classification engine for a personalized recommendation system. "
        "Classify the user's input into EXACTLY ONE of the following valid intent labels:\n"
        "- GENERATE_RECOMMENDATION: User wants new or initial recommendations (e.g. 'Recommend some AI courses')\n"
        "- REFINE_RECOMMENDATION: User wants to adjust, filter, exclude, or customize current recommendations (e.g. 'Give me more beginner-friendly options', 'I do not want web dev')\n"
        "- SHOW_PROFILE: User wants to view their current profile or preferences (e.g. 'Show my profile')\n"
        "- EXPLAIN_RECOMMENDATION: User is asking why an item was recommended (e.g. 'Why did you recommend this course?')\n"
        "- SAVE_RECOMMENDATION: User wants to save or download recommendations to file (e.g. 'Save these recommendations')\n"
        "- EXIT: User wants to end the session (e.g. 'Exit', 'Quit', 'Goodbye')\n\n"
        "Return ONLY a JSON object: {\"intent\": \"<INTENT_LABEL>\", \"reason\": \"<Brief justification>\"}"
    )

    prompt = f"User Input: \"{clean_input}\""
    if conversation_context:
        prompt += f"\nContext: {conversation_context}"

    try:
        response_text = call_llm(prompt, system_prompt=system_prompt, temperature=0.1)
        data = clean_json_response(response_text)
        intent = data.get("intent", "").strip().upper()
        if intent in VALID_INTENTS:
            return {"intent": intent, "reason": data.get("reason", "Detected by LLM")}
    except Exception as e:
        print(f"[Notice] LLM intent detection fallback ({e})")

    # Fallback to rule-based
    fallback_intent = detect_intent_rule_based(clean_input)
    return {"intent": fallback_intent, "reason": "Rule-based pattern matching fallback."}
