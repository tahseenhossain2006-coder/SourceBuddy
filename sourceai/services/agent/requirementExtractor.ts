import { generateTextWithFallback } from '../aiRouter';
import { RequirementSchema, AmbiguitySchema, Requirement, Ambiguity } from '@/lib/types';
import { safeParseJSON } from '@/lib/json';

export async function extractRequirements(prompt: string): Promise<Requirement> {
  const systemPrompt = `
You are a sourcing assistant. Extract structured requirements from the user's natural language request.

Return a JSON object with the following fields (all optional except product):
- product: string (required)
- category: string or null
- quantity: number or null
- budget_per_unit: number or null
- total_budget: number or null
- currency: string (default "INR")
- target_country: string or null
- target_region: string or null
- target_city: string or null
- nearby_search: boolean or null
- customization_required: boolean or null
- material: string or null
- color: string or null
- size: string or null
- certifications: array of strings or null
- shipping_destination: string or null
- required_delivery_time: string or null
- keywords: array of strings or null

Do not invent values. If not mentioned, set to null or omit.
User request: "${prompt}"
`;
  const result = await generateTextWithFallback(
    systemPrompt,
    { temperature: 0.1, max_tokens: 1024 },
    'requirement_extraction'
  );
  const parsed = safeParseJSON(result);
  return RequirementSchema.parse(parsed);
}

export async function detectAmbiguity(prompt: string, requirements: Requirement): Promise<Ambiguity> {
  const systemPrompt = `
Given the user request and extracted requirements, determine if the request is ambiguous.
Identify missing critical requirements (e.g., product, quantity, budget, location) and suggest clarifying questions.

User request: "${prompt}"
Extracted requirements: ${JSON.stringify(requirements, null, 2)}

Return JSON: { "is_ambiguous": boolean, "missing_requirements": string[], "questions": string[] }
`;
  const result = await generateTextWithFallback(
    systemPrompt,
    { temperature: 0.2, max_tokens: 512 },
    'general'
  );
  const parsed = safeParseJSON(result);
  return AmbiguitySchema.parse(parsed);
}