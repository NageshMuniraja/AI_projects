import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token interceptor
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Agent APIs
  async executeFinanceAgent(action: string, data: any) {
    const response = await this.client.post('/api/agents/finance/run', {
      action,
      data,
    });
    return response.data;
  }

  async executeSalesAgent(action: string, data: any) {
    const response = await this.client.post('/api/agents/sales/run', {
      action,
      data,
    });
    return response.data;
  }

  async executeReportingAgent(action: string, data: any) {
    const response = await this.client.post('/api/agents/reporting/run', {
      action,
      data,
    });
    return response.data;
  }

  async getAgentActions(agentType: string, limit: number = 20) {
    const response = await this.client.get(`/api/agents/${agentType}/actions`, {
      params: { limit },
    });
    return response.data;
  }

  // Connector APIs
  async listConnectors() {
    const response = await this.client.get('/api/connectors');
    return response.data;
  }

  async getConnector(id: string) {
    const response = await this.client.get(`/api/connectors/${id}`);
    return response.data;
  }

  async createConnector(data: {
    type: string;
    name: string;
    credentials: any;
    config?: any;
  }) {
    const response = await this.client.post('/api/connectors', data);
    return response.data;
  }

  async updateConnector(id: string, data: any) {
    const response = await this.client.put(`/api/connectors/${id}`, data);
    return response.data;
  }

  async deleteConnector(id: string) {
    const response = await this.client.delete(`/api/connectors/${id}`);
    return response.data;
  }

  async testConnector(id: string) {
    const response = await this.client.post(`/api/connectors/${id}/test`);
    return response.data;
  }

  // Workflow APIs
  async executeWorkflow(workflowId: string, data: any) {
    const response = await this.client.post('/api/workflows/execute', {
      workflowId,
      data,
    });
    return response.data;
  }

  async getWorkflowExecutions(limit: number = 20) {
    const response = await this.client.get('/api/workflows/executions', {
      params: { limit },
    });
    return response.data;
  }

  async getExecutionLogs(executionId: string) {
    const response = await this.client.get(`/api/workflows/executions/${executionId}/logs`);
    return response.data;
  }

  // Invoices
  async listInvoices(params?: { status?: string; limit?: number }) {
    const response = await this.client.get('/api/invoices', { params });
    return response.data;
  }

  async createInvoice(data: any) {
    const response = await this.client.post('/api/invoices', data);
    return response.data;
  }

  // Leads
  async listLeads(params?: { status?: string; priority?: string; limit?: number }) {
    const response = await this.client.get('/api/leads', { params });
    return response.data;
  }

  async createLead(data: any) {
    const response = await this.client.post('/api/leads', data);
    return response.data;
  }

  async updateLead(id: string, data: any) {
    const response = await this.client.put(`/api/leads/${id}`, data);
    return response.data;
  }

  // Reports
  async listReports(params?: { type?: string; limit?: number }) {
    const response = await this.client.get('/api/reports', { params });
    return response.data;
  }

  async generateReport(type: string, config: any) {
    const response = await this.client.post('/api/reports/generate', {
      type,
      config,
    });
    return response.data;
  }

  async downloadReport(id: string) {
    const response = await this.client.get(`/api/reports/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
