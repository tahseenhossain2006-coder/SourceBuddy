/**
 * Centralized HTTP client.
 *
 * Backend response conventions (verified against sourceai):
 *   - /auth/* endpoints return raw Pydantic models (no envelope).
 *   - /api/v1/search and /api/v1/search/{id} return
 *     { "status": "success", "data": <payload> } — an envelope.
 *     Callers of runSearch/getSearch must read `.data`.
 *   - Errors follow the shapes documented in src/lib/errors.ts.
 *
 * Auth uses Bearer tokens from localStorage. No cookies.
 */

import { ApiError, parseErrorBody } from '@/lib/errors';
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from '@/lib/storage';
import type { TokenResponse } from '@/types';

const DEV_FALLBACK = 'http://localhost:8000';

function resolveBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (configured && configured.length > 0) return configured;
  if (import.meta.env.DEV) return DEV_FALLBACK;
  throw new Error(
    'VITE_API_BASE_URL is not set. Refusing to fall back to localhost in production.',
  );
}

export const API_BASE_URL = resolveBaseUrl();
const DEFAULT_TIMEOUT_MS = 30_000;
export const SEARCH_TIMEOUT_MS = 180_000;

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  timeoutMs?: number;
  /** Skip the Authorization header (used by /auth/login, /register, /refresh). */
  skipAuth?: boolean;
  /** Caller-supplied cancellation. Composed with the timeout controller. */
  signal?: AbortSignal;
  /** Internal guard to prevent infinite refresh loops. */
  _isRetry?: boolean;
}

let refreshInFlight: Promise<boolean> | null = null;

async function performRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refresh = getRefreshToken();
    if (!refresh) return false;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });

      if (!res.ok) {
        clearTokens();
        return false;
      }

      const data = (await res.json()) as TokenResponse;
      setTokens({ access: data.access_token, refresh: data.refresh_token });
      return true;
    } catch {
      clearTokens();
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = 'GET',
    body,
    headers = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    skipAuth = false,
    signal,
    _isRetry = false,
  } = options;

  const requestHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...headers,
  };

  if (body !== undefined) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  const timeoutController = new AbortController();
  const timer = window.setTimeout(() => timeoutController.abort(), timeoutMs);

  // Compose timeout + caller signal without relying on AbortSignal.any.
  const composedSignal = signal
    ? composeSignals(signal, timeoutController.signal)
    : timeoutController.signal;

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: composedSignal,
    });
  } catch (err) {
    window.clearTimeout(timer);
    // Caller-initiated abort: rethrow as a distinct error so callers can ignore it.
    if (signal?.aborted) {
      throw new ApiError(0, 'Request aborted', err, null, null);
    }
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(0, 'Request timed out', null, null, null);
    }
    throw new ApiError(0, 'Network error', err, null, null);
  }
  window.clearTimeout(timer);

  // 401 → refresh once → retry once
  if (response.status === 401 && !skipAuth && !_isRetry) {
    const refreshed = await performRefresh();
    if (refreshed) {
      return apiRequest<T>(path, { ...options, _isRetry: true });
    }
    clearTokens();
    const errBody = await safeJson(response);
    throw parseErrorBody(401, errBody);
  }

  if (!response.ok) {
    const errBody = await safeJson(response);
    throw parseErrorBody(response.status, errBody);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.toLowerCase().includes('application/json')) {
    // A 2xx that isn't JSON means a proxy/interstitial returned HTML.
    // Do not attempt .json(); surface it as a typed error.
    throw new ApiError(
      response.status,
      'Unexpected response format (expected JSON)',
      null,
      null,
      null,
    );
  }

  return (await response.json()) as T;
}

function composeSignals(a: AbortSignal, b: AbortSignal): AbortSignal {
  const controller = new AbortController();
  const abort = (reason: unknown) => {
    if (!controller.signal.aborted) controller.abort(reason);
  };
  if (a.aborted || b.aborted) {
    abort(undefined);
    return controller.signal;
  }
  a.addEventListener('abort', () => abort(a.reason), { once: true });
  b.addEventListener('abort', () => abort(b.reason), { once: true });
  return controller.signal;
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}