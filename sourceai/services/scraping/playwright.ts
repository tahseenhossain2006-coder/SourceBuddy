// services/scraping/playwright.ts
import { chromium } from 'playwright';
import { LIMITS } from '@/lib/limits';
import { logger } from '@/lib/logger';

export async function scrapeWithPlaywright(url: string): Promise<string | null> {
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setDefaultNavigationTimeout(LIMITS.SCRAPE_TIMEOUT_MS);
    await page.goto(url, { waitUntil: 'networkidle' });
    const content = await page.content();
    return content;
  } catch (error) {
    logger.error('Playwright scrape failed', { url, error: error.message });
    return null;
  } finally {
    if (browser) await browser.close();
  }
}