// lib/json.ts
import { AIMalformedResponseError } from '@/services/aiService';

export function extractJSON(text: string): string {
  // Try code fences first
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (fenceMatch) {
    return fenceMatch[1].trim();
  }
  // Try raw JSON object
  const braceMatch = text.match(/\{[\s\S]*\}/);
  if (braceMatch) {
    return braceMatch[0];
  }
  // If no JSON found, return as is (will fail parse)
  return text;
}

export function safeParseJSON<T>(text: string): T {
  const cleaned = extractJSON(text);
  try {
    return JSON.parse(cleaned);
  } catch (e) {
    throw new AIMalformedResponseError(`Invalid JSON: ${e.message}`);
  }
}