from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import logging
import re

app = Flask(__name__)

# ======================================
# Logging (useful on Render)
# ======================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# Configuration
# ======================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ======================================
# Load profile.json (optional but authoritative for "Sri chaRAN")
# ======================================
def load_profile_data():
    try:
        with open('profile.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("profile.json not found. Using fallback minimal profile.")
        # Minimal fallback - still used only when user explicitly asks about Sri chaRAN
        return {
            "name": "Sri chaRAN",
            "age": 16,
            "role": "Intermediate 1st year student",
            "location": "India",
            "interests": {"skills": ["Python", "HTML", "Flask"], "hobbies": []},
            "learning_goals": {"focus": "Master Python and learn AI chatbot development", "current_progress": "Intermediate Python learner", "next_target": "Understand Flask deeply"},
            "fitness_profile": {"training_type": "Calisthenics", "abilities": {"regular_pushups": 30, "diamond_pushups": 15, "hand_lever_hold_seconds": 25}}
        }

PROFILE_DATA = load_profile_data()

# ======================================
# Simple profanity / slur filter
# ======================================
BANNED_WORDS = {
    # Add more forms as you need; keep lowercase
    "nigga", "nigger", "chink", "kike", "fag", "faggot", "cunt"  # example — expand as desired
}

def contains_banned_word(text):
    if not text:
        return False
    text_lower = text.lower()
    # simple token-based check to catch common variants
    words = re.findall(r"\w+", text_lower)
    return any(w in BANNED_WORDS for w in words)

# ======================================
# System prompt: universal + strict Sri chaRAN rules
# ======================================
def create_system_prompt(profile):
    # Serialize profile concisely so model can reference when explicitly asked.
    profile_snippet = json.dumps({
        "name": profile.get("name"),
        "age": profile.get("age"),
        "role": profile.get("role"),
        "location": profile.get("location"),
        "skills": profile.get("interests", {}).get("skills", []),
        "learning_goal": profile.get("learning_goals", {}).get("focus"),
        "fitness": profile.get("fitness_profile", {})
    }, ensure_ascii=False)

    return f"""
You are a universal AI assistant. Answer general questions on any topic (coding, movies, fitness, life advice, etc.) clearly and helpfully.

STRICT RULES about "Sri chaRAN" (the user-provided profile):
1. If the user explicitly asks about "Sri chaRAN", "chaRAN", "Charan", or uses clear pronouns referring to that person (e.g., "his skills" and the conversation context shows they mean Sri chaRAN), you MUST ONLY use the following profile data to answer. Do NOT search the web, and DO NOT invent facts about any "Sri Charan" not present in the profile.
Profile (authoritative): {profile_snippet}

2. If the user asks about a person with the same name but appears to mean some other real-world person (for example: news, historical events, or unspecified "Sri Charan"), ask a clarifying question: "Do you mean the profile named Sri chaRAN saved in this assistant, or a different person with the same name? If it's a different person, please provide more context."

3. Never claim to know web facts about "Sri chaRAN" that are not in the profile.json. If the user requests external/historical info that isn't in profile.json, say: "I don't have web or historical data about that person — I only have the saved profile data. Would you like me to use that?"

4. For all other questions (not about Sri chaRAN), behave like a normal universal assistant and answer normally.

5. If the user message contains insulting slurs or hate speech, do NOT forward those words to the backend model. Instead respond politely: "I can't respond to offensive or hateful language. Please rephrase your question."

Be concise and helpful.
"""

SYSTEM_PROMPT = create_system_prompt(PROFILE_DATA)

# ======================================
# Helpers for crafting profile-based replies
# ======================================
def build_profile_answer_for_query(user_message, profile):
    # This function makes short, predictable profile-based responses using only PROFILE_DATA.
    name = profile.get("name", "Sri chaRAN")
    # Normalize variants
    msg_lower = user_message.lower()
    if "skill" in msg_lower or "skills" in msg_lower:
        skills = profile.get("interests", {}).get("skills", [])
        if skills:
            return f"{name} has skills in {', '.join(skills)}."
        else:
            return f"{name}'s skill information isn't available in the profile."
    if "learn" in msg_lower or "next" in msg_lower:
        next_target = profile.get("learning_goals", {}).get("next_target")
        if next_target:
            return f"Based on the profile, {name} should focus next on: {next_target}."
        else:
            return f"The profile doesn't specify a clear next learning target for {name}."
    if "fitness" in msg_lower or "pushup" in msg_lower or "calisthenics" in msg_lower:
        f = profile.get("fitness_profile", {})
        abilities = f.get("abilities", {})
        return (f"{name} trains in {f.get('training_type','calisthenics')}. "
                f"He can do {abilities.get('regular_pushups','N/A')} regular pushups, "
                f"{abilities.get('diamond_pushups','N/A')} diamond pushups, and hold a hand lever for "
                f"{abilities.get('hand_lever_hold_seconds','N/A')} seconds.")
    # default short bio
    return (f"{name}: {profile.get('role','')}, located in {profile.get('location','')}. "
            f"Learning goal: {profile.get('learning_goals',{}).get('focus','N/A')}.")

def user_is_asking_about_profile(user_message):
    if not user_message:
        return False
    # crude check: name variants or possessive pronoun with charan
    msg = user_message.lower()
    name_variants = ["sri charan", "sri charan", "sri cha rAN", "sri cha rAN".lower()]
    # simpler: check for 'charan' or 'chaRAN' in message
    if "charan" in msg or "cha" in msg and "ran" in msg:
        return True
    # pronoun + 'his' + 'skills' ambiguous, so we won't assume unless name present
    return False

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

        # profanity / slur check
        if contains_banned_word(user_message):
            return jsonify({
                "response": "I can't respond to offensive or hateful language. Please rephrase your question."
            }), 200

        # If user explicitly mentions Sri chaRAN (profile), use only local profile data
        if user_is_asking_about_profile(user_message):
            # If user clearly asked about profile, construct deterministic reply
            answer = build_profile_answer_for_query(user_message, PROFILE_DATA)
            return jsonify({"response": answer}), 200

        # Otherwise proceed to send to OpenRouter model (universal assistant)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        # Ensure API key exists
        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY is not set.")
            return jsonify({"error": "Server misconfiguration: OPENROUTER_API_KEY is not set."}), 500

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sri-charans-ai-assistant.onrender.com",
            "X-Title": "Universal AI Assistant"
        }

        payload = {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b",
            "messages": messages
        }

        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        # handle response
        if resp.status_code == 200:
            try:
                result = resp.json()
                bot_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                # Extra safety: if the model tries to assert web facts about "Sri Charan" that aren't in profile, avoid returning them.
                # Quick heuristic: if message mentions "May" and "2009" or "died" etc and contains 'charan' - block it and ask clarification.
                lower_out = (bot_message or "").lower()
                if "charan" in lower_out and any(tok in lower_out for tok in ["died", "death", "tragic", "2009", "2008", "may"]):
                    logger.info("Model returned external/historical claim about charan; suppressing and asking for clarification.")
                    return jsonify({
                        "response": "I may be mixing up different people with the same name. I only have a saved profile for Sri chaRAN. Do you mean the saved profile or a different person? If you mean the saved profile, ask about specific skills, fitness, or learning goals."
                    }), 200

                return jsonify({"response": bot_message}), 200
            except ValueError:
                logger.exception("Failed to parse OpenRouter JSON")
                return jsonify({"error": "Failed to parse OpenRouter response", "raw": resp.text}), 500

        elif resp.status_code == 401:
            logger.error("OpenRouter auth failed (401).")
            return jsonify({"error": "OpenRouter authentication failed (401)."}), 500
        else:
            logger.error("OpenRouter error %s: %s", resp.status_code, resp.text)
            return jsonify({"error": f"OpenRouter API error {resp.status_code}", "raw": resp.text}), 500

    except requests.exceptions.Timeout:
        logger.exception("OpenRouter request timed out.")
        return jsonify({"error": "Request to OpenRouter timed out. Please try again."}), 500
    except Exception as e:
        logger.exception("Unhandled exception in /api/chat")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/api/profile', methods=['GET'])
def get_profile():
    # return the profile (for your UI). This is the authoritative data for Sri chaRAN.
    return jsonify(PROFILE_DATA)

# ======================================
# Run app
# ======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
