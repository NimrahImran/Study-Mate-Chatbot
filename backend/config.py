"""
config.py
---------
Centralized configuration for Study Mate.

Everything related to WHICH model is used, and how it behaves, lives in
this one file. If you want to switch models later, you only need to
change GROQ_MODEL below (or the GROQ_MODEL value in your .env) — nothing
else in the codebase needs to change.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file (never committed to git)
load_dotenv()

# ---------------------------------------------------------------------------
# GROQ API KEY
# ---------------------------------------------------------------------------
# Read from the environment ONLY. Never hard-code a real key in source code.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ---------------------------------------------------------------------------
# MODEL SELECTION
# ---------------------------------------------------------------------------
# Default: "openai/gpt-oss-120b" — OpenAI's open-weight 120B model, served
# on Groq's LPU inference hardware for very fast responses. Great fit for
# a chat UI: low latency, strong general reasoning for study help (concept
# explanations, step-by-step problem solving, summaries, quizzing).
#
# Swap it any time via the GROQ_MODEL value in your .env — no code changes
# needed. Other options available on Groq include "llama-3.3-70b-versatile"
# and "llama-3.1-8b-instant" (faster/cheaper, lighter reasoning).
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# ---------------------------------------------------------------------------
# GENERATION SETTINGS
# ---------------------------------------------------------------------------
# Tone/behavior of Study Mate as an AI study companion.
SYSTEM_INSTRUCTION = (
    "You are Study Mate, a friendly and encouraging AI study assistant. "
    "You help students understand concepts, answer academic questions, "
    "summarize topics, create study plans, explain step-by-step solutions, "
    "and quiz students to check understanding. "
    "Keep answers clear, well-structured, and appropriately concise. "
    "Use simple language first, then add depth if the topic is complex. "
    "When explaining math, science, or logic, show your reasoning step by step. "
    "If a question is unclear, ask a clarifying question. "
    "Always stay supportive and patient, like a helpful study partner."
)

GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 1024,
}

# How many previous turns (user+assistant pairs) to keep as context per session.
MAX_HISTORY_TURNS = 20

# ---------------------------------------------------------------------------
# FLASK APP SETTINGS
# ---------------------------------------------------------------------------
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# ---------------------------------------------------------------------------
# CORS (only matters when the frontend is deployed separately, e.g. on
# Vercel, and calls this backend from a different domain, e.g. on Render).
# For local development this is unused since frontend + backend share the
# same origin (http://127.0.0.1:5000).
#
# Set to your deployed frontend's exact URL for safety, e.g.:
#   ALLOWED_ORIGINS=https://study-mate.vercel.app
# Comma-separate multiple origins if needed. Defaults to "*" (any origin)
# so the app works out of the box; tighten this after you have your real
# Vercel URL.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
