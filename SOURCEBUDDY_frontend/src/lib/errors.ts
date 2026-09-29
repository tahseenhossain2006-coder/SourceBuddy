/**
 * Normalized API error type.
 *
 * Backend returns one of three error shapes (contract §12):
 *   400 / 401 / 404 / 500 / 503  →  { detail: string }
 *   429                          →  { detail: string, retry_after: number }
 *   422                          →  { detail: ValidationIssue[] }
 */

import type { ValidationIssue } from '@/types';

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;
  readonly retryAfter: number | null;
  readonly validationIssues: ValidationIssue[] | null;

  constructor(
    status: number,
    message: string,
    body: unknown,
    retryAfter: number | null,
    validationIssues: ValidationIssue[] | null,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
    this.retryAfter = retryAfter;
    this.validationIssues = validationIssues;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isRateLimited(): boolean {
    return this.status === 429;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isValidationError(): boolean {
    return this.status === 422;
  }
}

export function parseErrorBody(status: number, body: unknown): ApiError {
  // 429 with retry_after
  if (
    body &&
    typeof body === 'object' &&
    'detail' in body &&
    'retry_after' in body
  ) {
    const b = body as { detail: string; retry_after: number };
    return new ApiError(status, b.detail, body, b.retry_after, null);
  }

  // 422 with list of issues
  if (
    body &&
    typeof body === 'object' &&
    'detail' in body &&
    Array.isArray((body as { detail: unknown }).detail)
  ) {
    const issues = (body as { detail: ValidationIssue[] }).detail;
    const firstMsg = issues[0]?.msg ?? 'Validation error';
    return new ApiError(status, firstMsg, body, null, issues);
  }

  // { detail: string }
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    const message = typeof detail === 'string' ? detail : 'Request failed';
    return new ApiError(status, message, body, null, null);
  }

  return new ApiError(status, `HTTP ${status}`, body, null, null);
}