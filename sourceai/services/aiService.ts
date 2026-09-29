/// <reference types="node" />

// services/aiService.ts
// Low-level OmniRoute client – single request, no fallback/retry

export class AIServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AIServiceError';
  }
}
export class AIAuthenticationError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIAuthenticationError';
  }
}
export class AIProviderUnavailableError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIProviderUnavailableError';
  }
}
export class AIRateLimitError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIRateLimitError';
  }
}
export class AIRequestTooLargeError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIRequestTooLargeError';
  }
}
export class AITimeoutError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AITimeoutError';
  }
}
export class AIEmptyResponseError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIEmptyResponseError';
  }
}
export class AIMalformedResponseError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIMalformedResponseError';
  }
}
export class AINetworkError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AINetworkError';
  }
}
export class AIPermissionError extends AIServiceError {
  constructor(message: string) {
    super(message);
    this.name = 'AIPermissionError';
  }
}

function toNumber(value: unknown, fallback: number): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed === '') return fallback;
    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

const OMNIROUTE_BASE_URL = process.env.OMNIROUTE_BASE_URL || 'http://localhost:20128/v1';
const OMNIROUTE_API_KEY = process.env.OMNIROUTE_API_KEY || '';
const DEFAULT_TIMEOUT_MS = toNumber(process.env.OMNIROUTE_TIMEOUT, 30000);

if (!OMNIROUTE_API_KEY) {
  console.warn('⚠️ OMNIROUTE_API_KEY is not set. AI service will fail.');
}

export interface AIRequestOptions {
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

/**
 * Make a single request to OmniRoute.
 * Does NOT handle fallback or retry – that is the router's responsibility.
 */
export async function generateText(
  prompt: string,
  model: string,
  options: AIRequestOptions = {}
): Promise<string> {
  const messages = [{ role: 'user', content: prompt }];
  const payload: any = { model, messages };

  if (options.temperature !== undefined) payload.temperature = options.temperature;
  if (options.max_tokens !== undefined) payload.max_tokens = options.max_tokens;
  if (options.stream) payload.stream = options.stream; // not handled yet, but preserved

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(`${OMNIROUTE_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OMNIROUTE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const msg = errorBody.error?.message || response.statusText;
      const status = response.status;
      if (status === 401) throw new AIAuthenticationError(msg);
      if (status === 403) throw new AIPermissionError(msg);
      if (status === 413) throw new AIRequestTooLargeError(msg);
      if (status === 429) throw new AIRateLimitError(msg);
      if (status >= 500) throw new AIProviderUnavailableError(msg);
      throw new AIServiceError(`HTTP ${status}: ${msg}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content;
    if (content === undefined || content === null) {
      throw new AIEmptyResponseError('No content in OmniRoute response');
    }
    if (typeof content !== 'string') {
      throw new AIMalformedResponseError('Unexpected response type');
    }
    return content;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === 'AbortError') {
      throw new AITimeoutError(`Request to ${model} timed out after ${DEFAULT_TIMEOUT_MS}ms`);
    }
    if (err instanceof TypeError && (err.message.includes('fetch') || err.message.includes('network'))) {
      throw new AINetworkError(`Network error: ${err.message}`);
    }
    throw err; // rethrow already-classified errors
  }
}