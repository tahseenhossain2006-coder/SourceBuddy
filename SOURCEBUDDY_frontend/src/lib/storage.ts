/**
 * Token storage.
 *
 * The backend does NOT set auth cookies (confirmed in
 * SOURCEBUDDY_BACKEND_CONTRACT.md §2). Tokens must be stored client-side
 * and reattached on every request by the API client.
 */

const ACCESS_KEY = 'sb.access_token';
const REFRESH_KEY = 'sb.refresh_token';

export interface StoredTokens {
  access: string;
  refresh: string;
}

export function getAccessToken(): string | null {
  try {
    return window.localStorage.getItem(ACCESS_KEY);
  } catch {
    return null;
  }
}

export function getRefreshToken(): string | null {
  try {
    return window.localStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

export function setTokens(tokens: StoredTokens): void {
  try {
    window.localStorage.setItem(ACCESS_KEY, tokens.access);
    window.localStorage.setItem(REFRESH_KEY, tokens.refresh);
  } catch {
    // Storage can be disabled (private browsing, quota). Silently ignore.
  }
}

export function clearTokens(): void {
  try {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
  } catch {
    // ignore
  }
}