// services/agent/missingDataDetector.ts
import { Supplier } from '@/lib/types';

const FIELDS_TO_CHECK = [
  'moq',
  'price_min',
  'price_currency',
  'certifications',
  'country',
  'contact_email',
  'customization_available',
  'rating',
  'response_rate',
];

export function detectMissingData(supplier: Supplier): string[] {
  const missing: string[] = [];
  for (const field of FIELDS_TO_CHECK) {
    const value = (supplier as any)[field];
    if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) {
      missing.push(field.toUpperCase());
    }
  }
  return missing;
}