"""
study_engine.py
----------------
Core AI logic for the Study Mate chatbot, used by the Streamlit app
(app.py). Mirrors backend/config.py + backend/app.py's Groq integration
so the hosted Streamlit chatbot and the local Flask app behave the same
way — same model, same system prompt, same generation settings.

No Hugging Face. No hard-coded responses. Real Groq-generated replies.
"""

from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"

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


def build_client(api_key: str) -> Groq:
    """Create a Groq client from an API key (read from Streamlit secrets or env)."""
    return Groq(api_key=api_key)


def generate_reply(client: Groq, model: str, history: list, user_message: str) -> str:
    """
    Generate a real, live reply from the Groq model.

    history: list of {"role": "user"/"assistant", "content": str} — prior
             turns only (do NOT include the current user_message in it).
    Returns the assistant's reply text (never a canned/hard-coded string).
    """
    messages = (
        [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        + list(history)
        + [{"role": "user", "content": user_message}]
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=GENERATION_CONFIG["temperature"],
        top_p=GENERATION_CONFIG["top_p"],
        max_tokens=GENERATION_CONFIG["max_tokens"],
    )

    reply = (response.choices[0].message.content or "").strip()
    return reply or "I couldn't generate a response for that — could you rephrase your question?"
