import { Router, Request, Response, NextFunction } from 'express';
import { FinanceAgent } from '../agents/financeAgent';
import { SalesAgent } from '../agents/salesAgent';
import { ReportingAgent } from '../agents/reportingAgent';
import { ApiError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

// Finance Agent
router.post('/finance/run', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { action, data } = req.body;
    
    if (!action) {
      throw new ApiError(400, 'Action is required');
    }

    const agent = new FinanceAgent();
    const result = await agent.execute(action, data);

    logger.info('Finance agent executed', { action, result });
    res.json({ success: true, result });
  } catch (error) {
    next(error);
  }
});

// Sales Agent
router.post('/sales/run', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { action, data } = req.body;
    
    if (!action) {
      throw new ApiError(400, 'Action is required');
    }

    const agent = new SalesAgent();
    const result = await agent.execute(action, data);

    logger.info('Sales agent executed', { action, result });
    res.json({ success: true, result });
  } catch (error) {
    next(error);
  }
});

// Reporting Agent
router.post('/reporting/run', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { action, data } = req.body;
    
    if (!action) {
      throw new ApiError(400, 'Action is required');
    }

    const agent = new ReportingAgent();
    const result = await agent.execute(action, data);

    logger.info('Reporting agent executed', { action, result });
    res.json({ success: true, result });
  } catch (error) {
    next(error);
  }
});

// List agent actions
router.get('/:agentType/actions', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { agentType } = req.params;
    // TODO: Fetch from database
    res.json({
      agentType,
      actions: [],
    });
  } catch (error) {
    next(error);
  }
});

export { router as agentRouter };
