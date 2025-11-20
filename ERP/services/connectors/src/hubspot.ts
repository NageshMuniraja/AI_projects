import axios from 'axios';

export class HubSpotConnector {
  private accessToken: string;
  private baseUrl = 'https://api.hubapi.com';

  constructor(accessToken: string) {
    this.accessToken = accessToken;
  }

  private getHeaders() {
    return {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
    };
  }

  async createContact(contactData: {
    email: string;
    firstname?: string;
    lastname?: string;
    company?: string;
    phone?: string;
    lifecyclestage?: string;
  }) {
    const response = await axios.post(
      `${this.baseUrl}/crm/v3/objects/contacts`,
      {
        properties: contactData,
      },
      { headers: this.getHeaders() }
    );

    return response.data;
  }

  async updateContact(contactId: string, properties: Record<string, any>) {
    const response = await axios.patch(
      `${this.baseUrl}/crm/v3/objects/contacts/${contactId}`,
      { properties },
      { headers: this.getHeaders() }
    );

    return response.data;
  }

  async getContact(contactId: string) {
    const response = await axios.get(
      `${this.baseUrl}/crm/v3/objects/contacts/${contactId}`,
      { headers: this.getHeaders() }
    );

    return response.data;
  }

  async searchContacts(email: string) {
    const response = await axios.post(
      `${this.baseUrl}/crm/v3/objects/contacts/search`,
      {
        filterGroups: [
          {
            filters: [
              {
                propertyName: 'email',
                operator: 'EQ',
                value: email,
              },
            ],
          },
        ],
      },
      { headers: this.getHeaders() }
    );

    return response.data.results || [];
  }

  async createDeal(dealData: {
    dealname: string;
    amount?: number;
    dealstage?: string;
    pipeline?: string;
    closedate?: string;
  }) {
    const response = await axios.post(
      `${this.baseUrl}/crm/v3/objects/deals`,
      { properties: dealData },
      { headers: this.getHeaders() }
    );

    return response.data;
  }

  async testConnection(): Promise<boolean> {
    try {
      await axios.get(`${this.baseUrl}/crm/v3/objects/contacts?limit=1`, {
        headers: this.getHeaders(),
      });
      return true;
    } catch (error) {
      return false;
    }
  }
}
