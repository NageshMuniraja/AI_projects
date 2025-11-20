import { Router, Request, Response, NextFunction } from 'express';
import { ApiError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';
import axios from 'axios';

const router = Router();
const N8N_BASE_URL = process.env.N8N_BASE_URL || 'http://localhost:5678';
const N8N_API_KEY = process.env.N8N_API_KEY;

// Execute workflow
router.post('/execute', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { workflowId, data } = req.body;
    
    if (!workflowId) {
      throw new ApiError(400, 'Workflow ID is required');
    }

    // Call n8n webhook
    const response = await axios.post(
      `${N8N_BASE_URL}/webhook/${workflowId}`,
      data,
      {
        headers: {
          'X-N8N-API-KEY': N8N_API_KEY,
        },
      }
    );

    logger.info('Workflow executed', { workflowId, status: response.status });
    res.json({
      success: true,
      data: response.data,
    });
  } catch (error) {
    logger.error('Workflow execution failed', { error });
    next(error);
  }
});

// Get workflow executions
router.get('/executions', async (req: Request, res: Response, next: NextFunction) => {
  try {
    // TODO: Fetch from n8n API or database
    res.json({
      executions: [],
    });
  } catch (error) {
    next(error);
  }
});

// Get execution logs
router.get('/executions/:id/logs', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    // TODO: Fetch logs
    res.json({
      executionId: id,
      logs: [],
    });
  } catch (error) {
    next(error);
  }
});

export { router as workflowRouter };
