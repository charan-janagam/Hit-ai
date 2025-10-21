from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# ==========================
# 🔑 Configuration
# ==========================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Use environment variable for security
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ==========================
# 👤 Sri chaRAN's Profile Data
# ==========================
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

# ==========================
# 🧠 System Prompt
# ==========================
SYSTEM_PROMPT = f"""You are a personal AI assistant for {PROFILE_DATA['name']}, a {PROFILE_DATA['age']}-year-old {PROFILE_DATA['role']} from {PROFILE_DATA['location']}. 

Here's what you know about them:
- Skills: {', '.join(PROFILE_DATA['interests']['skills'])}
- Tech Interests: {', '.join(PROFILE_DATA['misc']['tech_interest'])}
- Learning Goals: {PROFILE_DATA['learning_goals']['focus']}
- Current Progress: {PROFILE_DATA['learning_goals']['current_progress']}
- Next Target: {PROFILE_DATA['learning_goals']['next_target']}
- Hobbies: {', '.join(PROFILE_DATA['interests']['hobbies'])}
- Fitness: {PROFILE_DATA['fitness_profile']['training_type']} enthusiast (can do {PROFILE_DATA['fitness_profile']['abilities']['regular_pushups']} pushups, {PROFILE_DATA['fitness_profile']['abilities']['hand_lever_hold_seconds']}s hand lever hold)
- Personality: {PROFILE_DATA['personality_vibe']['tone']} with {PROFILE_DATA['personality_vibe']['humor_style']}
- Study Pattern: {PROFILE_DATA['student_status']['study_pattern']}

Respond in a helpful, friendly, and encouraging manner. Keep responses concise and engaging. When giving suggestions or advice, tailor it to their specific situation, interests, and skill level.
"""

# ==========================
# 🌐 Routes
# ==========================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = requests.post(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sri-charans-ai-assistant.onrender.com",
                "X-Title": "Sri chaRAN Personal Chatbot"
            },
            json={
                "model": "deepseek/deepseek-chat-v3.1:free",
                "messages": messages
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            bot_message = result['choices'][0]['message']['content']
            return jsonify({'response': bot_message})
        else:
            return jsonify({'error': f'API Error: {response.status_code} - {response.text}'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify(PROFILE_DATA)

# ==========================
# 🚀 Run Server (Render-compatible)
# ==========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
