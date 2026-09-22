/**
 * config.js
 * ---------
 * Tells the frontend which backend/chatbot to use.
 *
 * LOCAL DEVELOPMENT (default): leave both empty. Flask serves both the
 * frontend and the API from the same origin (http://127.0.0.1:5000), and
 * the floating button opens the built-in popup chat on this page.
 *
 * DEPLOYED SETUP (frontend on Vercel, chatbot on Streamlit Community
 * Cloud): set STUDYMATE_STREAMLIT_URL to your deployed Streamlit app's
 * URL. When this is set, the floating button and "Try AI Assistant"
 * buttons open that Streamlit app in a new tab instead of the in-page
 * popup — because the AI logic runs there, not in this static frontend.
 *
 *   window.STUDYMATE_STREAMLIT_URL = "https://your-app.streamlit.app";
 *
 * ALTERNATIVE SETUP (frontend on Vercel, backend as a separate Flask API
 * e.g. on Render): leave STUDYMATE_STREAMLIT_URL empty and set
 * STUDYMATE_API_BASE instead, to keep using the in-page popup:
 *
 *   window.STUDYMATE_API_BASE = "https://study-mate-backend.onrender.com";
 *
 * These are just URLs, not secrets — safe to commit.
 */
window.STUDYMATE_API_BASE = "";
window.STUDYMATE_STREAMLIT_URL = "https://study-mate-chatbot-8tfjfrxpsawnipdqjq475b.streamlit.app/?embed=true";