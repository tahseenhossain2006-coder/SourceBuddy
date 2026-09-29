// lib/errors.ts
import { AIServiceError } from '@/services/aiService';

export class AgentError extends Error {
  constructor(message: string, public statusCode: number = 500) {
    super(message);
    this.name = 'AgentError';
  }
}

export class ValidationError extends AgentError {
  constructor(message: string) {
    super(message, 400);
    this.name = 'ValidationError';
  }
}

export class SearchError extends AgentError {
  constructor(message: string) {
    super(message, 503);
    this.name = 'SearchError';
  }
}

export class ScrapingError extends AgentError {
  constructor(message: string) {
    super(message, 503);
    this.name = 'ScrapingError';
  }
}

export class RankingError extends AgentError {
  constructor(message: string) {
    super(message, 500);
    this.name = 'RankingError';
  }
}

export function classifyError(error: unknown): { status: number; message: string } {
  if (error instanceof ValidationError) {
    return { status: 400, message: error.message };
  }
  if (error instanceof AgentError && error.statusCode) {
    return { status: error.statusCode, message: error.message };
  }
  // AI errors from aiService
  if (error instanceof AIServiceError) {
    if (error.name === 'AIAuthenticationError' || error.name === 'AIPermissionError') {
      return { status: 401, message: 'AI service authentication failed' };
    }
    if (error.name === 'AIRateLimitError') {
      return { status: 429, message: 'Rate limit exceeded' };
    }
    if (error.name === 'AITimeoutError' || error.name === 'AINetworkError' || error.name === 'AIProviderUnavailableError') {
      return { status: 503, message: 'AI service temporarily unavailable' };
    }
    if (error.name === 'AIRequestTooLargeError') {
      return { status: 413, message: 'Request too large for AI processing' };
    }
    return { status: 500, message: 'AI processing failed' };
  }
  // Fallback
  return { status: 500, message: 'Internal server error' };
}