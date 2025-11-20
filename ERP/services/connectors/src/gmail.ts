import { google } from 'googleapis';
import CryptoJS from 'crypto-js';

const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'your-secret-key';

export class GmailConnector {
  private oauth2Client: any;

  constructor(credentials?: any) {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      process.env.GOOGLE_REDIRECT_URI
    );

    if (credentials) {
      this.oauth2Client.setCredentials(credentials);
    }
  }

  getAuthUrl(): string {
    const scopes = [
      'https://www.googleapis.com/auth/gmail.send',
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/gmail.modify',
    ];

    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent',
    });
  }

  async handleCallback(code: string) {
    const { tokens } = await this.oauth2Client.getToken(code);
    return tokens;
  }

  async sendEmail(to: string, subject: string, body: string) {
    const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });

    const message = [
      `To: ${to}`,
      'Content-Type: text/html; charset=utf-8',
      'MIME-Version: 1.0',
      `Subject: ${subject}`,
      '',
      body,
    ].join('\n');

    const encodedMessage = Buffer.from(message)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    const result = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage,
      },
    });

    return result.data;
  }

  async listEmails(maxResults: number = 10) {
    const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });

    const result = await gmail.users.messages.list({
      userId: 'me',
      maxResults,
    });

    return result.data.messages || [];
  }

  async getEmail(messageId: string) {
    const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });

    const result = await gmail.users.messages.get({
      userId: 'me',
      id: messageId,
      format: 'full',
    });

    return result.data;
  }

  async testConnection(): Promise<boolean> {
    try {
      const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });
      await gmail.users.getProfile({ userId: 'me' });
      return true;
    } catch (error) {
      return false;
    }
  }

  static encryptCredentials(credentials: any): string {
    return CryptoJS.AES.encrypt(
      JSON.stringify(credentials),
      ENCRYPTION_KEY
    ).toString();
  }

  static decryptCredentials(encrypted: string): any {
    const bytes = CryptoJS.AES.decrypt(encrypted, ENCRYPTION_KEY);
    return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
  }
}
