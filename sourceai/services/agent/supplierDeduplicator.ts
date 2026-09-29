// services/agent/supplierDeduplicator.ts
import { Supplier } from '@/lib/types';

export function deduplicateSuppliers(suppliers: Supplier[]): Supplier[] {
  const map = new Map<string, Supplier>();
  for (const s of suppliers) {
    const domain = new URL(s.website).hostname.replace(/^www\./, '');
    if (map.has(domain)) {
      // Merge evidence: keep the one with more fields
      const existing = map.get(domain)!;
      // Simple merge: prefer non-null values and combine evidence
      const merged: Supplier = {
        ...existing,
        ...s,
        // keep more complete evidence
        evidence: {
          ...existing.evidence,
          ...s.evidence,
          field_evidence: {
            ...existing.evidence.field_evidence,
            ...s.evidence.field_evidence,
          },
        },
      };
      map.set(domain, merged);
    } else {
      map.set(domain, s);
    }
  }
  return Array.from(map.values());
}