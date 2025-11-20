import { SalesAgent } from '../salesAgent';

describe('SalesAgent', () => {
  let agent: SalesAgent;

  beforeEach(() => {
    agent = new SalesAgent();
  });

  describe('scoreLead', () => {
    it('should score lead as high priority for large tech company', async () => {
      const mockData = {
        lead: {
          company_size: 500,
          industry: 'technology',
          role: 'VP Engineering',
          budget: 50000,
          timeline: 'immediate',
        },
      };

      const result = await agent.execute('score_lead', mockData);
      expect(result.score).toBeGreaterThanOrEqual(70);
      expect(result.priority).toBe('high');
    });

    it('should score lead as low priority for small company', async () => {
      const mockData = {
        lead: {
          company_size: 10,
          industry: 'retail',
          role: 'Manager',
          budget: 1000,
          timeline: 'researching',
        },
      };

      const result = await agent.execute('score_lead', mockData);
      expect(result.score).toBeLessThan(40);
      expect(result.priority).toBe('low');
    });
  });

  describe('intakeLead', () => {
    it('should create high-priority sequence for high-scoring lead', async () => {
      const mockData = {
        lead: {
          id: 'lead-123',
          email: 'john@bigcorp.com',
          full_name: 'John Smith',
          company_size: 1000,
          industry: 'technology',
          role: 'CTO',
          budget: 100000,
          timeline: 'immediate',
        },
      };

      const result = await agent.execute('intake_lead', mockData);
      expect(result.priority).toBe('high');
      expect(result.sequence).toContain('immediate_call');
      expect(result.status).toBe('intake_complete');
    });

    it('should create nurture sequence for low-priority lead', async () => {
      const mockData = {
        lead: {
          id: 'lead-456',
          email: 'jane@startup.com',
          full_name: 'Jane Doe',
          company_size: 5,
          industry: 'other',
          role: 'Founder',
          budget: 500,
          timeline: 'future',
        },
      };

      const result = await agent.execute('intake_lead', mockData);
      expect(result.priority).toBe('low');
      expect(result.sequence).toContain('add_to_newsletter');
    });
  });

  describe('scheduleMeeting', () => {
    it('should schedule meeting successfully', async () => {
      const mockData = {
        lead: {
          id: 'lead-123',
          email: 'john@company.com',
          full_name: 'John Smith',
        },
        preferred_times: ['2025-12-01T10:00:00Z', '2025-12-02T14:00:00Z'],
      };

      const result = await agent.execute('schedule_meeting', mockData);
      expect(result.meeting_scheduled).toBe(true);
      expect(result).toHaveProperty('calendar_link');
    });
  });
});
