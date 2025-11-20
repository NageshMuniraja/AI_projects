// User & Team Types
export interface User {
  id: string;
  clerkUserId: string;
  email: string;
  fullName?: string;
  avatarUrl?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  plan: 'free' | 'starter' | 'pro' | 'enterprise';
  status: 'active' | 'suspended' | 'cancelled';
  createdAt: Date;
  updatedAt: Date;
}

export interface TeamMember {
  id: string;
  teamId: string;
  userId: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joinedAt: Date;
}

// Connector Types
export type ConnectorType = 
  | 'gmail' 
  | 'calendar' 
  | 'hubspot' 
  | 'zoho'
  | 'stripe' 
  | 'razorpay' 
  | 'whatsapp'
  | 'salesforce';

export interface Connector {
  id: string;
  teamId: string;
  type: ConnectorType;
  name: string;
  credentialsEncrypted: string;
  config: Record<string, any>;
  status: 'active' | 'inactive' | 'error' | 'pending';
  lastSyncAt?: Date;
  errorMessage?: string;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ConnectorCredentials {
  gmail?: {
    accessToken: string;
    refreshToken: string;
    expiresAt: Date;
  };
  calendar?: {
    accessToken: string;
    refreshToken: string;
    expiresAt: Date;
  };
  hubspot?: {
    accessToken: string;
    refreshToken?: string;
  };
  stripe?: {
    secretKey: string;
    publishableKey: string;
  };
  razorpay?: {
    keyId: string;
    keySecret: string;
  };
  whatsapp?: {
    accountSid: string;
    authToken: string;
    phoneNumber: string;
  };
}

// Agent Types
export type AgentType = 'finance' | 'sales' | 'reporting' | 'supervisor';

export interface AgentAction {
  id: string;
  teamId: string;
  agentType: AgentType;
  actionType: string;
  inputData: Record<string, any>;
  outputData?: Record<string, any>;
  confidenceScore?: number;
  reasoning?: string;
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'failed';
  approvedBy?: string;
  approvedAt?: Date;
  executedAt?: Date;
  errorMessage?: string;
  createdAt: Date;
}

export interface AgentExecutionRequest {
  action: string;
  data: Record<string, any>;
}

export interface AgentExecutionResponse {
  success: boolean;
  result?: any;
  error?: string;
}

// Workflow Types
export interface WorkflowExecution {
  id: string;
  teamId: string;
  workflowId: string;
  workflowName?: string;
  n8nExecutionId?: string;
  triggeredBy: 'agent' | 'user' | 'webhook' | 'schedule';
  triggerSourceId?: string;
  status: 'running' | 'success' | 'failed' | 'cancelled';
  inputData?: Record<string, any>;
  outputData?: Record<string, any>;
  errorMessage?: string;
  startedAt: Date;
  completedAt?: Date;
  durationMs?: number;
}

// Finance Types
export interface Invoice {
  id: string;
  teamId: string;
  invoiceNumber: string;
  vendorName?: string;
  amount: number;
  currency: string;
  issueDate: Date;
  dueDate: Date;
  status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  paymentDate?: Date;
  paymentReference?: string;
  pdfUrl?: string;
  parsedData?: Record<string, any>;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Sales Types
export interface Lead {
  id: string;
  teamId: string;
  email: string;
  fullName?: string;
  company?: string;
  role?: string;
  phone?: string;
  industry?: string;
  companySize?: number;
  budget?: number;
  timeline?: string;
  source?: string;
  score: number;
  priority: 'low' | 'medium' | 'high';
  status: 'new' | 'contacted' | 'qualified' | 'opportunity' | 'won' | 'lost';
  assignedTo?: string;
  crmId?: string;
  lastContactAt?: Date;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface LeadActivity {
  id: string;
  leadId: string;
  activityType: 'email' | 'call' | 'meeting' | 'note';
  description: string;
  performedBy?: string;
  performedAt: Date;
}

// Reporting Types
export interface Report {
  id: string;
  teamId: string;
  reportType: 'daily_summary' | 'weekly_performance' | 'financial_overview' | 'custom';
  periodStart?: Date;
  periodEnd?: Date;
  format: 'pdf' | 'html' | 'json';
  content: Record<string, any>;
  fileUrl?: string;
  generatedBy: 'agent' | 'user';
  createdAt: Date;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
