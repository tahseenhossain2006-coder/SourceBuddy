// lib/schemas.ts
import { z } from 'zod';

// ---------- Request ----------
export const AgentRequestSchema = z.object({
  prompt: z.string().min(1),
  quantity: z.number().positive().optional(),
  location: z.string().optional(),
});
export type AgentRequest = z.infer<typeof AgentRequestSchema>;

// ---------- Requirement ----------
export const RequirementSchema = z.object({
  product: z.string().min(1),
  category: z.string().optional(),
  quantity: z.number().positive().optional(),
  budget_per_unit: z.number().positive().optional(),
  total_budget: z.number().positive().optional(),
  currency: z.string().default('INR'),
  target_country: z.string().optional(),
  target_region: z.string().optional(),
  target_city: z.string().optional(),
  nearby_search: z.boolean().optional(),
  customization_required: z.boolean().optional(),
  material: z.string().optional(),
  color: z.string().optional(),
  size: z.string().optional(),
  certifications: z.array(z.string()).optional(),
  shipping_destination: z.string().optional(),
  required_delivery_time: z.string().optional(),
  keywords: z.array(z.string()).optional(),
  location_hint: z.string().optional(),
});
export type Requirement = z.infer<typeof RequirementSchema>;

// ---------- Ambiguity ----------
export const AmbiguitySchema = z.object({
  is_ambiguous: z.boolean(),
  missing_requirements: z.array(z.string()),
  questions: z.array(z.string()),
});
export type Ambiguity = z.infer<typeof AmbiguitySchema>;

// ---------- Supplier Extraction (LLM output) ----------
export const SupplierExtractionSchema = z.object({
  name: z.string().optional(),
  country: z.string().optional(),
  region: z.string().optional(),
  city: z.string().optional(),
  address: z.string().optional(),
  moq: z.number().nullable().optional(),
  moq_unit: z.string().optional(),
  price_min: z.number().nullable().optional(),
  price_max: z.number().nullable().optional(),
  price_currency: z.string().optional(),
  price_unit: z.string().optional(),
  product_categories: z.array(z.string()).optional(),
  materials: z.array(z.string()).optional(),
  customization_available: z.boolean().nullable().optional(),
  certifications: z.array(z.string()).optional(),
  response_rate: z.number().min(0).max(100).nullable().optional(),
  rating: z.number().min(0).max(5).nullable().optional(),
  years_in_business: z.number().nullable().optional(),
  contact_email: z.string().optional(),
  contact_phone: z.string().optional(),
});
export type SupplierExtraction = z.infer<typeof SupplierExtractionSchema>;

// ---------- Canonical Supplier ----------
export const SupplierSchema = z.object({
  id: z.string(),
  name: z.string(),
  website: z.string().url(),
  source: z.string(),
  source_url: z.string().url(),
  snippet: z.string(),
  description: z.string().optional(),
  country: z.string().nullable().optional(),
  region: z.string().nullable().optional(),
  city: z.string().nullable().optional(),
  address: z.string().nullable().optional(),
  moq: z.number().nullable().optional(),
  moq_unit: z.string().nullable().optional(),
  price_min: z.number().nullable().optional(),
  price_max: z.number().nullable().optional(),
  price_currency: z.string().nullable().optional(),
  price_unit: z.string().nullable().optional(),
  product_categories: z.array(z.string()).optional(),
  materials: z.array(z.string()).optional(),
  customization_available: z.boolean().nullable().optional(),
  certifications: z.array(z.string()).optional(),
  response_rate: z.number().nullable().optional(),
  rating: z.number().nullable().optional(),
  years_in_business: z.number().nullable().optional(),
  contact_email: z.string().nullable().optional(),
  contact_phone: z.string().nullable().optional(),
  evidence: z.object({
    source_url: z.string(),
    search_title: z.string(),
    search_snippet: z.string(),
    scraped_source: z.string(),
    extracted_at: z.string(),
    field_evidence: z.object({
      price: z.string().nullable(),
      moq: z.string().nullable(),
      location: z.string().nullable(),
      certifications: z.string().nullable(),
    }),
  }),
  discovered_at: z.string(),
  last_verified_at: z.string().optional(),
  ranking: z.object({
    score: z.number().min(0).max(100),
    reason: z.string(),
  }).optional(),
  missing_data: z.array(z.string()).optional(),
  confidence: z.number().min(0).max(100).optional(), // ✅ added
});
export type Supplier = z.infer<typeof SupplierSchema>;