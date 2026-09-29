// services/search/searchOrchestrator.ts
import { searchDuckDuckGo } from './duckduckgo';
import { searchSearXNG } from './searxng';
import { runWithConcurrency } from '@/lib/concurrency';
import { LIMITS } from '@/lib/limits';
import { logger } from '@/lib/logger';
import { CircuitBreaker } from '@/lib/circuitBreaker';

// Canonical SearchResult interface – shared across all providers
export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;       // e.g., 'duckduckgo', 'searxng'
  query: string;        // the query that produced this result
  discoveredAt: string; // ISO timestamp
}

/**
 * Search multiple providers with concurrency limits and circuit breakers.
 */
export async function searchAllProviders(queries: string[]): Promise<SearchResult[]> {
  const limitedQueries = queries.slice(0, LIMITS.MAX_SEARCH_QUERIES);

  // Build a list of search tasks for each query/provider combination
  const tasks: Array<() => Promise<SearchResult[]>> = [];

  for (const query of limitedQueries) {
    // Always include DuckDuckGo
    tasks.push(() => searchDuckDuckGo(query));

    // Optionally include SearXNG if configured and circuit is closed
    if (CircuitBreaker.isAvailable('searxng') && process.env.SEARXNG_BASE_URL) {
      tasks.push(() => searchSearXNG(query));
    }
    // Future: add platform adapters here
  }

  // Run with bounded concurrency (e.g., 3 simultaneous searches)
  const results = await runWithConcurrency(tasks, 3, async (task) => {
    try {
      return await task();
    } catch (error) {
      logger.warn('Search task failed', { error: error.message });
      return [] as SearchResult[];
    }
  });

  // Flatten and deduplicate by normalized URL
  const flat = results.flat();
  const unique = new Map<string, SearchResult>();
  for (const r of flat) {
    const normalized = normalizeUrl(r.url);
    if (!unique.has(normalized)) {
      unique.set(normalized, { ...r, url: normalized });
    }
  }

  return Array.from(unique.values());
}

/**
 * Normalize URL: remove tracking parameters, fragments, and www.
 */
function normalizeUrl(url: string): string {
  try {
    const u = new URL(url);
    u.search = '';
    u.hash = '';
    let hostname = u.hostname.replace(/^www\./, '');
    u.hostname = hostname;
    return u.toString();
  } catch {
    return url;
  }
}