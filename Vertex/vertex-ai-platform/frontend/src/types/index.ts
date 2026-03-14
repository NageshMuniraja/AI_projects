export interface Tenant {
  id: string;
  name: string;
  slug: string;
  industry: string;
  plan: "free" | "starter" | "professional" | "enterprise";
  is_active: boolean;
  settings: TenantSettings;
  created_at: string;
  updated_at: string;
}

export interface TenantSettings {
  ai_persona_name: string;
  ai_tone: string;
  greeting_message: string;
  custom_instructions: string;
  widget_primary_color: string;
  widget_position: "bottom-right" | "bottom-left";
  whatsapp_phone_number?: string;
  whatsapp_api_key?: string;
  business_hours?: BusinessHours;
}

export interface BusinessHours {
  timezone: string;
  schedule: {
    [day: string]: { open: string; close: string; is_open: boolean };
  };
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "agent" | "viewer";
  tenant_id: string;
  is_active: boolean;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  tenant_id: string;
  contact_name: string;
  contact_phone?: string;
  contact_email?: string;
  channel: "whatsapp" | "web" | "voice" | "email";
  status: "active" | "resolved" | "escalated" | "pending";
  intent?: string;
  sentiment?: "positive" | "neutral" | "negative";
  language: string;
  metadata?: Record<string, unknown>;
  messages_count: number;
  last_message_at: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  message_type: "text" | "image" | "audio" | "document" | "location";
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Service {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  duration_minutes: number;
  price: number;
  currency: string;
  is_active: boolean;
  category?: string;
  created_at: string;
  updated_at: string;
}

export interface Appointment {
  id: string;
  tenant_id: string;
  conversation_id?: string;
  service_id?: string;
  service_name: string;
  customer_name: string;
  customer_phone?: string;
  customer_email?: string;
  scheduled_at: string;
  duration_minutes: number;
  status: "scheduled" | "confirmed" | "completed" | "cancelled" | "no_show";
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: string;
  tenant_id: string;
  conversation_id?: string;
  name: string;
  email?: string;
  phone?: string;
  source: "whatsapp" | "web" | "voice" | "email" | "manual";
  status: "new" | "contacted" | "qualified" | "converted" | "lost";
  score: number;
  notes?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocument {
  id: string;
  tenant_id: string;
  title: string;
  content: string;
  doc_type: "faq" | "policy" | "product" | "general";
  source_url?: string;
  is_active: boolean;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsSummary {
  total_conversations: number;
  active_conversations: number;
  resolved_conversations: number;
  escalated_conversations: number;
  total_messages: number;
  total_appointments: number;
  upcoming_appointments: number;
  total_leads: number;
  qualified_leads: number;
  converted_leads: number;
  avg_response_time_seconds: number;
  avg_resolution_time_seconds: number;
  satisfaction_score: number;
  messages_by_day: { date: string; count: number }[];
  conversations_by_channel: { channel: string; count: number }[];
  top_intents: { intent: string; count: number }[];
  sentiment_distribution: { sentiment: string; count: number }[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  business_name: string;
  industry: string;
  email: string;
  password: string;
  full_name: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
