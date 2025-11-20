import { FinanceAgent } from '../financeAgent';

describe('FinanceAgent', () => {
  let agent: FinanceAgent;

  beforeEach(() => {
    agent = new FinanceAgent();
  });

  describe('parseInvoice', () => {
    it('should parse invoice data correctly', async () => {
      const mockData = {
        text: 'Invoice #123, Amount: $1000, Due Date: 2025-12-01',
      };

      const result = await agent.execute('parse_invoice', mockData);
      expect(result).toHaveProperty('parsed');
    });
  });

  describe('detectOverdue', () => {
    it('should identify overdue invoices', async () => {
      const mockData = {
        invoices: [
          {
            invoiceNumber: 'INV-001',
            amount: 1000,
            dueDate: '2025-01-01',
            status: 'pending',
          },
          {
            invoiceNumber: 'INV-002',
            amount: 2000,
            dueDate: '2025-12-31',
            status: 'pending',
          },
        ],
      };

      const result = await agent.execute('detect_overdue', mockData);
      expect(result).toHaveProperty('overdue');
      expect(result.overdue.length).toBeGreaterThan(0);
    });

    it('should not flag paid invoices as overdue', async () => {
      const mockData = {
        invoices: [
          {
            invoiceNumber: 'INV-001',
            amount: 1000,
            dueDate: '2025-01-01',
            status: 'paid',
          },
        ],
      };

      const result = await agent.execute('detect_overdue', mockData);
      expect(result.overdue.length).toBe(0);
    });
  });

  describe('reconcilePayment', () => {
    it('should match payment to invoice by amount', async () => {
      const mockData = {
        payment: {
          amount: 1000,
          reference: 'PAYMENT-123',
        },
        invoices: [
          {
            invoiceNumber: 'INV-001',
            amount: 1000,
          },
          {
            invoiceNumber: 'INV-002',
            amount: 2000,
          },
        ],
      };

      const result = await agent.execute('reconcile_payment', mockData);
      expect(result.matched).toBe(true);
      expect(result.invoice.invoiceNumber).toBe('INV-001');
    });

    it('should recommend manual review if no match found', async () => {
      const mockData = {
        payment: {
          amount: 999,
          reference: 'PAYMENT-123',
        },
        invoices: [
          {
            invoiceNumber: 'INV-001',
            amount: 1000,
          },
        ],
      };

      const result = await agent.execute('reconcile_payment', mockData);
      expect(result.matched).toBe(false);
      expect(result.recommendation).toContain('manual review');
    });
  });

  describe('detectAnomaly', () => {
    it('should flag unusually high amounts', async () => {
      const mockData = {
        transactions: [
          {
            id: 'TXN-001',
            amount: 15000,
            vendor: 'Vendor A',
          },
        ],
      };

      const result = await agent.execute('detect_anomaly', mockData);
      expect(result.anomalies.length).toBeGreaterThan(0);
      expect(result.anomalies[0].reason).toContain('high amount');
    });

    it('should detect duplicate payments', async () => {
      const mockData = {
        transactions: [
          {
            id: 'TXN-001',
            amount: 1000,
            vendor: 'Vendor A',
          },
          {
            id: 'TXN-002',
            amount: 1000,
            vendor: 'Vendor A',
          },
        ],
      };

      const result = await agent.execute('detect_anomaly', mockData);
      expect(result.anomalies.length).toBeGreaterThan(0);
      expect(result.anomalies[0].reason).toContain('duplicate');
    });
  });
});
