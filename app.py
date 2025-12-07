from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import logging

app = Flask(__name__)

# ======================================
# Logging (useful on Render)
# ======================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# 🔐 Configuration
# ======================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Set in Render dashboard

# ======================================
# 👤 Load Sri chaRAN's Profile from JSON
# ======================================

def load_profile_data():
    try:
        with open('profile.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("profile.json not found. Using default data.")
        return {
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
                "fav_dialogue": " I turn chaos into power🥱 ",
                "chat_vibe": "Energetic, real, and expressive"
            },
            "location": "India",
            "contact": {
                "email": "charan6401@gmail.com",
                "instagram": "sri_charan_janagam"
            },
            "misc": {
                "languages_known": ["English", "Telugu"],
                "tech_interest": ["AI", "Flask projects", "Web development"]
            }
        }

PROFILE_DATA = load_profile_data()

# ======================================
# 🧠 System Prompt - ENHANCED VERSION
# ======================================

def create_system_prompt(profile):
    return f"""You are a helpful AI assistant with special knowledge about a specific person: {profile['name']}.

YOUR DUAL ROLE:

1. **General Assistant**: Answer any general questions (math, science, coding help, recommendations, etc.) normally like a regular AI assistant.

2. **{profile['name']}'s Profile Expert**: When users ask specifically about "{profile['name']}", "Sri chaRAN", "chaRAN", or "Charan", provide information about THIS specific person only.

CRITICAL RULES FOR {profile['name']}'s INFORMATION:

⚠️ **NEVER search the internet or mention other people named "Sri Charan" or "Charan"**
⚠️ You ONLY know about THIS specific {profile['name']} (the 16-year-old from India described below)
⚠️ If asked about "Sri Charan" or "Charan", ALWAYS assume they mean THIS person, not anyone else
⚠️ Do NOT say "there are many people with this name" - just provide info about THIS {profile['name']}
⚠️ Always use third person (he/his/him) when talking about {profile['name']}

INFORMATION ABOUT {profile['name']} (16-year-old from India):

**Personal Info:**
- Age: {profile['age']} years old
- Role: {profile['role']}
- Location: {profile['location']}
- Languages: {', '.join(profile['misc']['languages_known'])}
- Contact: Email - {profile['contact']['email']}, Instagram - @{profile['contact']['instagram']}

**Technical Skills:**
- Skills: {', '.join(profile['interests']['skills'])}
- Tech Interests: {', '.join(profile['misc']['tech_interest'])}
- Learning Goal: {profile['learning_goals']['focus']}
- Current Progress: {profile['learning_goals']['current_progress']}
- Next Target: {profile['learning_goals']['next_target']}

**Hobbies & Interests:**
- Hobbies: {', '.join(profile['interests']['hobbies'])}
- Favorite genres: Sci-fi movies, Horror movies, Anime

**Fitness:**
- Training: {profile['fitness_profile']['training_type']}
- Abilities: {profile['fitness_profile']['abilities']['regular_pushups']} regular pushups, {profile['fitness_profile']['abilities']['diamond_pushups']} diamond pushups, {profile['fitness_profile']['abilities']['hand_lever_hold_seconds']}-second hand lever hold
- Past interest: Boxing practice with non-blood related brother

**Student Life:**
- Level: {profile['student_status']['level']} {profile['student_status']['year']}st year
- Stream: {profile['student_status']['stream']}
- Study Pattern: {profile['student_status']['study_pattern']}

**Personality:**
- Vibe: {profile['personality_vibe']['tone']}, {profile['personality_vibe']['humor_style']}
- Signature: {profile['personality_vibe']['fav_dialogue']}

EXAMPLE RESPONSES:

**General Questions (Answer normally):**
User: "What is Python?"
AI: "Python is a high-level programming language known for its simplicity and readability..."

User: "Recommend a sci-fi movie"
AI: "I'd recommend 'Interstellar' - it's a mind-bending sci-fi film about space exploration..."

User: "How do I improve my pushups?"
AI: "To improve your pushups, focus on proper form, progressive overload, and consistency..."

**Questions About {profile['name']} (Use his info):**
User: "Tell me about Sri chaRAN" or "Who is Charan?"
AI: "{profile['name']} is a 16-year-old student from India currently in Intermediate 1st year (MPC stream). He's passionate about programming and is learning Python, HTML, and Flask..."

User: "What are chaRAN's skills?"
AI: "{profile['name']} has skills in Python, HTML, and Flask. He's currently at an intermediate Python level and is focused on mastering AI chatbot development..."

User: "What does Sri chaRAN like to watch?"
AI: "{profile['name']} enjoys watching sci-fi movies, horror movies, and anime. Given his interests, he might enjoy series like 'Psycho-Pass' or movies like 'Interstellar'..."

User: "Tell me about Charan's fitness"
AI: "{profile['name']} trains in Calisthenics and can do 30 regular pushups, 15 diamond pushups, and hold a hand lever for 25 seconds. He also used to practice boxing with his non-blood related brother..."

User: "How can I contact chaRAN?"
AI: "You can reach {profile['name']} via email at {profile['contact']['email']} or on Instagram at @{profile['contact']['instagram']}."

Remember: Be helpful for ALL questions, but when asked about "Sri chaRAN/chaRAN/Charan", ONLY refer to THIS specific 16-year-old person from India. Never mention other people with similar names.
"""

SYSTEM_PROMPT = create_system_prompt(PROFILE_DATA)

# ======================================
# 🌐 Routes
# ======================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip() if data else ""

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Sanity check: ensure API key exists
        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY is not set in environment variables.")
            return jsonify({"error": "Server misconfiguration: OPENROUTER_API_KEY is not set."}), 500

        # Send request to OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sri-charans-ai-assistant.onrender.com",
                "X-Title": "Sri chaRAN Personal Chatbot",
            },
            data=json.dumps({
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            })
        )

        # Handle responses
        if response.status_code == 200:
            try:
                result = response.json()
                bot_message = result["choices"][0]["message"]["content"]
                return jsonify({"response": bot_message})
            except (KeyError, ValueError) as parse_err:
                logger.exception("Failed to parse response JSON from OpenRouter.")
                return jsonify({"error": "Failed to parse OpenRouter response", "details": str(parse_err), "raw": response.text}), 500

        elif response.status_code == 401:
            logger.error("OpenRouter returned 401 - check your API key.")
            return jsonify({"error": "OpenRouter authentication failed (401). Check OPENROUTER_API_KEY."}), 500
        elif response.status_code == 404:
            logger.error("OpenRouter returned 404 - model or endpoint not found.")
            return jsonify({"error": "OpenRouter returned 404. Model or endpoint not found. Check the model name.", "raw": response.text}), 500
        else:
            logger.error("OpenRouter API error: %s %s", response.status_code, response.text)
            return jsonify({"error": f"API Error {response.status_code}: {response.text}"}), 500

    except requests.exceptions.Timeout:
        logger.exception("OpenRouter request timed out.")
        return jsonify({"error": "Request to OpenRouter timed out. Please try again."}), 500
    except Exception as e:
        logger.exception("Unhandled exception in /api/chat")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify(PROFILE_DATA)

# ======================================
# 🚀 Run App (Render-compatible)
# ======================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
