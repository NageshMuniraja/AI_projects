import axios from 'axios';

export class StripeConnector {
  private secretKey: string;
  private baseUrl = 'https://api.stripe.com/v1';

  constructor(secretKey: string) {
    this.secretKey = secretKey;
  }

  private getHeaders() {
    return {
      'Authorization': `Bearer ${this.secretKey}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    };
  }

  async listPayments(limit: number = 10) {
    const response = await axios.get(`${this.baseUrl}/payment_intents`, {
      headers: this.getHeaders(),
      params: { limit },
    });

    return response.data.data || [];
  }

  async getPayment(paymentIntentId: string) {
    const response = await axios.get(
      `${this.baseUrl}/payment_intents/${paymentIntentId}`,
      { headers: this.getHeaders() }
    );

    return response.data;
  }

  async listCustomers(limit: number = 10) {
    const response = await axios.get(`${this.baseUrl}/customers`, {
      headers: this.getHeaders(),
      params: { limit },
    });

    return response.data.data || [];
  }

  async getCustomer(customerId: string) {
    const response = await axios.get(`${this.baseUrl}/customers/${customerId}`, {
      headers: this.getHeaders(),
    });

    return response.data;
  }

  async createInvoice(invoiceData: {
    customer: string;
    description?: string;
    auto_advance?: boolean;
  }) {
    const params = new URLSearchParams();
    Object.entries(invoiceData).forEach(([key, value]) => {
      params.append(key, String(value));
    });

    const response = await axios.post(`${this.baseUrl}/invoices`, params, {
      headers: this.getHeaders(),
    });

    return response.data;
  }

  async listInvoices(limit: number = 10, status?: string) {
    const params: any = { limit };
    if (status) params.status = status;

    const response = await axios.get(`${this.baseUrl}/invoices`, {
      headers: this.getHeaders(),
      params,
    });

    return response.data.data || [];
  }

  async testConnection(): Promise<boolean> {
    try {
      await axios.get(`${this.baseUrl}/customers?limit=1`, {
        headers: this.getHeaders(),
      });
      return true;
    } catch (error) {
      return false;
    }
  }
}
