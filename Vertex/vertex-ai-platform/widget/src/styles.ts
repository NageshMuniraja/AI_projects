/**
 * Vertex Widget — Scoped CSS Styles
 *
 * All styles are injected as template literals inside a shadow DOM
 * to prevent conflicts with the host page.
 */

export function getWidgetStyles(primaryColor: string): string {
  // Derive lighter/darker variants from the primary color
  const lighterBg = hexToRgba(primaryColor, 0.08);
  const hoverColor = hexToRgba(primaryColor, 0.9);

  return `
    /* ─── Reset & Host ─────────────────────────────────────── */

    :host {
      all: initial;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
        'Helvetica Neue', Arial, sans-serif;
      font-size: 14px;
      line-height: 1.5;
      color: #1f2937;
      direction: ltr;
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    /* ─── Chat Bubble Button ──────────────────────────────── */

    .vtx-bubble {
      position: fixed;
      z-index: 2147483646;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: ${primaryColor};
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
                  box-shadow 0.25s ease;
      outline: none;
    }

    .vtx-bubble:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 24px rgba(0, 0, 0, 0.22);
    }

    .vtx-bubble:active {
      transform: scale(0.96);
    }

    .vtx-bubble.vtx-bottom-right {
      bottom: 24px;
      right: 24px;
    }

    .vtx-bubble.vtx-bottom-left {
      bottom: 24px;
      left: 24px;
    }

    .vtx-bubble svg {
      width: 28px;
      height: 28px;
      fill: #ffffff;
      transition: transform 0.3s ease;
    }

    .vtx-bubble.vtx-open svg.vtx-icon-chat {
      display: none;
    }

    .vtx-bubble.vtx-open svg.vtx-icon-close {
      display: block;
    }

    .vtx-bubble:not(.vtx-open) svg.vtx-icon-close {
      display: none;
    }

    /* Unread badge */
    .vtx-badge {
      position: absolute;
      top: -4px;
      right: -4px;
      width: 20px;
      height: 20px;
      background: #ef4444;
      color: #fff;
      border-radius: 50%;
      font-size: 11px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transform: scale(0);
      transition: all 0.25s ease;
    }

    .vtx-badge.vtx-visible {
      opacity: 1;
      transform: scale(1);
    }

    /* ─── Chat Panel ──────────────────────────────────────── */

    .vtx-panel {
      position: fixed;
      z-index: 2147483647;
      width: 380px;
      height: 560px;
      max-height: calc(100vh - 100px);
      border-radius: 16px;
      background: #ffffff;
      box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15),
                  0 0 0 1px rgba(0, 0, 0, 0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                  transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .vtx-panel.vtx-bottom-right {
      bottom: 96px;
      right: 24px;
    }

    .vtx-panel.vtx-bottom-left {
      bottom: 96px;
      left: 24px;
    }

    .vtx-panel.vtx-visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    /* ─── Header ──────────────────────────────────────────── */

    .vtx-header {
      background: ${primaryColor};
      color: #ffffff;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }

    .vtx-header-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .vtx-header-avatar svg {
      width: 22px;
      height: 22px;
      fill: #ffffff;
    }

    .vtx-header-info {
      flex: 1;
      min-width: 0;
    }

    .vtx-header-name {
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .vtx-header-status {
      font-size: 12px;
      opacity: 0.85;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .vtx-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #34d399;
      display: inline-block;
    }

    .vtx-header-close {
      background: rgba(255, 255, 255, 0.15);
      border: none;
      color: #ffffff;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
      flex-shrink: 0;
    }

    .vtx-header-close:hover {
      background: rgba(255, 255, 255, 0.25);
    }

    .vtx-header-close svg {
      width: 16px;
      height: 16px;
      fill: #ffffff;
    }

    /* ─── Messages Area ───────────────────────────────────── */

    .vtx-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      background: #f9fafb;
      scroll-behavior: smooth;
    }

    .vtx-messages::-webkit-scrollbar {
      width: 5px;
    }

    .vtx-messages::-webkit-scrollbar-track {
      background: transparent;
    }

    .vtx-messages::-webkit-scrollbar-thumb {
      background: #d1d5db;
      border-radius: 10px;
    }

    /* ─── Message Bubbles ─────────────────────────────────── */

    .vtx-msg {
      display: flex;
      flex-direction: column;
      max-width: 82%;
      animation: vtxFadeIn 0.25s ease;
    }

    .vtx-msg-assistant {
      align-self: flex-start;
    }

    .vtx-msg-user {
      align-self: flex-end;
    }

    .vtx-msg-bubble {
      padding: 10px 14px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
      white-space: pre-wrap;
    }

    .vtx-msg-assistant .vtx-msg-bubble {
      background: #ffffff;
      color: #1f2937;
      border: 1px solid #e5e7eb;
      border-bottom-left-radius: 4px;
    }

    .vtx-msg-user .vtx-msg-bubble {
      background: ${primaryColor};
      color: #ffffff;
      border-bottom-right-radius: 4px;
    }

    .vtx-msg-time {
      font-size: 11px;
      color: #9ca3af;
      margin-top: 3px;
      padding: 0 4px;
    }

    .vtx-msg-user .vtx-msg-time {
      text-align: right;
    }

    /* System messages (greeting, errors) */
    .vtx-msg-system {
      align-self: center;
      max-width: 90%;
    }

    .vtx-msg-system .vtx-msg-bubble {
      background: ${lighterBg};
      color: #374151;
      border: none;
      border-radius: 12px;
      text-align: center;
      font-size: 13px;
    }

    /* ─── Typing Indicator ────────────────────────────────── */

    .vtx-typing {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 12px 16px;
      align-self: flex-start;
      animation: vtxFadeIn 0.25s ease;
    }

    .vtx-typing-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #9ca3af;
      animation: vtxBounce 1.4s ease-in-out infinite;
    }

    .vtx-typing-dot:nth-child(2) {
      animation-delay: 0.16s;
    }

    .vtx-typing-dot:nth-child(3) {
      animation-delay: 0.32s;
    }

    /* ─── Input Area ──────────────────────────────────────── */

    .vtx-input-area {
      padding: 12px 16px;
      border-top: 1px solid #e5e7eb;
      background: #ffffff;
      display: flex;
      align-items: flex-end;
      gap: 8px;
      flex-shrink: 0;
    }

    .vtx-input {
      flex: 1;
      border: 1.5px solid #e5e7eb;
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 14px;
      font-family: inherit;
      line-height: 1.5;
      resize: none;
      outline: none;
      max-height: 120px;
      min-height: 42px;
      background: #f9fafb;
      color: #1f2937;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    .vtx-input:focus {
      border-color: ${primaryColor};
      box-shadow: 0 0 0 3px ${hexToRgba(primaryColor, 0.12)};
      background: #ffffff;
    }

    .vtx-input::placeholder {
      color: #9ca3af;
    }

    .vtx-send-btn {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: ${primaryColor};
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: background 0.2s, transform 0.15s;
      outline: none;
    }

    .vtx-send-btn:hover {
      background: ${hoverColor};
    }

    .vtx-send-btn:active {
      transform: scale(0.93);
    }

    .vtx-send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .vtx-send-btn svg {
      width: 18px;
      height: 18px;
      fill: #ffffff;
    }

    /* ─── Powered-by Footer ───────────────────────────────── */

    .vtx-powered {
      text-align: center;
      padding: 6px;
      font-size: 11px;
      color: #9ca3af;
      background: #ffffff;
      border-top: 1px solid #f3f4f6;
      flex-shrink: 0;
    }

    .vtx-powered a {
      color: #6b7280;
      text-decoration: none;
      font-weight: 500;
    }

    .vtx-powered a:hover {
      color: ${primaryColor};
    }

    /* ─── Error State ─────────────────────────────────────── */

    .vtx-error {
      padding: 12px 16px;
      background: #fef2f2;
      color: #dc2626;
      font-size: 13px;
      text-align: center;
      border-top: 1px solid #fecaca;
      flex-shrink: 0;
    }

    .vtx-error-retry {
      background: none;
      border: 1px solid #dc2626;
      color: #dc2626;
      padding: 4px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      margin-top: 6px;
      transition: background 0.2s;
    }

    .vtx-error-retry:hover {
      background: #dc2626;
      color: #fff;
    }

    /* ─── Animations ──────────────────────────────────────── */

    @keyframes vtxFadeIn {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes vtxBounce {
      0%, 80%, 100% {
        transform: scale(0.6);
        opacity: 0.4;
      }
      40% {
        transform: scale(1);
        opacity: 1;
      }
    }

    /* ─── Mobile Responsive ───────────────────────────────── */

    @media (max-width: 480px) {
      .vtx-panel {
        width: 100vw;
        height: 100vh;
        max-height: 100vh;
        border-radius: 0;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
      }

      .vtx-panel.vtx-bottom-right,
      .vtx-panel.vtx-bottom-left {
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
      }
    }
  `;
}

/**
 * Convert a hex color to rgba string.
 */
function hexToRgba(hex: string, alpha: number): string {
  const cleaned = hex.replace("#", "");
  const bigint = parseInt(cleaned, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
