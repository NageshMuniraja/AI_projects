import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';
import * as Sentry from '@sentry/node';

export interface AppError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

export const errorHandler = (
  err: AppError,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';

  // Log error
  logger.error(message, {
    statusCode,
    stack: err.stack,
    path: req.path,
    method: req.method,
  });

  // Report to Sentry
  if (process.env.SENTRY_DSN) {
    Sentry.captureException(err);
  }

  // Send response
  res.status(statusCode).json({
    error: {
      message,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
    },
  });
};

export class ApiError extends Error implements AppError {
  statusCode: number;
  isOperational: boolean;

  constructor(statusCode: number, message: string, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    Error.captureStackTrace(this, this.constructor);
  }
}
