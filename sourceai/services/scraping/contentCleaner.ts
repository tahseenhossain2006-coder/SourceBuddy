// services/scraping/contentCleaner.ts
import { load } from 'cheerio'; // Install cheerio if not present

export function cleanHtml(html: string): string {
  const $ = load(html);
  // Remove scripts, styles, nav, footer, ads
  $('script, style, nav, footer, .advertisement, .banner').remove();
  // Extract body text
  const body = $('body');
  const text = body.text().replace(/\s+/g, ' ').trim();
  // Limit length
  return text.slice(0, 5000);
}