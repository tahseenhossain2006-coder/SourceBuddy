/**
 * SourceBuddy backend types.
 *
 * Shapes here are transcribed from the backend source of truth:
 *   - sourceai/auth/models.py        (UserCreate, UserLogin, User, TokenResponse, RefreshRequest)
 *   - sourceai/llm/structured.py     (SupplierExtractionResult -> FullSearchSupplier)
 *   - sourceai/api/routes.py         (search envelopes, reduced supplier)
 *   - sourceai/storage/models.py     (Supplier ORM: moq/price are Text)
 *   - sourceai/rfq/models.py
 *   - sourceai/watchlists/models.py
 *   - sourceai/alerts/models.py
 *
 * If the backend changes, these types change. There is no separate
 * contract file — the backend code IS the contract.
 *
 * Two response conventions exist in the backend:
 *   - /auth/* endpoints return raw Pydantic models (no envelope).
 *   - /api/v1/search and /api/v1/search/{id} return
 *     { "status": "success", "data": <payload> } — an envelope.
 *     Callers of runSearch/getSearch must read `.data`.
 */

// ---------------------------------------------------------------------------
// Envelope
// ---------------------------------------------------------------------------

export interface SuccessEnvelope<T> {
  status: 'success';
  data: T;
}

export interface ErrorBody {
  detail: string;
}

export interface RateLimitErrorBody {
  detail: string;
  retry_after: number;
}

export interface ValidationIssue {
  type: string;
  loc: Array<string | number>;
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

export interface ValidationErrorBody {
  detail: ValidationIssue[];
}

// ---------------------------------------------------------------------------
// Auth  (sourceai/auth/models.py)
// ---------------------------------------------------------------------------

export interface UserCreate {
  email: string;
  password: string;
  full_name?: string | null;
}

export interface UserLogin {
  email: string;
  password: string;
}

/**
 * Backend UserResponse. `id` may be str or UUID; JSON always serialises
 * as a string, so this is `string` on the wire.
 */
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string; // ISO 8601
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer' | string;
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token: string;
}

// ---------------------------------------------------------------------------
// Search — request  (sourceai/api/routes.py SearchRequest)
// ---------------------------------------------------------------------------

export interface SearchRequest {
  query: string;
}

// ---------------------------------------------------------------------------
// Search — plan  (sourceai/search/planner.py SearchPlan)
// ---------------------------------------------------------------------------

export interface SearchEntities {
  product: string | null;
  quantity: number | null;
  quantity_unit: string | null;
  supplier_type: string | null;
  location: string | null;
  country: string | null;
}

export interface SearchConstraints {
  max_moq?: number;
  moq_unit?: string;
  // Additional constraint keys may be present; treat as open.
  [key: string]: unknown;
}

export interface SearchPlan {
  original_query: string;
  normalized_query: string;
  intent: string;
  entities: SearchEntities;
  constraints: SearchConstraints;
  keywords: string[];
  expanded_queries: string[];
  preferred_engines: string[];
  max_results: number;
  max_pages: number;
  crawl_enabled: boolean;
  extraction_enabled: boolean;
  verification_required: boolean;
  research_depth: number;
}

// ---------------------------------------------------------------------------
// Search — supplier schemas
//
// POST /api/v1/search returns the FULL supplier schema, built from
// sourceai/llm/structured.py SupplierExtractionResult plus the
// `research_stopped_reason` field injected by SearchAgent._finalize.
//
// GET /api/v1/search/{id} returns the REDUCED 9-field schema, built
// directly in sourceai/api/routes.py get_search().
//
// They are modelled as SEPARATE types. Never use one where the other
// is expected.
// ---------------------------------------------------------------------------

export interface FullSearchSupplier {
  supplier_name: string | null;
  company_name: string | null;
  website: string | null;
  domain: string | null;
  country: string | null;
  state: string | null;
  city: string | null;
  address: string | null;
  email: string | null;
  phone: string | null;
  whatsapp: string | null;
  supplier_type: string | null;
  supplier_type_signals: string[];
  manufacturer_status: string | null;
  products: string[];
  product_categories: string[];
  moq: number | null;
  price: number | null;
  currency: string | null;
  certifications: string[];
  years_in_business: number | null;
  factory_information: string | null;
  capacity: string | null;
  shipping_regions: string[];
  payment_terms: string | null;
  source_urls: string[];
  evidence: Record<string, unknown>;
  data_completeness: number;
  confidence: number;
  /**
   * Injected by SearchAgent._finalize on each supplier. One of:
   * "single_pass", "sufficient_evidence", "budget_exhausted (time)",
   * "budget_exhausted (searches)", "budget_exhausted (suppliers)",
   * "no_new_queries", "max_iterations_reached", "completed".
   */
  research_stopped_reason: string;
}

/**
 * Reduced supplier shape returned by GET /api/v1/search/{search_id}.
 *
 * `moq` and `price` are `Text` columns in sourceai/storage/models.py
 * (lines 111-112), and api/routes.py passes them through unchanged.
 * So on the wire they are always strings or null — never numbers.
 */
export interface ReducedSearchSupplier {
  company_name: string | null;
  website: string | null;
  country: string | null;
  location: string | null;
  moq: string | null;
  price: string | null;
  currency: string | null;
  evidence: Record<string, unknown>;
  created_at: string | null;
}

// ---------------------------------------------------------------------------
// Search — responses  (sourceai/api/routes.py)
// ---------------------------------------------------------------------------

export interface SearchData {
  search_id: string;
  request_id: string;
  query: string;
  plan: SearchPlan;
  suppliers: FullSearchSupplier[];
  answer: string;
  research_stopped_reason: string;
  /** One entry per supplier: that supplier's evidence dict. */
  evidence: Record<string, unknown>[];
}

export type SearchResponse = SuccessEnvelope<SearchData>;

export interface SearchDetailData {
  search_id: string;
  query: string;
  plan: SearchPlan;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  suppliers: ReducedSearchSupplier[];
}

export type SearchDetailResponse = SuccessEnvelope<SearchDetailData>;

// ---------------------------------------------------------------------------
// Watchlists  (sourceai/watchlists/models.py)
//
// Note: the backend file defines WatchlistResponse twice; the second
// definition wins in Python. Only the second shape is modelled here.
// ---------------------------------------------------------------------------

export type WatchType = 'supplier' | 'product' | 'price' | 'moq' | 'rfq';

export interface WatchlistCreate {
  type: WatchType;
  target_id: string;
  condition?: string | null;
}

export interface Watchlist {
  id: string;
  user_id: string;
  type: WatchType;
  target_id: string;
  condition: string | null;
  last_hash: string | null;
  last_checked: string | null;
  created_at: string;
}

export interface WatchlistCheckResult {
  watchlist_id: string;
  changed: boolean;
  alert_created: boolean;
  last_hash: string;
  checked_at: string;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Alerts  (sourceai/alerts/models.py)
// ---------------------------------------------------------------------------

export type AlertType =
  | 'price_change'
  | 'moq_change'
  | 'supplier_change'
  | 'new_supplier'
  | 'quote_received'
  | 'rfq_response';

export interface Alert {
  id: string;
  user_id: string;
  type: AlertType;
  message: string;
  data: Record<string, unknown>;
  read: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// RFQ  (sourceai/rfq/models.py)
// ---------------------------------------------------------------------------

export type RFQStatus =
  | 'draft'
  | 'approved'
  | 'sending'
  | 'sent'
  | 'waiting'
  | 'partial_response'
  | 'completed'
  | 'cancelled';

export interface RFQItem {
  product_name: string;
  quantity: number;
  unit: string;
  specifications?: Record<string, unknown> | null;
  target_price?: number | null;
  target_moq?: number | null;
}

export interface RFQCreate {
  title: string;
  description?: string | null;
  items: RFQItem[];
  /** Supplier IDs. */
  suppliers: string[];
  deadline?: string | null;
  delivery_location?: string | null;
  currency?: string;
}

export interface RFQ {
  id: string;
  user_id: string;
  title: string;
  status: RFQStatus;
  items: RFQItem[];
  suppliers: string[];
  deadline: string | null;
  created_at: string;
  updated_at: string;
  sent_at: string | null;
  completed_at: string | null;
}

/**
 * Client-side state-machine hint. NOT enforced by the backend —
 * sourceai/rfq/routes.py passes `status` straight to the service with
 * no transition validation. Treat this as UI guidance only. Verify
 * against sourceai/rfq/service.py before relying on it.
 */
export const RFQ_TRANSITIONS: Record<RFQStatus, RFQStatus[]> = {
  draft: ['approved', 'cancelled'],
  approved: ['sending', 'cancelled'],
  sending: ['sent', 'cancelled'],
  sent: ['waiting', 'cancelled'],
  waiting: ['partial_response', 'completed', 'cancelled'],
  partial_response: ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
};