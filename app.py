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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ======================================
# 👤 Optional Profile Loading
# (Still available but not forced on chatbot responses)
# ======================================
def load_profile_data():
    try:
        with open('profile.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("profile.json not found. Continuing without it.")
        return {}

PROFILE_DATA = load_profile_data()

# ======================================
# 🧠 Universal System Prompt
# ======================================
def create_system_prompt():
    return """
You are a universal AI assistant designed to answer ANY type of question.

RULES:
- Provide general knowledge unless the user specifically asks about "Sri chaRAN".
- Do NOT tell the user that you only know about one person.
- If the user asks about themselves, answer normally — do not refuse.
- If the user asks about Sri chaRAN, you may use the profile.json data ONLY if relevant.
- Be friendly, smart, helpful, and clear.

Your job is to:
• Answer questions on ANY topic (movies, coding, science, fitness, advice, etc.)
• Provide recommendations when asked
• Help users learn new skills
• Solve problems creatively
• Assist without limiting responses to one person

Behave like a normal intelligent AI assistant.
"""

SYSTEM_PROMPT = create_system_prompt()

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
            "X-Title": "Universal AI Assistant"
        }

        payload = {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b",
            "messages": messages
        }

        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY missing.")
            return jsonify({"error": "Missing API key."}), 500

        response = requests.post(
            API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            bot_message = result["choices"][0]["message"]["content"]
            return jsonify({"response": bot_message})

        # Common errors
        logger.error(f"API Error {response.status_code}: {response.text}")
        return jsonify({"error": response.text}), 500

    except Exception as e:
        logger.exception("Server error:")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify(PROFILE_DATA)


# ======================================
# 🚀 Run App
# ======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
