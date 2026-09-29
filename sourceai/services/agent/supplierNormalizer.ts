// services/agent/supplierNormalizer.ts
import { Supplier, SupplierExtraction } from '@/lib/types';
import crypto from 'crypto';

export function normalizeSupplier(
  extracted: SupplierExtraction,
  searchResult: { title: string; url: string; snippet: string } | undefined,
  url: string
): Supplier {
  const id = crypto.createHash('sha256').update(url).digest('hex').slice(0, 16);
  const now = new Date().toISOString();
  return {
    id,
    name: extracted.name || 'Unknown',
    website: url,
    source: 'duckduckgo',
    source_url: url,
    snippet: searchResult?.snippet || '',
    description: searchResult?.title || '',
    country: extracted.country || null,
    region: extracted.region || null,
    city: extracted.city || null,
    address: extracted.address || null,
    moq: extracted.moq ?? null,
    moq_unit: extracted.moq_unit || null,
    price_min: extracted.price_min ?? null,
    price_max: extracted.price_max ?? null,
    price_currency: extracted.price_currency || null,
    price_unit: extracted.price_unit || null,
    product_categories: extracted.product_categories || [],
    materials: extracted.materials || [],
    customization_available: extracted.customization_available ?? null,
    certifications: extracted.certifications || [],
    response_rate: extracted.response_rate ?? null,
    rating: extracted.rating ?? null,
    years_in_business: extracted.years_in_business ?? null,
    contact_email: extracted.contact_email || null,
    contact_phone: extracted.contact_phone || null,
    evidence: {
      source_url: url,
      search_title: searchResult?.title || '',
      search_snippet: searchResult?.snippet || '',
      scraped_source: 'html',
      extracted_at: now,
      field_evidence: {
        price: extracted.price_min ? `${extracted.price_min} ${extracted.price_currency || ''}` : null,
        moq: extracted.moq ? String(extracted.moq) : null,
        location: [extracted.country, extracted.region, extracted.city].filter(Boolean).join(', ') || null,
        certifications: extracted.certifications?.join(', ') || null,
      },
    },
    discovered_at: now,
    last_verified_at: now,
  };
}