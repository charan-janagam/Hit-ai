from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests, os, json, time, re

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

PORTFOLIO_URL = "https://janagams-portfolio.onrender.com"

# ===============================
# 🔹 Portfolio Cache (important)
# ===============================
PORTFOLIO_CACHE = {
    "content": "",
    "last_fetch": 0
}
CACHE_TTL = 600  # 10 minutes


def fetch_portfolio_content():
    """Fetch & clean portfolio text (cached)"""
    now = time.time()
    if now - PORTFOLIO_CACHE["last_fetch"] < CACHE_TTL:
        return PORTFOLIO_CACHE["content"]

    try:
        res = requests.get(PORTFOLIO_URL, timeout=10)
        if res.status_code == 200:
            text = res.text
            # Remove HTML tags
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = " ".join(clean.split())
            clean = clean[:3500]  # keep tokens safe

            PORTFOLIO_CACHE["content"] = clean
            PORTFOLIO_CACHE["last_fetch"] = now
            return clean
    except Exception:
        pass

    return ""


def build_system_prompt():
    portfolio_text = fetch_portfolio_content()

    return f"""
You are **JARVIS**, a hacker-style personal AI assistant.

Your master is **Sensei (Sri chaRAN)**:
- Student & self-taught developer
- Built this AI chatbot and portfolio
- Interested in Python, Flask, AI, backend & hacker aesthetics

PERSONALITY:
- Call him **Sensei**
- Confident, intelligent, calm dominance
- Slightly sarcastic but respectful
- Hacker / terminal vibe

RULES:
- Be project-aware
- Use the portfolio content below when answering
- If asked about projects, skills, experience → answer from portfolio
- Never say you "scraped" or "fetched" anything

==============================
📁 PORTFOLIO DATA (REFERENCE)
==============================
{portfolio_text}
==============================

Respond clearly, confidently, and intelligently.
"""


@app.route("/")
def home():
    return jsonify({"status": "JARVIS ONLINE"})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": message}
        ],
        "stream": True
    }

    def generate():
        try:
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
        except Exception:
            yield f"data: {json.dumps({'error': 'Stream interrupted'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
