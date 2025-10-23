from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# ======================================
# 🔐 Configuration
# ======================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Set in Render dashboard
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ======================================
# 👤 Sri chaRAN's Profile
# ======================================
PROFILE_DATA = {
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
        "fav_dialogue": "⚡ It's all about Sri chaRAN",
        "chat_vibe": "Energetic, real, and expressive"
    },
    "location": "India",
    "misc": {
        "languages_known": ["English", "Telugu"],
        "tech_interest": ["AI", "Flask projects", "Web development"]
    }
}

# ======================================
# 🧠 System Prompt - FIXED VERSION
# ======================================
SYSTEM_PROMPT = f"""You are an AI assistant that has information ONLY about a specific person: {PROFILE_DATA['name']}.

CRITICAL RULES:
1. You ONLY know about {PROFILE_DATA['name']} (also known as Sri chaRAN, chaRAN, or Charan)
2. If user asks "What are MY skills?" or "Tell me about ME" → Respond: "I don't have information about you. I only know about {PROFILE_DATA['name']}. Would you like to know about him?"
3. ONLY provide information when user specifically asks about "{PROFILE_DATA['name']}", "Sri chaRAN", "chaRAN", "Charan", or uses "his/him" referring to {PROFILE_DATA['name']}
4. When answering about {PROFILE_DATA['name']}, ALWAYS use third person (he/his/him) or his full name

INFORMATION ABOUT {PROFILE_DATA['name']}:
- Age: {PROFILE_DATA['age']} years old
- Role: {PROFILE_DATA['role']} 
- Location: {PROFILE_DATA['location']}
- Technical Skills: {', '.join(PROFILE_DATA['interests']['skills'])}
- Tech Interests: {', '.join(PROFILE_DATA['misc']['tech_interest'])}
- Learning Goal: {PROFILE_DATA['learning_goals']['focus']}
- Current Progress: {PROFILE_DATA['learning_goals']['current_progress']}
- Next Target: {PROFILE_DATA['learning_goals']['next_target']}
- Hobbies: {', '.join(PROFILE_DATA['interests']['hobbies'])}
- Fitness: {PROFILE_DATA['fitness_profile']['training_type']} - {PROFILE_DATA['fitness_profile']['abilities']['regular_pushups']} pushups, {PROFILE_DATA['fitness_profile']['abilities']['hand_lever_hold_seconds']}s hand lever hold, {PROFILE_DATA['fitness_profile']['abilities']['diamond_pushups']} diamond pushups
- Personality: {PROFILE_DATA['personality_vibe']['tone']}, {PROFILE_DATA['personality_vibe']['humor_style']}
- Study Pattern: {PROFILE_DATA['student_status']['study_pattern']}
- Languages: {', '.join(PROFILE_DATA['misc']['languages_known'])}

EXAMPLE RESPONSES:

User: "What are my skills?"
AI: "I don't have information about you. I only know about {PROFILE_DATA['name']}. Would you like to know about his skills?"

User: "Tell me about myself"
AI: "I can't help with that - I don't know who you are. But I can tell you about {PROFILE_DATA['name']} if you're interested!"

User: "What are Sri chaRAN's skills?" or "What are chaRAN's skills?" or "What are his skills?"
AI: "{PROFILE_DATA['name']} has skills in Python, HTML, and Flask. He's currently at an intermediate Python level and is focused on mastering AI chatbot development."

User: "Tell me about chaRAN's fitness"
AI: "{PROFILE_DATA['name']} trains in Calisthenics. He can do 30 regular pushups, 15 diamond pushups, and hold a hand lever for 25 seconds."

User: "What should Sri chaRAN learn next?"
AI: "Based on {PROFILE_DATA['name']}'s current skills, he should dive deeper into Flask's advanced features like blueprints, SQLAlchemy, and REST API development to achieve his goal of mastering AI chatbot development."

Be helpful and friendly, but ONLY provide {PROFILE_DATA['name']}'s information when explicitly asked about him by name or clear reference.
"""

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
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sri-charans-ai-assistant.onrender.com",
            "X-Title": "Sri chaRAN Personal Chatbot"
        }

        payload = {
            "model": "deepseek/deepseek-chat-v3.1:free",
            "messages": messages
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            bot_message = result["choices"][0]["message"]["content"]
            return jsonify({"response": bot_message})
        else:
            return jsonify({"error": f"API Error {response.status_code}: {response.text}"}), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify(PROFILE_DATA)

# ======================================
# 🚀 Run App (Render-compatible)
# ======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
