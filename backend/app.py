"""
app.py
------
Study Mate backend.

Responsibilities:
  1. Serve the static frontend (landing page + chatbot page) so the whole
     project can be opened with ONE command and no separate frontend server.
  2. Expose a single JSON API endpoint, POST /api/chat, which:
       - receives the user's message + a session id
       - keeps a short server-side conversation history per session
       - calls the Groq API (via the official groq SDK)
       - returns the model's real, generated reply

No Hugging Face. No hard-coded responses. No deployment tooling.
Run locally with:  python app.py
"""

import os
import uuid
import traceback

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq

import config

# ---------------------------------------------------------------------------
# App + Groq client setup
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path="",
)

# Allow the deployed frontend (e.g. on Vercel) to call this API from a
# different origin. Harmless and unused for local development, where
# frontend + backend are served from the same origin.
allowed_origins = (
    "*" if config.ALLOWED_ORIGINS == "*"
    else [o.strip() for o in config.ALLOWED_ORIGINS.split(",") if o.strip()]
)
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# Fail fast (but with a friendly message) if no API key is configured.
if not config.GROQ_API_KEY:
    print(
        "\n[Study Mate] WARNING: GROQ_API_KEY is not set.\n"
        "Create a '.env' file in backend/ (see .env.example) and add:\n"
        "  GROQ_API_KEY=your_real_key_here\n"
    )

client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None

# In-memory per-session conversation history.
# Structure: { session_id: [ {"role": "user"/"assistant", "content": text}, ... ] }
# This resets whenever the Flask server restarts — perfectly fine for a
# local demo/portfolio project (no database required).
SESSIONS = {}


def get_or_create_session(session_id):
    """Return the session id to use, creating a new one if needed."""
    if not session_id or session_id not in SESSIONS:
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = []
    return session_id


def trim_history(history):
    """Keep only the most recent N turns to control context size/cost."""
    max_items = config.MAX_HISTORY_TURNS * 2  # user+assistant per turn
    if len(history) > max_items:
        return history[-max_items:]
    return history


# ---------------------------------------------------------------------------
# Frontend routes (serves the landing page and chat page as static files)
# ---------------------------------------------------------------------------

@app.route("/")
def serve_landing():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/chat")
def serve_chat_page():
    return send_from_directory(FRONTEND_DIR, "chat.html")


# Static assets (css/js/images) are automatically served because
# static_folder points at the frontend directory.


# ---------------------------------------------------------------------------
# API route
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({
            "error": "Server is missing GROQ_API_KEY. Add it to backend/.env "
                     "(see .env.example) and restart the server."
        }), 500

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    session_id = get_or_create_session(session_id)
    history = SESSIONS[session_id]

    # Build the full conversation (system prompt + previous turns + new
    # user turn) in the OpenAI-style format Groq's API expects.
    messages = (
        [{"role": "system", "content": config.SYSTEM_INSTRUCTION}]
        + list(history)
        + [{"role": "user", "content": user_message}]
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=config.GENERATION_CONFIG["temperature"],
            top_p=config.GENERATION_CONFIG["top_p"],
            max_tokens=config.GENERATION_CONFIG["max_tokens"],
        )

        reply_text = (response.choices[0].message.content or "").strip()
        if not reply_text:
            reply_text = "I couldn't generate a response for that — could you rephrase your question?"

        # Persist the turn in session history for future context.
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply_text})
        SESSIONS[session_id] = trim_history(history)

        return jsonify({
            "reply": reply_text,
            "session_id": session_id,
            "model": config.GROQ_MODEL,
        })

    except Exception as exc:  # noqa: BLE001 - surface a clean error to the UI
        traceback.print_exc()
        return jsonify({
            "error": f"Groq API request failed: {str(exc)}"
        }), 502


@app.route("/api/reset", methods=["POST"])
def reset_session():
    """Clear a session's history (used by the 'New Chat' button)."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if session_id in SESSIONS:
        SESSIONS[session_id] = []
    return jsonify({"status": "ok"})


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model": config.GROQ_MODEL,
        "api_key_configured": bool(config.GROQ_API_KEY),
    })


if __name__ == "__main__":
    print(f"\n[Study Mate] Starting on http://{config.HOST}:{config.PORT}")
    print(f"[Study Mate] Using Groq model: {config.GROQ_MODEL}\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
