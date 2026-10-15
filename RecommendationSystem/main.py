"""
main.py - Master Orchestrator for Personalized Recommendation System
Experiment 4 - 24CS2506: Building Applications using GPT-4

Provides:
1. Complete interactive CLI application with continuous interaction loop (Part I Q10)
2. Flask Web API & server serving modern Web UI for all 12 required lab screenshots
"""

import sys
import os
import argparse
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

# Add project root to sys.path so modules can import seamlessly
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR.parent))

from RecommendationSystem.profile_module import UserProfile, build_profile
from RecommendationSystem.input_module import get_user_input_cli, validate_user_input
from RecommendationSystem.preference_module import analyze_preferences, format_preference_display
from RecommendationSystem.prompt_module import construct_initial_prompt
from RecommendationSystem.recommendation_module import generate_recommendations, format_recommendations_display
from RecommendationSystem.ranking_module import rank_recommendations, format_ranking_display
from RecommendationSystem.explanation_module import explain_single_item, format_explanations_display
from RecommendationSystem.feedback_module import refine_recommendations, format_refined_display
from RecommendationSystem.intent_module import detect_intent
from RecommendationSystem.save_module import save_recommendations_to_file, get_default_output_path
from RecommendationSystem.utils import print_banner, get_llm_config

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=str(CURRENT_DIR / "templates"),
    static_folder=str(CURRENT_DIR / "static")
)

# Global in-memory session store for web requests
CURRENT_SESSION = {
    "profile": None,
    "preferences": None,
    "initial_prompt": None,
    "recommendations": [],
    "feedback": None,
    "refined_recommendations": [],
    "saved_path": None
}


# ==========================================
# FLASK WEB ROUTES & API ENDPOINTS
# ==========================================

@app.route("/")
def home():
    """Serves the main web dashboard (Home Screen)."""
    llm_info = get_llm_config()
    return render_template("index.html", llm_info=llm_info)


@app.route("/api/config", methods=["GET"])
def api_config():
    """Returns the current LLM backend information."""
    return jsonify({"status": "success", "config": get_llm_config()})


@app.route("/api/profile", methods=["POST"])
def api_set_profile():
    """Step 1 & 2: Validates input, builds profile, and analyzes preferences."""
    try:
        raw_data = request.json or {}
        validated = validate_user_input(raw_data)
        profile = build_profile(validated)
        preferences = analyze_preferences(profile, use_llm=True)
        initial_prompt = construct_initial_prompt(profile, preferences)

        CURRENT_SESSION["profile"] = profile
        CURRENT_SESSION["preferences"] = preferences
        CURRENT_SESSION["initial_prompt"] = initial_prompt
        CURRENT_SESSION["recommendations"] = []
        CURRENT_SESSION["refined_recommendations"] = []

        return jsonify({
            "status": "success",
            "profile": profile.to_dict(),
            "profile_display": profile.display(),
            "preferences": preferences,
            "preference_display": format_preference_display(preferences),
            "prompt": initial_prompt
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Step 3: Generates and ranks recommendations using LLM."""
    try:
        profile = CURRENT_SESSION.get("profile")
        if not profile:
            return jsonify({"status": "error", "message": "User profile not found. Please create profile first."}), 400

        preferences = CURRENT_SESSION.get("preferences")
        items = generate_recommendations(profile, preferences)
        ranked = rank_recommendations(items, profile=profile, use_sentence_transformers=False)

        CURRENT_SESSION["recommendations"] = ranked

        return jsonify({
            "status": "success",
            "recommendations": ranked,
            "recommendations_display": format_recommendations_display(ranked),
            "ranking_display": format_ranking_display(ranked),
            "explanations_display": format_explanations_display(ranked)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/explain", methods=["POST"])
def api_explain():
    """Generates detailed explanation for a specific item."""
    try:
        profile = CURRENT_SESSION.get("profile")
        data = request.json or {}
        item_name = data.get("item_name")
        item_reason = data.get("reason", "")

        if not profile or not item_name:
            return jsonify({"status": "error", "message": "Missing profile or item name."}), 400

        explanation = explain_single_item(profile, {"name": item_name, "reason": item_reason})
        return jsonify({"status": "success", "item_name": item_name, "explanation": explanation})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """Step 4: Refines recommendations based on user feedback."""
    try:
        profile = CURRENT_SESSION.get("profile")
        recommendations = CURRENT_SESSION.get("recommendations", [])
        data = request.json or {}
        feedback_text = data.get("feedback", "").strip()

        if not profile:
            return jsonify({"status": "error", "message": "No active profile."}), 400
        if not feedback_text:
            return jsonify({"status": "error", "message": "Feedback text cannot be empty."}), 400

        refined = refine_recommendations(profile, recommendations, feedback_text)
        CURRENT_SESSION["feedback"] = feedback_text
        CURRENT_SESSION["refined_recommendations"] = refined

        return jsonify({
            "status": "success",
            "feedback": feedback_text,
            "refined_recommendations": refined,
            "refined_display": format_refined_display(refined, feedback_text)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/intent", methods=["POST"])
def api_intent():
    """Intelligent intent detection endpoint."""
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        result = detect_intent(query)
        return jsonify({"status": "success", "query": query, "intent": result["intent"], "reason": result["reason"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/save", methods=["POST"])
def api_save():
    """Step 5: Persists recommendation report to outputs/recommendations.txt."""
    try:
        profile = CURRENT_SESSION.get("profile")
        ranked = CURRENT_SESSION.get("refined_recommendations") or CURRENT_SESSION.get("recommendations", [])

        if not profile or not ranked:
            return jsonify({"status": "error", "message": "No recommendations available to save."}), 400

        result = save_recommendations_to_file(
            profile=profile,
            ranked_items=ranked,
            preferences=CURRENT_SESSION.get("preferences"),
            feedback=CURRENT_SESSION.get("feedback"),
            refined_items=CURRENT_SESSION.get("refined_recommendations")
        )
        CURRENT_SESSION["saved_path"] = result["file_path"]
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/view-saved", methods=["GET"])
def api_view_saved():
    """Returns the text contents of the saved output file."""
    try:
        target_path = Path(CURRENT_SESSION.get("saved_path") or get_default_output_path())
        if not target_path.exists():
            return jsonify({
                "status": "error",
                "message": "Output file outputs/recommendations.txt has not been generated yet. Please generate recommendations and click Save."
            }), 404
        content = target_path.read_text(encoding="utf-8")
        return jsonify({
            "status": "success",
            "file_path": str(target_path),
            "content": content
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/download-saved", methods=["GET"])
def api_download_saved():
    """Allows browser direct download of outputs/recommendations.txt."""
    try:
        target_path = Path(CURRENT_SESSION.get("saved_path") or get_default_output_path())
        if not target_path.exists():
            # If not yet created on disk, auto-generate if session has recommendations
            profile = CURRENT_SESSION.get("profile")
            ranked = CURRENT_SESSION.get("refined_recommendations") or CURRENT_SESSION.get("recommendations", [])
            if profile and ranked:
                save_recommendations_to_file(
                    profile=profile,
                    ranked_items=ranked,
                    preferences=CURRENT_SESSION.get("preferences"),
                    feedback=CURRENT_SESSION.get("feedback"),
                    refined_items=CURRENT_SESSION.get("refined_recommendations")
                )
            else:
                return jsonify({"status": "error", "message": "No session recommendations to export."}), 400
        return send_file(str(target_path), as_attachment=True, download_name="recommendations.txt")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# INTERACTIVE CLI LOOP (PART I - Q10)
# ==========================================

def run_cli():
    """Runs the terminal application with a continuous interaction loop until Exit."""
    print_banner("PERSONALIZED RECOMMENDATION SYSTEM (GPT-4 / LLM)")
    print("Welcome! Press [Enter] at prompts to accept sample defaults from the lab assignment.")

    # 1. Profile Collection
    profile_data = get_user_input_cli()
    profile = build_profile(profile_data)
    print(profile.display())

    # 2. Preference Analysis
    print("\n[Analyzing user preferences...]")
    preferences = analyze_preferences(profile, use_llm=True)
    print(format_preference_display(preferences))

    # 3. Prompt Construction
    prompt = construct_initial_prompt(profile, preferences)
    print("\n" + "=" * 45)
    print("CONSTRUCTED GPT-4 PROMPT:")
    print("=" * 45)
    print(prompt)
    print("=" * 45)

    # 4. Recommendation Generation & Ranking
    print("\n[Generating personalized recommendations using LLM...]")
    raw_items = generate_recommendations(profile, preferences)
    print(format_recommendations_display(raw_items))

    print("[Ranking recommendations by suitability score...]")
    ranked_items = rank_recommendations(raw_items, profile=profile, use_sentence_transformers=False)
    print(format_ranking_display(ranked_items))

    # 5. Explanations
    print(format_explanations_display(ranked_items))

    current_recommendations = ranked_items
    last_feedback = None
    refined_items = None

    # 6. Continuous Interaction Loop
    print("\n" + "=" * 60)
    print("CONTINUOUS INTERACTION & INTENT MODE (Q10)")
    print("You can enter any natural language query, or choose an intent:")
    print("  - 'Recommend more courses' (GENERATE_RECOMMENDATION)")
    print("  - 'I prefer AI and do not want Web Dev' (REFINE_RECOMMENDATION)")
    print("  - 'Why did you recommend item 1?' (EXPLAIN_RECOMMENDATION)")
    print("  - 'Show my profile' (SHOW_PROFILE)")
    print("  - 'Save recommendations' (SAVE_RECOMMENDATION)")
    print("  - 'Exit' (EXIT)")
    print("=" * 60)

    while True:
        try:
            user_msg = input("\nEnter your command / query: ").strip()
            if not user_msg:
                continue

            intent_result = detect_intent(user_msg)
            detected = intent_result["intent"]
            print(f"-> Detected Intent: {detected} ({intent_result['reason']})")

            if detected == "EXIT":
                print("\nThank you for using the Personalized Recommendation System! Exiting now.\n")
                break

            elif detected == "SHOW_PROFILE":
                print(profile.display())
                print(format_preference_display(preferences))

            elif detected == "GENERATE_RECOMMENDATION":
                print("\n[Generating new recommendation candidates...]")
                raw_items = generate_recommendations(profile, preferences)
                current_recommendations = rank_recommendations(raw_items, profile=profile, use_sentence_transformers=False)
                print(format_ranking_display(current_recommendations))

            elif detected == "REFINE_RECOMMENDATION":
                print(f"\n[Refining recommendations based on: \"{user_msg}\"...]")
                last_feedback = user_msg
                refined_items = refine_recommendations(profile, current_recommendations, user_msg)
                current_recommendations = refined_items
                print(format_refined_display(refined_items, user_msg))

            elif detected == "EXPLAIN_RECOMMENDATION":
                first_item = current_recommendations[0] if current_recommendations else {"name": "Recommended Resource"}
                print(f"\n[Generating detailed explanation for '{first_item.get('name')}'...]")
                explanation = explain_single_item(profile, first_item)
                print(f"\nExplanation:\n{explanation}\n")

            elif detected == "SAVE_RECOMMENDATION":
                save_res = save_recommendations_to_file(
                    profile=profile,
                    ranked_items=current_recommendations,
                    preferences=preferences,
                    feedback=last_feedback,
                    refined_items=refined_items
                )
                print(f"\n[Success] {save_res['message']}!")
                print(f"File location: {save_res['file_path']}")

            else:
                print("Intent processed.")

        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


# ==========================================
# MAIN ENTRYPOINT
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Personalized Recommendation System")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal CLI mode")
    parser.add_argument("--web", action="store_true", help="Launch Flask Web Interface")
    parser.add_argument("--port", type=int, default=5000, help="Port for web server (default: 5000)")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        # Default or --web launches web server with instructions
        port = int(os.getenv("PORT", args.port or 5000))
        print_banner(f"STARTING RECOMMENDATION SYSTEM WEB SERVER ON PORT {port}")
        print(f"Access the Dashboard at: http://127.0.0.1:{port}")
        print("To run in terminal CLI mode instead, execute: python main.py --cli\n")
        app.run(host="0.0.0.0", port=port, debug=False)
