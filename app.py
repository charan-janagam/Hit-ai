from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import logging
import re

app = Flask(__name__)

# ======================================
# Logging
# ======================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# Configuration
# ======================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Set in Render dashboard
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ======================================
# Fallback PROFILE (the JSON you provided)
# ======================================
FALLBACK_PROFILE = {
  "name": "Sri chaRAN",
  "age": 16,
  "role": "Intermediate 1st year student",
  "student_status": {
    "level": "Intermediate",
    "year": 1,
    "stream": "MPC",
    "hostel_life": True,
    "study_pattern": "Can only practice programming during holidays or vacations when at home"
  },
  "interests": {
    "main_focus": "Developing programming and coding skills",
    "skills": ["Python", "HTML", "Flask"],
    "hobbies": ["Sketching", "Watching sci-fi movies", "Horror movies", "Anime"]
  },
  "fitness_profile": {
    "training_type": "Calisthenics",
    "abilities": {
      "hand_lever_hold_seconds": 25,
      "regular_pushups": 30,
      "diamond_pushups": 15
    },
    "past_interest": "Boxing practice with non-blood related brother"
  },
  "learning_goals": {
    "focus": "Master Python and learn AI chatbot development",
    "current_progress": "Intermediate Python learner",
    "next_target": "Understand Flask deeply and apply in projects"
  },
  "personality_vibe": {
    "tone": "Chill, confident, and witty",
    "humor_style": "Playful with smooth rizz and light roast energy",
    "fav_dialogue": "i turn chaos into power!",
    "chat_vibe": "Energetic, real, and expressive"
  },
  "location": "India",
  "misc": {
    "languages_known": ["English", "Telugu"],
    "tech_interest": ["AI", "Flask projects", "Web development"]
  }
}

# ======================================
# Load profile.json if present (authoritative), else use FALLBACK_PROFILE
# ======================================
def load_profile_data():
    try:
        with open('profile.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info("Loaded profile.json")
            return data
    except FileNotFoundError:
        logger.warning("profile.json not found. Using provided fallback profile.")
        return FALLBACK_PROFILE

PROFILE_DATA = load_profile_data()

# ======================================
# Profanity / slur filter (simple)
# ======================================
BANNED_WORDS = {
    "nigga", "nigger", "chink", "kike", "fag", "faggot", "cunt"
}

def contains_banned_word(text):
    if not text:
        return False
    words = re.findall(r"\w+", text.lower())
    return any(w in BANNED_WORDS for w in words)

# ======================================
# System prompt: universal assistant + strict profile rules
# ======================================
def create_system_prompt(profile):
    # small profile snippet for model reference (only to be used when user asks about the profile)
    profile_snippet = {
        "name": profile.get("name"),
        "age": profile.get("age"),
        "role": profile.get("role"),
        "location": profile.get("location"),
        "skills": profile.get("interests", {}).get("skills", []),
        "learning_goal": profile.get("learning_goals", {}).get("focus")
    }
    return f"""
You are a universal AI assistant. Answer general questions on any topic (coding, movies, fitness, learning advice, etc.) clearly and helpfully.

IMPORTANT RULES ABOUT THE SAVED PROFILE:
- The assistant has an optional saved profile for one person: {profile.get('name')}. The profile data (authoritative) is:
{json.dumps(profile_snippet, ensure_ascii=False)}

- You MUST ONLY use that saved profile when the user explicitly asks about "Sri chaRAN", "chaRAN", "Charan", or uses clear context referring to that person.
- Do NOT invent web facts, news, historical events, or any external claims about that person beyond the saved profile.
- If the user seems to mean some other real-world person with the same name, ask for clarification: "Do you mean the saved profile for Sri chaRAN, or a different person with the same name? Please provide context."

- For all other queries (not explicitly about Sri chaRAN), behave like a normal universal assistant.

- If the user uses offensive slurs or hate speech, refuse politely and ask them to rephrase.

Be helpful, concise, and do not make assumptions about the user's personal life unless they explicitly provide details.
"""

SYSTEM_PROMPT = create_system_prompt(PROFILE_DATA)

# ======================================
# Helper: Detect explicit ask about Sri chaRAN
# ======================================
def user_is_asking_about_profile(user_message):
    if not user_message:
        return False
    msg = user_message.lower()
    # check for name variants
    if "sri charan" in msg or "sri charan" in msg.replace(" ", "") or "charan" in msg:
        return True
    # also allow "chaRAN" typed uppercase variants via case-insensitive check above
    return False

# ======================================
# Helper: Provide deterministic profile answers
# (only uses PROFILE_DATA)
# ======================================
def build_profile_answer_for_query(user_message, profile):
    name = profile.get("name", "Sri chaRAN")
    msg = user_message.lower()

    if "skill" in msg or "skills" in msg or "projects" in msg:
        skills = profile.get("interests", {}).get("skills", [])
        return f"{name} has skills in {', '.join(skills)}."

    if "learn" in msg or "next" in msg or "what should" in msg:
        next_target = profile.get("learning_goals", {}).get("next_target") or profile.get("learning_goals", {}).get("focus")
        return f"Based on the profile, {name} should focus next on: {next_target}."

    if "fitness" in msg or "pushup" in msg or "calisthenics" in msg:
        f = profile.get("fitness_profile", {})
        abilities = f.get("abilities", {})
        return (f"{name} trains in {f.get('training_type','calisthenics')}. "
                f"He can do {abilities.get('regular_pushups','N/A')} regular pushups, "
                f"{abilities.get('diamond_pushups','N/A')} diamond pushups, and a {abilities.get('hand_lever_hold_seconds','N/A')}s hand lever hold.")

    if "age" in msg or "how old" in msg:
        return f"{name} is {profile.get('age')} years old."

    # fallback short bio
    return (f"{name}: {profile.get('role')}. "
            f"Skills: {', '.join(profile.get('interests', {}).get('skills', []))}. "
            f"Location: {profile.get('location', 'N/A')}.")

# ======================================
# Routes
# ======================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        req = request.get_json(silent=True) or {}
        user_message = (req.get("message") or "").strip()

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # profanity check
        if contains_banned_word(user_message):
            return jsonify({"response": "I can't respond to offensive or hateful language. Please rephrase your question."}), 200

        # If user explicitly asks about Sri chaRAN, answer from PROFILE_DATA deterministically
        if user_is_asking_about_profile(user_message):
            answer = build_profile_answer_for_query(user_message, PROFILE_DATA)
            return jsonify({"response": answer}), 200

        # Otherwise call OpenRouter (universal assistant)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        # sanity check: ensure API key exists
        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY is not set in environment variables.")
            return jsonify({"error": "Server misconfiguration: OPENROUTER_API_KEY is not set."}), 500

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sri-charans-ai-assistant.onrender.com",
            "X-Title": "Sri chaRAN Personal Chatbot"
        }

        payload = {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b",
            "messages": messages
        }

        # Use data=json.dumps(...) per your request
        resp = requests.post(url=API_URL, headers=headers, data=json.dumps(payload), timeout=30)

        # Handle responses
        if resp.status_code == 200:
            try:
                result = resp.json()
                bot_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                # Safety: if the model returns suspicious external claims about "charan", block and ask to clarify
                lower_out = (bot_message or "").lower()
                if "charan" in lower_out and any(tok in lower_out for tok in ["died", "death", "tragic", "2009", "may", "killed"]):
                    logger.info("Suppressed potential external/historical claim about Charan.")
                    return jsonify({
                        "response": "I may be mixing up different people with the same name. I only have a saved profile for Sri chaRAN. Do you mean the saved profile or a different person? If you mean the saved profile, ask about skills, fitness, or learning goals."
                    }), 200

                return jsonify({"response": bot_message}), 200
            except ValueError:
                logger.exception("Failed to parse OpenRouter JSON")
                return jsonify({"error": "Failed to parse OpenRouter response", "raw": resp.text}), 500

        elif resp.status_code == 401:
            logger.error("OpenRouter returned 401 - check your API key.")
            return jsonify({"error": "OpenRouter authentication failed (401). Check OPENROUTER_API_KEY."}), 500
        else:
            logger.error("OpenRouter API error: %s %s", resp.status_code, resp.text)
            return jsonify({"error": f"API Error {resp.status_code}: {resp.text}"}), 500

    except requests.exceptions.Timeout:
        logger.exception("OpenRouter request timed out.")
        return jsonify({"error": "Request to OpenRouter timed out. Please try again."}), 500
    except Exception as e:
        logger.exception("Unhandled exception in /api/chat")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    # return the profile for the UI
    return jsonify(PROFILE_DATA)

# ======================================
# Run app (Render-compatible)
# ======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
