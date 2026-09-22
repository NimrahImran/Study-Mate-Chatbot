# Study Mate 🎓✎

A Generative AI chatbot for students, built as a portfolio/demo project.
Runs fully locally with one command, and is also ready to deploy
(frontend on Vercel + chatbot on Streamlit Community Cloud, or frontend
on Vercel + backend on Render — see Section 8).

No Hugging Face. Real, live replies from **Groq** (`openai/gpt-oss-120b`)
— never hard-coded responses.

```
Landing page → click the floating AI button (or "Try AI Assistant")
→ chat popup opens over the page → type + Send → real AI reply
```

Runs fully locally out of the box. Section 8 below covers optional
deployment (backend → Render, frontend → Vercel).

**Design:** a premium blue → purple → violet gradient theme with soft
pink/cyan highlights, glassmorphism surfaces, and an AI + education themed
hero illustration.

**Chat experience:**
- A gradient **floating AI button** sits fixed at the bottom-right of the
  landing page. Clicking it (or the "Try AI Assistant" buttons) opens the
  chatbot as a **popup docked to the bottom-right** — the page itself never
  navigates away.
- The popup has a fixed header ("🤖 Study Mate — AI Study Assistant" with
  **+ New Chat** and **× Close**), a scrollable message area, and a fixed
  composer at the bottom.
- A **chat history panel** (toggle icon in the header) lists every past
  conversation with an auto-generated title, and last-updated time. Click
  one to reopen it; hover to delete it.
- `chat.html` (served at `/chat`) is a full-page version of the same
  assistant, with the history panel always visible as a sidebar — handy if
  you'd rather not use the popup.

## 1. What's inside

```
study-mate/
├── backend/                Local Flask app (always available, run with python app.py)
├── frontend/                Landing page + chat UI — deploy this to Vercel
├── streamlit_app/          Hosted chatbot — deploy this to Streamlit Community Cloud
```

Full detail:

```
study-mate/
├── backend/
│   ├── app.py              Flask server: serves the frontend + /api/chat
│   ├── config.py           ALL model/config settings live here
│   ├── requirements.txt    Python dependencies
│   ├── Procfile             Start command for Render/Railway
│   ├── runtime.txt          Pinned Python version for Render
│   └── .env.example        Template for your API key (copy → .env)
├── frontend/
│   ├── index.html          Landing page + embedded chat popup + floating button
│   ├── chat.html           Full-page chat fallback (same assistant, page mode)
│   ├── vercel.json          Vercel static-hosting config
│   ├── css/
│   │   ├── style.css       Design tokens (gradient theme) + landing page styles
│   │   └── assistant.css   Floating button, popup, history panel, chat UI
│   └── js/
│       ├── config.js       Points the frontend at Render and/or Streamlit
│       ├── assistant.js    Core chat logic + conversation history (shared)
│       └── widget.js       Opens the popup, or the Streamlit app in a new tab
├── streamlit_app/
│   ├── app.py               The hosted chatbot UI (Streamlit)
│   ├── study_engine.py      Same Groq logic as backend/app.py
│   ├── requirements.txt     streamlit + groq
│   └── .streamlit/
│       └── secrets.toml.example   Template for your API key (local testing only)
├── render.yaml              One-click backend deploy config for Render
└── README.md
```

## 2. Why `openai/gpt-oss-120b` on Groq

The model is chosen in one place — `backend/config.py` — so you can swap it
any time without touching any other file.

**Default: `openai/gpt-oss-120b`**

- **OpenAI's open-weight 120B model**, served on **Groq's LPU inference
  hardware** — this combination gives strong general reasoning (concept
  explanations, step-by-step problem solving, summarizing, quizzing) with
  very low latency, which matters for a chat UI that should feel snappy.
- **Free-tier friendly** — good fit for a student demo/portfolio project.
- **Large context window** — keeps a multi-turn study conversation coherent.

Want something even faster/lighter? Set `GROQ_MODEL=llama-3.1-8b-instant`
in your `.env`. Want a well-rounded alternative? Try
`GROQ_MODEL=llama-3.3-70b-versatile`. No code changes needed — just the
`.env` value.

## 3. Prerequisites

- Python 3.9+
- A free Groq API key from **[Groq Console](https://console.groq.com/keys)**

## 4. Setup (one-time)

```bash
# 1. Go into the backend folder
cd study-mate/backend

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# then open .env and paste your real key after GROQ_API_KEY=
```

Your `.env` should look like:

```
GROQ_API_KEY=gsk_...your_real_key...
GROQ_MODEL=openai/gpt-oss-120b
HOST=127.0.0.1
PORT=5000
FLASK_DEBUG=True
```

`.env` is your personal file and should **never** be committed to git —
only `.env.example` (the template, with no real key) is shared.

## 5. Run it

```bash
python app.py
```

You should see:

```
[Study Mate] Starting on http://127.0.0.1:5000
[Study Mate] Using Groq model: openai/gpt-oss-120b
```

Now open your browser to:

**http://127.0.0.1:5000**

- You'll land on the Study Mate landing page.
- Click the floating AI button (bottom-right) or **"Try AI Assistant"**.
- Type a question and click **Send** (or press Enter).
- Study Mate calls the Groq API live and returns a real, generated answer.

That's it — one server, one command, everything local.

## 6. How the pieces fit together

1. **Frontend** (`index.html`, `chat.html`) is plain HTML/CSS/JS — no
   build step, no framework, nothing to compile.
2. **Flask** (`app.py`) serves those files directly and exposes one JSON
   API: `POST /api/chat`.
3. When you send a message, the browser calls `/api/chat` with your text
   and a session id. The backend keeps a short conversation history per
   session **in memory** (resets when the server restarts — fine for a
   local demo).
4. The backend calls the **official `groq` Python SDK**, which sends your
   message + recent history to the real model on Groq and returns a
   genuinely generated response — never a hard-coded string.
5. The API key lives only in `backend/.env` on your machine and is read
   server-side (`config.py`) — it is **never sent to or exposed in the
   browser**.
6. **Chat history** (conversation titles, timestamps, messages) is kept in
   the browser's `localStorage` so you can see and reopen past
   conversations across visits. The AI's own short-term memory of a
   conversation lives server-side, keyed by that conversation's session id
   — so it resets if you restart `python app.py`, but persists as you use
   the app normally.

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| Badge on chat page says "API key missing" | Make sure `backend/.env` exists and has a real `GROQ_API_KEY` value, then restart `python app.py`. |
| "backend offline" badge | Confirm `python app.py` is still running in your terminal. |
| `ModuleNotFoundError: groq` | Run `pip install -r requirements.txt` inside your virtual environment. |
| 429 / rate limit errors from Groq | You've hit the free-tier request limit — wait a bit or check your Groq Console usage. |

## 8. Deploying (optional)

The project runs entirely locally by default. Two ways to deploy it —
pick whichever matches your setup:

### Option A: Frontend on Vercel + Chatbot on Streamlit Community Cloud

This mirrors a common lightweight pattern: a static landing page on
Vercel, and the actual AI chatbot hosted as its own Streamlit app. The
"Try AI Assistant" button and floating button open the Streamlit app in
a new tab instead of an in-page popup.

**8A.1 — Deploy the chatbot to Streamlit Community Cloud**

1. Push this project to a GitHub repo.
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → **New app**
   → connect your repo.
   - **Main file path:** `streamlit_app/app.py`
3. Before deploying (or right after, under **Settings → Secrets**), add:
   ```toml
   GROQ_API_KEY = "your_real_key"
   GROQ_MODEL = "openai/gpt-oss-120b"
   ```
4. Deploy. You'll get a URL like
   `https://study-mate-xxxxx.streamlit.app`. Open it and confirm the
   chatbot replies.

**8A.2 — Deploy the landing page to Vercel**

1. Open `frontend/js/config.js` and set:
   ```js
   window.STUDYMATE_STREAMLIT_URL = "https://study-mate-xxxxx.streamlit.app";
   ```
   Commit and push this change.
2. Go to **[vercel.com](https://vercel.com)** → **Add New → Project** →
   import the same repo.
3. Set **Root Directory** to `frontend`. Framework preset: **Other** (it's
   plain static HTML/CSS/JS — no build command needed).
4. Deploy. You'll get a URL like `https://study-mate.vercel.app`.
5. Open it — the floating AI button and "Try AI Assistant" buttons now
   open your Streamlit chatbot in a new tab.

### Option B: Frontend on Vercel + Backend (Flask) on Render

Keeps the exact in-page popup experience (no new tab) by hosting the
Flask API separately instead of using Streamlit.

**8B.1 — Deploy the backend to Render**

1. Go to **[render.com](https://render.com)** → **New + → Web Service** →
   connect your repo.
   - If Render detects `render.yaml` at the repo root it pre-fills
     everything (Blueprint deploy) — just confirm.
   - Otherwise set manually: **Root directory:** `backend` ·
     **Build command:** `pip install -r requirements.txt` ·
     **Start command:** `gunicorn app:app`
2. Add environment variables: `GROQ_API_KEY`, `GROQ_MODEL=openai/gpt-oss-120b`,
   `ALLOWED_ORIGINS=*` (tighten later, see 8B.3).
3. Deploy → you'll get e.g. `https://study-mate-backend.onrender.com`.
   Visit `<url>/api/health` to confirm.

> Render's free tier sleeps after inactivity — the first request after a
> while can take ~30–60s to wake up.

**8B.2 — Deploy the frontend to Vercel**

1. In `frontend/js/config.js`, set (leave `STUDYMATE_STREAMLIT_URL` empty):
   ```js
   window.STUDYMATE_API_BASE = "https://study-mate-backend.onrender.com";
   ```
2. Vercel → **Add New → Project** → import repo → **Root Directory:**
   `frontend` → deploy.

**8B.3 — Lock down CORS (recommended)**

Once you have your Vercel URL, set on Render:
```
ALLOWED_ORIGINS=https://study-mate.vercel.app
```
and redeploy the backend.

### What changed to make deployment possible

- **`frontend/js/config.js`** — the one place that points the frontend at
  either a Streamlit chatbot or a Flask backend URL. Empty in both fields
  = local mode (in-page popup talking to `python backend/app.py`).
- **`streamlit_app/`** — a second, independent implementation of the same
  Groq-powered assistant (same model, same system prompt), built for
  Streamlit Community Cloud's hosting model.
- **`flask-cors`, `gunicorn`, `Procfile`, `runtime.txt`, `render.yaml`** —
  only needed for Option B (Flask on Render); harmless if you use Option A.

Nothing about the AI integration itself changed — still Groq,
`openai/gpt-oss-120b`, no Hugging Face, no hard-coded responses. The app
still runs exactly the same way locally regardless of which deployment
option you pick.
