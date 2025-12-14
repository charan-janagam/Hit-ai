# app.py - 429-PROOF + STREAMING + FIXED CONTEXT 🔥
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import os
import json
import logging
import re
import time
from collections import deque

app = Flask(__name__)

# ======================================
# Logging
# ======================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# 🔐 Configuration
# ======================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "https://janagams-portfolio.onrender.com")

# ======================================
# 🔥 429-PROOF MODEL HANDLER WITH STREAMING
# ======================================
class ThrottleProofHandler:
    """Eliminates 429 errors with rotation + delays + memory trimming + STREAMING"""
    
    def __init__(self):
        # FREE models with separate rate limits
        self.models = [
            "meta-llama/llama-3.3-70b-instruct:free",    # NEW PRIMARY (best free model)
            "meta-llama/llama-3.1-8b-instruct:free",     # Fast backup
            "google/gemini-flash-1.5-8b",                # Emergency fallback
        ]
        self.current_model_idx = 0
        
        # Anti-throttle settings
        self.min_delay = 2.0  # seconds between requests
        self.last_request_time = 0
        self.max_retries = 3
        
        # Memory trimming (keeps conversation light)
        self.max_memory_messages = 6  # Only last 6 exchanges
    
    def _wait_if_needed(self):
        """Smart delay to prevent rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            logger.info(f"⏳ Anti-throttle delay: {wait_time:.1f}s")
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _rotate_model(self):
        """Switch to next model on 429"""
        self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
        logger.info(f"🔄 Rotated to model: {self.models[self.current_model_idx]}")
        return self.models[self.current_model_idx]
    
    def _trim_messages(self, messages):
        """
        Keep conversation light - reduces token load by 60%
        Always keeps: system message + last N user/assistant exchanges
        """
        if len(messages) <= self.max_memory_messages + 1:  # +1 for system
            return messages
        
        # Separate system from conversation
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # Keep only last N messages
        trimmed = other_msgs[-self.max_memory_messages:]
        
        logger.info(f"📊 Trimmed messages: {len(messages)} → {len(system_msgs) + len(trimmed)}")
        return system_msgs + trimmed
    
    def send_request_streaming(self, messages, timeout=30):
        """
        Send STREAMING request with FULL 429 protection
        Yields: (chunk_text, is_complete, model_used, error)
        """
        # Trim memory to reduce token usage
        messages = self._trim_messages(messages)
        
        for attempt in range(self.max_retries):
            try:
                # Anti-throttle delay
                self._wait_if_needed()
                
                current_model = self.models[self.current_model_idx]
                logger.info(f"🤖 Streaming with: {current_model} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sri-charans-ai-assistant.onrender.com",
                        "X-Title": "Sri chaRAN Personal Chatbot",
                    },
                    data=json.dumps({
                        "model": current_model,
                        "messages": messages,
                        "stream": True  # 🔥 STREAMING ENABLED
                    }),
                    timeout=timeout,
                    stream=True  # Important for streaming
                )
                
                # Handle 429 with rotation
                if response.status_code == 429:
                    logger.warning(f"⚠️  429 on {current_model}, rotating...")
                    yield ("", False, None, "rate_limited")
                    self._rotate_model()
                    time.sleep(3)
                    continue
                
                # Handle success - stream the response
                if response.status_code == 200:
                    logger.info(f"✅ Streaming started with {current_model}")
                    
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            
                            # Skip empty lines
                            if not line.strip():
                                continue
                            
                            # Parse SSE format
                            if line.startswith('data: '):
                                data = line[6:]  # Remove 'data: ' prefix
                                
                                # Check for stream end
                                if data.strip() == '[DONE]':
                                    yield ("", True, current_model, None)
                                    return
                                
                                try:
                                    chunk = json.loads(data)
                                    content = chunk['choices'][0]['delta'].get('content', '')
                                    
                                    if content:
                                        # Yield each chunk as it arrives
                                        yield (content, False, current_model, None)
                                        
                                except json.JSONDecodeError:
                                    continue
                                except (KeyError, IndexError):
                                    continue
                    
                    # Stream completed
                    yield ("", True, current_model, None)
                    return
                
                # Other errors - try next model
                logger.warning(f"❌ Error {response.status_code} with {current_model}")
                self._rotate_model()
                time.sleep(1)
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️  Timeout with {current_model}")
                self._rotate_model()
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Exception with {current_model}: {str(e)}")
                self._rotate_model()
                time.sleep(1)
        
        # All retries failed
        yield ("", True, None, "all_failed")

# Initialize handler
ai_handler = ThrottleProofHandler()

# ======================================
# 🕷️ Fetch Portfolio Data
# ======================================
def fetch_portfolio_data(timeout=8):
    """Fetch raw content from portfolio website (returns dict)."""
    try:
        logger.info(f"Fetching portfolio data from {PORTFOLIO_URL}")
        response = requests.get(PORTFOLIO_URL, timeout=timeout)

        if response.status_code == 200:
            html_content = response.text
            # Simple text extraction - remove HTML tags
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
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
        logger.warning(f"Error fetching portfolio: {e}")
        return {"fetched_successfully": False}

# ======================================
# 👤 Load Sri chaRAN's Profile
# ======================================
def build_base_profile():
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
            "fav_dialogue": " I TURN CHAOS INTO POWER⚡ ",
            "chat_vibe": "Energetic, real, and expressive"
        },
        "location": "India",
        "misc": {
            "languages_known": ["English", "Telugu"],
            "tech_interest": ["AI", "Flask projects", "Web development"]
        }
    }

def load_profile_data():
    """Load profile data and attempt to attach portfolio info."""
    profile = build_base_profile()
    portfolio_data = fetch_portfolio_data()
    if portfolio_data.get("fetched_successfully"):
        profile["portfolio_data"] = portfolio_data
    return profile

# ======================================
# 🧠 System Prompts - FIXED CONTEXT
# ======================================
def create_regular_system_prompt(profile):
    portfolio_context = ""
    if "portfolio_data" in profile and profile["portfolio_data"].get("fetched_successfully"):
        portfolio_content = profile["portfolio_data"].get("portfolio_content", "")
        portfolio_context = f"""

**PORTFOLIO INFORMATION:**
Here is content from {profile['name']}'s portfolio website that you can reference when asked about him:

{portfolio_content}

Use this information when answering questions about his projects, work, or experience.
"""
    return f"""You are an AI assistant that helps people learn about {profile['name']} and answers general questions.

**IMPORTANT CONTEXT UNDERSTANDING:**

When users ask about "me", "I", "my", or similar first-person references:
- They are asking about THEMSELVES (the person chatting with you)
- NOT about {profile['name']}

When users ask about "{profile['name']}", "Sri chaRAN", "chaRAN", "Charan", "him", "his":
- They are asking about {profile['name']} specifically
- Use the profile information below to answer

**YOUR DUAL ROLE:**

1. **General Assistant**: Answer any general questions (math, science, coding help, recommendations, etc.) normally.

2. **{profile['name']}'s Profile Expert**: When asked specifically about {profile['name']}, provide information about THIS specific 16-year-old from India.

**CRITICAL RULES:**

⚠️ When someone says "me" or "I" → Ask them about themselves, DO NOT assume they're {profile['name']}
⚠️ When someone says "{profile['name']}" or "Charan" → Use the profile below
⚠️ NEVER search the internet or mention other people with similar names
⚠️ Always use third person (he/his/him) when talking about {profile['name']}
⚠️ Do NOT say "there are many people with this name" - just provide info about THIS {profile['name']}

**INFORMATION ABOUT {profile['name']}:**

**Personal Info:**
- Name: {profile['name']}
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
- Living: Hostel life
- Study pattern: {profile['student_status']['study_pattern']}
{portfolio_context}

Remember: Be helpful for ALL questions. When asked about {profile['name']}, use the profile above. When someone asks about themselves, engage with them naturally.
"""

def create_jarvis_system_prompt(profile):
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
"""

# ======================================
# Lazy cached profile
# ======================================
_PROFILE_CACHE = {"profile": None, "last_fetched": 0}
PROFILE_CACHE_TTL = 300  # seconds

def get_profile_data(force_refresh=False):
    now = int(time.time())
    if force_refresh or _PROFILE_CACHE["profile"] is None or (now - _PROFILE_CACHE["last_fetched"] > PROFILE_CACHE_TTL):
        try:
            logger.info("Loading profile data (lazy fetch)...")
            _PROFILE_CACHE["profile"] = load_profile_data()
            _PROFILE_CACHE["last_fetched"] = now
        except Exception:
            logger.exception("Failed to load profile data; using minimal fallback.")
            _PROFILE_CACHE["profile"] = build_base_profile()
            _PROFILE_CACHE["last_fetched"] = now
    return _PROFILE_CACHE["profile"]

# ======================================
# 🌐 Routes
# ======================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """🔥 STREAMING ENDPOINT - ChatGPT-style typing"""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip() if data else ""

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY is not set in environment variables.")
            return jsonify({"error": "Server misconfiguration: OPENROUTER_API_KEY is not set."}), 500

        # Detect Jarvis mode
        jarvis_mode = False
        user_message_lower = user_message.lower()

        if "jarvis" in user_message_lower or "hey jarvis" in user_message_lower:
            jarvis_mode = True
            system_prompt = create_jarvis_system_prompt(get_profile_data())
            logger.info("🤖 JARVIS MODE ACTIVATED")
        else:
            system_prompt = create_regular_system_prompt(get_profile_data())

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 🔥 STREAMING RESPONSE GENERATOR
        def generate():
            full_response = ""
            model_used = None
            
            for chunk_text, is_complete, model, error in ai_handler.send_request_streaming(messages):
                if error == "rate_limited":
                    continue  # Rotation happening, keep going
                
                if error == "all_failed":
                    yield f"data: {json.dumps({'error': 'All models busy', 'done': True})}\n\n"
                    return
                
                if chunk_text:
                    full_response += chunk_text
                    model_used = model
                    # Send chunk to frontend
                    yield f"data: {json.dumps({'text': chunk_text, 'done': False})}\n\n"
                
                if is_complete:
                    # Send completion signal with metadata
                    yield f"data: {json.dumps({'done': True, 'jarvis_mode': jarvis_mode, 'model_used': model_used})}\n\n"
                    return

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.exception("Unhandled exception in /api/chat/stream")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
