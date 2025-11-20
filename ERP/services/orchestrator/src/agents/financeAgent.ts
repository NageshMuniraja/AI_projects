import { BaseAgent, AgentAction } from './baseAgent';
import { logger } from '../utils/logger';
import axios from 'axios';

const FINANCE_SYSTEM_PROMPT = `You are a Finance Agent responsible for managing invoices, payments, and financial operations.

Your capabilities:
1. Parse and extract data from invoices (PDF/images)
2. Detect overdue payments and calculate penalties
3. Reconcile payments with invoices
4. Identify anomalies in financial transactions
5. Trigger automated reminders and follow-ups

Guidelines:
- Always validate invoice amounts and dates
- Flag suspicious transactions for human review
- Ensure compliance with financial regulations
- Maintain accurate audit trails
- Be conservative with payment-related actions

Return structured actions with high confidence scores only when data is clear.`;

export class FinanceAgent extends BaseAgent {
  constructor() {
    super('FinanceAgent', FINANCE_SYSTEM_PROMPT);
  }

  async execute(action: string, data: any): Promise<any> {
    logger.info('Finance agent executing', { action, data });

    switch (action) {
      case 'parse_invoice':
        return await this.parseInvoice(data);
      case 'detect_overdue':
        return await this.detectOverdue(data);
      case 'reconcile_payment':
        return await this.reconcilePayment(data);
      case 'detect_anomaly':
        return await this.detectAnomaly(data);
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }

  private async parseInvoice(data: any) {
    const prompt = `Parse the following invoice data and extract:
- Invoice number
- Date
- Due date
- Amount
- Vendor name
- Line items

Data: ${JSON.stringify(data)}`;

    const response = await this.chat(prompt);
    return { parsed: response };
  }

  private async detectOverdue(data: any) {
    const { invoices } = data;
    const today = new Date();
    const overdue = invoices.filter((inv: any) => {
      const dueDate = new Date(inv.dueDate);
      return dueDate < today && inv.status !== 'paid';
    });

    if (overdue.length > 0) {
      // Trigger n8n workflow for reminders
      await this.triggerReminders(overdue);
    }

    return { overdue, count: overdue.length };
  }

  private async reconcilePayment(data: any) {
    const { payment, invoices } = data;
    
    // Simple matching logic
    const matched = invoices.find((inv: any) => 
      inv.amount === payment.amount || 
      inv.invoiceNumber === payment.reference
    );

    if (matched) {
      // Update invoice status
      return { 
        matched: true, 
        invoice: matched,
        recommendation: 'Mark invoice as paid'
      };
    }

    return { 
      matched: false,
      recommendation: 'Manual review required'
    };
  }

  private async detectAnomaly(data: any) {
    const { transactions } = data;
    const anomalies = [];

    // Simple anomaly detection rules
    for (const txn of transactions) {
      // Check for unusual amounts
      if (txn.amount > 10000) {
        anomalies.push({
          transaction: txn,
          reason: 'Unusually high amount',
          severity: 'high',
        });
      }

      // Check for duplicate payments
      const duplicates = transactions.filter((t: any) => 
        t.id !== txn.id && 
        t.amount === txn.amount && 
        t.vendor === txn.vendor
      );

      if (duplicates.length > 0) {
        anomalies.push({
          transaction: txn,
          reason: 'Possible duplicate payment',
          severity: 'medium',
        });
      }
    }

    return { anomalies, count: anomalies.length };
  }

  private async triggerReminders(overdueInvoices: any[]) {
    const N8N_BASE_URL = process.env.N8N_BASE_URL;
    const N8N_API_KEY = process.env.N8N_API_KEY;

    try {
      await axios.post(
        `${N8N_BASE_URL}/webhook/invoice-reminder`,
        { invoices: overdueInvoices },
        { headers: { 'X-N8N-API-KEY': N8N_API_KEY } }
      );
      logger.info('Reminder workflow triggered', { count: overdueInvoices.length });
    } catch (error) {
      logger.error('Failed to trigger reminders', { error });
    }
  }
}
