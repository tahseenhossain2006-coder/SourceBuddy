import { SearchResult } from './searchOrchestrator';
import { LIMITS } from '@/lib/limits';
import { logger } from '@/lib/logger';

export async function searchDuckDuckGo(query: string): Promise<SearchResult[]> {
  const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), LIMITS.SEARCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' },
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      logger.warn('DuckDuckGo returned non-OK', { query, status: res.status });
      return [];
    }
    const html = await res.text();

    const results: SearchResult[] = [];
    const linkRegex = /<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)<\/a>/g;
    const snippetRegex = /<a class="result__snippet"[^>]*>([^<]+)<\/a>/g;

    let linkMatch;
    while ((linkMatch = linkRegex.exec(html)) !== null) {
      let url = linkMatch[1];
      if (url.startsWith('/l/?uddg=')) {
        url = decodeURIComponent(url.replace('/l/?uddg=', '').split('&')[0]);
      }
      const title = linkMatch[2].trim();
      const snippetMatch = snippetRegex.exec(html);
      const snippet = snippetMatch ? snippetMatch[1].trim() : '';
      results.push({
        title,
        url,
        snippet,
        source: 'duckduckgo',
        query,
        discoveredAt: new Date().toISOString(),
      });
    }
    return results.slice(0, LIMITS.MAX_SEARCH_RESULTS_PER_QUERY);
  } catch (error) {
    clearTimeout(timeout);
    logger.error('DuckDuckGo search failed', { query, error: error.message });
    return [];
  }
}