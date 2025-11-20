import { google } from 'googleapis';

export class CalendarConnector {
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
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.events',
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

  async createEvent(eventData: {
    summary: string;
    description?: string;
    location?: string;
    startTime: Date;
    endTime: Date;
    attendees?: string[];
  }) {
    const calendar = google.calendar({ version: 'v3', auth: this.oauth2Client });

    const event = {
      summary: eventData.summary,
      description: eventData.description,
      location: eventData.location,
      start: {
        dateTime: eventData.startTime.toISOString(),
        timeZone: 'America/New_York',
      },
      end: {
        dateTime: eventData.endTime.toISOString(),
        timeZone: 'America/New_York',
      },
      attendees: eventData.attendees?.map(email => ({ email })),
      conferenceData: {
        createRequest: {
          requestId: `meet-${Date.now()}`,
          conferenceSolutionKey: { type: 'hangoutsMeet' },
        },
      },
    };

    const result = await calendar.events.insert({
      calendarId: 'primary',
      requestBody: event,
      conferenceDataVersion: 1,
    });

    return result.data;
  }

  async listEvents(timeMin?: Date, timeMax?: Date, maxResults: number = 10) {
    const calendar = google.calendar({ version: 'v3', auth: this.oauth2Client });

    const result = await calendar.events.list({
      calendarId: 'primary',
      timeMin: (timeMin || new Date()).toISOString(),
      timeMax: timeMax?.toISOString(),
      maxResults,
      singleEvents: true,
      orderBy: 'startTime',
    });

    return result.data.items || [];
  }

  async checkAvailability(startTime: Date, endTime: Date) {
    const calendar = google.calendar({ version: 'v3', auth: this.oauth2Client });

    const result = await calendar.freebusy.query({
      requestBody: {
        timeMin: startTime.toISOString(),
        timeMax: endTime.toISOString(),
        items: [{ id: 'primary' }],
      },
    });

    const busy = result.data.calendars?.['primary']?.busy || [];
    return busy.length === 0; // true if available
  }

  async testConnection(): Promise<boolean> {
    try {
      const calendar = google.calendar({ version: 'v3', auth: this.oauth2Client });
      await calendar.calendarList.list();
      return true;
    } catch (error) {
      return false;
    }
  }
}
