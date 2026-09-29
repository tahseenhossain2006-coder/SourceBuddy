import { SearchResult } from './searchOrchestrator';
import { LIMITS } from '@/lib/limits';
import { logger } from '@/lib/logger';
import { CircuitBreaker } from '@/lib/circuitBreaker';

const SEARXNG_BASE_URL = process.env.SEARXNG_BASE_URL || '';
const TIMEOUT = Number(process.env.SEARXNG_TIMEOUT) || LIMITS.SEARCH_TIMEOUT_MS;

export async function searchSearXNG(query: string): Promise<SearchResult[]> {
  if (!SEARXNG_BASE_URL) {
    logger.warn('SearXNG not configured, skipping');
    return [];
  }

  if (!CircuitBreaker.isAvailable('searxng')) {
    logger.warn('SearXNG circuit open, skipping');
    return [];
  }

  const url = `${SEARXNG_BASE_URL}/search?q=${encodeURIComponent(query)}&format=json`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT);

  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) {
      CircuitBreaker.recordFailure('searxng');
      logger.warn('SearXNG returned non-OK', { query, status: res.status });
      return [];
    }
    const data = await res.json();
    CircuitBreaker.recordSuccess('searxng');
    // SearXNG JSON format: { results: [ { title, url, snippet, ... } ] }
    return (data.results || []).slice(0, LIMITS.MAX_SEARCH_RESULTS_PER_QUERY).map((r: any) => ({
      title: r.title || '',
      url: r.url || '',
      snippet: r.snippet || r.content || '',
      source: 'searxng',
      query,
      discoveredAt: new Date().toISOString(),
    }));
  } catch (error) {
    clearTimeout(timeout);
    CircuitBreaker.recordFailure('searxng');
    logger.error('SearXNG search failed', { query, error: error.message });
    return [];
  }
}