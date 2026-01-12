from flask import Flask, request, jsonify, Response, stream_with_context, render_template
from flask_cors import CORS
import requests, os, json, time, re

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

PORTFOLIO_URL = "https://janagams-portfolio.onrender.com"

# ===============================
# Portfolio cache
# ===============================
CACHE = {"text": "", "time": 0}
TTL = 600

def get_portfolio_text():
    now = time.time()
    if now - CACHE["time"] < TTL:
        return CACHE["text"]

    try:
        r = requests.get(PORTFOLIO_URL, timeout=10)
        clean = re.sub(r"<[^>]+>", " ", r.text)
        clean = " ".join(clean.split())[:3000]
        CACHE["text"] = clean
        CACHE["time"] = now
        return clean
    except:
        return ""

def system_prompt():
    return f"""
You are JARVIS, a calm and honest personal AI assistant.

About Sensei (Sri chaRAN):
- Student developer
- Learning C, Python, frontend & backend
- Deploys projects and fixes real bugs
- Uses open-source AI tools (not hype)

Portfolio context:
{get_portfolio_text()}
"""

# ✅ SERVE UI
@app.route("/")
def index():
    return render_template("index.html")

# ✅ CHAT API
@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json()
    message = data.get("message", "").strip()

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": message}
        ],
        "stream": True
    }

    def generate():
        with requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        ) as r:
            for line in r.iter_lines():
                if line and line.startswith(b"data: "):
                    yield line.decode() + "\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )

# ✅ HEALTH CHECK (optional)
@app.route("/health")
def health():
    return jsonify({"status": "ok"})
