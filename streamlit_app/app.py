"""
app.py
------
Study Mate — Streamlit chatbot app.

This is the HOSTED version of Study Mate's AI assistant, meant to be
deployed on Streamlit Community Cloud and linked to from the Vercel-hosted
landing page (see ../frontend). It uses the same Groq model + system
prompt as the local Flask backend (see study_engine.py and
../backend/config.py), so behavior is consistent whether you run Study
Mate locally (`python backend/app.py`) or via this hosted app.

No Hugging Face. No hard-coded responses. Real, live Groq-generated
replies, with multi-conversation chat history for the session.
"""

import os
from datetime import datetime

import streamlit as st

from study_engine import build_client, generate_reply, DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Page setup + light theming to match Study Mate's gradient brand
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Study Mate — AI Study Assistant",
    page_icon="🎓",
    layout="centered",
)

st.markdown(
    """
    <style>
      .stApp { background: linear-gradient(180deg, #FAFAFE 0%, #F3F1FD 100%); }
      .sm-hero {
        background: linear-gradient(135deg, #4F6EF7 0%, #8B5CF6 55%, #A78BFA 100%);
        padding: 22px 26px; border-radius: 18px; color: #fff; margin-bottom: 18px;
      }
      .sm-hero h1 { margin: 0; font-size: 22px; }
      .sm-hero p { margin: 4px 0 0; opacity: 0.92; font-size: 14px; }
      section[data-testid="stSidebar"] button { text-align: left; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="sm-hero">
      <h1>🎓 Study Mate</h1>
      <p>Your intelligent AI study companion — ask anything you're studying.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# API key / model (Streamlit Cloud → App settings → Secrets, or env locally)
# ---------------------------------------------------------------------------


def get_secret(name, default=""):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


api_key = get_secret("GROQ_API_KEY")
model = get_secret("GROQ_MODEL", DEFAULT_MODEL)

if not api_key:
    st.error(
        "**GROQ_API_KEY is not configured.**\n\n"
        "On Streamlit Community Cloud: go to your app → **Settings → Secrets** "
        "and add:\n```\nGROQ_API_KEY = \"your_real_key\"\n```\n"
        "Running locally: create `.streamlit/secrets.toml` with the same line."
    )
    st.stop()

client = build_client(api_key)

# ---------------------------------------------------------------------------
# Conversation state — multiple conversations, like the web app's history
# ---------------------------------------------------------------------------

if "conversations" not in st.session_state:
    first_id = "conv-1"
    st.session_state.conversations = {
        first_id: {"title": "New chat", "created": datetime.now(), "messages": []}
    }
    st.session_state.active_id = first_id


def new_chat():
    new_id = f"conv-{len(st.session_state.conversations) + 1}-{datetime.now().timestamp()}"
    st.session_state.conversations[new_id] = {
        "title": "New chat",
        "created": datetime.now(),
        "messages": [],
    }
    st.session_state.active_id = new_id


def make_title(text):
    text = text.strip().replace("\n", " ")
    words = text.split(" ")
    title = " ".join(words[:7])
    if len(words) > 7:
        title += "…"
    return title[:48] or "New chat"


# ---------------------------------------------------------------------------
# Sidebar — chat history (mirrors the history panel in the web widget)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 💬 Conversations")
    if st.button("+ New chat", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()

    sorted_ids = sorted(
        st.session_state.conversations.keys(),
        key=lambda cid: st.session_state.conversations[cid]["created"],
        reverse=True,
    )
    for cid in sorted_ids:
        convo = st.session_state.conversations[cid]
        is_active = cid == st.session_state.active_id
        marker = "🟣" if is_active else "⚪"
        time_label = convo["created"].strftime("%b %d, %H:%M")
        if st.button(f"{marker} {convo['title']}\n{time_label}", key=f"conv_{cid}", use_container_width=True):
            st.session_state.active_id = cid
            st.rerun()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

active = st.session_state.conversations[st.session_state.active_id]

if not active["messages"]:
    st.chat_message("assistant", avatar="🤖").write(
        "Hi, I'm Study Mate. Ask me about anything you're studying — a "
        "concept, a homework problem, an essay outline — and I'll help "
        "you work through it."
    )

for msg in active["messages"]:
    avatar = "🤖" if msg["role"] == "assistant" else "🧑‍🎓"
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

user_input = st.chat_input("Ask a question about anything you're studying…")

if user_input:
    history_for_api = list(active["messages"])  # turns before this one

    active["messages"].append({"role": "user", "content": user_input})
    if active["title"] == "New chat":
        active["title"] = make_title(user_input)

    st.chat_message("user", avatar="🧑‍🎓").write(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
            try:
                reply = generate_reply(client, model, history_for_api, user_input)
            except Exception as exc:  # noqa: BLE001
                reply = f"⚠️ Something went wrong talking to Groq: {exc}"
        st.write(reply)

    active["messages"].append({"role": "assistant", "content": reply})
