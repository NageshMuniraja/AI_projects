/**
 * Vertex Widget — REST API Client
 *
 * Handles communication with the Vertex AI Platform backend
 * when WebSocket is unavailable or as a fallback.
 */

export interface StartChatResponse {
  conversation_id: string;
  greeting: string;
  business_name: string;
  ai_name: string;
  primary_color: string | null;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  channel: string | null;
  tokens_used: number | null;
  confidence: number | null;
  status: string;
  created_at: string;
}

export class VertexAPI {
  private baseUrl: string;

  constructor(baseUrl: string = "") {
    // Default to same origin if not specified
    this.baseUrl = baseUrl || window.location.origin;
  }

  /**
   * Start a new chat session for the given tenant.
   */
  async startChat(
    tenantSlug: string,
    visitorName?: string
  ): Promise<StartChatResponse> {
    const url = new URL(
      `/api/v1/chat/widget/${tenantSlug}/start`,
      this.baseUrl
    );

    const body: Record<string, string> = {};
    if (visitorName) {
      body.visitor_name = visitorName;
    }

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Failed to start chat (${response.status})`
      );
    }

    return response.json();
  }

  /**
   * Send a message and receive the AI response (REST fallback).
   */
  async sendMessage(
    tenantSlug: string,
    conversationId: string,
    content: string
  ): Promise<MessageResponse> {
    const url = new URL(
      `/api/v1/chat/widget/${tenantSlug}/message?conversation_id=${conversationId}`,
      this.baseUrl
    );

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, channel: "web" }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Failed to send message (${response.status})`
      );
    }

    return response.json();
  }
}
