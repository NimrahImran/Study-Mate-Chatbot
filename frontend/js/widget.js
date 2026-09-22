/**
 * widget.js
 * ---------
 * Wires up the floating AI button + "Try AI Assistant" CTAs on the
 * landing page.
 *
 * Two modes, decided by frontend/js/config.js:
 *   - STUDYMATE_STREAMLIT_URL is set → the chatbot lives on a separately
 *     deployed Streamlit app. Buttons open that URL in a new tab.
 *   - STUDYMATE_STREAMLIT_URL is empty (default/local) → the built-in
 *     popup opens on this page, talking to the Flask backend via
 *     assistant.js (StudyMateAssistant).
 */

(() => {
  const streamlitUrl = (window.STUDYMATE_STREAMLIT_URL || "").trim();

  const widgetRoot = document.getElementById("assistant-widget");
  const fab = document.getElementById("fab-chat");
  const popup = document.getElementById("assistant-popup");
  const closeBtn = document.getElementById("close-chat-btn");

  // ------------------------- Mode: hosted Streamlit chatbot ---------------

  if (streamlitUrl) {
    // The in-page popup isn't used in this mode — the real chat UI lives
    // on the deployed Streamlit app.
    if (popup) popup.remove();

    if (fab) {
      fab.setAttribute("aria-label", "Open Study Mate AI assistant (opens in a new tab)");
      fab.addEventListener("click", () => window.open(streamlitUrl, "_blank", "noopener"));
    }

    document.querySelectorAll("[data-open-chat]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        window.open(streamlitUrl, "_blank", "noopener");
      });
    });

    return;
  }

  // ------------------------- Mode: in-page popup (local / Flask API) ------

  function openPopup() {
    popup.classList.add("open");
    popup.setAttribute("aria-hidden", "false");
    fab.setAttribute("aria-expanded", "true");
    fab.classList.add("is-open");
    setTimeout(() => {
      const input = document.getElementById("popup-chat-input");
      if (input) input.focus();
    }, 150);
  }

  function closePopup() {
    popup.classList.remove("open");
    popup.setAttribute("aria-hidden", "true");
    fab.setAttribute("aria-expanded", "false");
    fab.classList.remove("is-open");
    const drawer = document.getElementById("history-drawer");
    if (drawer) drawer.classList.remove("open");
  }

  function togglePopup() {
    if (popup.classList.contains("open")) {
      closePopup();
    } else {
      openPopup();
    }
  }

  fab.addEventListener("click", togglePopup);
  closeBtn.addEventListener("click", closePopup);

  // Close when clicking outside the widget (but not on elements that
  // trigger the widget, like the header/hero CTA buttons).
  document.addEventListener("click", (e) => {
    if (!popup.classList.contains("open")) return;
    if (widgetRoot.contains(e.target)) return;
    if (e.target.closest("[data-open-chat]")) return;
    closePopup();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && popup.classList.contains("open")) {
      closePopup();
    }
  });

  // Any element with [data-open-chat] opens the popup instead of navigating.
  document.querySelectorAll("[data-open-chat]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      openPopup();
    });
  });

  // Expose for assistant.js's close button hookup if needed later.
  window.__studyMateOpenPopup = openPopup;
  window.__studyMateClosePopup = closePopup;
})();
