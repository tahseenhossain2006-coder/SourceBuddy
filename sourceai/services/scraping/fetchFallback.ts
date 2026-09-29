// services/scraping/fetchFallback.ts
import { LIMITS } from '@/lib/limits';

export async function fetchFallback(url: string): Promise<string | null> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), LIMITS.SCRAPE_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) return null;
    const text = await res.text();
    if (text.length > LIMITS.MAX_SCRAPE_CONTENT_SIZE) {
      return text.slice(0, LIMITS.MAX_SCRAPE_CONTENT_SIZE);
    }
    return text;
  } catch {
    clearTimeout(timeout);
    return null;
  }
}