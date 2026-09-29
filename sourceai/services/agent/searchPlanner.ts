import { Requirement } from '@/lib/types';
import { LIMITS } from '@/lib/limits';

export function planSearches(requirements: Requirement): string[] {
  const product = requirements.product || '';
  const location = requirements.location_hint || requirements.target_country || 'global';
  const queries = [
    `${product} supplier manufacturer ${location}`,
    `${product} OEM supplier ${location}`,
    `${product} wholesale ${location}`,
  ];
  if (requirements.customization_required) {
    queries.push(`custom ${product} manufacturer`);
  }
  if (requirements.certifications && requirements.certifications.length > 0) {
    queries.push(`${product} ${requirements.certifications[0]} certified`);
  }
  return Array.from(new Set(queries)).slice(0, LIMITS.MAX_SEARCH_QUERIES);
}