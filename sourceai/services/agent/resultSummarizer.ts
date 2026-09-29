// services/agent/resultSummarizer.ts
import { generateTextWithFallback } from '../aiRouter';
import { Supplier, Requirement } from '@/lib/types';

export async function generateResultSummary(suppliers: Supplier[], requirements: Requirement): Promise<string> {
  if (suppliers.length === 0) return 'No suppliers found. Try adjusting your search criteria.';

  const top = suppliers.slice(0, 3).map(s =>
    `${s.name} (score: ${s.ranking?.score || 0}) - ${s.ranking?.reason || ''}`
  ).join('\n');

  const prompt = `
Summarize the sourcing results for the user request: "${requirements.product || 'unspecified product'}"
Top suppliers:
${top}
Total suppliers found: ${suppliers.length}

Provide a concise summary (2-3 sentences) highlighting the best options and any missing info.
`;
  try {
    const result = await generateTextWithFallback(
      prompt,
      { temperature: 0.3, max_tokens: 256 },
      'summarization'
    );
    return result.trim();
  } catch {
    // Fallback deterministic summary
    return `Found ${suppliers.length} suppliers. Top match: ${suppliers[0]?.name || 'None'}. Check details below.`;
  }
}