// services/scraping/scraper.ts
import { LIMITS } from '@/lib/limits';
import { isUrlSafe } from '@/lib/security';
import { logger } from '@/lib/logger';
import { scrapeWithApify } from './apify';
import { fetchFallback } from './fetchFallback';
import { scrapeWithPlaywright } from './playwright'; // ✅ new import

export interface ScrapedContent {
  url: string;
  html: string | null;
  error?: string;
}

export async function scrapeSupplierPages(urls: string[]): Promise<ScrapedContent[]> {
  const results: ScrapedContent[] = [];
  const limited = urls.slice(0, LIMITS.MAX_PAGES_TO_SCRAPE);

  for (const url of limited) {
    if (!isUrlSafe(url)) {
      logger.warn('Blocked unsafe URL', { url });
      results.push({ url, html: null, error: 'URL blocked for security' });
      continue;
    }

    let html: string | null = null;
    let error: string | undefined;

    try {
      // 1. Try Apify (optional)
      html = await scrapeWithApify(url);
      if (!html) {
        // 2. Try fetch fallback
        html = await fetchFallback(url);
      }
      if (!html) {
        // 3. Try Playwright (JavaScript rendering)
        html = await scrapeWithPlaywright(url);
      }
    } catch (e: any) {
      error = e.message;
      logger.error('Scraping failed for URL', { url, error });
    }

    results.push({ url, html, error });
  }

  return results;
}