/**
 * assistant.js
 * ------------
 * Core Study Mate assistant logic, shared by:
 *   - the popup widget embedded in index.html
 *   - the full-page fallback at chat.html
 *
 * Talks ONLY to our own local backend (/api/chat, /api/reset, /api/health).
 * The Gemini API key never touches the browser.
 *
 * Conversation history (id, title, createdAt, updatedAt, messages) is
 * kept client-side in localStorage so the person can see and revisit
 * previous conversations. The actual AI context per conversation is kept
 * server-side (in-memory) by the Flask backend, keyed by session_id.
 */

(function (global) {
  const STORAGE_CONVERSATIONS = "studymate_conversations_v1";
  const STORAGE_ACTIVE_ID = "studymate_active_id_v1";

  function uid() {
    if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
    return "id-" + Date.now() + "-" + Math.random().toString(16).slice(2);
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function formatTime(iso) {
    const d = new Date(iso);
    const today = new Date();
    const sameDay = d.toDateString() === today.toDateString();
    if (sameDay) {
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return d.toLocaleDateString([], { month: "short", day: "numeric" }) +
      " · " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function generateTitle(text) {
    const clean = (text || "").replace(/\s+/g, " ").trim();
    if (!clean) return "New chat";
    const words = clean.split(" ");
    let title = words.slice(0, 7).join(" ");
    if (words.length > 7) title += "…";
    if (title.length > 48) title = title.slice(0, 48).trim() + "…";
    return title.charAt(0).toUpperCase() + title.slice(1);
  }

  function escapeForCompare(s) { return (s || "").trim(); }

  function apiUrl(path) {
    const base = (global.STUDYMATE_API_BASE || "").replace(/\/$/, "");
    return base + path;
  }

  class StudyMateAssistant {
    /**
     * @param {Object} opts
     *  Required elements: messagesEl, formEl, inputEl, sendBtn, newChatBtn,
     *  historyListEl.
     *  Optional: modelBadgeEl, closeBtn (+ onClose), historyToggleBtn,
     *  historyDrawerEl, historyCloseBtn, welcomeText.
     */
    constructor(opts) {
      this.messagesEl = opts.messagesEl;
      this.formEl = opts.formEl;
      this.inputEl = opts.inputEl;
      this.sendBtn = opts.sendBtn;
      this.newChatBtn = opts.newChatBtn;
      this.historyListEl = opts.historyListEl;

      this.modelBadgeEl = opts.modelBadgeEl || null;
      this.historyToggleBtn = opts.historyToggleBtn || null;
      this.historyDrawerEl = opts.historyDrawerEl || null;
      this.historyCloseBtn = opts.historyCloseBtn || null;
      this.welcomeText = opts.welcomeText ||
        "Hi, I'm Study Mate. Ask me about anything you're studying — " +
        "a concept, a homework problem, an essay outline — and I'll help you work through it.";

      this.isSending = false;
      this.conversations = [];
      this.activeId = null;

      this._bindEvents();
      this._loadState();
      this.checkHealth();
    }

    /* ---------------------------- persistence ---------------------------- */

    _loadState() {
      try {
        const raw = localStorage.getItem(STORAGE_CONVERSATIONS);
        this.conversations = raw ? JSON.parse(raw) : [];
      } catch (e) {
        this.conversations = [];
      }

      if (!Array.isArray(this.conversations) || this.conversations.length === 0) {
        this.conversations = [this._makeConversation()];
      }

      this.activeId = localStorage.getItem(STORAGE_ACTIVE_ID);
      if (!this.activeId || !this._findConversation(this.activeId)) {
        this.activeId = this.conversations[0].id;
      }

      this._renderHistory();
      this._renderActiveConversation();
    }

    _saveState() {
      localStorage.setItem(STORAGE_CONVERSATIONS, JSON.stringify(this.conversations));
      localStorage.setItem(STORAGE_ACTIVE_ID, this.activeId);
    }

    _makeConversation() {
      return {
        id: uid(),
        title: "New chat",
        createdAt: nowIso(),
        updatedAt: nowIso(),
        sessionId: null,
        messages: [],
      };
    }

    _findConversation(id) {
      return this.conversations.find((c) => c.id === id) || null;
    }

    get activeConversation() {
      return this._findConversation(this.activeId);
    }

    /* ------------------------------ events -------------------------------- */

    _bindEvents() {
      this.formEl.addEventListener("submit", (e) => {
        e.preventDefault();
        this._handleSend();
      });

      this.inputEl.addEventListener("input", () => this._autoGrow());
      this.inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.formEl.requestSubmit();
        }
      });

      this.newChatBtn.addEventListener("click", () => this.startNewChat());

      if (this.historyToggleBtn && this.historyDrawerEl) {
        this.historyToggleBtn.addEventListener("click", () => {
          this.historyDrawerEl.classList.toggle("open");
        });
      }
      if (this.historyCloseBtn && this.historyDrawerEl) {
        this.historyCloseBtn.addEventListener("click", () => {
          this.historyDrawerEl.classList.remove("open");
        });
      }
    }

    _autoGrow() {
      this.inputEl.style.height = "auto";
      this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 140) + "px";
    }

    _setSending(state) {
      this.isSending = state;
      this.sendBtn.disabled = state;
      this.inputEl.disabled = state;
    }

    /* ------------------------------ rendering ------------------------------ */

    _scrollToBottom() {
      this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    _renderActiveConversation() {
      const convo = this.activeConversation;
      this.messagesEl.innerHTML = "";

      if (!convo || convo.messages.length === 0) {
        this._appendMessageEl("model", this.welcomeText);
        return;
      }

      convo.messages.forEach((m) => this._appendMessageEl(m.role, m.text));
      this._scrollToBottom();
    }

    _appendMessageEl(role, text) {
      const wrapper = document.createElement("div");
      wrapper.className = `message message-${role}`;

      const avatar = document.createElement("div");
      avatar.className = `avatar avatar-${role === "user" ? "user" : "model"}`;
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = role === "user" ? "You" : "AI";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;

      wrapper.appendChild(avatar);
      wrapper.appendChild(bubble);
      this.messagesEl.appendChild(wrapper);
      this._scrollToBottom();
      return bubble;
    }

    _appendThinkingEl() {
      const wrapper = document.createElement("div");
      wrapper.className = "message message-model";
      wrapper.id = "sm-thinking-bubble";

      const avatar = document.createElement("div");
      avatar.className = "avatar avatar-model";
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = "AI";

      const bubble = document.createElement("div");
      bubble.className = "bubble thinking";
      bubble.innerHTML = "<i></i><i></i><i></i>";

      wrapper.appendChild(avatar);
      wrapper.appendChild(bubble);
      this.messagesEl.appendChild(wrapper);
      this._scrollToBottom();
    }

    _removeThinkingEl() {
      const el = document.getElementById("sm-thinking-bubble");
      if (el) el.remove();
    }

    _renderHistory() {
      this.historyListEl.innerHTML = "";

      if (this.conversations.length === 0) {
        const empty = document.createElement("div");
        empty.className = "history-empty";
        empty.textContent = "No conversations yet.";
        this.historyListEl.appendChild(empty);
        return;
      }

      const sorted = [...this.conversations].sort(
        (a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)
      );

      sorted.forEach((convo) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "history-item" + (convo.id === this.activeId ? " active" : "");

        const title = document.createElement("div");
        title.className = "history-item-title";
        title.textContent = convo.title || "New chat";

        const time = document.createElement("div");
        time.className = "history-item-time";
        time.textContent = formatTime(convo.updatedAt);

        const del = document.createElement("button");
        del.type = "button";
        del.className = "history-item-delete";
        del.setAttribute("aria-label", "Delete conversation");
        del.innerHTML = "&times;";
        del.addEventListener("click", (e) => {
          e.stopPropagation();
          this.deleteConversation(convo.id);
        });

        item.appendChild(title);
        item.appendChild(time);
        item.appendChild(del);

        item.addEventListener("click", () => this.switchConversation(convo.id));
        this.historyListEl.appendChild(item);
      });
    }

    /* ------------------------------ actions -------------------------------- */

    startNewChat() {
      const convo = this._makeConversation();
      this.conversations.push(convo);
      this.activeId = convo.id;
      this._saveState();
      this._renderHistory();
      this._renderActiveConversation();
      if (this.historyDrawerEl) this.historyDrawerEl.classList.remove("open");
      this.inputEl.focus();
    }

    switchConversation(id) {
      if (!this._findConversation(id)) return;
      this.activeId = id;
      this._saveState();
      this._renderHistory();
      this._renderActiveConversation();
      if (this.historyDrawerEl) this.historyDrawerEl.classList.remove("open");
    }

    deleteConversation(id) {
      this.conversations = this.conversations.filter((c) => c.id !== id);
      if (this.conversations.length === 0) {
        this.conversations = [this._makeConversation()];
      }
      if (this.activeId === id) {
        this.activeId = this.conversations[0].id;
      }
      this._saveState();
      this._renderHistory();
      this._renderActiveConversation();
    }

    async checkHealth() {
      if (!this.modelBadgeEl) return;
      try {
        const res = await fetch(apiUrl("/api/health"));
        const data = await res.json();
        if (data.api_key_configured) {
          this.modelBadgeEl.textContent = data.model;
        } else {
          this.modelBadgeEl.textContent = "API key missing";
        }
      } catch (err) {
        this.modelBadgeEl.textContent = "backend offline";
      }
    }

    async _handleSend() {
      if (this.isSending) return;
      const text = this.inputEl.value.trim();
      if (!text) return;

      const convo = this.activeConversation;
      const isFirstUserMessage = !convo.messages.some((m) => m.role === "user");

      convo.messages.push({ role: "user", text, ts: nowIso() });
      convo.updatedAt = nowIso();
      if (isFirstUserMessage && escapeForCompare(convo.title) === "" || convo.title === "New chat") {
        convo.title = generateTitle(text);
      }
      this._saveState();
      this._renderHistory();

      this._appendMessageEl("user", text);
      this.inputEl.value = "";
      this._autoGrow();
      this._setSending(true);
      this._appendThinkingEl();

      try {
        const res = await fetch(apiUrl("/api/chat"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, session_id: convo.sessionId }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Something went wrong talking to Gemini.");

        convo.sessionId = data.session_id || convo.sessionId;
        convo.messages.push({ role: "model", text: data.reply, ts: nowIso() });
        convo.updatedAt = nowIso();
        this._saveState();
        this._renderHistory();

        this._removeThinkingEl();
        this._appendMessageEl("model", data.reply);
      } catch (err) {
        this._removeThinkingEl();
        const bubble = this._appendMessageEl("error", err.message);
        bubble.parentElement.classList.add("message-error");
      } finally {
        this._setSending(false);
        this.inputEl.focus();
      }
    }
  }

  global.StudyMateAssistant = StudyMateAssistant;
})(window);
