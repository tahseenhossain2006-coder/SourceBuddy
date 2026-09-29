// services/agent/orchestrator.ts
import { AgentRequest, Requirement, Ambiguity, Supplier } from '@/lib/types';
import { logger } from '@/lib/logger';
import { LIMITS } from '@/lib/limits';

import { extractRequirements, detectAmbiguity } from './requirementExtractor';
import { planSearches } from './searchPlanner';
import { searchAllProviders, SearchResult } from '../search/searchOrchestrator';
import { scrapeSupplierPages } from '../scraping/scraper';
import { cleanHtml } from '../scraping/contentCleaner';
import { extractSupplierFromHtml } from './supplierExtractor';
import { normalizeSupplier } from './supplierNormalizer';
import { deduplicateSuppliers } from './supplierDeduplicator';
import { applyFilters } from './supplierFilter';
import { rankSuppliersWithAI } from './supplierRanker';
import { detectMissingData } from './missingDataDetector';
import { generateResultSummary } from './resultSummarizer';

export interface AgentResult {
  prompt: string;
  requirements: Requirement;
  ambiguity: Ambiguity;
  suppliers: Supplier[];
  summary: string;
  meta: {
    total: number;
    partial: boolean;
    cached: boolean;
    providersUsed: string[];
    queriesPerformed: number;
    pagesFetched: number;
    rankingUsed: boolean;
  };
  warnings: string[];
}

export async function runAgent(
  request: AgentRequest,
  requestId?: string
): Promise<AgentResult> {
  const { prompt, quantity, location } = request;
  const warnings: string[] = [];
  const providersUsed: string[] = [];
  let queriesPerformed = 0;
  let pagesFetched = 0;
  let rankingUsed = true;

  logger.info('Agent started', { requestId, prompt: prompt.slice(0, 100) });

  // ---------- 1. Requirement extraction ----------
  let requirements: Requirement;
  try {
    requirements = await extractRequirements(prompt);
    if (quantity) requirements.quantity = quantity;
    if (location) requirements.location_hint = location;
  } catch (error) {
    logger.error('Requirement extraction failed', { requestId, error: (error as Error).message });
    // Fallback: create minimal requirements with required currency
    requirements = { product: prompt || 'unknown', currency: 'INR' };
    warnings.push('Requirement extraction failed, using fallback.');
  }

  // ---------- 2. Ambiguity detection (non‑blocking) ----------
  let ambiguity: Ambiguity = { is_ambiguous: false, missing_requirements: [], questions: [] };
  try {
    ambiguity = await detectAmbiguity(prompt, requirements);
  } catch (error) {
    logger.warn('Ambiguity detection failed', { requestId, error: (error as Error).message });
    warnings.push('Ambiguity detection unavailable.');
  }

  // ---------- 3. Search planning ----------
  const queries = planSearches(requirements);
  queriesPerformed = queries.length;
  logger.info(`Planned ${queries.length} search queries`, { requestId, queries });

  // ---------- 4. Multi‑source search ----------
  let allResults: SearchResult[] = [];
  try {
    allResults = await searchAllProviders(queries);
    const providerSet = new Set(allResults.map(r => r.source));
    providersUsed.push(...providerSet);
    if (allResults.length === 0) {
      warnings.push('No search results found from any provider.');
    }
  } catch (error) {
    logger.error('Search failed', { requestId, error: (error as Error).message });
    warnings.push('All search providers failed. Returning empty results.');
    return {
      prompt,
      requirements,
      ambiguity,
      suppliers: [],
      summary: 'No suppliers found. Please try a different search.',
      meta: {
        total: 0,
        partial: true,
        cached: false,
        providersUsed: [],
        queriesPerformed,
        pagesFetched: 0,
        rankingUsed: false,
      },
      warnings,
    };
  }

  // ---------- 5. Score and select top pages to scrape ----------
  const product = requirements.product || prompt;
  const scored = allResults.map(r => ({
    ...r,
    score: scoreLink(r, product),
  }));
  scored.sort((a, b) => b.score - a.score);
  const topUrls = scored
    .slice(0, LIMITS.MAX_PAGES_TO_SCRAPE)
    .map(r => r.url);

  // ---------- 6. Scrape pages ----------
  const scrapedContent = await scrapeSupplierPages(topUrls);
  pagesFetched = scrapedContent.filter(c => c.html !== null).length;

  // ---------- 7. Extract supplier data from HTML ----------
  const rawSuppliers: Supplier[] = [];
  for (const { url, html } of scrapedContent) {
    if (!html) continue;
    try {
      const cleanedHtml = cleanHtml(html);
      const searchResult = allResults.find(r => r.url === url);
      const extracted = await extractSupplierFromHtml(cleanedHtml, url);
      const supplier = normalizeSupplier(extracted, searchResult, url);
      rawSuppliers.push(supplier);
    } catch (error) {
      logger.warn('Supplier extraction failed', { requestId, url, error: (error as Error).message });
      warnings.push(`Extraction failed for ${url}`);
    }
  }

  // ---------- 8. Deduplicate suppliers by domain ----------
  let deduped = deduplicateSuppliers(rawSuppliers);
  if (deduped.length === 0) {
    warnings.push('No suppliers could be extracted.');
    return {
      prompt,
      requirements,
      ambiguity,
      suppliers: [],
      summary: 'No supplier data could be extracted from the discovered pages.',
      meta: {
        total: 0,
        partial: true,
        cached: false,
        providersUsed,
        queriesPerformed,
        pagesFetched,
        rankingUsed: false,
      },
      warnings,
    };
  }

  // ---------- 9. Deterministic filtering ----------
  let filtered = applyFilters(deduped, requirements);
  if (filtered.length === 0) {
    warnings.push('All suppliers were filtered out by deterministic rules.');
    // Return all suppliers but mark as partial
    filtered = deduped;
  }

  // ---------- 10. AI ranking (or fallback) ----------
  let ranked: Supplier[];
  try {
    ranked = await rankSuppliersWithAI(filtered, prompt, requirements);
  } catch (error) {
    logger.warn('AI ranking failed, using deterministic fallback', {
      requestId,
      error: (error as Error).message,
    });
    rankingUsed = false;
    warnings.push('AI ranking unavailable, using fallback ordering.');
    ranked = filtered.map((s, i) => ({
      ...s,
      ranking: { score: 100 - i * 5, reason: 'Fallback ordering based on data completeness' },
    }));
  }

  // ---------- 11. Missing‑data detection & confidence calculation ----------
  for (const s of ranked) {
    s.missing_data = detectMissingData(s);
    s.confidence = calculateConfidence(s);
  }

  // ---------- 12. Result summary ----------
  let summary: string;
  try {
    summary = await generateResultSummary(ranked, requirements);
  } catch (error) {
    logger.warn('Summary generation failed', { requestId, error: (error as Error).message });
    warnings.push('AI summary unavailable, using fallback.');
    summary = `Found ${ranked.length} suppliers. Top match: ${ranked[0]?.name || 'None'}. Check details below.`;
  }

  // ---------- 13. Return final result ----------
  return {
    prompt,
    requirements,
    ambiguity,
    suppliers: ranked,
    summary,
    meta: {
      total: ranked.length,
      partial: warnings.length > 0 || ranked.length < rawSuppliers.length,
      cached: false,
      providersUsed,
      queriesPerformed,
      pagesFetched,
      rankingUsed,
    },
    warnings,
  };
}

// ---------- Helper: confidence score (0-100) ----------
function calculateConfidence(supplier: Supplier): number {
  let score = 0;

  // 1. Ranking score (already 0-100) – weight 40%
  const rankingScore = supplier.ranking?.score || 0;
  score += rankingScore * 0.4;

  // 2. Evidence coverage – weight 30%
  const importantFields = ['price', 'moq', 'location', 'certifications', 'contact_email'];
  let evidenceCount = 0;
  for (const field of importantFields) {
    if (supplier.evidence?.field_evidence?.[field as keyof typeof supplier.evidence.field_evidence]) {
      evidenceCount++;
    }
  }
  const coverageScore = (evidenceCount / importantFields.length) * 100;
  score += coverageScore * 0.3;

  // 3. Source quality – weight 30% (simple heuristic)
  let sourceQuality = 50; // default
  try {
    const url = new URL(supplier.website);
    const domain = url.hostname;
    if (domain.includes('alibaba.com')) sourceQuality = 60;
    else if (domain.includes('indiamart.com')) sourceQuality = 70;
    else if (domain.includes('tradeindia.com')) sourceQuality = 70;
    else if (domain.includes('globalsources.com')) sourceQuality = 75;
    else if (domain.match(/\.(com|org|net)$/) && !domain.includes('amazon') && !domain.includes('ebay')) {
      sourceQuality = 90; // likely company website
    } else {
      sourceQuality = 50;
    }
  } catch {
    // keep default
  }
  score += sourceQuality * 0.3;

  // Clamp to 0-100
  return Math.min(100, Math.max(0, Math.round(score)));
}

// ---------- Helper: score link for selecting pages ----------
function scoreLink(result: SearchResult, product: string): number {
  let score = 0;
  const text = (result.title + ' ' + result.snippet).toLowerCase();
  if (text.includes('moq')) score += 20;
  if (text.includes('price')) score += 15;
  if (text.includes('verified')) score += 10;
  if (text.includes('manufacturer')) score += 10;
  if (result.url.includes('alibaba.com')) score += 5;
  if (result.url.includes('indiamart.com')) score += 5;
  if (result.url.includes('amazon.com')) score += 3;
  if (result.url.startsWith('https')) score += 5;
  return score;
}