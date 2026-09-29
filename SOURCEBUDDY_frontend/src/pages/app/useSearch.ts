import type { SearchData } from '@/types';

/**
 * Ephemeral, in-memory only. Cleared on full page reload.
 * Used so SearchDetail can render the query immediately after a POST
 * without waiting for the GET to resolve. Never treated as the source
 * of truth — SearchDetail always fetches.
 */
const cache = new Map<string, SearchData>();

export function rememberSearch(data: SearchData): void {
  if (!data.search_id) return;
  cache.set(data.search_id, data);
}

export function recallSearch(searchId: string): SearchData | undefined {
  return cache.get(searchId);
}

export function forgetSearch(searchId: string): void {
  cache.delete(searchId);
}