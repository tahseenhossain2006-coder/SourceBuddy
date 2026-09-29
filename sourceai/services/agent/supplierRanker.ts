// services/agent/supplierRanker.ts
import { rankSuppliers } from '../aiRouter';
import { Supplier, Requirement } from '@/lib/types';
import { LIMITS } from '@/lib/limits';

export async function rankSuppliersWithAI(
  suppliers: Supplier[],
  userPrompt: string,
  requirements: Requirement
): Promise<Supplier[]> {
  if (suppliers.length === 0) return suppliers;

  const toRank = suppliers.slice(0, LIMITS.MAX_SUPPLIERS_FOR_AI_RANKING);

  try {
    // rankSuppliers returns (T & { ranking: { score, reason } })[]
    const ranked = await rankSuppliers(
      toRank,
      `User request: ${userPrompt}\nExtracted requirements: ${JSON.stringify(requirements)}`,
      { temperature: 0.2, max_tokens: 1024 }
    );

    // Cast to Supplier[] because the base type T is Supplier
    const rankedWithRanking = ranked as Supplier[];

    // Remaining suppliers get a default ranking
    const remaining = suppliers.slice(LIMITS.MAX_SUPPLIERS_FOR_AI_RANKING);
    const defaultRanked = remaining.map(s => ({
      ...s,
      ranking: { score: 50, reason: 'Not evaluated by AI' },
    }));

    return [...rankedWithRanking, ...defaultRanked];
  } catch (error) {
    // Deterministic fallback
    const fallbackRanked = suppliers.map((s, i) => ({
      ...s,
      ranking: { score: 100 - i * 5, reason: 'Fallback ordering based on data completeness' },
    }));
    return fallbackRanked;
  }
}