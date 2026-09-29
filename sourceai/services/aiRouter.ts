// services/aiRouter.ts
import {
  generateText,
  AIRequestOptions,
  AIServiceError,
  AIAuthenticationError,
  AIProviderUnavailableError,
  AIRateLimitError,
  AIRequestTooLargeError,
  AITimeoutError,
  AIEmptyResponseError,
  AIMalformedResponseError,
  AINetworkError,
  AIPermissionError,
} from './aiService';

// ----------------------------
// Configuration
// ----------------------------

const PRIMARY_MODEL = process.env.OMNIROUTE_MODEL || 'Qwen3.6 27B';
const FALLBACK_MODELS = (process.env.OMNIROUTE_FALLBACK_MODELS || 'Qwen3 32B,GPT-OSS 120B,Llama 3.3 70B,Llama 4 Scout')
  .split(',')
  .map((m) => m.trim())
  .filter((m) => m.length > 0);
const MAX_RETRIES = Number(process.env.OMNIROUTE_MAX_RETRIES) || 2;
const MAX_PROMPT_CHARS = 8000; // conservative estimate ~2000 tokens

// ----------------------------
// Types
// ----------------------------

/**
 * All AI task types supported by the router.
 * Use this to enable future task‑specific model routing.
 */
export type AITask =
  | 'requirement_extraction'
  | 'search_planning'
  | 'supplier_extraction'
  | 'supplier_matching'
  | 'supplier_ranking'
  | 'reasoning'
  | 'summarization'
  | 'general';

export interface RankingResult {
  id: string;
  score: number;
  reason: string;
}

export interface RankingResponse {
  ranked: RankingResult[];
}

// ----------------------------
// Router: generate text with fallback
// ----------------------------

/**
 * Generate text using the primary model, with fallback chain.
 * Only the router controls fallback/retry logic.
 * The `task` parameter is reserved for future model‑specific routing.
 */
export async function generateTextWithFallback(
  prompt: string,
  options?: AIRequestOptions,
  task?: AITask,
  preferredModel?: string
): Promise<string> {
  // Determine model list: if preferredModel is given, try it first; else use primary.
  let models: string[];
  if (preferredModel) {
    const all = [preferredModel, PRIMARY_MODEL, ...FALLBACK_MODELS];
    models = Array.from(new Set(all));
  } else {
    models = [PRIMARY_MODEL, ...FALLBACK_MODELS];
  }

  models = models.filter((m) => m && m.trim().length > 0);
  models = Array.from(new Set(models));

  // Truncate prompt to avoid 413
  const truncatedPrompt = truncatePrompt(prompt);

  let lastError: Error | null = null;

  for (let i = 0; i < models.length; i++) {
    const model = models[i];
    const attempts = i === 0 ? MAX_RETRIES : 1;

    for (let attempt = 0; attempt < attempts; attempt++) {
      try {
        return await generateText(truncatedPrompt, model, options);
      } catch (err) {
        lastError = err as Error;
        if (isRetryableError(err) && attempt < attempts - 1) {
          const delay = Math.min(1000, Math.pow(2, attempt) * 200);
          await new Promise((r) => setTimeout(r, delay));
          continue;
        }
        break;
      }
    }
  }

  throw new AIServiceError(`All models failed. Last error: ${lastError?.message}`);
}

// ----------------------------
// Ranking engine
// ----------------------------

const MAX_SUPPLIERS_FOR_RANKING = 15;

/**
 * Rank suppliers using AI, with fallback to unranked order.
 * Returns the same array with ranking metadata attached.
 */
export async function rankSuppliers<T extends { id: string }>(
  suppliers: T[],
  userPrompt: string,
  options?: AIRequestOptions
): Promise<(T & { ranking: { score: number; reason: string } })[]> {
  if (!suppliers || suppliers.length === 0) {
    return suppliers as any;
  }

  const trimmed = suppliers.slice(0, MAX_SUPPLIERS_FOR_RANKING);

  const compact = trimmed.map((s) => ({
    id: s.id,
    name: (s as any).name || '',
    location: (s as any).location || (s as any).country || '',
    moq: (s as any).moq,
    price_min: (s as any).price_min,
  }));

  const prompt = `
Rank these suppliers based on relevance to the user request: "${userPrompt}"
Supplier data (compact):
${JSON.stringify(compact, null, 2)}
Return JSON: { "ranked": [ { "id": "...", "score": 0-100, "reason": "..." } ] }
`;

  try {
    const result = await generateTextWithFallback(
      prompt,
      { ...options, temperature: 0.2 },
      'supplier_ranking'
    );
    const parsed = parseRankingResponse(result, trimmed);

    const scoreMap = new Map(parsed.map((r) => [r.id, { score: r.score, reason: r.reason }]));

    const ranked = trimmed.map((s) => {
      const info = scoreMap.get(s.id);
      return {
        ...s,
        ranking: info
          ? { score: info.score, reason: info.reason }
          : { score: 50, reason: 'No AI ranking available' },
      };
    });

    ranked.sort((a, b) => (b.ranking?.score || 0) - (a.ranking?.score || 0));

    const remaining = suppliers.slice(trimmed.length);
    const defaultRanked = remaining.map((s) => ({
      ...s,
      ranking: { score: 50, reason: 'Not evaluated by AI' },
    }));

    return [...ranked, ...defaultRanked] as any;
  } catch {
    // Deterministic fallback: sort by available data completeness
    const fallbackRanked = suppliers.map((s) => {
      let score = 50;
      const hasMoq = (s as any).moq != null;
      const hasPrice = (s as any).price_min != null;
      const hasLocation = (s as any).country || (s as any).location;
      if (hasMoq) score += 15;
      if (hasPrice) score += 15;
      if (hasLocation) score += 10;
      return {
        ...s,
        ranking: { score, reason: 'Fallback ranking based on data completeness' },
      };
    });
    fallbackRanked.sort((a, b) => (b.ranking.score || 0) - (a.ranking.score || 0));
    return fallbackRanked as any;
  }
}

// ----------------------------
// Helpers
// ----------------------------

function isRetryableError(err: unknown): boolean {
  return (
    err instanceof AITimeoutError ||
    err instanceof AIProviderUnavailableError ||
    err instanceof AINetworkError
  );
}

function truncatePrompt(prompt: string): string {
  if (prompt.length > MAX_PROMPT_CHARS) {
    return prompt.slice(0, MAX_PROMPT_CHARS) + '... (truncated)';
  }
  return prompt;
}

function parseRankingResponse(raw: string, suppliers: { id: string }[]): RankingResult[] {
  let jsonStr = raw;
  const codeFence = raw.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (codeFence) {
    jsonStr = codeFence[1];
  } else {
    const match = raw.match(/\{[\s\S]*\}/);
    if (match) jsonStr = match[0];
  }

  let parsed: any;
  try {
    parsed = JSON.parse(jsonStr);
  } catch {
    throw new AIMalformedResponseError('Invalid JSON from ranking model');
  }

  if (!parsed.ranked || !Array.isArray(parsed.ranked)) {
    throw new AIMalformedResponseError('Missing "ranked" array');
  }

  const result: RankingResult[] = [];
  const seen = new Set<string>();
  for (const item of parsed.ranked) {
    const id = item.id;
    if (!id || typeof id !== 'string') continue;
    if (seen.has(id)) continue;
    seen.add(id);
    const score = typeof item.score === 'number' ? Math.min(100, Math.max(0, item.score)) : 50;
    const reason = typeof item.reason === 'string' ? item.reason : '';
    result.push({ id, score, reason });
  }

  // Ensure all supplier IDs are present
  for (const s of suppliers) {
    if (!seen.has(s.id)) {
      result.push({ id: s.id, score: 50, reason: 'No AI score provided' });
    }
  }

  return result;
}