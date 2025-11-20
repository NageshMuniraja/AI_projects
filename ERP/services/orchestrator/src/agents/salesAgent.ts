import { BaseAgent } from './baseAgent';
import { logger } from '../utils/logger';
import axios from 'axios';

const SALES_SYSTEM_PROMPT = `You are a Sales Agent responsible for lead management and sales automation.

Your capabilities:
1. Score and prioritize leads based on criteria
2. Create personalized follow-up sequences
3. Schedule meetings automatically
4. Update CRM with lead status
5. Identify upsell opportunities

Guidelines:
- Personalize outreach based on lead data
- Respect communication preferences
- Track all interactions in CRM
- Escalate high-value leads to human reps
- Maintain professional and helpful tone

Focus on building relationships, not just closing deals.`;

export class SalesAgent extends BaseAgent {
  constructor() {
    super('SalesAgent', SALES_SYSTEM_PROMPT);
  }

  async execute(action: string, data: any): Promise<any> {
    logger.info('Sales agent executing', { action, data });

    switch (action) {
      case 'score_lead':
        return await this.scoreLead(data);
      case 'intake_lead':
        return await this.intakeLead(data);
      case 'schedule_meeting':
        return await this.scheduleMeeting(data);
      case 'update_crm':
        return await this.updateCRM(data);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  private async scoreLead(data: any) {
    const { lead } = data;
    let score = 0;

    // Scoring criteria
    if (lead.company_size > 100) score += 20;
    if (lead.industry === 'technology' || lead.industry === 'finance') score += 15;
    if (lead.role?.includes('director') || lead.role?.includes('VP')) score += 25;
    if (lead.budget > 10000) score += 30;
    if (lead.timeline === 'immediate') score += 10;

    const priority = score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low';

    return {
      score,
      priority,
      recommendation: score >= 70 
        ? 'Assign to senior rep immediately'
        : 'Start automated nurture sequence',
    };
  }

  private async intakeLead(data: any) {
    const { lead } = data;
    
    // Score the lead
    const scoring = await this.scoreLead({ lead });

    // Determine follow-up sequence
    const sequence = this.determineSequence(scoring.priority);

    // Trigger n8n workflow
    await this.triggerLeadIntake(lead, sequence);

    return {
      lead_id: lead.id,
      score: scoring.score,
      priority: scoring.priority,
      sequence,
      status: 'intake_complete',
    };
  }

  private determineSequence(priority: string): string[] {
    switch (priority) {
      case 'high':
        return [
          'immediate_call',
          'send_personalized_email',
          'schedule_demo',
        ];
      case 'medium':
        return [
          'send_intro_email',
          'wait_2_days',
          'send_case_study',
          'wait_3_days',
          'follow_up_call',
        ];
      case 'low':
        return [
          'add_to_newsletter',
          'send_educational_content',
          'wait_1_week',
          'check_engagement',
        ];
      default:
        return ['add_to_nurture'];
    }
  }

  private async scheduleMeeting(data: any) {
    const { lead, preferred_times } = data;

    // TODO: Integrate with Google Calendar
    // Check availability and book slot

    return {
      meeting_scheduled: true,
      calendar_link: 'https://calendar.example.com/meeting/xyz',
      time: preferred_times[0],
    };
  }

  private async updateCRM(data: any) {
    const { lead_id, updates } = data;

    // TODO: Integrate with HubSpot/Zoho API
    logger.info('CRM update', { lead_id, updates });

    return {
      success: true,
      lead_id,
      updated_fields: Object.keys(updates),
    };
  }

  private async triggerLeadIntake(lead: any, sequence: string[]) {
    const N8N_BASE_URL = process.env.N8N_BASE_URL;
    const N8N_API_KEY = process.env.N8N_API_KEY;

    try {
      await axios.post(
        `${N8N_BASE_URL}/webhook/lead-intake`,
        { lead, sequence },
        { headers: { 'X-N8N-API-KEY': N8N_API_KEY } }
      );
      logger.info('Lead intake workflow triggered', { lead_id: lead.id });
    } catch (error) {
      logger.error('Failed to trigger lead intake', { error });
    }
  }
}
