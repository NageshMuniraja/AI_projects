import type {
  AuthTokens,
  LoginRequest,
  SignupRequest,
  User,
  Tenant,
  Conversation,
  Message,
  Service,
  Appointment,
  Lead,
  KnowledgeDocument,
  AnalyticsSummary,
  PaginatedResponse,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.message || `Request failed with status ${response.status}`);
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }

  // Auth
  async login(data: LoginRequest): Promise<AuthTokens> {
    const formData = new URLSearchParams();
    formData.append("username", data.email);
    formData.append("password", data.password);

    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Login failed");
    }

    const tokens: AuthTokens = await response.json();
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
    }
    return tokens;
  }

  async signup(data: SignupRequest): Promise<AuthTokens> {
    return this.request<AuthTokens>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  // Tenant
  async getTenant(): Promise<Tenant> {
    return this.request<Tenant>("/tenant");
  }

  async updateTenant(data: Partial<Tenant>): Promise<Tenant> {
    return this.request<Tenant>("/tenant", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Conversations
  async getConversations(params?: {
    status?: string;
    channel?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Conversation>> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.channel) searchParams.set("channel", params.channel);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return this.request<PaginatedResponse<Conversation>>(
      `/conversations${query ? `?${query}` : ""}`
    );
  }

  async getConversation(id: string): Promise<Conversation> {
    return this.request<Conversation>(`/conversations/${id}`);
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    return this.request<Message[]>(`/conversations/${conversationId}/messages`);
  }

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    return this.request<Message>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, role: "user" }),
    });
  }

  // Services
  async getServices(): Promise<Service[]> {
    return this.request<Service[]>("/services");
  }

  async createService(data: Partial<Service>): Promise<Service> {
    return this.request<Service>("/services", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateService(id: string, data: Partial<Service>): Promise<Service> {
    return this.request<Service>(`/services/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteService(id: string): Promise<void> {
    return this.request<void>(`/services/${id}`, { method: "DELETE" });
  }

  // Appointments
  async getAppointments(params?: {
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Appointment>> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return this.request<PaginatedResponse<Appointment>>(
      `/appointments${query ? `?${query}` : ""}`
    );
  }

  async updateAppointment(id: string, data: Partial<Appointment>): Promise<Appointment> {
    return this.request<Appointment>(`/appointments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Leads
  async getLeads(params?: {
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Lead>> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    const query = searchParams.toString();
    return this.request<PaginatedResponse<Lead>>(
      `/leads${query ? `?${query}` : ""}`
    );
  }

  async updateLead(id: string, data: Partial<Lead>): Promise<Lead> {
    return this.request<Lead>(`/leads/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Knowledge Base
  async getDocuments(): Promise<KnowledgeDocument[]> {
    return this.request<KnowledgeDocument[]>("/knowledge");
  }

  async createDocument(data: Partial<KnowledgeDocument>): Promise<KnowledgeDocument> {
    return this.request<KnowledgeDocument>("/knowledge", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateDocument(id: string, data: Partial<KnowledgeDocument>): Promise<KnowledgeDocument> {
    return this.request<KnowledgeDocument>(`/knowledge/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteDocument(id: string): Promise<void> {
    return this.request<void>(`/knowledge/${id}`, { method: "DELETE" });
  }

  // Analytics
  async getAnalytics(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<AnalyticsSummary> {
    const searchParams = new URLSearchParams();
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);
    const query = searchParams.toString();
    return this.request<AnalyticsSummary>(
      `/analytics${query ? `?${query}` : ""}`
    );
  }
}

export const api = new ApiClient(BASE_URL);
export default api;
