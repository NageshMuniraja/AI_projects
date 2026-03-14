/**
 * Vertex AI Platform — Embeddable Chat Widget
 *
 * Usage:
 *   <script src="vertex-widget.js"
 *     data-tenant-slug="my-clinic"
 *     data-primary-color="#6366f1"
 *     data-position="bottom-right">
 *   </script>
 *
 * The widget auto-initializes by reading data attributes from its own script tag.
 */

import { VertexAPI, type MessageResponse, type StartChatResponse } from "./api";
import { getWidgetStyles } from "./styles";

// ─── Types ─────────────────────────────────────────────────────

interface WidgetConfig {
  tenantSlug: string;
  primaryColor: string;
  position: "bottom-right" | "bottom-left";
  apiBaseUrl: string;
  wsBaseUrl: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

// ─── SVG Icons ─────────────────────────────────────────────────

const ICONS = {
  chat: `<svg class="vtx-icon-chat" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>`,
  close: `<svg class="vtx-icon-close" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>`,
  send: `<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>`,
  minimize: `<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>`,
  bot: `<svg viewBox="0 0 24 24"><path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zM7.5 13a2.5 2.5 0 000 5 2.5 2.5 0 000-5zm9 0a2.5 2.5 0 000 5 2.5 2.5 0 000-5z"/></svg>`,
};

// ─── Storage Keys ──────────────────────────────────────────────

function storageKey(tenantSlug: string): string {
  return `vtx_chat_${tenantSlug}`;
}

function loadState(tenantSlug: string): {
  conversationId: string | null;
  messages: ChatMessage[];
} {
  try {
    const raw = localStorage.getItem(storageKey(tenantSlug));
    if (!raw) return { conversationId: null, messages: [] };
    const data = JSON.parse(raw);
    // Rehydrate dates
    if (data.messages) {
      data.messages = data.messages.map((m: any) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      }));
    }
    return data;
  } catch {
    return { conversationId: null, messages: [] };
  }
}

function saveState(
  tenantSlug: string,
  conversationId: string | null,
  messages: ChatMessage[]
): void {
  try {
    // Only persist the last 50 messages to keep storage small
    const trimmed = messages.slice(-50);
    localStorage.setItem(
      storageKey(tenantSlug),
      JSON.stringify({ conversationId, messages: trimmed })
    );
  } catch {
    // localStorage might be full or blocked — ignore silently
  }
}

// ─── Main Widget Class ────────────────────────────────────────

class VertexChatWidget {
  private config: WidgetConfig;
  private api: VertexAPI;
  private ws: WebSocket | null = null;
  private wsConnected = false;

  // State
  private conversationId: string | null = null;
  private businessName = "Support";
  private aiName = "AI Assistant";
  private messages: ChatMessage[] = [];
  private isOpen = false;
  private isTyping = false;
  private unreadCount = 0;

  // DOM references
  private shadowRoot!: ShadowRoot;
  private host!: HTMLDivElement;
  private bubble!: HTMLButtonElement;
  private badge!: HTMLSpanElement;
  private panel!: HTMLDivElement;
  private messagesContainer!: HTMLDivElement;
  private inputEl!: HTMLTextAreaElement;
  private sendBtn!: HTMLButtonElement;
  private typingIndicator!: HTMLDivElement;
  private errorBar!: HTMLDivElement;

  constructor(config: WidgetConfig) {
    this.config = config;
    this.api = new VertexAPI(config.apiBaseUrl);

    // Restore persisted state
    const saved = loadState(config.tenantSlug);
    this.conversationId = saved.conversationId;
    this.messages = saved.messages;

    this.render();
    this.initChat();
  }

  // ─── Rendering ─────────────────────────────────────────

  private render(): void {
    // Create host element with Shadow DOM
    this.host = document.createElement("div");
    this.host.id = "vertex-chat-widget";
    this.shadowRoot = this.host.attachShadow({ mode: "open" });

    // Inject styles
    const style = document.createElement("style");
    style.textContent = getWidgetStyles(this.config.primaryColor);
    this.shadowRoot.appendChild(style);

    // Build the chat bubble
    this.bubble = document.createElement("button");
    this.bubble.className = `vtx-bubble vtx-${this.config.position}`;
    this.bubble.setAttribute("aria-label", "Open chat");
    this.bubble.innerHTML = `${ICONS.chat}${ICONS.close}`;
    this.bubble.addEventListener("click", () => this.toggle());

    // Unread badge
    this.badge = document.createElement("span");
    this.badge.className = "vtx-badge";
    this.badge.textContent = "0";
    this.bubble.appendChild(this.badge);

    // Build the chat panel
    this.panel = document.createElement("div");
    this.panel.className = `vtx-panel vtx-${this.config.position}`;
    this.panel.innerHTML = this.buildPanelHTML();

    this.shadowRoot.appendChild(this.panel);
    this.shadowRoot.appendChild(this.bubble);
    document.body.appendChild(this.host);

    // Cache DOM references inside the shadow
    this.messagesContainer = this.panel.querySelector(
      ".vtx-messages"
    ) as HTMLDivElement;
    this.inputEl = this.panel.querySelector(".vtx-input") as HTMLTextAreaElement;
    this.sendBtn = this.panel.querySelector(
      ".vtx-send-btn"
    ) as HTMLButtonElement;
    this.typingIndicator = this.panel.querySelector(
      ".vtx-typing"
    ) as HTMLDivElement;
    this.errorBar = this.panel.querySelector(".vtx-error") as HTMLDivElement;

    // Wire up events
    this.sendBtn.addEventListener("click", () => this.handleSend());
    this.inputEl.addEventListener("keydown", (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.handleSend();
      }
    });
    this.inputEl.addEventListener("input", () => this.autoResizeInput());

    const closeBtn = this.panel.querySelector(
      ".vtx-header-close"
    ) as HTMLButtonElement;
    closeBtn.addEventListener("click", () => this.toggle());

    // Render persisted messages
    if (this.messages.length > 0) {
      this.messages.forEach((m) => this.appendMessageDOM(m));
      this.scrollToBottom();
    }
  }

  private buildPanelHTML(): string {
    return `
      <div class="vtx-header">
        <div class="vtx-header-avatar">${ICONS.bot}</div>
        <div class="vtx-header-info">
          <div class="vtx-header-name">${this.escapeHtml(this.businessName)}</div>
          <div class="vtx-header-status">
            <span class="vtx-status-dot"></span>
            Online
          </div>
        </div>
        <button class="vtx-header-close" aria-label="Close chat">${ICONS.minimize}</button>
      </div>
      <div class="vtx-messages"></div>
      <div class="vtx-typing" style="display:none;">
        <div class="vtx-typing-dot"></div>
        <div class="vtx-typing-dot"></div>
        <div class="vtx-typing-dot"></div>
      </div>
      <div class="vtx-error" style="display:none;"></div>
      <div class="vtx-input-area">
        <textarea class="vtx-input" placeholder="Type a message..." rows="1" maxlength="5000"></textarea>
        <button class="vtx-send-btn" aria-label="Send message">${ICONS.send}</button>
      </div>
      <div class="vtx-powered">
        Powered by <a href="https://vertexai.dev" target="_blank" rel="noopener">Vertex AI</a>
      </div>
    `;
  }

  // ─── Chat Lifecycle ────────────────────────────────────

  private async initChat(): Promise<void> {
    if (this.conversationId) {
      // Existing conversation — connect WebSocket directly
      this.connectWebSocket();
      return;
    }

    // No existing conversation — will start on first open or first message
  }

  private async startNewConversation(): Promise<void> {
    try {
      const data: StartChatResponse = await this.api.startChat(
        this.config.tenantSlug
      );

      this.conversationId = data.conversation_id;
      this.businessName = data.business_name || "Support";
      this.aiName = data.ai_name || "AI Assistant";

      // Update header with business name
      const headerName = this.panel.querySelector(".vtx-header-name");
      if (headerName) {
        headerName.textContent = this.businessName;
      }

      // Apply server-side primary color if available and no override
      if (data.primary_color && !this.scriptTagHasColor()) {
        this.config.primaryColor = data.primary_color;
      }

      // Show greeting
      if (data.greeting) {
        const greeting: ChatMessage = {
          id: "greeting-" + Date.now(),
          role: "assistant",
          content: data.greeting,
          timestamp: new Date(),
        };
        this.addMessage(greeting);
      }

      // Connect WebSocket for real-time messaging
      this.connectWebSocket();

      this.hideError();
      this.persist();
    } catch (err) {
      console.error("[Vertex Widget] Failed to start chat:", err);
      this.showError(
        "Unable to connect. Please try again.",
        () => this.startNewConversation()
      );
    }
  }

  private scriptTagHasColor(): boolean {
    const script = document.querySelector(
      'script[data-tenant-slug]'
    ) as HTMLScriptElement | null;
    return !!script?.dataset.primaryColor;
  }

  // ─── WebSocket ─────────────────────────────────────────

  private connectWebSocket(): void {
    if (!this.conversationId) return;

    try {
      const wsUrl = `${this.config.wsBaseUrl}/ws/chat/${this.config.tenantSlug}?conversation_id=${this.conversationId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.wsConnected = true;
        this.hideError();
        console.debug("[Vertex Widget] WebSocket connected");
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWSMessage(data);
        } catch {
          console.warn("[Vertex Widget] Invalid WS message");
        }
      };

      this.ws.onclose = () => {
        this.wsConnected = false;
        console.debug("[Vertex Widget] WebSocket disconnected");
        // Attempt reconnect after 3 seconds
        setTimeout(() => {
          if (!this.wsConnected && this.conversationId) {
            this.connectWebSocket();
          }
        }, 3000);
      };

      this.ws.onerror = () => {
        this.wsConnected = false;
        console.debug(
          "[Vertex Widget] WebSocket error — will use REST fallback"
        );
      };
    } catch {
      this.wsConnected = false;
      console.debug(
        "[Vertex Widget] WebSocket unavailable — using REST fallback"
      );
    }
  }

  private handleWSMessage(data: any): void {
    switch (data.type) {
      case "system":
        // Server greeting via WebSocket (only if no messages yet)
        if (this.messages.length === 0 && data.content) {
          this.addMessage({
            id: "ws-system-" + Date.now(),
            role: "assistant",
            content: data.content,
            timestamp: new Date(),
          });
        }
        if (data.conversation_id) {
          this.conversationId = data.conversation_id;
          this.persist();
        }
        break;

      case "message":
        if (data.role === "assistant") {
          this.setTyping(false);
          const msg: ChatMessage = {
            id: data.message_id || "ws-" + Date.now(),
            role: "assistant",
            content: data.content,
            timestamp: data.timestamp
              ? new Date(data.timestamp)
              : new Date(),
          };
          this.addMessage(msg);

          // Increment unread if panel is closed
          if (!this.isOpen) {
            this.unreadCount++;
            this.updateBadge();
          }
        }
        break;

      case "typing":
        if (data.sender === "assistant") {
          this.setTyping(data.is_typing);
        }
        break;
    }
  }

  // ─── Sending Messages ─────────────────────────────────

  private async handleSend(): Promise<void> {
    const content = this.inputEl.value.trim();
    if (!content) return;

    // Clear input immediately
    this.inputEl.value = "";
    this.autoResizeInput();

    // Start conversation if needed
    if (!this.conversationId) {
      await this.startNewConversation();
      if (!this.conversationId) return; // Failed to start
    }

    // Add user message to UI
    const userMsg: ChatMessage = {
      id: "user-" + Date.now(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    this.addMessage(userMsg);
    this.setTyping(true);

    // Send via WebSocket if connected, otherwise REST
    if (this.wsConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "message",
          content,
        })
      );
    } else {
      // REST fallback
      try {
        const response: MessageResponse = await this.api.sendMessage(
          this.config.tenantSlug,
          this.conversationId!,
          content
        );

        this.setTyping(false);
        const aiMsg: ChatMessage = {
          id: response.id,
          role: "assistant",
          content: response.content,
          timestamp: new Date(response.created_at),
        };
        this.addMessage(aiMsg);
      } catch (err) {
        this.setTyping(false);
        console.error("[Vertex Widget] Send failed:", err);
        this.showError("Failed to send message. Please try again.", () =>
          this.retrySend(content)
        );
      }
    }
  }

  private async retrySend(content: string): Promise<void> {
    this.hideError();
    this.setTyping(true);

    try {
      const response = await this.api.sendMessage(
        this.config.tenantSlug,
        this.conversationId!,
        content
      );

      this.setTyping(false);
      this.addMessage({
        id: response.id,
        role: "assistant",
        content: response.content,
        timestamp: new Date(response.created_at),
      });
    } catch (err) {
      this.setTyping(false);
      this.showError("Still unable to send. Please check your connection.");
    }
  }

  // ─── Message Management ────────────────────────────────

  private addMessage(msg: ChatMessage): void {
    this.messages.push(msg);
    this.appendMessageDOM(msg);
    this.scrollToBottom();
    this.persist();
  }

  private appendMessageDOM(msg: ChatMessage): void {
    const div = document.createElement("div");
    div.className = `vtx-msg vtx-msg-${msg.role}`;

    const bubble = document.createElement("div");
    bubble.className = "vtx-msg-bubble";
    bubble.textContent = msg.content;

    const time = document.createElement("div");
    time.className = "vtx-msg-time";
    time.textContent = this.formatTime(msg.timestamp);

    div.appendChild(bubble);
    div.appendChild(time);
    this.messagesContainer.appendChild(div);
  }

  // ─── UI Helpers ────────────────────────────────────────

  private toggle(): void {
    this.isOpen = !this.isOpen;

    if (this.isOpen) {
      this.panel.classList.add("vtx-visible");
      this.bubble.classList.add("vtx-open");
      this.unreadCount = 0;
      this.updateBadge();
      this.inputEl.focus();
      this.scrollToBottom();

      // Start conversation on first open if needed
      if (!this.conversationId && this.messages.length === 0) {
        this.startNewConversation();
      }
    } else {
      this.panel.classList.remove("vtx-visible");
      this.bubble.classList.remove("vtx-open");
    }
  }

  private setTyping(typing: boolean): void {
    this.isTyping = typing;
    if (this.typingIndicator) {
      this.typingIndicator.style.display = typing ? "flex" : "none";
    }
    if (typing) {
      this.scrollToBottom();
    }
  }

  private scrollToBottom(): void {
    requestAnimationFrame(() => {
      if (this.messagesContainer) {
        this.messagesContainer.scrollTop =
          this.messagesContainer.scrollHeight;
      }
    });
  }

  private autoResizeInput(): void {
    this.inputEl.style.height = "auto";
    this.inputEl.style.height =
      Math.min(this.inputEl.scrollHeight, 120) + "px";
  }

  private updateBadge(): void {
    if (this.unreadCount > 0) {
      this.badge.textContent =
        this.unreadCount > 9 ? "9+" : String(this.unreadCount);
      this.badge.classList.add("vtx-visible");
    } else {
      this.badge.classList.remove("vtx-visible");
    }
  }

  private showError(message: string, retry?: () => void): void {
    if (!this.errorBar) return;
    this.errorBar.innerHTML = this.escapeHtml(message);
    if (retry) {
      const btn = document.createElement("button");
      btn.className = "vtx-error-retry";
      btn.textContent = "Retry";
      btn.addEventListener("click", retry);
      this.errorBar.appendChild(document.createElement("br"));
      this.errorBar.appendChild(btn);
    }
    this.errorBar.style.display = "block";
  }

  private hideError(): void {
    if (this.errorBar) {
      this.errorBar.style.display = "none";
      this.errorBar.innerHTML = "";
    }
  }

  private persist(): void {
    saveState(this.config.tenantSlug, this.conversationId, this.messages);
  }

  private formatTime(date: Date): string {
    try {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  private escapeHtml(str: string): string {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ─── Public API ────────────────────────────────────────

  /** Open the chat panel programmatically */
  open(): void {
    if (!this.isOpen) this.toggle();
  }

  /** Close the chat panel programmatically */
  close(): void {
    if (this.isOpen) this.toggle();
  }

  /** Destroy the widget and clean up */
  destroy(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.host.remove();
  }
}

// ─── Auto-initialization ──────────────────────────────────────

function autoInit(): void {
  // Find the script tag that loaded this file
  const scripts = document.querySelectorAll(
    'script[data-tenant-slug]'
  ) as NodeListOf<HTMLScriptElement>;

  const script = scripts[scripts.length - 1]; // Last matching script tag
  if (!script) {
    console.warn(
      "[Vertex Widget] No script tag with data-tenant-slug found. " +
        "Add data-tenant-slug to your script tag to auto-initialize."
    );
    return;
  }

  const tenantSlug = script.dataset.tenantSlug;
  if (!tenantSlug) {
    console.error("[Vertex Widget] data-tenant-slug is required.");
    return;
  }

  const primaryColor = script.dataset.primaryColor || "#6366f1";
  const position =
    (script.dataset.position as "bottom-right" | "bottom-left") ||
    "bottom-right";
  const apiBaseUrl = script.dataset.apiBaseUrl || window.location.origin;

  // Derive WS base URL from API base URL
  const wsProtocol = apiBaseUrl.startsWith("https") ? "wss" : "ws";
  const wsHost = apiBaseUrl.replace(/^https?:\/\//, "");
  const wsBaseUrl = script.dataset.wsBaseUrl || `${wsProtocol}://${wsHost}`;

  const widget = new VertexChatWidget({
    tenantSlug,
    primaryColor,
    position,
    apiBaseUrl,
    wsBaseUrl,
  });

  // Expose on window for programmatic access
  (window as any).vertexWidget = widget;
}

// Run when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", autoInit);
} else {
  autoInit();
}

export { VertexChatWidget };
