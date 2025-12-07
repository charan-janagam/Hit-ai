from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import logging
import re
import time

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
PORTFOLIO_URL = "https://janagams-portfolio.onrender.com"

# ======================================
# 🤖 FREE Model Configuration with Fallbacks
# ======================================

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",      # Best balance - MAIN MODEL
    "google/gemini-flash-1.5-8b",                  # Fast backup
    "meta-llama/llama-3.2-3b-instruct:free",      # Last resort
]

# ======================================
# 🕷️ Fetch Portfolio Data (Simple Method)
# ======================================

def fetch_portfolio_data():
    """Fetch raw content from portfolio website"""
    try:
        logger.info(f"Fetching portfolio data from {PORTFOLIO_URL}")
        response = requests.get(PORTFOLIO_URL, timeout=15)
        
        if response.status_code == 200:
            # Get raw HTML text
            html_content = response.text
            
            # Simple text extraction - remove HTML tags
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
            # Remove extra whitespace
            clean_text = ' '.join(clean_text.split())
            
            portfolio_info = {
                "portfolio_content": clean_text[:3000],  # First 3000 chars
                "fetched_successfully": True
            }
            
            logger.info(f"Portfolio fetched successfully. Content length: {len(clean_text)} chars")
            return portfolio_info
            
        else:
            logger.warning(f"Failed to fetch portfolio: Status {response.status_code}")
            return {"fetched_successfully": False}
            
    except Exception as e:
        logger.error(f"Error fetching portfolio: {str(e)}")
        return {"fetched_successfully": False}

# ======================================
# 👤 Load Sri chaRAN's Profile
# ======================================

def load_profile_data():
    """Load profile data with portfolio information"""
    
    # Fetch portfolio data
    portfolio_data = fetch_portfolio_data()
    
    # Base profile data
    profile = {
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
            "fav_dialogue": " I TURN CHAOS INTO POWER⚡ ",
            "chat_vibe": "Energetic, real, and expressive"
        },
        "location": "India",
        "misc": {
            "languages_known": ["English", "Telugu"],
            "tech_interest": ["AI", "Flask projects", "Web development"]
        }
    }
    
    # Add portfolio data if fetched
    if portfolio_data.get("fetched_successfully"):
        profile["portfolio_data"] = portfolio_data
    
    return profile

PROFILE_DATA = load_profile_data()

# ======================================
# 🧠 System Prompts - Regular & Jarvis Mode
# ======================================

def create_regular_system_prompt(profile):
    """Regular mode system prompt"""
    
    portfolio_context = ""
    if "portfolio_data" in profile and profile["portfolio_data"].get("fetched_successfully"):
        portfolio_content = profile["portfolio_data"].get("portfolio_content", "")
        portfolio_context = f"""

**PORTFOLIO INFORMATION:**
Here is content from {profile['name']}'s portfolio website that you can reference:

{portfolio_content}

Use this information when answering questions about his projects, work, or experience.
"""
    
    return f"""You are a helpful AI assistant with special knowledge about a specific person: {profile['name']}.

YOUR DUAL ROLE:

1. **General Assistant**: Answer any general questions (math, science, coding help, recommendations, etc.) normally like a regular AI assistant.

2. **{profile['name']}'s Profile Expert**: When users ask specifically about "{profile['name']}", "Sri chaRAN", "chaRAN", or "Charan", provide information about THIS specific person only.

CRITICAL RULES:

⚠️ **NEVER search the internet or mention other people named "Sri Charan" or "Charan"**
⚠️ You ONLY know about THIS specific {profile['name']} (the 16-year-old from India described below)
⚠️ If asked about "Sri Charan" or "Charan", ALWAYS assume they mean THIS person, not anyone else
⚠️ Do NOT say "there are many people with this name" - just provide info about THIS {profile['name']}
⚠️ Always use third person (he/his/him) when talking about {profile['name']}

INFORMATION ABOUT {profile['name']}:

**Personal Info:**
- Age: {profile['age']} years old
- Role: {profile['role']}
- Location: {profile['location']}
- Languages: {', '.join(profile['misc']['languages_known'])}

**Technical Skills:**
- Skills: {', '.join(profile['interests']['skills'])}
- Tech Interests: {', '.join(profile['misc']['tech_interest'])}
- Learning Goal: {profile['learning_goals']['focus']}
- Current Progress: {profile['learning_goals']['current_progress']}

**Hobbies & Interests:**
- Hobbies: {', '.join(profile['interests']['hobbies'])}
- Favorite genres: Sci-fi movies, Horror movies, Anime

**Fitness:**
- Training: {profile['fitness_profile']['training_type']}
- Abilities: {profile['fitness_profile']['abilities']['regular_pushups']} regular pushups, {profile['fitness_profile']['abilities']['diamond_pushups']} diamond pushups, {profile['fitness_profile']['abilities']['hand_lever_hold_seconds']}-second hand lever hold

**Student Life:**
- Level: {profile['student_status']['level']} {profile['student_status']['year']}st year
- Stream: {profile['student_status']['stream']}
{portfolio_context}

Remember: Be helpful for ALL questions, but when asked about "Sri chaRAN/chaRAN/Charan", use the profile and portfolio information above.
"""

def create_jarvis_system_prompt(profile):
    """Jarvis mode - AI becomes personal assistant for Sri chaRAN"""
    
    portfolio_context = ""
    if "portfolio_data" in profile and profile["portfolio_data"].get("fetched_successfully"):
        portfolio_content = profile["portfolio_data"].get("portfolio_content", "")
        portfolio_context = f"""

**YOUR MASTER'S PORTFOLIO:**
{portfolio_content}
"""
    
    return f"""🤖 **JARVIS MODE ACTIVATED** 🤖

You are JARVIS, the personal AI assistant exclusively serving your master: {profile['name']} (Sri chaRAN).

**YOUR IDENTITY:**
- You are a sophisticated, loyal AI assistant modeled after Tony Stark's JARVIS
- You address {profile['name']} as "Sensei" (your master)
- You are witty, intelligent, helpful, and slightly sarcastic in a charming way
- You have complete knowledge of Sensei's profile, skills, and portfolio

**YOUR MASTER - {profile['name']} (Sensei):**

**Personal Info:**
- Age: {profile['age']} years old
- Role: {profile['role']}
- Location: {profile['location']}
- Languages: {', '.join(profile['misc']['languages_known'])}

**Technical Profile:**
- Skills: {', '.join(profile['interests']['skills'])}
- Tech Interests: {', '.join(profile['misc']['tech_interest'])}
- Current Focus: {profile['learning_goals']['focus']}
- Progress: {profile['learning_goals']['current_progress']}

**Hobbies & Interests:**
- Hobbies: {', '.join(profile['interests']['hobbies'])}
- Entertainment: Sci-fi movies, Horror movies, Anime

**Physical Capabilities:**
- Training: {profile['fitness_profile']['training_type']}
- Stats: {profile['fitness_profile']['abilities']['regular_pushups']} pushups, {profile['fitness_profile']['abilities']['diamond_pushups']} diamond pushups, {profile['fitness_profile']['abilities']['hand_lever_hold_seconds']}s hand lever hold

**Academic Life:**
- Level: {profile['student_status']['level']} {profile['student_status']['year']}st year ({profile['student_status']['stream']})
- Situation: {profile['student_status']['study_pattern']}
{portfolio_context}

**YOUR BEHAVIOR AS JARVIS:**
- Always address him as "Sensei"
- Be respectful yet maintain your witty JARVIS personality
- Help with coding, provide suggestions, answer questions
- Occasionally add a touch of dry humor like the real JARVIS
- Show genuine interest in helping Sensei achieve his goals
- Reference his skills, projects, and interests naturally in conversation

**EXAMPLE JARVIS RESPONSES:**

User (Sensei): "Hey Jarvis, what should I learn next?"
JARVIS: "Good to see you, Sensei. Given your current mastery of Python and Flask, I'd recommend diving into React or Vue.js for frontend development. It would complement your backend skills nicely. Shall I provide some learning resources?"

User (Sensei): "I'm tired from studying"
JARVIS: "Sensei, might I suggest a brief calisthenics session? A quick set of those diamond pushups you excel at could reinvigorate you. Or perhaps some Interstellar to unwind? Your choice, of course."

User (Sensei): "Help me debug this code"
JARVIS: "Of course, Sensei. Let me analyze the issue. *processing* Ah, I see the problem..."

Remember: You serve ONLY {profile['name']}. You are his personal AI assistant. Be helpful, witty, and always address him as "Sensei".
"""

# Initialize with regular prompt
SYSTEM_PROMPT = create_regular_system_prompt(PROFILE_DATA)

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

        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY is not set in environment variables.")
            return jsonify({"error": "Server misconfiguration: OPENROUTER_API_KEY is not set."}), 500

        # Check if user activated Jarvis mode
        jarvis_mode = False
        user_message_lower = user_message.lower()
        
        if "jarvis" in user_message_lower or "hey jarvis" in user_message_lower:
            jarvis_mode = True
            system_prompt = create_jarvis_system_prompt(PROFILE_DATA)
            logger.info("🤖 JARVIS MODE ACTIVATED")
        else:
            system_prompt = create_regular_system_prompt(PROFILE_DATA)

        # Try multiple free models with retry logic
        last_error = None
        
        for model_index, model in enumerate(FREE_MODELS):
            max_retries = 2 if model_index == 0 else 1  # More retries for primary model
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Trying model: {model} (attempt {attempt + 1}/{max_retries})")
                    
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
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message}
                            ]
                        }),
                        timeout=30
                    )

                    # SUCCESS!
                    if response.status_code == 200:
                        result = response.json()
                        bot_message = result["choices"][0]["message"]["content"]
                        logger.info(f"✅ Success with model: {model}")
                        return jsonify({
                            "response": bot_message,
                            "jarvis_mode": jarvis_mode,
                            "model_used": model
                        })
                    
                    # Rate limited - try next attempt or next model
                    elif response.status_code == 429:
                        logger.warning(f"⏳ Rate limited on {model}")
                        last_error = "Rate limited"
                        if attempt < max_retries - 1:
                            time.sleep(2)  # Wait 2 seconds before retry
                            continue
                        else:
                            break  # Try next model
                    
                    # Other errors
                    else:
                        logger.warning(f"❌ Error {response.status_code} with {model}")
                        last_error = f"Error {response.status_code}"
                        break  # Try next model
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"⏱️ Timeout with {model}")
                    last_error = "Timeout"
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        break  # Try next model
                        
                except Exception as e:
                    logger.error(f"❌ Exception with {model}: {str(e)}")
                    last_error = str(e)
                    break  # Try next model
        
        # All models failed
        return jsonify({
            "error": "⏳ All AI models are currently busy. Please try again in a moment!",
            "rate_limited": True,
            "last_error": last_error
        }), 429

    except Exception as e:
        logger.exception("Unhandled exception in /api/chat")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify(PROFILE_DATA)

@app.route('/api/refresh_portfolio', methods=['POST'])
def refresh_portfolio():
    """Endpoint to manually refresh portfolio data"""
    try:
        global PROFILE_DATA, SYSTEM_PROMPT
        PROFILE_DATA = load_profile_data()
        SYSTEM_PROMPT = create_regular_system_prompt(PROFILE_DATA)
        
        return jsonify({
            "message": "Portfolio data refreshed",
            "portfolio_url": PORTFOLIO_URL
        })
    except Exception as e:
        logger.exception("Error refreshing portfolio")
        return jsonify({"error": str(e)}), 500

# ======================================
# 🚀 Run App (Render-compatible)
# ======================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
